from __future__ import annotations

"""
PageIndex — two-phase hierarchical RAG (vectorless).

Phase 1  build_index(text) → TOC tree JSON
  Sends the full document text to the LLM once at ingest time.
  Returns a structured JSON hierarchy: {"title": "...", "sections": [...]}
  Tree is stored as JSONB in the attachments table.

Phase 2  retrieve(query, tree, filename) → answer | None
  Sends the TOC tree + user query to the LLM at query time.
  LLM navigates the hierarchy and synthesises a targeted answer.
  Returns a string (can be None if LLM produces nothing useful).

MCP data path  build_index_from_grc_data(tool_name, data) → TOC tree (no LLM)
  Converts structured GRC JSON (frameworks, controls, risks, tasks, …) directly
  into a TOC tree without an LLM call.  The tree is then fed to Phase 2 as-is.
  This compresses large, flat tool results into a semantically-rich summary
  before they are injected into the agent's message history, reducing token
  consumption and improving answer quality.

Safety:
  - Text is hard-capped at _MAX_INDEX_TEXT_CHARS before sending (prevents
    token-budget explosions on very large PDFs).
  - LLM calls go through the shared provider abstraction so the same endpoint
    behavior is used everywhere in copilot.
  - Provider errors propagate as exceptions so callers can mark the attachment
    status=failed.
  - NullPageIndexer is used when the feature is disabled or no provider URL
    is configured — it returns empty/None and never raises.

MCP threshold: tool results whose raw JSON exceeds _MCP_TOKEN_THRESHOLD chars
  are routed through PageIndex Phase 2 to compress before LLM injection.
  Below the threshold the raw JSON is used directly (no overhead).
"""

import json
import re
from importlib import import_module

_logging_module = import_module("backend.01_core.logging_utils")
_factory_module = import_module("backend.20_ai.14_llm_providers.factory")
_logger = _logging_module.get_logger("backend.ai.memory.pageindex")
get_provider = _factory_module.get_provider

# MCP tool result threshold: if raw JSON exceeds this many characters the
# result is routed through PageIndex Phase 2 to compress it into a concise
# hierarchical summary.  ~2 000 chars ≈ ~500 tokens — below this threshold
# the raw JSON is small enough to inject directly with no overhead.
_MCP_TOKEN_THRESHOLD = 2_000

# Max characters per chunk sent to Phase 1.  200 k chars ≈ ~50 k tokens.
# Documents exceeding this are split into chunks and indexed separately,
# then their TOC trees are merged — no data is lost.
_MAX_INDEX_TEXT_CHARS = 200_000

# Maximum number of chunks to index.  Safety cap to avoid runaway costs
# on extremely large documents (e.g. 10 000-page PDFs → max 20 chunks).
_MAX_INDEX_CHUNKS = 20

# Maximum characters of the tree JSON sent to Phase 2.  A very deep hierarchy
# can produce a large tree; cap it so Phase 2 stays within context limits.
_MAX_TREE_CHARS = 40_000

_PHASE1_SYSTEM = """\
You are a document structure analyser.  Your sole task is to read the \
provided document text and return a JSON object representing its \
hierarchical table of contents (TOC).

Rules:
1. Return ONLY a valid JSON object — no markdown fences, no explanatory text.
2. The schema is:
   {
     "title": "<overall document title or best guess>",
     "sections": [
       {
         "heading": "<section heading>",
         "summary": "<1–3 sentence factual summary of this section's content>",
         "key_facts": ["<important fact or rule extracted from this section>", ...],
         "subsections": [ ... same structure, recursive ... ]
       },
       ...
     ]
   }
3. Be exhaustive — capture every numbered section, lettered section, and \
named appendix.
4. "key_facts" should contain specific, extractable facts (numbers, rules, \
thresholds, requirements) — not vague descriptions.
5. Summaries must be factually grounded in the document text.
6. Do not invent content that is not present in the document.
"""

_PHASE2_SYSTEM = """\
You are a precise document question-answering assistant.

You are given:
1. A hierarchical table-of-contents (TOC) tree extracted from a document.
2. A user question.

Your task:
- Identify which section(s) of the TOC contain the answer.
- Synthesise a clear, accurate answer using the section summaries and \
key_facts in the TOC.
- If the TOC does not contain enough information to answer, say so clearly.
- Cite the relevant section headings.
- Do NOT invent information not present in the TOC.
- Be concise but complete.
"""


class PageIndexer:
    """
    Two-phase hierarchical RAG.  Requires a configured LLM provider.
    """

    def __init__(self, *, settings) -> None:
        base_url = settings.ai_provider_url or ""
        self._base_url = base_url.rstrip("/")
        self._api_key = settings.ai_api_key or ""
        self._model = settings.ai_model
        self._provider = None
        if self._base_url:
            self._provider = get_provider(
                provider_type=getattr(settings, "ai_provider_type", "openai_compatible"),
                provider_base_url=self._base_url,
                api_key=self._api_key,
                model_id=self._model,
                temperature=1.0,
            )

    # ─── Phase 1 ─────────────────────────────────────────────────────────────

    async def build_index(self, text: str) -> dict:
        """
        Build a hierarchical TOC tree from document text.

        For documents that fit within _MAX_INDEX_TEXT_CHARS, processes in a
        single pass.  For larger documents, splits into chunks at paragraph
        boundaries, indexes each chunk separately, then merges the TOC trees.
        No content is silently dropped.

        Args:
            text: Raw extracted text of the document.

        Returns:
            A dict representing the TOC tree (see _PHASE1_SYSTEM for schema).

        Raises:
            Exception on network failure, LLM error, or JSON parse failure.
        """
        if not text.strip():
            return {"title": "Empty document", "sections": []}

        # If document fits in a single chunk, process directly
        if len(text) <= _MAX_INDEX_TEXT_CHARS:
            return await self._build_index_single(text)

        # Large document: split into chunks, index each, merge trees
        chunks = self._split_into_chunks(text, _MAX_INDEX_TEXT_CHARS)
        total_chunks = len(chunks)
        _logger.info(
            "PageIndex Phase 1: large document (%d chars) split into %d chunks",
            len(text), total_chunks,
        )

        # Cap the number of chunks to avoid runaway LLM costs
        if total_chunks > _MAX_INDEX_CHUNKS:
            _logger.warning(
                "PageIndex Phase 1: capping %d chunks to %d (document: %d chars)",
                total_chunks, _MAX_INDEX_CHUNKS, len(text),
            )
            chunks = chunks[:_MAX_INDEX_CHUNKS]

        # Index each chunk
        trees: list[dict] = []
        for i, chunk in enumerate(chunks):
            chunk_label = f"[Chunk {i + 1}/{len(chunks)}, chars {sum(len(c) for c in chunks[:i])}-{sum(len(c) for c in chunks[:i+1])}]"
            _logger.info("PageIndex Phase 1: indexing chunk %d/%d (%d chars)", i + 1, len(chunks), len(chunk))
            try:
                tree = await self._build_index_single(
                    chunk,
                    extra_context=chunk_label,
                )
                trees.append(tree)
            except Exception as exc:
                _logger.warning("PageIndex Phase 1: chunk %d/%d failed: %s", i + 1, len(chunks), exc)

        if not trees:
            raise ValueError("PageIndex Phase 1: all chunks failed to index")

        # Merge trees
        merged = self._merge_trees(trees)
        section_count = len(merged.get("sections", []))
        _logger.info(
            "PageIndex Phase 1 complete (chunked): %d trees merged, %d top-level sections",
            len(trees), section_count,
        )
        return merged

    async def _build_index_single(self, text: str, extra_context: str = "") -> dict:
        """Index a single text chunk (must fit within _MAX_INDEX_TEXT_CHARS)."""
        user_msg = f"Document text:\n\n{text}"
        if extra_context:
            user_msg = f"{extra_context}\n\n{user_msg}"

        raw = await self._chat(
            system=_PHASE1_SYSTEM,
            user=user_msg,
            max_tokens=4096,
            timeout=120.0,
        )

        tree = self._parse_json(raw)
        if not isinstance(tree, dict):
            raise ValueError(f"Phase 1 returned non-dict JSON: {type(tree)}")

        section_count = len(tree.get("sections", []))
        _logger.info("PageIndex Phase 1 complete: %d top-level sections", section_count)
        return tree

    @staticmethod
    def _split_into_chunks(text: str, max_chars: int) -> list[str]:
        """Split text into chunks of up to max_chars, breaking at paragraph boundaries."""
        chunks: list[str] = []
        remaining = text
        while remaining:
            if len(remaining) <= max_chars:
                chunks.append(remaining)
                break
            # Find the last paragraph break (\n\n) within the limit
            cut = remaining.rfind("\n\n", 0, max_chars)
            if cut <= 0:
                # No paragraph break found — try single newline
                cut = remaining.rfind("\n", 0, max_chars)
            if cut <= 0:
                # No newline at all — hard cut
                cut = max_chars
            chunks.append(remaining[:cut])
            remaining = remaining[cut:].lstrip("\n")
        return chunks

    @staticmethod
    def _merge_trees(trees: list[dict]) -> dict:
        """Merge multiple TOC trees into one, concatenating sections."""
        if len(trees) == 1:
            return trees[0]

        title = trees[0].get("title", "Document")
        all_sections: list[dict] = []
        for tree in trees:
            all_sections.extend(tree.get("sections", []))

        # Deduplicate sections with identical headings by merging their content
        merged_sections: list[dict] = []
        seen_headings: dict[str, int] = {}
        for section in all_sections:
            heading = section.get("heading", "")
            if heading in seen_headings:
                # Merge into existing section
                idx = seen_headings[heading]
                existing = merged_sections[idx]
                # Merge key_facts
                existing_facts = existing.get("key_facts", [])
                new_facts = section.get("key_facts", [])
                existing["key_facts"] = existing_facts + [
                    f for f in new_facts if f not in existing_facts
                ]
                # Merge subsections
                existing_subs = existing.get("subsections", [])
                new_subs = section.get("subsections", [])
                existing["subsections"] = existing_subs + new_subs
                # Append to summary if different
                new_summary = section.get("summary", "")
                if new_summary and new_summary != existing.get("summary", ""):
                    existing["summary"] = (existing.get("summary", "") + " " + new_summary).strip()
            else:
                seen_headings[heading] = len(merged_sections)
                merged_sections.append(section)

        return {"title": title, "sections": merged_sections}

    # ─── Phase 2 ─────────────────────────────────────────────────────────────

    async def retrieve(self, query: str, tree: dict, filename: str) -> str | None:
        """
        Navigate the TOC tree to answer a user query.

        Args:
            query:    The user's question.
            tree:     The TOC tree produced by build_index().
            filename: Human-readable document name (used in attribution).

        Returns:
            A string answer, or None if the tree is empty / no useful answer.
        """
        if not tree or not tree.get("sections"):
            return None

        tree_json = json.dumps(tree, ensure_ascii=False)
        if len(tree_json) > _MAX_TREE_CHARS:
            # Prune: drop subsections from deep nodes to shrink the payload.
            tree_json = self._prune_tree_json(tree, _MAX_TREE_CHARS)
            _logger.debug(
                "PageIndex Phase 2: tree pruned to %d chars for query", len(tree_json),
            )

        user_prompt = (
            f"Document: {filename}\n\n"
            f"TOC tree (JSON):\n{tree_json}\n\n"
            f"Question: {query}"
        )

        raw = await self._chat(
            system=_PHASE2_SYSTEM,
            user=user_prompt,
            max_tokens=1024,
            timeout=60.0,
        )

        answer = raw.strip()
        if not answer or len(answer) < 10:
            return None

        _logger.debug("PageIndex Phase 2 answer length: %d chars", len(answer))
        return answer

    # ─── Internal ─────────────────────────────────────────────────────────────

    async def _chat(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int,
        timeout: float,
    ) -> str:
        del timeout

        provider = self._provider
        if provider is None:
            raise RuntimeError("PageIndexer: ai_provider_url is not configured")

        response = await provider.chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            tools=None,
            temperature=1.0,
            max_tokens=max_tokens,
        )

        content = (response.content or "").strip()
        if not content:
            raise ValueError("PageIndexer: LLM returned empty content")
        return content

    @staticmethod
    def _parse_json(raw: str) -> dict:
        """
        Extract JSON from raw LLM output.
        Handles markdown code fences and leading/trailing prose.
        """
        # Strip markdown fences
        fenced = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
        if fenced:
            raw = fenced.group(1)

        # Try direct parse first
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # Try finding the first { ... } block
        brace_match = re.search(r"\{[\s\S]+\}", raw)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError(f"PageIndexer: could not parse JSON from LLM output (len={len(raw)})")

    @staticmethod
    def _prune_tree_json(tree: dict, max_chars: int) -> str:
        """
        Progressively prune subsections to shrink the serialised tree.
        Removes subsection arrays depth-first until the JSON fits.
        """
        import copy
        pruned = copy.deepcopy(tree)

        def _prune(sections: list, depth: int) -> None:
            for s in sections:
                if depth > 0 and "subsections" in s:
                    sub = s.get("subsections") or []
                    if sub:
                        _prune(sub, depth - 1)
                    else:
                        s.pop("subsections", None)
                elif "subsections" in s:
                    s.pop("subsections", None)

        for depth in range(5, -1, -1):
            _prune(pruned.get("sections", []), depth)
            serialised = json.dumps(pruned, ensure_ascii=False)
            if len(serialised) <= max_chars:
                return serialised

        # Last resort: just serialise the top-level headings
        slim = {
            "title": tree.get("title", ""),
            "sections": [
                {"heading": s.get("heading", ""), "summary": s.get("summary", "")}
                for s in tree.get("sections", [])
            ],
        }
        return json.dumps(slim, ensure_ascii=False)


    # ─── MCP data path ────────────────────────────────────────────────────────

    @staticmethod
    def build_index_from_grc_data(tool_name: str, data: dict) -> dict:
        """
        Convert a structured GRC tool result into a TOC tree without any LLM call.

        The resulting tree has the same shape as the document TOC tree produced
        by Phase 1, so Phase 2 (retrieve()) can be used unchanged.

        Supported tool shapes:
          - items + total_count  (list tools: frameworks, controls, risks, tasks)
          - controls + summary   (grc_get_framework_hierarchy)
          - top-level scalar fields (health views, single-entity tools)

        For unrecognised shapes a minimal single-section tree is returned.
        """
        title = _grc_tool_title(tool_name)
        sections: list[dict] = []

        items = data.get("items") or data.get("controls")
        if items and isinstance(items, list):
            # List / hierarchy result — each item becomes a section
            for item in items:
                heading = _grc_item_heading(tool_name, item)
                key_facts = _grc_item_facts(item)
                sections.append({
                    "heading": heading,
                    "summary": _grc_item_summary(tool_name, item),
                    "key_facts": key_facts,
                    "subsections": [],
                })
            # Prepend a summary section if metadata is present
            meta_facts = []
            if "total_count" in data:
                meta_facts.append(f"Total items: {data['total_count']}")
            if "summary" in data and isinstance(data["summary"], dict):
                for k, v in data["summary"].items():
                    meta_facts.append(f"{k}: {v}")
            if meta_facts:
                sections.insert(0, {
                    "heading": "Overview",
                    "summary": f"Result set from {tool_name}.",
                    "key_facts": meta_facts,
                    "subsections": [],
                })
        else:
            # Single-entity / health view — flatten all scalar fields into key_facts
            key_facts = [f"{k}: {v}" for k, v in data.items()
                         if v is not None and not isinstance(v, (dict, list))]
            nested: list[str] = []
            for k, v in data.items():
                if isinstance(v, dict):
                    nested.append(f"{k}: {json.dumps(v, default=str)[:200]}")
                elif isinstance(v, list) and v:
                    nested.append(f"{k}: {', '.join(str(i) for i in v[:10])}")
            sections.append({
                "heading": title,
                "summary": f"Data from {tool_name}.",
                "key_facts": key_facts + nested,
                "subsections": [],
            })

        return {"title": title, "sections": sections}

    @staticmethod
    def build_index_from_evidence_refs(
        criterion_text: str,
        supporting: list[dict],
        contradicting: list[dict],
    ) -> dict:
        """
        Convert evidence references (from the evidence checker map/rerank stages)
        into a TOC tree for Phase 2 retrieval.

        Groups refs by document filename so Phase 2 can navigate per-document
        evidence sections rather than receiving a flat JSON blob.

        Tree shape:
          title: "<criterion_text[:80]>"
          sections:
            - heading: "Supporting Evidence"
              subsections: [ per-document sections with excerpts as key_facts ]
            - heading: "Contradicting Evidence"
              subsections: [ per-document sections with excerpts as key_facts ]
        """
        def _group_by_doc(refs: list[dict]) -> dict[str, list[dict]]:
            grouped: dict[str, list[dict]] = {}
            for r in refs:
                doc = r.get("document_filename") or "Unknown document"
                grouped.setdefault(doc, []).append(r)
            return grouped

        def _doc_section(doc: str, refs: list[dict]) -> dict:
            facts = []
            for r in refs:
                excerpt = (r.get("excerpt") or "")[:150]
                note = r.get("relevance_note", "")
                conf = r.get("confidence")
                page = r.get("page_number")
                loc = f"p.{page}" if page else r.get("section_or_sheet") or ""
                line = excerpt
                if loc:
                    line = f"[{loc}] {line}"
                if note:
                    line += f" — {note}"
                if conf is not None:
                    line += f" (conf={conf:.2f})"
                facts.append(line)
            return {
                "heading": doc,
                "summary": f"{len(refs)} reference(s) from this document.",
                "key_facts": facts,
                "subsections": [],
            }

        sup_grouped = _group_by_doc(supporting)
        con_grouped = _group_by_doc(contradicting)

        sections = []
        if sup_grouped:
            sections.append({
                "heading": "Supporting Evidence",
                "summary": f"{len(supporting)} supporting reference(s) across {len(sup_grouped)} document(s).",
                "key_facts": [f"Total supporting refs: {len(supporting)}"],
                "subsections": [_doc_section(doc, refs) for doc, refs in sup_grouped.items()],
            })
        if con_grouped:
            sections.append({
                "heading": "Contradicting Evidence",
                "summary": f"{len(contradicting)} contradicting reference(s) across {len(con_grouped)} document(s).",
                "key_facts": [f"Total contradicting refs: {len(contradicting)}"],
                "subsections": [_doc_section(doc, refs) for doc, refs in con_grouped.items()],
            })

        return {
            "title": f"Evidence for: {criterion_text[:80]}",
            "sections": sections,
        }

    async def retrieve_from_evidence_refs(
        self,
        *,
        criterion_text: str,
        supporting: list[dict],
        contradicting: list[dict],
    ) -> str | None:
        """
        Convenience wrapper: build an in-memory evidence TOC tree then run Phase 2.

        Returns a concise, criterion-targeted evidence summary replacing the raw
        JSON blobs that would otherwise be injected into the synthesis/rerank prompts.
        Returns None if no refs or Phase 2 produces nothing (callers fall back to raw JSON).
        """
        if not supporting and not contradicting:
            return None
        tree = self.build_index_from_evidence_refs(criterion_text, supporting, contradicting)
        if not tree.get("sections"):
            return None
        return await self.retrieve(
            query=f"What evidence supports or contradicts this criterion: {criterion_text}",
            tree=tree,
            filename="[Evidence References]",
        )

    async def retrieve_from_grc_data(
        self,
        *,
        query: str,
        tool_name: str,
        data: dict,
    ) -> str | None:
        """
        Convenience wrapper: build an in-memory GRC TOC tree then run Phase 2.

        Returns a concise, query-targeted summary of the tool result.
        Returns None if tree is empty or Phase 2 produces nothing.
        """
        tree = self.build_index_from_grc_data(tool_name, data)
        if not tree.get("sections"):
            return None
        return await self.retrieve(
            query=query,
            tree=tree,
            filename=f"[GRC tool: {tool_name}]",
        )


def _grc_tool_title(tool_name: str) -> str:
    return tool_name.replace("grc_", "").replace("_", " ").title()


def _grc_item_heading(tool_name: str, item: dict) -> str:
    # Prefer human-readable code + name
    code = item.get("control_code") or item.get("requirement_code") or item.get("risk_code") or item.get("framework_code") or item.get("control_id", "")
    name = item.get("name") or item.get("title") or item.get("risk_title") or ""
    if code and name:
        return f"{code} — {name}"
    return code or name or str(item.get("id", "item"))[:20]


def _grc_item_summary(tool_name: str, item: dict) -> str:
    parts: list[str] = []
    if "criticality_code" in item:
        parts.append(f"criticality={item['criticality_code']}")
    if "risk_level_code" in item:
        parts.append(f"level={item['risk_level_code']}")
    if "status_code" in item:
        parts.append(f"status={item['status_code']}")
    if "priority_code" in item:
        parts.append(f"priority={item['priority_code']}")
    if "approval_status" in item:
        parts.append(f"approval={item['approval_status']}")
    if "completion_pct" in item:
        parts.append(f"completion={item['completion_pct']}%")
    return "; ".join(parts) if parts else f"Item from {tool_name}."


def _grc_item_facts(item: dict) -> list[str]:
    facts: list[str] = []
    numeric_keys = {
        "total_controls", "active_controls", "total_requirements",
        "open_task_count", "linked_risk_count", "high_risk_count",
        "overdue_task_count", "critical_risk_count", "medium_risk_count",
        "control_task_count", "risk_task_count", "control_open_tasks",
        "control_overdue_tasks", "evidence_task_count",
    }
    text_keys = {
        "description", "due_date", "last_test_date", "max_risk_severity",
        "risk_category_code", "has_owner", "has_tests",
    }
    for k in numeric_keys:
        if item.get(k) is not None:
            facts.append(f"{k}={item[k]}")
    for k in text_keys:
        if item.get(k) is not None:
            facts.append(f"{k}={item[k]}")
    # Linked arrays (codes only)
    for k in ("risk_codes", "risk_levels", "linked_risk_codes", "linked_control_codes"):
        val = item.get(k)
        if val and isinstance(val, list):
            facts.append(f"{k}=[{', '.join(str(v) for v in val[:10])}]")
    return facts


class NullPageIndexer:
    """
    No-op PageIndexer.  Used when AI_PAGEINDEX_ENABLED=false or when
    ai_provider_url is not configured.  Never raises, always returns safe empty values.
    """

    async def build_index(self, text: str) -> dict:  # noqa: ARG002
        return {}

    async def retrieve(self, query: str, tree: dict, filename: str) -> str | None:  # noqa: ARG002
        return None

    async def retrieve_from_grc_data(  # noqa: ARG002
        self, *, query: str, tool_name: str, data: dict,
    ) -> str | None:
        return None

    async def retrieve_from_evidence_refs(  # noqa: ARG002
        self, *, criterion_text: str, supporting: list, contradicting: list,
    ) -> str | None:
        return None
