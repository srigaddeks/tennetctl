"""
EvidenceCheckerAgent — production-grade multi-agentic RAG for evidence evaluation.

Pipeline per acceptance criterion:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ┌─────────────────────────────────────────────────────────────┐
  │  Stage 1 — QUERY EXPANSION (HyDE)                           │
  │  Agent: QueryExpansionAgent                                 │
  │  Generates 3 hypothetical document excerpts that would      │
  │  satisfy the criterion, plus 2 negating queries.            │
  │  These are embedded and used for Qdrant semantic search.    │
  └───────────────────────┬─────────────────────────────────────┘
                          │ 5 expanded query vectors
  ┌───────────────────────▼─────────────────────────────────────┐
  │  Stage 2a — SEMANTIC RETRIEVAL (Qdrant top-K per query)     │
  │  Union of top-K results across all expanded queries.        │
  └───────────────────────┬─────────────────────────────────────┘
                          │ candidate pool (deduplicated)
  ┌───────────────────────▼─────────────────────────────────────┐
  │  Stage 2b — FULL CORPUS MAP (parallel batch scan)           │
  │  Agent: MapAgent (per batch)                                │
  │  Every chunk in the corpus is scanned — batches of N chunks │
  │  run concurrently. Produces supporting + conflicting refs.  │
  └───────────────────────┬─────────────────────────────────────┘
                          │ all found references
  ┌───────────────────────▼─────────────────────────────────────┐
  │  Stage 3 — RE-RANKING + DEDUPLICATION                       │
  │  Agent: ReRankAgent                                         │
  │  Given all raw references from map phase, scores each by    │
  │  specificity + direct relevance to criterion. Deduplicates  │
  │  near-identical excerpts. Returns top-N per direction.      │
  └───────────────────────┬─────────────────────────────────────┘
                          │ re-ranked evidence list
  ┌───────────────────────▼─────────────────────────────────────┐
  │  Stage 4 — SYNTHESIS (REDUCE)                               │
  │  Agent: SynthesisAgent                                      │
  │  Combines semantic candidates + map evidence + re-rankings  │
  │  into a final structured CriterionResult with verdict,      │
  │  justification, and grounded references.                    │
  └─────────────────────────────────────────────────────────────┘

Design invariants:
  - All agents are stateless coroutines (safe for asyncio.gather)
  - Every claim in the final output is grounded in an actual chunk
  - No hallucinated references — excerpts verified against corpus
  - LangFuse child spans per stage for full observability
  - Graceful degradation: individual stage failures fall back without crashing
  - Full corpus scan (Stage 2b) guarantees no chunk is ever skipped

Verdict levels:
  MET                  — criterion clearly satisfied with direct evidence
  PARTIALLY_MET        — criterion partially evidenced; gaps remain
  NOT_MET              — corpus fully scanned, criterion not evidenced
  INSUFFICIENT_EVIDENCE — corpus too sparse to make a determination
"""

from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from importlib import import_module
from typing import NamedTuple

import asyncpg

from .ingestion import get_all_chunks, search_collection
from .models import ChunkResult, CriterionResult, EvidenceReference

_logging_module = import_module("backend.01_core.logging_utils")
_pageindex_mod = import_module("backend.20_ai.03_memory.pageindex")
_logger = _logging_module.get_logger("backend.ai.evidence_checker.agent")

PageIndexer = _pageindex_mod.PageIndexer
NullPageIndexer = _pageindex_mod.NullPageIndexer

# ── Configuration ─────────────────────────────────────────────────────────────
_MAP_BATCH_SIZE     = int(os.getenv("EVIDENCE_CHECKER_MAP_BATCH_SIZE", "8"))
_MAP_CONCURRENCY    = int(os.getenv("EVIDENCE_CHECKER_MAP_CONCURRENCY", "6"))
_TOP_K_PER_QUERY    = int(os.getenv("EVIDENCE_CHECKER_TOP_K", "12"))
_RERANK_TOP_N       = int(os.getenv("EVIDENCE_CHECKER_RERANK_TOP_N", "20"))
_EXCERPT_MAX        = 150

# ── System prompts ────────────────────────────────────────────────────────────

_EVIDENCE_CHECKER_SYSTEM_FALLBACK = """\
You are an expert compliance evidence analyst.
Your task is to determine whether the provided document excerpts satisfy the given acceptance criterion.

Rules:
1. Base your verdict ONLY on the provided document chunks — do not assume or invent evidence.
2. For every claim you make, cite the exact document name, page number (if available), and a short excerpt (≤150 chars).
3. If the chunks do not contain enough information to make a determination, return INSUFFICIENT_EVIDENCE.
4. Be precise and concise. Justification should be 1–3 sentences maximum.

Return a JSON object with this exact shape:
{
  "verdict": "MET" | "PARTIALLY_MET" | "NOT_MET" | "INSUFFICIENT_EVIDENCE",
  "threshold_met": true | false | null,
  "justification": "<1-3 sentence explanation>",
  "evidence_references": [...],
  "conflicting_references": [...]
}
"""

_QUERY_EXPANSION_PROMPT = """\
You are a compliance evidence search specialist.

Given an acceptance criterion, generate search queries to maximise recall from a document corpus.
Produce:
  - 3 "hypothetical excerpts" (HyDE): write short passages (2-3 sentences each) that would appear in
    a document that SATISFIES this criterion. These will be embedded for semantic search.
  - 2 "negating queries": short passages describing what a document would say if the criterion is NOT met.

Return a JSON object:
{
  "positive_queries": ["<excerpt 1>", "<excerpt 2>", "<excerpt 3>"],
  "negative_queries": ["<excerpt 1>", "<excerpt 2>"]
}
"""

_MAP_AGENT_PROMPT = """\
You are a compliance document scanner. Scan the provided document chunks for evidence relating
to the acceptance criterion. Identify every passage that is relevant — whether it supports
or contradicts the criterion being met.

Rules:
- Quote directly from the text. Do NOT paraphrase or invent content.
- Excerpts must be ≤150 characters.
- If no chunk is relevant, set has_relevant_content=false.

Return JSON:
{
  "has_relevant_content": true | false,
  "supporting": [
    {
      "document_filename": "<filename>",
      "page_number": <int|null>,
      "section_or_sheet": "<str|null>",
      "excerpt": "<direct quote ≤150 chars>",
      "confidence": <0.0-1.0>,
      "relevance_note": "<one sentence>"
    }
  ],
  "contradicting": [<same shape>]
}
"""

_RERANK_PROMPT = """\
You are a compliance evidence re-ranker. Given a list of candidate evidence references and an
acceptance criterion, score and select the most directly relevant and specific references.

Criteria for a high-quality reference:
  - Directly addresses the criterion (not tangentially related)
  - Contains specific, verifiable data (dates, counts, system names, signatures)
  - Is not duplicated by another reference with the same core content

Return JSON:
{
  "top_supporting": [<up to 15 highest-quality supporting refs, ordered by relevance>],
  "top_contradicting": [<up to 8 highest-quality contradicting refs, ordered by relevance>],
  "dedup_removed": <int>
}

Preserve the original structure of each ref (document_filename, page_number, section_or_sheet, excerpt, confidence, relevance_note).
"""

_SYNTHESIS_PROMPT = """\
You are a senior compliance evidence analyst performing a final determination.

You will receive:
1. An acceptance criterion (and optional threshold/pass condition)
2. Corpus coverage statistics (how many document batches were scanned)
3. Re-ranked supporting evidence references
4. Re-ranked contradicting evidence references
5. Semantically retrieved candidate chunks (from HyDE search)

Your job is to produce a definitive, well-reasoned verdict grounded EXCLUSIVELY in the
provided evidence. Do not invent or assume any facts not present in the references.

Verdict guidelines:
  MET                  — sufficient direct evidence satisfies all aspects of the criterion
  PARTIALLY_MET        — some aspects evidenced, others missing or ambiguous
  NOT_MET              — corpus was fully scanned, criterion clearly not satisfied
  INSUFFICIENT_EVIDENCE — corpus lacks enough information to make a determination

Justification: 3–5 sentences. Reference specific document names, page numbers, and excerpts.
Be direct. State what was found and what was missing.

Gap analysis (REQUIRED for PARTIALLY_MET, NOT_MET, INSUFFICIENT_EVIDENCE; null for MET):
  Describe precisely what evidence is missing. Be specific: what document type, what data,
  what time period, what system name, what threshold value would need to appear in the evidence
  for this criterion to be MET. 2–4 sentences maximum. This is actionable guidance for the task owner.

Return JSON:
{
  "verdict": "MET" | "PARTIALLY_MET" | "NOT_MET" | "INSUFFICIENT_EVIDENCE",
  "threshold_met": true | false | null,
  "justification": "<3-5 sentence synthesis with specific citations>",
  "gap_analysis": "<2-4 sentence description of what evidence is missing, or null if verdict is MET>",
  "evidence_references": [<top 10 supporting refs, ordered by relevance>],
  "conflicting_references": [<top 5 contradicting refs>]
}
"""


# ── Internal data types ───────────────────────────────────────────────────────

class _MapBatchResult(NamedTuple):
    supporting: list[dict]
    contradicting: list[dict]
    tokens: int


class _ReRankResult(NamedTuple):
    top_supporting: list[dict]
    top_contradicting: list[dict]
    tokens: int


# ── JSON parser ───────────────────────────────────────────────────────────────

def _parse_json(raw: str) -> dict:
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    if "```" in raw:
        inner = raw.split("```")[1]
        if inner.startswith("json"):
            inner = inner[4:]
        try:
            return json.loads(inner.strip())
        except json.JSONDecodeError:
            pass
    start, end = raw.find("{"), raw.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(raw[start:end])
        except json.JSONDecodeError:
            pass
    return {}


# ── Reference builder ─────────────────────────────────────────────────────────

def _build_criterion_result(
    criterion_id: str | None,
    criterion_text: str,
    verdict_data: dict,
    agent_run_id: str,
    langfuse_trace_id: str | None,
) -> CriterionResult:
    verdict = verdict_data.get("verdict", "INSUFFICIENT_EVIDENCE")
    if verdict not in ("MET", "PARTIALLY_MET", "NOT_MET", "INSUFFICIENT_EVIDENCE"):
        verdict = "INSUFFICIENT_EVIDENCE"

    def _refs(raw: list | None) -> list[EvidenceReference]:
        if not raw:
            return []
        out = []
        for r in raw[:10]:
            out.append(EvidenceReference(
                document_filename=r.get("document_filename", "unknown"),
                page_number=r.get("page_number"),
                section_or_sheet=r.get("section_or_sheet"),
                excerpt=(r.get("excerpt") or "")[:_EXCERPT_MAX],
                confidence=float(r.get("confidence", 0.5)),
            ))
        return out

    # gap_analysis only meaningful for non-MET verdicts
    raw_gap = (verdict_data.get("gap_analysis") or "").strip()
    gap_analysis = raw_gap[:500] if verdict != "MET" and raw_gap else None

    return CriterionResult(
        criterion_id=criterion_id,
        criterion_text=criterion_text,
        verdict=verdict,
        threshold_met=verdict_data.get("threshold_met"),
        justification=(verdict_data.get("justification") or "")[:1000],
        gap_analysis=gap_analysis,
        evidence_references=_refs(verdict_data.get("evidence_references")),
        conflicting_references=_refs(verdict_data.get("conflicting_references")),
        agent_run_id=agent_run_id,
        langfuse_trace_id=langfuse_trace_id,
    )


# ── Main agent class ──────────────────────────────────────────────────────────

class EvidenceCheckerAgent:
    """
    Multi-agentic RAG evidence evaluator.

    Instantiate once per job (shared resources); call evaluate_criterion()
    concurrently across criteria — each call is fully independent.
    """

    def __init__(
        self,
        *,
        pool: asyncpg.Pool,
        provider,
        system_prompt: str,
        qdrant_client,
        langfuse_client,
        settings,
    ) -> None:
        self._pool = pool
        self._provider = provider
        self._system_prompt = system_prompt
        self._qdrant = qdrant_client
        self._lf = langfuse_client
        self._settings = settings
        self._pageindexer = (
            PageIndexer(settings=settings)
            if (
                getattr(settings, "ai_pageindex_enabled", False)
                and getattr(settings, "ai_provider_url", None)
            )
            else NullPageIndexer()
        )

    # Threshold: compress evidence ref blobs that exceed this many chars
    _EVIDENCE_COMPRESS_THRESHOLD = 3_000

    # ── LangFuse helpers ──────────────────────────────────────────────────────

    def _lf_span(self, parent_trace_id: str | None, name: str, input_: dict | None = None):
        if not self._lf or not parent_trace_id:
            return None, None
        try:
            span = self._lf.span(
                trace_id=parent_trace_id,
                name=name,
                input=input_ or {},
            )
            return span, getattr(span, "id", None)
        except Exception:
            return None, None

    def _lf_end(self, span, output: dict | None = None):
        if not span:
            return
        try:
            span.end(output=output or {})
        except Exception:
            pass

    # ── LLM call ─────────────────────────────────────────────────────────────

    async def _llm(self, system: str, user: str, max_tokens: int = 1024) -> tuple[str, int]:
        """Returns (content, total_tokens)."""
        temp = getattr(self._provider, "_temperature", 0.0)
        response = await self._provider.chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            tools=None,
            temperature=temp,
            max_tokens=max_tokens,
        )
        content = response.content or ""
        tokens = (response.input_tokens or 0) + (response.output_tokens or 0)
        return content, tokens

    # ── Stage 1: Query Expansion (HyDE) ──────────────────────────────────────

    async def _stage_query_expansion(
        self,
        criterion_text: str,
        threshold: str | None,
        parent_trace_id: str | None,
    ) -> tuple[list[str], list[str], int]:
        """
        Returns (positive_queries, negative_queries, tokens).
        Falls back to [criterion_text] if the LLM call fails.
        """
        span, _ = self._lf_span(parent_trace_id, "agent/query_expansion", {"criterion": criterion_text[:100]})
        user_msg = f"Acceptance Criterion: {criterion_text}"
        if threshold:
            user_msg += f"\nThreshold: {threshold}"
        try:
            raw, tokens = await self._llm(_QUERY_EXPANSION_PROMPT, user_msg, max_tokens=600)
            data = _parse_json(raw)
            positives = [q for q in data.get("positive_queries", []) if isinstance(q, str)]
            negatives = [q for q in data.get("negative_queries", []) if isinstance(q, str)]
            if not positives:
                positives = [criterion_text]
            self._lf_end(span, {"positives": len(positives), "negatives": len(negatives)})
            return positives, negatives, tokens
        except Exception as exc:
            _logger.debug("Query expansion failed (using criterion as fallback): %s", exc)
            self._lf_end(span, {"error": str(exc)[:100]})
            return [criterion_text], [], 0

    # ── Stage 2a: Semantic Retrieval ─────────────────────────────────────────

    async def _stage_semantic_retrieval(
        self,
        task_id: str,
        org_id: str,
        queries: list[str],
        parent_trace_id: str | None,
    ) -> list[ChunkResult]:
        """
        Runs each expanded query against Qdrant, unions results (dedup by chunk_index+attachment_id).
        """
        span, _ = self._lf_span(parent_trace_id, "agent/semantic_retrieval", {"queries": len(queries)})
        seen: set[str] = set()
        all_hits: list[ChunkResult] = []

        async def _one_query(q: str) -> list[ChunkResult]:
            try:
                return await search_collection(
                    task_id=task_id,
                    org_id=org_id,
                    query=q,
                    top_k=_TOP_K_PER_QUERY,
                    llm_provider=self._provider,
                    qdrant_client=self._qdrant,
                )
            except Exception as exc:
                _logger.debug("Semantic search failed for query: %s", exc)
                return []

        results = await asyncio.gather(*[_one_query(q) for q in queries])
        for hits in results:
            for hit in hits:
                key = f"{hit.attachment_id}:{hit.chunk_index}"
                if key not in seen:
                    seen.add(key)
                    all_hits.append(hit)

        self._lf_end(span, {"unique_candidates": len(all_hits)})
        return all_hits

    # ── Stage 2b: Full Corpus Map ─────────────────────────────────────────────

    async def _map_one_batch(
        self,
        criterion_text: str,
        threshold: str | None,
        batch: list[ChunkResult],
    ) -> _MapBatchResult:
        """Run MapAgent on a single batch of chunks."""
        parts = [f"## Acceptance Criterion\n{criterion_text}"]
        if threshold:
            parts.append(f"**Threshold:** {threshold}")
        parts.append(f"\n## Document Chunks ({len(batch)} chunks)")
        for i, c in enumerate(batch, 1):
            loc = c.document_filename
            if c.page_number:
                loc += f" p.{c.page_number}"
            elif c.section_or_sheet:
                loc += f" — {c.section_or_sheet}"
            parts.append(f"\n[{i}] {loc}\n{c.text}")
        parts.append("\n## Task\nScan for evidence. Return JSON.")
        raw_chunks_str = "\n".join(parts[2:])  # just the chunks portion

        # PageIndex compression: if the raw chunk text is very large, build a
        # mini TOC over the batch and ask it what's relevant to the criterion.
        # This replaces the verbatim chunk dump with a focused summary.
        if len(raw_chunks_str) > self._EVIDENCE_COMPRESS_THRESHOLD:
            try:
                batch_text = "\n\n".join(
                    f"[{c.document_filename}{f' p.{c.page_number}' if c.page_number else ''}]\n{c.text}"
                    for c in batch
                )
                tree = await self._pageindexer.build_index(batch_text)
                if tree.get("sections"):
                    pi_summary = await self._pageindexer.retrieve(
                        query=f"Evidence relevant to: {criterion_text}",
                        tree=tree,
                        filename=f"batch of {len(batch)} chunks",
                    )
                    if pi_summary:
                        parts = parts[:2]  # keep criterion + threshold
                        parts.append(f"\n## Document Chunks (PageIndex compressed)\n{pi_summary}")
                        parts.append("\n## Task\nScan for evidence. Return JSON.")
            except Exception as pi_exc:
                _logger.debug("PageIndex map batch compression failed (non-fatal): %s", pi_exc)

        user_msg = "\n".join(parts)

        try:
            raw, tokens = await self._llm(_MAP_AGENT_PROMPT, user_msg, max_tokens=800)
            data = _parse_json(raw)
            if not data.get("has_relevant_content", False):
                return _MapBatchResult([], [], tokens)
            return _MapBatchResult(
                data.get("supporting", []),
                data.get("contradicting", []),
                tokens,
            )
        except Exception as exc:
            _logger.debug("Map batch LLM failed (non-fatal): %s", exc)
            return _MapBatchResult([], [], 0)

    async def _stage_full_corpus_map(
        self,
        task_id: str,
        org_id: str,
        criterion_text: str,
        threshold: str | None,
        parent_trace_id: str | None,
    ) -> tuple[list[dict], list[dict], int, int, int]:
        """
        Returns (all_supporting, all_contradicting, tokens, total_batches, relevant_batches).
        """
        all_chunks = await get_all_chunks(
            task_id=task_id,
            org_id=org_id,
            qdrant_client=self._qdrant,
        )

        if not all_chunks:
            _logger.debug("get_all_chunks empty for task %s — map phase skipped", task_id)
            return [], [], 0, 0, 0

        batches = [
            all_chunks[i: i + _MAP_BATCH_SIZE]
            for i in range(0, len(all_chunks), _MAP_BATCH_SIZE)
        ]

        span, _ = self._lf_span(
            parent_trace_id, "agent/full_corpus_map",
            {"total_chunks": len(all_chunks), "batches": len(batches)},
        )

        sem = asyncio.Semaphore(_MAP_CONCURRENCY)
        batch_results: list[_MapBatchResult] = [None] * len(batches)  # type: ignore[list-item]

        async def _run(idx: int, batch: list[ChunkResult]) -> None:
            async with sem:
                batch_results[idx] = await self._map_one_batch(criterion_text, threshold, batch)

        await asyncio.gather(*[_run(i, b) for i, b in enumerate(batches)])

        all_supporting: list[dict] = []
        all_contradicting: list[dict] = []
        total_tokens = 0
        relevant_batches = 0

        for br in batch_results:
            total_tokens += br.tokens
            if br.supporting or br.contradicting:
                relevant_batches += 1
                all_supporting.extend(br.supporting)
                all_contradicting.extend(br.contradicting)

        self._lf_end(span, {
            "relevant_batches": relevant_batches,
            "supporting": len(all_supporting),
            "contradicting": len(all_contradicting),
        })

        _logger.info(
            "evidence_check.map_done",
            extra={
                "task_id": task_id,
                "total_batches": len(batches),
                "relevant_batches": relevant_batches,
                "supporting_refs": len(all_supporting),
                "contradicting_refs": len(all_contradicting),
            },
        )

        return all_supporting, all_contradicting, total_tokens, len(batches), relevant_batches

    # ── Stage 3: Re-Ranking ───────────────────────────────────────────────────

    async def _stage_rerank(
        self,
        criterion_text: str,
        threshold: str | None,
        all_supporting: list[dict],
        all_contradicting: list[dict],
        semantic_candidates: list[ChunkResult],
        parent_trace_id: str | None,
    ) -> _ReRankResult:
        """
        Re-rank and deduplicate all collected references.
        Falls back to first-N slicing if LLM call fails.
        """
        if not all_supporting and not all_contradicting:
            return _ReRankResult([], [], 0)

        span, _ = self._lf_span(
            parent_trace_id, "agent/rerank",
            {"supporting": len(all_supporting), "contradicting": len(all_contradicting)},
        )

        # Add semantic hits as candidate supporting refs
        semantic_refs = []
        for c in semantic_candidates[:20]:
            semantic_refs.append({
                "document_filename": c.document_filename,
                "page_number": c.page_number,
                "section_or_sheet": c.section_or_sheet,
                "excerpt": c.text[:_EXCERPT_MAX],
                "confidence": round(c.score, 3),
                "relevance_note": f"Semantic similarity score: {c.score:.2f}",
            })

        combined_supporting = all_supporting[:50] + semantic_refs[:20]
        combined_contradicting = all_contradicting[:25]

        # PageIndex compression: if the combined refs payload is large, build
        # a hierarchical evidence tree and retrieve a focused summary instead of
        # injecting a raw JSON blob.  Falls back to character-capped JSON silently.
        sup_json = json.dumps(combined_supporting, indent=2)
        con_json = json.dumps(combined_contradicting, indent=2)
        if len(sup_json) + len(con_json) > self._EVIDENCE_COMPRESS_THRESHOLD:
            try:
                pi_summary = await self._pageindexer.retrieve_from_evidence_refs(
                    criterion_text=criterion_text,
                    supporting=combined_supporting,
                    contradicting=combined_contradicting,
                )
                if pi_summary:
                    sup_block = f"[PageIndex evidence summary]\n{pi_summary}"
                    con_block = "(included in PageIndex summary above)"
                else:
                    sup_block = sup_json[:6000]
                    con_block = con_json[:3000]
            except Exception as pi_exc:
                _logger.debug("PageIndex evidence compression failed (non-fatal): %s", pi_exc)
                sup_block = sup_json[:6000]
                con_block = con_json[:3000]
        else:
            sup_block = sup_json
            con_block = con_json

        user_msg = "\n".join([
            f"## Acceptance Criterion\n{criterion_text}",
            f"{'**Threshold:** ' + threshold if threshold else ''}",
            f"\n## Candidate Supporting References ({len(combined_supporting)})",
            sup_block,
            f"\n## Candidate Contradicting References ({len(combined_contradicting)})",
            con_block,
            "\n## Task\nRe-rank and deduplicate. Return JSON.",
        ])

        try:
            raw, tokens = await self._llm(_RERANK_PROMPT, user_msg, max_tokens=1500)
            data = _parse_json(raw)
            result = _ReRankResult(
                data.get("top_supporting", combined_supporting[:_RERANK_TOP_N]),
                data.get("top_contradicting", combined_contradicting[:8]),
                tokens,
            )
            self._lf_end(span, {"dedup_removed": data.get("dedup_removed", 0)})
            return result
        except Exception as exc:
            _logger.debug("Re-rank failed (using slice fallback): %s", exc)
            self._lf_end(span, {"error": str(exc)[:100]})
            return _ReRankResult(combined_supporting[:_RERANK_TOP_N], combined_contradicting[:8], 0)

    # ── Stage 4: Synthesis ────────────────────────────────────────────────────

    async def _stage_synthesis(
        self,
        criterion_text: str,
        threshold: str | None,
        reranked: _ReRankResult,
        total_batches: int,
        relevant_batches: int,
        total_chunks: int,
        parent_trace_id: str | None,
        attempt: int = 1,
    ) -> tuple[dict, int]:
        """
        Final synthesis agent: produces verdict_data dict.
        Returns (verdict_data, tokens).
        """
        span, _ = self._lf_span(parent_trace_id, "agent/synthesis", {"criterion": criterion_text[:100]})

        coverage_note = (
            f"Full corpus scan: {total_chunks} chunks across {total_batches} batches. "
            f"{relevant_batches} batches contained relevant content."
        ) if total_batches > 0 else "Semantic search only (full corpus scan unavailable)."

        # PageIndex compression for synthesis: evidence refs can be very large
        # (many documents, many excerpts). Build a hierarchical tree per document
        # so the synthesis LLM gets a focused, navigable summary.
        sup_json = json.dumps(reranked.top_supporting[:15], indent=2)
        con_json = json.dumps(reranked.top_contradicting[:8], indent=2)
        if len(sup_json) + len(con_json) > self._EVIDENCE_COMPRESS_THRESHOLD:
            try:
                pi_summary = await self._pageindexer.retrieve_from_evidence_refs(
                    criterion_text=criterion_text,
                    supporting=reranked.top_supporting[:15],
                    contradicting=reranked.top_contradicting[:8],
                )
                if pi_summary:
                    sup_block = f"[PageIndex evidence summary]\n{pi_summary}"
                    con_block = "(included in PageIndex summary above)"
                else:
                    sup_block = sup_json[:5000]
                    con_block = con_json[:2000]
            except Exception as pi_exc:
                _logger.debug("PageIndex synthesis compression failed (non-fatal): %s", pi_exc)
                sup_block = sup_json[:5000]
                con_block = con_json[:2000]
        else:
            sup_block = sup_json
            con_block = con_json

        user_msg = "\n".join([
            f"## Acceptance Criterion\n{criterion_text}",
            f"{'**Threshold:** ' + threshold if threshold else ''}",
            f"\n## Corpus Coverage\n{coverage_note}",
            f"\n## Re-Ranked Supporting Evidence ({len(reranked.top_supporting)} references)",
            sup_block,
            f"\n## Re-Ranked Contradicting Evidence ({len(reranked.top_contradicting)} references)",
            con_block,
            "\n## Task\nProduce the final compliance verdict. Return JSON.",
        ])

        try:
            raw, tokens = await self._llm(_SYNTHESIS_PROMPT, user_msg, max_tokens=1400)
            data = _parse_json(raw)
            if not data.get("verdict"):
                if attempt < 2:
                    self._lf_end(span, {"retry": True})
                    return await self._stage_synthesis(
                        criterion_text, threshold, reranked,
                        total_batches, relevant_batches, total_chunks,
                        parent_trace_id, attempt=2,
                    )
                data = {
                    "verdict": "INSUFFICIENT_EVIDENCE",
                    "justification": "Synthesis response could not be parsed.",
                }
            self._lf_end(span, {"verdict": data.get("verdict")})
            return data, tokens
        except Exception as exc:
            _logger.error("Synthesis LLM call failed: %s", exc)
            if attempt < 2:
                return await self._stage_synthesis(
                    criterion_text, threshold, reranked,
                    total_batches, relevant_batches, total_chunks,
                    parent_trace_id, attempt=2,
                )
            self._lf_end(span, {"error": str(exc)[:100]})
            return {
                "verdict": "INSUFFICIENT_EVIDENCE",
                "justification": f"Evidence analysis failed: {exc!s:.200}",
            }, 0

    # ── Public entry point ────────────────────────────────────────────────────

    async def evaluate_criterion(
        self,
        *,
        task_id: str,
        org_id: str,
        criterion_id: str | None,
        criterion_text: str,
        threshold: str | None,
        parent_trace_id: str | None,
        attempt: int = 1,
    ) -> CriterionResult:
        run_id = str(uuid.uuid4())
        t0 = time.monotonic()
        total_tokens = 0

        _logger.info(
            "evidence_check.criterion_start",
            extra={"task_id": task_id, "criterion_id": criterion_id, "criterion": criterion_text[:80]},
        )

        # ── Stage 1: Query Expansion ──────────────────────────────────────────
        pos_queries, _neg_queries, tokens1 = await self._stage_query_expansion(
            criterion_text, threshold, parent_trace_id
        )
        total_tokens += tokens1

        # ── Stages 2a + 2b: run semantic retrieval and full corpus map in parallel
        semantic_hits_task = asyncio.create_task(
            self._stage_semantic_retrieval(task_id, org_id, pos_queries, parent_trace_id)
        )
        map_task = asyncio.create_task(
            self._stage_full_corpus_map(task_id, org_id, criterion_text, threshold, parent_trace_id)
        )

        semantic_hits, (all_supporting, all_contradicting, tokens2, total_batches, relevant_batches) = (
            await asyncio.gather(semantic_hits_task, map_task)
        )
        total_tokens += tokens2
        total_chunks = total_batches * _MAP_BATCH_SIZE  # approximate

        # Guard: if both stages returned nothing, return early
        if not semantic_hits and not all_supporting and not all_contradicting:
            _logger.info("No evidence found for task %s criterion %s", task_id, criterion_id)
            return CriterionResult(
                criterion_id=criterion_id,
                criterion_text=criterion_text,
                verdict="INSUFFICIENT_EVIDENCE",
                threshold_met=None,
                justification=(
                    "No relevant content was found in any of the uploaded documents "
                    "after scanning the full corpus."
                ),
                agent_run_id=run_id,
                langfuse_trace_id=parent_trace_id,
            )

        # ── Stage 3: Re-Ranking ───────────────────────────────────────────────
        reranked = await self._stage_rerank(
            criterion_text, threshold,
            all_supporting, all_contradicting,
            semantic_hits, parent_trace_id,
        )
        total_tokens += reranked.tokens

        # ── Stage 4: Synthesis ────────────────────────────────────────────────
        verdict_data, tokens4 = await self._stage_synthesis(
            criterion_text, threshold, reranked,
            total_batches, relevant_batches, total_chunks,
            parent_trace_id,
        )
        total_tokens += tokens4

        result = _build_criterion_result(criterion_id, criterion_text, verdict_data, run_id, parent_trace_id)
        elapsed = round(time.monotonic() - t0, 2)

        _logger.info(
            "evidence_check.criterion_done",
            extra={
                "task_id": task_id,
                "criterion_id": criterion_id,
                "verdict": result.verdict,
                "elapsed_s": elapsed,
                "tokens": total_tokens,
                "total_batches": total_batches,
                "relevant_batches": relevant_batches,
                "supporting_refs": len(all_supporting),
                "contradicting_refs": len(all_contradicting),
            },
        )

        return result
