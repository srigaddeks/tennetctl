"""
Framework Builder Agent — multi-phase pipeline.

Phase 1: stream_hierarchy   — analyzes documents, proposes requirement hierarchy (SSE, no DB writes)
Phase 2: stream_controls    — generates controls + risk mappings (SSE, no DB writes)
Phase 3: run_creation       — writes approved proposal to DB (background job)

Enhance Mode:
  stream_enhance_diff       — reads existing framework, streams diff proposals (SSE, no DB writes)
  run_apply_changes         — writes accepted_changes to DB (background job)

Gap Analysis:
  run_gap_analysis          — reads framework, computes + stores gap report (background job)
"""

from __future__ import annotations

import asyncio
import json
import random
from importlib import import_module
from typing import AsyncGenerator

import asyncpg

from .prompts import (
    ENHANCE_SYSTEM,
    ENHANCE_USER_TEMPLATE,
    GAP_ANALYSIS_SYSTEM,
    GAP_ANALYSIS_USER_TEMPLATE,
    PHASE1_SYSTEM,
    PHASE1_USER_TEMPLATE,
    PHASE1B_CONTROLS_BATCH_USER_TEMPLATE,
    PHASE1B_CONTROLS_SYSTEM,
    PHASE1B_CONTROLS_USER_TEMPLATE,
    PHASE2_CONTROLS_SYSTEM,
    PHASE2_CONTROLS_USER_TEMPLATE,
    PHASE2_RISKS_SYSTEM,
    PHASE2_RISKS_USER_TEMPLATE,
)

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.framework_builder.agent")

_pageindex_module = import_module("backend.20_ai.03_memory.pageindex")
PageIndexer = _pageindex_module.PageIndexer
NullPageIndexer = _pageindex_module.NullPageIndexer


def _sse(event_type: str, data: dict) -> str:
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


def _flatten_hierarchy(nodes: list, parent_code: str | None = None, depth: int = 0) -> list[dict]:
    """Flatten requirement list to ordered list — strict 1-level only.

    Requirements are flat (no nesting). Any children the LLM might have
    generated are silently promoted to top-level requirements.
    """
    result = []
    for i, node in enumerate(nodes):
        flat = {
            "code": node["code"],
            "name": node["name"],
            "description": node.get("description", ""),
            "sort_order": node.get("sort_order", i + 1),
            "parent_code": None,
            "depth": 0,
            "children": [],
        }
        result.append(flat)
        # If the LLM produced nested children, promote them to top-level
        for j, child in enumerate(node.get("children") or []):
            result.append({
                "code": child["code"],
                "name": child["name"],
                "description": child.get("description", ""),
                "sort_order": child.get("sort_order", len(result) + 1),
                "parent_code": None,
                "depth": 0,
                "children": [],
            })
    return result


def _normalize_enhance_proposals(raw_proposals: list[dict]) -> list[dict]:
    """Normalize enhance proposals into a stable structure for UI and apply jobs."""
    normalized: list[dict] = []
    for proposal in raw_proposals:
        if not isinstance(proposal, dict):
            continue

        change_type = str(proposal.get("change_type", "")).strip()
        entity_type = str(proposal.get("entity_type", "")).strip()
        if not change_type or not entity_type:
            continue

        proposed_value = proposal.get("proposed_value")
        if isinstance(proposed_value, dict):
            pv = dict(proposed_value)
            if "code" in pv and "control_code" not in pv and change_type == "add_control":
                pv["control_code"] = pv.pop("code")
            if "criticality" in pv and "criticality_code" not in pv:
                pv["criticality_code"] = pv["criticality"]
            if "risk_mapping" in pv and "risk_mappings" not in pv:
                risk_mapping = pv.get("risk_mapping")
                if isinstance(risk_mapping, dict):
                    pv["risk_mappings"] = [risk_mapping]
            if "risk_mappings" in pv and not isinstance(pv.get("risk_mappings"), list):
                pv["risk_mappings"] = []
            proposed_value = pv

        normalized.append(
            {
                "change_type": change_type,
                "entity_type": entity_type,
                "entity_id": proposal.get("entity_id"),
                "entity_code": str(proposal.get("entity_code", "")).strip(),
                "field": str(proposal.get("field", "")).strip(),
                "current_value": proposal.get("current_value"),
                "proposed_value": proposed_value,
                "reason": str(proposal.get("reason", "")).strip(),
            }
        )
    return normalized


def _normalize_code(value: object) -> str:
    return str(value or "").strip().upper()


def _normalize_risk_title(value: object) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _normalize_coverage_type(value: object) -> str:
    raw = str(value or "mitigates").strip().lower()
    if raw in {"mitigates", "detects", "monitors"}:
        return raw
    if raw in {"mitigating", "primary", "secondary", "related"}:
        return "mitigates"
    if raw in {"detecting"}:
        return "detects"
    return "mitigates"


def _normalize_risk_mapping_payload(
    *,
    controls: list[dict],
    mappings: object,
    new_risks: object,
    existing_risks: list[dict],
) -> tuple[list[dict], list[dict]]:
    control_codes = {
        _normalize_code(control.get("control_code"))
        for control in controls
        if isinstance(control, dict) and control.get("control_code")
    }

    existing_risk_codes = {
        _normalize_code(risk.get("risk_code"))
        for risk in (existing_risks or [])
        if isinstance(risk, dict) and risk.get("risk_code")
    }
    existing_risk_titles = {
        _normalize_risk_title(risk.get("title"))
        for risk in (existing_risks or [])
        if isinstance(risk, dict) and risk.get("title")
    }

    normalized_new_risks: list[dict] = []
    seen_new_codes: set[str] = set()
    seen_new_titles: set[str] = set()
    if isinstance(new_risks, list):
        for raw_risk in new_risks:
            if not isinstance(raw_risk, dict):
                continue
            risk_code = _normalize_code(raw_risk.get("risk_code"))
            risk_title = _normalize_risk_title(raw_risk.get("title"))
            if not risk_code:
                continue
            if risk_code in existing_risk_codes:
                continue
            if risk_title and risk_title in existing_risk_titles:
                continue
            if risk_code in seen_new_codes:
                continue
            if risk_title and risk_title in seen_new_titles:
                continue

            normalized_risk = dict(raw_risk)
            normalized_risk["risk_code"] = risk_code
            if "risk_level_code" in normalized_risk:
                normalized_risk["risk_level_code"] = str(normalized_risk.get("risk_level_code") or "medium").strip().lower()
            if "risk_category_code" in normalized_risk:
                normalized_risk["risk_category_code"] = str(normalized_risk.get("risk_category_code") or "operational").strip().lower()
            normalized_new_risks.append(normalized_risk)
            seen_new_codes.add(risk_code)
            if risk_title:
                seen_new_titles.add(risk_title)

    normalized_mappings: list[dict] = []
    seen_mapping_keys: set[tuple[str, str, str]] = set()
    if isinstance(mappings, list):
        for raw_mapping in mappings:
            if not isinstance(raw_mapping, dict):
                continue
            control_code = _normalize_code(raw_mapping.get("control_code"))
            risk_code = _normalize_code(raw_mapping.get("risk_code"))
            if not control_code or control_code not in control_codes:
                continue
            if not risk_code:
                continue
            coverage_type = _normalize_coverage_type(
                raw_mapping.get("coverage_type") or raw_mapping.get("mapping_type")
            )
            key = (control_code, risk_code, coverage_type)
            if key in seen_mapping_keys:
                continue
            seen_mapping_keys.add(key)
            normalized_mappings.append(
                {
                    "control_code": control_code,
                    "risk_code": risk_code,
                    "coverage_type": coverage_type,
                }
            )

    return normalized_mappings, normalized_new_risks


def _missing_mapped_controls(controls: list[dict], mappings: list[dict]) -> list[str]:
    control_codes = {
        _normalize_code(control.get("control_code"))
        for control in controls
        if isinstance(control, dict) and control.get("control_code")
    }
    mapped_codes = {
        _normalize_code(mapping.get("control_code"))
        for mapping in mappings
        if isinstance(mapping, dict) and mapping.get("control_code")
    }
    return sorted(code for code in control_codes if code and code not in mapped_codes)


class FrameworkBuilderAgent:
    """
    Stateless agent — all methods are coroutines or async generators.
    Instantiated per request with injected LLM config.
    """

    def __init__(self, *, llm_config, settings, pool: asyncpg.Pool):
        self._config = llm_config
        self._settings = settings
        self._pool = pool

        provider_url = getattr(settings, "ai_provider_url", None)
        if provider_url:
            self._indexer = PageIndexer(settings=settings)
        else:
            self._indexer = NullPageIndexer()

    def _llm_complete_events(self, stage: str, elapsed_seconds: int, raw_response: str = "") -> list[str]:
        """Return SSE events for llm_call_complete + llm_response_preview with full meta."""
        meta = getattr(self, "_last_llm_meta", None) or {}
        events = [
            _sse("llm_call_complete", {
                "stage": stage,
                "message": "AI generation complete — parsing results…",
                "elapsed_seconds": elapsed_seconds,
                "model": meta.get("model"),
                "prompt_tokens": meta.get("prompt_tokens"),
                "completion_tokens": meta.get("completion_tokens"),
                "total_tokens": meta.get("total_tokens"),
                "system_chars": meta.get("system_chars"),
                "user_chars": meta.get("user_chars"),
                "response_chars": meta.get("response_chars"),
            }),
            _sse("llm_response_preview", {
                "stage": stage,
                "preview": meta.get("response_preview", raw_response[:500]),
                "total_chars": meta.get("response_chars") or len(raw_response),
            }),
        ]
        return events

    # ─────────────────────────────────────────────────────────────────────
    # PHASE 1 — stream requirement hierarchy
    # ─────────────────────────────────────────────────────────────────────

    async def stream_hierarchy(
        self,
        *,
        framework_name: str,
        framework_type_code: str,
        framework_category_code: str,
        user_context: str,
        attachment_ids: list[str],
        existing_risks: list[dict],
    ) -> AsyncGenerator[str, None]:
        """
        Yields SSE strings.
        Caller (StreamingResponse) iterates this generator.
        """
        doc_trees: list[dict] = []

        # Stage 1: analyze documents
        total_docs = len(attachment_ids)
        for i, att_id in enumerate(attachment_ids):
            try:
                text, filename = await self._fetch_attachment_text(att_id)
                yield _sse("doc_analyzing", {"filename": filename, "pct": int((i / max(total_docs, 1)) * 40)})
                tree = await self._indexer.build_index(text)
                doc_trees.append({"filename": filename, "tree": tree})
                yield _sse("doc_analyzed", {"filename": filename, "pct": int(((i + 1) / max(total_docs, 1)) * 40)})
            except Exception as exc:
                _logger.warning("framework_builder.doc_analysis_failed: %s att=%s", exc, att_id)
                yield _sse("doc_analysis_warning", {"attachment_id": att_id, "message": str(exc)})

        import time as _time
        model_id = getattr(self._config, "model_id", "unknown")
        doc_summary_text = json.dumps(
            [{"filename": d["filename"], "tree": d["tree"]} for d in doc_trees],
            indent=2,
        )[:30_000]

        existing_risks_json = json.dumps(
            [
                {"risk_code": r.get("risk_code"), "title": r.get("title"), "risk_category_code": r.get("risk_category_code")}
                for r in (existing_risks or [])[:200]
            ],
            indent=2,
        )[:12_000]

        # ── Step 1: Generate requirements only ─────────────────────────────
        yield _sse("stage_start", {"stage": "requirements", "label": "Generating Requirement Hierarchy"})

        user_prompt = PHASE1_USER_TEMPLATE.format(
            framework_type=framework_type_code,
            framework_category=framework_category_code,
            framework_name=framework_name or "(not specified)",
            user_context=user_context or "(none provided)",
            doc_summaries=doc_summary_text,
        )

        yield _sse("llm_call_start", {
            "stage": "requirements",
            "message": "Analyzing scope and generating requirements…",
            "model": model_id,
        })

        t0 = _time.monotonic()
        raw_chunks: list[str] = []
        chars_received = 0
        last_event_chars = 0

        async for chunk in self._llm_stream(PHASE1_SYSTEM, user_prompt):
            raw_chunks.append(chunk)
            chars_received += len(chunk)
            if chars_received - last_event_chars >= 200:
                yield _sse("llm_chunk", {
                    "stage": "requirements",
                    "chars_received": chars_received,
                    "elapsed_seconds": round(_time.monotonic() - t0, 1),
                    "preview": "".join(raw_chunks)[-120:],
                    "model": model_id,
                })
                last_event_chars = chars_received

        raw_json = "".join(raw_chunks).strip()
        if raw_json.startswith("```"):
            lines = raw_json.split("\n")
            raw_json = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:]).strip()

        elapsed_req = round(_time.monotonic() - t0, 1)
        for ev in self._llm_complete_events("requirements", int(elapsed_req), raw_json):
            yield ev

        try:
            hierarchy_data = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            yield _sse("error", {"message": f"Failed to parse requirements JSON: {exc}"})
            return

        requirements_flat = _flatten_hierarchy(hierarchy_data.get("requirements", []))
        total_reqs = len(requirements_flat)

        for req in requirements_flat:
            yield _sse("requirement_ready", {
                "code": req["code"],
                "name": req["name"],
                "description": req["description"],
                "parent_code": req["parent_code"],
                "depth": req["depth"],
                "sort_order": req["sort_order"],
            })
            await asyncio.sleep(0.03)

        _logger.info("framework_builder.phase1: %d requirements generated in %.1fs", total_reqs, elapsed_req)

        # ── Step 2: Generate controls per requirement ──────────────────────
        all_controls: list[dict] = []
        all_risk_mappings: list[dict] = []
        all_new_risks: list[dict] = []

        batch_size = max(1, int(getattr(self._settings, "framework_builder_batch_size", 8) or 8))

        def _emit_controls_for_req(req, ctrl_data):
            """Yields SSE events for controls/mappings of one requirement and updates accumulators.

            Returns (controls_count, mappings_count, sse_events_list).
            """
            events: list[str] = []
            if isinstance(ctrl_data, list):
                ctrl_data = {"controls": ctrl_data, "risk_mappings": [], "new_risks": []}
            controls = ctrl_data.get("controls", []) or []
            if not isinstance(controls, list):
                controls = []
            for ctrl in controls:
                all_controls.append(ctrl)
                events.append(_sse("control_proposed", {
                    "code": ctrl.get("control_code", ""),
                    "name": ctrl.get("name", ""),
                    "requirement_code": ctrl.get("requirement_code", req["code"]),
                    "criticality": ctrl.get("criticality", "medium"),
                    "control_type": ctrl.get("control_type", "preventive"),
                    "automation_potential": ctrl.get("automation_potential", "manual"),
                }))
            req_mappings = ctrl_data.get("risk_mappings", []) or []
            if not isinstance(req_mappings, list):
                req_mappings = []
            all_risk_mappings.extend(req_mappings)
            for m in req_mappings:
                events.append(_sse("risk_mapped", {
                    "control_code": m.get("control_code", ""),
                    "risk_code": m.get("risk_code", ""),
                    "coverage_type": m.get("coverage_type", "mitigates"),
                    "is_new": False,
                }))
            req_new_risks = ctrl_data.get("new_risks", []) or []
            if isinstance(req_new_risks, list):
                all_new_risks.extend(req_new_risks)
            return len(controls), len(req_mappings), events

        async def _single_req_fallback(req):
            """Per-requirement LLM call (used when a batch is missing a requirement or fails to parse)."""
            existing_ctrl_summary_local = "\n".join(
                f"  - {c.get('control_code')}: {c.get('name')} (req: {c.get('requirement_code')})"
                for c in all_controls[-50:]
            ) if all_controls else "(none yet)"
            prompt = PHASE1B_CONTROLS_USER_TEMPLATE.format(
                framework_name=framework_name or "(not specified)",
                framework_type=framework_type_code,
                req_code=req["code"],
                req_name=req["name"],
                req_description=req["description"],
                user_context=user_context or "(none)",
                doc_summary=doc_summary_text[:8000],
                existing_risks_json=existing_risks_json,
                existing_controls_summary=existing_ctrl_summary_local,
            )
            chunks: list[str] = []
            async for ch in self._llm_stream(PHASE1B_CONTROLS_SYSTEM, prompt):
                chunks.append(ch)
            raw = "".join(chunks).strip()
            if raw.startswith("```"):
                lines_ = raw.split("\n")
                raw = "\n".join(lines_[1:-1] if lines_[-1].strip() == "```" else lines_[1:]).strip()
            try:
                return json.loads(raw)
            except Exception:
                return {"controls": [], "risk_mappings": [], "new_risks": []}

        for batch_start in range(0, total_reqs, batch_size):
            batch = requirements_flat[batch_start : batch_start + batch_size]
            batch_end = batch_start + len(batch)
            stage_id = f"controls_batch_{batch_start}"
            batch_label = f"[{batch_start+1}-{batch_end}/{total_reqs}]"

            yield _sse("stage_start", {
                "stage": stage_id,
                "label": f"{batch_label} Generating controls for {len(batch)} requirements",
            })
            yield _sse("llm_call_start", {
                "stage": stage_id,
                "message": f"{batch_label} Generating controls for {len(batch)} requirements…",
                "model": model_id,
            })

            existing_ctrl_summary = "\n".join(
                f"  - {c.get('control_code')}: {c.get('name')} (req: {c.get('requirement_code')})"
                for c in all_controls[-50:]
            ) if all_controls else "(none yet)"

            requirements_block = "\n\n".join(
                f"{idx+1}. Code: {r['code']}\n   Name: {r['name']}\n   Description: {r['description']}"
                for idx, r in enumerate(batch)
            )

            ctrl_prompt = PHASE1B_CONTROLS_BATCH_USER_TEMPLATE.format(
                framework_name=framework_name or "(not specified)",
                framework_type=framework_type_code,
                user_context=user_context or "(none)",
                doc_summary=doc_summary_text[:8000],
                existing_risks_json=existing_risks_json,
                existing_controls_summary=existing_ctrl_summary,
                n=len(batch),
                requirements_block=requirements_block,
            )

            t1 = _time.monotonic()
            ctrl_chunks: list[str] = []
            ctrl_chars = 0
            ctrl_last_ev = 0
            async for chunk in self._llm_stream(PHASE1B_CONTROLS_SYSTEM, ctrl_prompt):
                ctrl_chunks.append(chunk)
                ctrl_chars += len(chunk)
                if ctrl_chars - ctrl_last_ev >= 200:
                    yield _sse("llm_chunk", {
                        "stage": stage_id,
                        "chars_received": ctrl_chars,
                        "elapsed_seconds": round(_time.monotonic() - t1, 1),
                        "preview": "".join(ctrl_chunks)[-120:],
                        "model": model_id,
                    })
                    ctrl_last_ev = ctrl_chars

            ctrl_raw = "".join(ctrl_chunks).strip()
            if ctrl_raw.startswith("```"):
                lines = ctrl_raw.split("\n")
                ctrl_raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:]).strip()

            ctrl_elapsed = round(_time.monotonic() - t1, 1)
            for ev in self._llm_complete_events(stage_id, int(ctrl_elapsed), ctrl_raw):
                yield ev

            # Parse batch response: prefer {"batches":[...]}, accept bare list of per-req objects
            by_code: dict[str, dict] = {}
            parse_ok = True
            try:
                data = json.loads(ctrl_raw)
            except Exception as exc:
                _logger.warning("phase1b batch %s: parse failed: %s", batch_label, exc)
                parse_ok = False
                data = None

            if parse_ok and isinstance(data, dict):
                batches_out = data.get("batches")
                if isinstance(batches_out, list):
                    for entry in batches_out:
                        if isinstance(entry, dict) and entry.get("requirement_code"):
                            by_code[str(entry["requirement_code"])] = entry
                elif isinstance(data.get("controls"), list):
                    # Single-req shape returned for a batch — assign to first req as best effort
                    by_code[batch[0]["code"]] = data
            elif parse_ok and isinstance(data, list):
                for entry in data:
                    if isinstance(entry, dict) and entry.get("requirement_code"):
                        by_code[str(entry["requirement_code"])] = entry

            batch_total_controls = 0
            batch_total_mappings = 0
            for req in batch:
                rb = by_code.get(req["code"])
                if rb is None:
                    # Fallback: re-issue a single-requirement call for this missing one
                    _logger.warning("phase1b batch %s: requirement %s missing from response, falling back",
                                    batch_label, req["code"])
                    rb = await _single_req_fallback(req)
                c_count, m_count, evs = _emit_controls_for_req(req, rb)
                for ev in evs:
                    yield ev
                batch_total_controls += c_count
                batch_total_mappings += m_count

            _logger.info("phase1b batch %s: %d reqs, %d controls, %d mappings in %.1fs",
                         batch_label, len(batch), batch_total_controls, batch_total_mappings, ctrl_elapsed)

        # ── Step 3: Assemble final hierarchy data ──────────────────────────
        # Normalize risk mappings and deduplicate new risks
        normalized_mappings, normalized_new_risks = _normalize_risk_mapping_payload(
            controls=all_controls,
            mappings=all_risk_mappings,
            new_risks=all_new_risks,
            existing_risks=existing_risks,
        )

        hierarchy_data["controls"] = all_controls
        hierarchy_data["risks"] = normalized_new_risks
        hierarchy_data["risk_mappings"] = normalized_mappings

        yield _sse("phase1_complete", {
            "requirement_count": total_reqs,
            "control_count": len(all_controls),
            "risk_count": len(normalized_new_risks),
            "risk_mapping_count": len(normalized_mappings),
            "hierarchy": hierarchy_data,
            "suggested_name": hierarchy_data.get("suggested_name"),
            "suggested_description": hierarchy_data.get("suggested_description"),
            "framework_code": hierarchy_data.get("framework_code"),
        })

    # ─────────────────────────────────────────────────────────────────────
    # PHASE 2 — stream controls + risk mappings
    # ─────────────────────────────────────────────────────────────────────

    async def stream_controls_and_risks(
        self,
        *,
        framework_name: str,
        framework_type_code: str,
        hierarchy: dict,
        node_overrides: dict[str, str],
        user_context: str,
        attachment_ids: list[str],
        existing_risks: list[dict],
    ) -> AsyncGenerator[str, None]:
        """Yields SSE strings for Phase 2."""

        # Rebuild doc summaries quickly (PageIndex Phase 2 retrieve)
        doc_summary = await self._summarize_attachments(attachment_ids)

        # Flat requirements — all top-level, controls attach directly
        requirements = _flatten_hierarchy(hierarchy.get("requirements", []))

        all_controls: list[dict] = []

        # Batch requirements and run batches in parallel.
        # batch_size and concurrency come from settings so they're tunable
        # without code changes (FRAMEWORK_BUILDER_BATCH_SIZE / *_CONCURRENCY).
        batch_size_raw = getattr(self._settings, "framework_builder_batch_size", None)
        batch_size = max(1, int(batch_size_raw)) if batch_size_raw else 8
        concurrency_raw = getattr(self._settings, "framework_builder_concurrency", None)
        concurrency = max(1, int(concurrency_raw)) if concurrency_raw else 3

        model_id = getattr(self._config, "model_id", "unknown")
        import time as _time

        batches: list[list[dict]] = [
            requirements[i : i + batch_size] for i in range(0, len(requirements), batch_size)
        ]
        total_batches = len(batches)
        total_reqs = len(requirements)

        # Queue carries SSE strings produced by worker tasks; the generator
        # below drains it and yields events as they happen so the frontend
        # still streams in real time even though batches run concurrently.
        event_queue: asyncio.Queue[str | None] = asyncio.Queue()
        semaphore = asyncio.Semaphore(concurrency)
        completed_batches = 0
        completed_lock = asyncio.Lock()

        async def _process_batch(batch_idx: int, batch: list[dict]) -> list[dict]:
            nonlocal completed_batches
            stage_id = f"controls_batch_{batch_idx}"
            batch_label = f"[batch {batch_idx + 1}/{total_batches}]"
            codes_preview = ", ".join(r["code"] for r in batch[:3]) + (
                "…" if len(batch) > 3 else ""
            )

            async with semaphore:
                await event_queue.put(_sse("stage_start", {
                    "stage": stage_id,
                    "label": f"{batch_label} Generating controls for {len(batch)} requirements ({codes_preview})",
                }))
                await event_queue.put(_sse("llm_call_start", {
                    "stage": stage_id,
                    "message": f"{batch_label} Generating controls for {len(batch)} requirements…",
                    "model": model_id,
                }))

                reqs_json = json.dumps(
                    [
                        {
                            "code": r["code"],
                            "name": r["name"],
                            "description": r["description"],
                            "override_context": node_overrides.get(r["code"], ""),
                        }
                        for r in batch
                    ],
                    indent=2,
                )

                user_prompt = PHASE2_CONTROLS_USER_TEMPLATE.format(
                    framework_name=framework_name,
                    framework_type=framework_type_code,
                    requirements_json=reqs_json,
                    user_context=user_context or "(none)",
                    doc_summary=doc_summary[:15_000],
                )

                t0 = _time.monotonic()
                raw_chunks: list[str] = []
                chars_rx = 0
                last_ev_chars = 0
                try:
                    async for chunk in self._llm_stream(PHASE2_CONTROLS_SYSTEM, user_prompt):
                        raw_chunks.append(chunk)
                        chars_rx += len(chunk)
                        if chars_rx - last_ev_chars >= 500:
                            await event_queue.put(_sse("llm_chunk", {
                                "stage": stage_id,
                                "chars_received": chars_rx,
                                "elapsed_seconds": round(_time.monotonic() - t0, 1),
                                "preview": "".join(raw_chunks)[-120:],
                                "model": model_id,
                            }))
                            last_ev_chars = chars_rx
                except Exception as exc:
                    _logger.warning("phase2 batch %s: llm call failed: %s", batch_label, exc)
                    await event_queue.put(_sse("llm_call_error", {
                        "stage": stage_id,
                        "message": f"LLM call failed for {batch_label}: {str(exc)[:200]}",
                    }))
                    return []

                raw = "".join(raw_chunks).strip()
                if raw.startswith("```"):
                    lines = raw.split("\n")
                    raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:]).strip()

                for ev in self._llm_complete_events(stage_id, int(_time.monotonic() - t0), raw):
                    await event_queue.put(ev)

                try:
                    parsed = json.loads(raw)
                except Exception as exc:
                    _logger.warning("phase2 batch %s: parse failed: %s | raw=%s",
                                    batch_label, exc, raw[:200])
                    parsed = None

                # Accept either bare array of controls or {"controls":[...]}
                controls: list[dict] = []
                if isinstance(parsed, list):
                    controls = [c for c in parsed if isinstance(c, dict)]
                elif isinstance(parsed, dict) and isinstance(parsed.get("controls"), list):
                    controls = [c for c in parsed["controls"] if isinstance(c, dict)]

                # Emit per-control events so the frontend UI keeps ticking per requirement
                for ctrl in controls:
                    await event_queue.put(_sse("control_proposed", {
                        "code": ctrl.get("control_code", ""),
                        "name": ctrl.get("name", ""),
                        "requirement_code": ctrl.get("requirement_code", ""),
                        "criticality": ctrl.get("criticality", "medium"),
                        "control_type": ctrl.get("control_type", "preventive"),
                        "automation_potential": ctrl.get("automation_potential", "manual"),
                    }))

                async with completed_lock:
                    completed_batches += 1
                    done_so_far = completed_batches

                _logger.info("phase2 batch %s: %d reqs → %d controls in %.1fs",
                             batch_label, len(batch), len(controls),
                             _time.monotonic() - t0)
                await event_queue.put(_sse("stage_complete", {
                    "stage": stage_id,
                    "message": f"{batch_label} done ({done_so_far}/{total_batches} batches complete)",
                    "control_count": len(controls),
                }))
                return controls

        async def _run_all_batches():
            try:
                results = await asyncio.gather(
                    *(_process_batch(idx, batch) for idx, batch in enumerate(batches))
                )
                for controls_list in results:
                    all_controls.extend(controls_list)
            finally:
                # Sentinel so the drain loop below knows we're done.
                await event_queue.put(None)

        runner_task = asyncio.create_task(_run_all_batches())

        # Drain the queue and stream events to the SSE client as they arrive.
        try:
            while True:
                ev = await event_queue.get()
                if ev is None:
                    break
                yield ev
        finally:
            # Make sure the runner finishes cleanly even if the client disconnects.
            await runner_task

        _logger.info("phase2: %d requirements in %d batches → %d controls total",
                     total_reqs, total_batches, len(all_controls))

        # Risk mapping
        yield _sse("stage_start", {"stage": "risk_mapping", "label": "Mapping controls to risks…"})

        existing_risks_json = json.dumps(
            [{"risk_code": r.get("risk_code"), "title": r.get("title"), "risk_category_code": r.get("risk_category_code")}
             for r in existing_risks[:100]],
            indent=2,
        )
        controls_json = json.dumps(
            [{"control_code": c.get("control_code"), "name": c.get("name"), "requirement_code": c.get("requirement_code"),
              "control_type": c.get("control_type"), "criticality": c.get("criticality")}
             for c in all_controls],
            indent=2,
        )[:15_000]

        risk_prompt = PHASE2_RISKS_USER_TEMPLATE.format(
            existing_risks_json=existing_risks_json,
            controls_json=controls_json,
            user_context=user_context or "(none)",
        )

        model_id = getattr(self._config, "model_id", "unknown")
        yield _sse("llm_call_start", {
            "stage": "risk_mapping",
            "message": "Mapping controls to risks…",
            "model": model_id,
        })
        import time as _time
        t0 = _time.monotonic()
        raw_risk_chunks: list[str] = []
        chars_rx = 0
        last_ev_chars = 0
        async for chunk in self._llm_stream(PHASE2_RISKS_SYSTEM, risk_prompt):
            raw_risk_chunks.append(chunk)
            chars_rx += len(chunk)
            if chars_rx - last_ev_chars >= 200:
                yield _sse("llm_chunk", {
                    "stage": "risk_mapping",
                    "chars_received": chars_rx,
                    "elapsed_seconds": round(_time.monotonic() - t0, 1),
                    "preview": "".join(raw_risk_chunks)[-120:],
                    "model": model_id,
                })
                last_ev_chars = chars_rx
        raw_risks = "".join(raw_risk_chunks).strip()
        if raw_risks.startswith("```"):
            lines = raw_risks.split("\n")
            raw_risks = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:]).strip()
        for ev in self._llm_complete_events("risk_mapping", int(_time.monotonic() - t0), raw_risks):
            yield ev
        try:
            risk_data = json.loads(raw_risks)
        except Exception:
            risk_data = {"mappings": [], "new_risks": []}

        mappings, new_risks = _normalize_risk_mapping_payload(
            controls=all_controls,
            mappings=risk_data.get("mappings", []),
            new_risks=risk_data.get("new_risks", []),
            existing_risks=existing_risks,
        )
        missing_control_codes = _missing_mapped_controls(all_controls, mappings)

        if missing_control_codes:
            yield _sse(
                "stage_start",
                {
                    "stage": "risk_mapping_recovery",
                    "label": f"Recovering mappings for {len(missing_control_codes)} unmapped controls…",
                },
            )
            missing_set = set(missing_control_codes)
            missing_controls = [
                control
                for control in all_controls
                if isinstance(control, dict)
                and _normalize_code(control.get("control_code")) in missing_set
            ]
            recovery_prompt = PHASE2_RISKS_USER_TEMPLATE.format(
                existing_risks_json=existing_risks_json,
                controls_json=json.dumps(
                    [
                        {
                            "control_code": control.get("control_code"),
                            "name": control.get("name"),
                            "requirement_code": control.get("requirement_code"),
                            "control_type": control.get("control_type"),
                            "criticality": control.get("criticality"),
                        }
                        for control in missing_controls
                    ],
                    indent=2,
                )[:15_000],
                user_context=user_context or "(none)",
            )
            model_id = getattr(self._config, "model_id", "unknown")
            yield _sse("llm_call_start", {
                "stage": "risk_mapping_recovery",
                "message": f"Recovering mappings for {len(missing_control_codes)} unmapped controls…",
                "model": model_id,
            })
            import time as _time
            t0 = _time.monotonic()
            retry_chunks: list[str] = []
            chars_rx = 0
            last_ev_chars = 0
            async for chunk in self._llm_stream(PHASE2_RISKS_SYSTEM, recovery_prompt):
                retry_chunks.append(chunk)
                chars_rx += len(chunk)
                if chars_rx - last_ev_chars >= 200:
                    yield _sse("llm_chunk", {
                        "stage": "risk_mapping_recovery",
                        "chars_received": chars_rx,
                        "elapsed_seconds": round(_time.monotonic() - t0, 1),
                        "preview": "".join(retry_chunks)[-120:],
                        "model": model_id,
                    })
                    last_ev_chars = chars_rx
            raw_retry = "".join(retry_chunks).strip()
            if raw_retry.startswith("```"):
                lines = raw_retry.split("\n")
                raw_retry = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:]).strip()
            for ev in self._llm_complete_events("risk_mapping_recovery", int(_time.monotonic() - t0), raw_retry):
                yield ev
            try:
                retry_data = json.loads(raw_retry)
            except Exception:
                retry_data = {"mappings": [], "new_risks": []}

            retry_mappings = retry_data.get("mappings", [])
            if not isinstance(retry_mappings, list):
                retry_mappings = []
            retry_new_risks = retry_data.get("new_risks", [])
            if not isinstance(retry_new_risks, list):
                retry_new_risks = []

            combined_mappings = list(mappings) + retry_mappings
            combined_new_risks = list(new_risks) + retry_new_risks
            mappings, new_risks = _normalize_risk_mapping_payload(
                controls=all_controls,
                mappings=combined_mappings,
                new_risks=combined_new_risks,
                existing_risks=existing_risks,
            )
            missing_control_codes = _missing_mapped_controls(all_controls, mappings)

        if missing_control_codes:
            yield _sse(
                "risk_mapping_warning",
                {
                    "message": "Some controls remain unmapped after recovery.",
                    "unmapped_control_codes": missing_control_codes,
                },
            )

        new_risk_codes = {
            _normalize_code(risk.get("risk_code"))
            for risk in new_risks
            if isinstance(risk, dict) and risk.get("risk_code")
        }

        for mapping in mappings:
            mapped_control_code = _normalize_code(mapping.get("control_code", ""))
            mapped_risk_code = _normalize_code(mapping.get("risk_code", ""))
            yield _sse("risk_mapped", {
                "control_code": mapped_control_code,
                "risk_code": mapped_risk_code,
                "is_new": mapped_risk_code in new_risk_codes,
                "coverage_type": _normalize_coverage_type(mapping.get("coverage_type")),
            })
            await asyncio.sleep(0.02)

        yield _sse("phase2_complete", {
            "control_count": len(all_controls),
            "risk_count": len(new_risks),
            "new_risk_count": len(new_risks),
            "unmapped_control_count": len(missing_control_codes),
            "unmapped_control_codes": missing_control_codes,
            "all_controls": all_controls,
            "new_risks": new_risks,
            "risk_mappings": mappings,
        })

    # ─────────────────────────────────────────────────────────────────────
    # ENHANCE MODE — stream diff proposals
    # ─────────────────────────────────────────────────────────────────────

    async def stream_enhance_diff(
        self,
        *,
        framework_data: dict,
        existing_risks: list[dict],
        user_context: str,
        attachment_ids: list[str],
    ) -> AsyncGenerator[str, None]:
        """Reads existing framework data and streams diff proposals."""

        yield _sse("analyzing_framework", {"message": "Analyzing existing framework for enhancement opportunities…"})

        # Use PageIndex RAG to query each attachment for enhancement-relevant content
        extra_doc_context = ""
        if attachment_ids:
            yield _sse("indexing_documents", {"message": f"Indexing {len(attachment_ids)} document(s) via RAG…"})
            extra_doc_context = await self._retrieve_enhance_findings_from_attachments(
                attachment_ids=attachment_ids,
                framework_data=framework_data,
            )

        full_context = user_context or ""
        if extra_doc_context:
            full_context += f"\n\nFindings from uploaded reference documents:\n{extra_doc_context}"

        framework_json = json.dumps(framework_data, indent=2)[:25_000]

        user_prompt = ENHANCE_USER_TEMPLATE.format(
            framework_name=framework_data.get("name", ""),
            framework_type=framework_data.get("framework_type_code", ""),
            framework_category=framework_data.get("framework_category_code", ""),
            framework_json=framework_json,
            existing_risks_json=json.dumps(
                [
                    {
                        "risk_code": r.get("risk_code"),
                        "title": r.get("title"),
                        "risk_category_code": r.get("risk_category_code"),
                    }
                    for r in (existing_risks or [])[:200]
                ],
                indent=2,
            )[:12_000],
            user_context=full_context or "(none)",
        )

        model_id = getattr(self._config, "model_id", "unknown")
        yield _sse("llm_call_start", {
            "stage": "enhance_analysis",
            "message": "Analyzing framework for enhancements…",
            "model": model_id,
        })
        import time as _time
        t0 = _time.monotonic()
        raw_chunks: list[str] = []
        chars_rx = 0
        last_ev_chars = 0
        async for chunk in self._llm_stream(ENHANCE_SYSTEM, user_prompt):
            raw_chunks.append(chunk)
            chars_rx += len(chunk)
            if chars_rx - last_ev_chars >= 200:
                yield _sse("llm_chunk", {
                    "stage": "enhance_analysis",
                    "chars_received": chars_rx,
                    "elapsed_seconds": round(_time.monotonic() - t0, 1),
                    "preview": "".join(raw_chunks)[-120:],
                    "model": model_id,
                })
                last_ev_chars = chars_rx
        raw = "".join(raw_chunks).strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:]).strip()
        for ev in self._llm_complete_events("enhance_analysis", int(_time.monotonic() - t0), raw):
            yield ev
        try:
            proposals = json.loads(raw)
            if not isinstance(proposals, list):
                proposals = []
        except Exception:
            proposals = []
        proposals = _normalize_enhance_proposals(proposals)

        for proposal in proposals:
            yield _sse("change_proposed", {
                "change_type": proposal.get("change_type"),
                "entity_type": proposal.get("entity_type"),
                "entity_id": proposal.get("entity_id"),
                "entity_code": proposal.get("entity_code"),
                "field": proposal.get("field"),
                "current_value": proposal.get("current_value"),
                "proposed_value": proposal.get("proposed_value"),
                "reason": proposal.get("reason"),
            })
            await asyncio.sleep(0.04)

        yield _sse("enhance_complete", {
            "proposal_count": len(proposals),
            "proposals": proposals,
        })

    # ─────────────────────────────────────────────────────────────────────
    # GAP ANALYSIS — compute structured report
    # ─────────────────────────────────────────────────────────────────────

    async def run_gap_analysis(
        self,
        *,
        framework_data: dict,
        user_context: str = "",
        attachment_ids: list[str] | None = None,
    ) -> dict:
        """Returns structured gap analysis report as a dict. Called from job handler.

        Uses PageIndex RAG (Phase 1 + Phase 2) for attachments so even 1000-page
        audit reports are queried properly — never truncated.
        """
        req_count = len(framework_data.get("requirements", []))
        ctrl_count = len(framework_data.get("controls", []))
        risk_count = len(framework_data.get("risk_mappings", []))

        # ── RAG: index each attachment, then retrieve gap-relevant findings ──
        att_section = ""
        if attachment_ids:
            rag_results = await self._retrieve_gap_findings_from_attachments(
                attachment_ids=attachment_ids,
                framework_data=framework_data,
            )
            if rag_results.strip():
                att_section = (
                    "\nReference document findings (extracted via RAG from uploaded audit reports, "
                    "test results, assessments):\n" + rag_results + "\n"
                )

        framework_json = json.dumps(framework_data, indent=2)[:30_000]
        uc_section = f"\nUser analysis directive:\n{user_context.strip()}\n" if user_context.strip() else ""
        user_prompt = GAP_ANALYSIS_USER_TEMPLATE.format(
            framework_name=framework_data.get("name", ""),
            framework_type=framework_data.get("framework_type_code", ""),
            requirement_count=req_count,
            control_count=ctrl_count,
            risk_count=risk_count,
            framework_json=framework_json,
            user_context_section=uc_section,
            attachment_section=att_section,
        )
        raw = await self._llm_complete(GAP_ANALYSIS_SYSTEM, user_prompt)
        try:
            report = json.loads(raw)
        except Exception:
            report = {"health_score": 0, "findings": [], "error": "Failed to parse gap analysis"}
        return report

    async def _retrieve_gap_findings_from_attachments(
        self,
        *,
        attachment_ids: list[str],
        framework_data: dict,
    ) -> str:
        """Use PageIndex RAG to query each attachment for gap-relevant findings.

        Phase 1 (build_index): full doc text → TOC tree (handles any doc size)
        Phase 2 (retrieve): targeted query against the tree → concise answer
        """
        fw_name = framework_data.get("name", "the framework")
        req_codes = [r.get("code", "") for r in framework_data.get("requirements", [])[:50]]
        query = (
            f"What audit findings, test failures, compliance gaps, missing requirements, "
            f"missing controls, or unaddressed risks does this document identify? "
            f"Focus on findings relevant to the '{fw_name}' framework which has "
            f"requirements: {', '.join(req_codes[:20])}. "
            f"List specific findings with severity if available."
        )

        parts: list[str] = []
        for att_id in attachment_ids:
            try:
                text, filename = await self._fetch_attachment_text(att_id)
                if not text:
                    continue
                # Phase 1: build TOC tree from full document (no truncation)
                tree = await self._indexer.build_index(text)
                if not tree:
                    continue
                # Phase 2: RAG retrieve — targeted query against the tree
                answer = await self._indexer.retrieve(query, tree, filename)
                if answer:
                    parts.append(f"[{filename}]:\n{answer}")
            except Exception as exc:
                _logger.warning("gap_rag_retrieval_failed: %s att=%s", exc, att_id)
        return "\n\n".join(parts)

    async def _retrieve_enhance_findings_from_attachments(
        self,
        *,
        attachment_ids: list[str],
        framework_data: dict,
    ) -> str:
        """Use PageIndex RAG to query each attachment for enhancement-relevant content.

        Same Phase 1 + Phase 2 pattern as gap analysis but with an enhance-focused query.
        """
        fw_name = framework_data.get("name", "the framework")
        req_codes = [r.get("code", "") for r in framework_data.get("requirements", [])[:50]]
        ctrl_codes = [c.get("code", "") for c in framework_data.get("controls", [])[:50]]
        query = (
            f"What requirements, controls, best practices, compliance standards, "
            f"audit recommendations, or regulatory mandates does this document describe "
            f"that could improve or extend the '{fw_name}' framework? "
            f"Current requirements: {', '.join(req_codes[:20])}. "
            f"Current controls: {', '.join(ctrl_codes[:20])}. "
            f"Identify gaps, missing areas, and enhancement opportunities."
        )

        parts: list[str] = []
        for att_id in attachment_ids:
            try:
                text, filename = await self._fetch_attachment_text(att_id)
                if not text:
                    continue
                tree = await self._indexer.build_index(text)
                if not tree:
                    continue
                answer = await self._indexer.retrieve(query, tree, filename)
                if answer:
                    parts.append(f"[{filename}]:\n{answer}")
            except Exception as exc:
                _logger.warning("enhance_rag_retrieval_failed: %s att=%s", exc, att_id)
        return "\n\n".join(parts)

    # ─────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────

    async def _fetch_attachment_text(self, attachment_id: str) -> tuple[str, str]:
        """Returns (extracted_text, filename) for an attachment."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT filename, extracted_text
                FROM "20_ai"."19_fct_attachments"
                WHERE id = $1 AND status_code = 'ready'
                """,
                attachment_id,
            )
        if not row:
            return "", f"attachment_{attachment_id[:8]}"
        return row["extracted_text"] or "", row["filename"] or f"attachment_{attachment_id[:8]}"

    async def _summarize_attachments(self, attachment_ids: list[str]) -> str:
        """Fetches and summarizes all attachments into a single context string."""
        parts = []
        for att_id in attachment_ids:
            try:
                text, filename = await self._fetch_attachment_text(att_id)
                if text and self._indexer:
                    tree = await self._indexer.build_index(text)
                    parts.append(f"[{filename}]: {json.dumps(tree)[:8000]}")
            except Exception as exc:
                _logger.warning("summarize_attachment_failed: %s att=%s", exc, att_id)
        return "\n\n".join(parts)

    async def _llm_complete(
        self,
        system: str,
        user: str,
        *,
        max_retries: int = 10,
        on_retry: object | None = None,
    ) -> str:
        """
        Single LLM completion call with automatic retry (non-streaming).
        Used as fallback when streaming is not needed.
        """
        result = ""
        async for chunk in self._llm_stream(system, user, max_retries=max_retries, on_retry=on_retry):
            result += chunk
        return result

    async def _llm_stream(
        self,
        system: str,
        user: str,
        *,
        max_retries: int = 10,
        on_retry: object | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Streaming LLM completion — yields text chunks as they arrive.

        Retries up to ``max_retries`` times on transient failures (rate limits,
        server errors, timeouts).  If ``on_retry`` is an async callable it is
        invoked with ``(attempt, max_retries, error_message, wait_seconds)`` so
        the caller can emit an SSE event.
        """
        import httpx

        provider_url = getattr(self._config, "provider_base_url", None) or getattr(self._settings, "ai_provider_url", None)
        api_key = getattr(self._config, "api_key", None) or getattr(self._settings, "ai_api_key", None)
        model = getattr(self._config, "model_id", None) or getattr(self._settings, "ai_model", "gpt-4o")

        if not provider_url or not api_key:
            raise RuntimeError("LLM provider URL/API key not configured")

        system_chars = len(system)
        user_chars = len(user)
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 1.0,
            "stream": True,
        }

        _logger.info(
            "llm_stream.request model=%s system_chars=%d user_chars=%d",
            model, system_chars, user_chars,
        )

        last_error: Exception | None = None
        for attempt in range(1, max_retries + 1):
            try:
                full_content = ""
                prompt_tokens = None
                completion_tokens = None
                async with httpx.AsyncClient(timeout=600.0) as client:
                    async with client.stream(
                        "POST",
                        f"{provider_url}/chat/completions",
                        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                        json=payload,
                    ) as resp:
                        resp.raise_for_status()
                        async for line in resp.aiter_lines():
                            if not line.startswith("data: "):
                                continue
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk_data = json.loads(data_str)
                            except json.JSONDecodeError:
                                continue
                            # Extract usage from the final chunk if available
                            usage = chunk_data.get("usage")
                            if usage:
                                prompt_tokens = usage.get("prompt_tokens")
                                completion_tokens = usage.get("completion_tokens")
                            delta = (chunk_data.get("choices") or [{}])[0].get("delta", {})
                            text = delta.get("content", "")
                            if text:
                                full_content += text
                                yield text

                # Strip markdown fences if LLM adds them despite instructions
                content = full_content.strip()
                if content.startswith("```"):
                    lines = content.split("\n")
                    content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

                self._last_llm_meta = {
                    "model": model,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": (prompt_tokens or 0) + (completion_tokens or 0) if prompt_tokens or completion_tokens else None,
                    "system_chars": system_chars,
                    "user_chars": user_chars,
                    "response_chars": len(content),
                    "response_preview": content[:500],
                }
                _logger.info(
                    "llm_stream.response model=%s prompt_tokens=%s completion_tokens=%s response_chars=%d",
                    model, prompt_tokens, completion_tokens, len(content),
                )
                return  # streaming complete — generator done

            except Exception as exc:
                last_error = exc
                error_msg = str(exc)
                status_code = getattr(exc, "status_code", None) or getattr(getattr(exc, "response", None), "status_code", None)
                if status_code:
                    error_msg = f"HTTP {status_code}: {error_msg}"

                if attempt < max_retries:
                    wait = random.randint(60, 300)
                    _logger.warning(
                        "framework_builder.llm_retry attempt=%d/%d error=%s wait=%ds",
                        attempt, max_retries, error_msg, wait,
                    )
                    if callable(on_retry):
                        try:
                            await on_retry(attempt, max_retries, error_msg, wait)
                        except Exception:
                            pass
                    await asyncio.sleep(wait)
                else:
                    _logger.error(
                        "framework_builder.llm_exhausted attempts=%d error=%s",
                        max_retries, error_msg,
                    )

        raise RuntimeError(f"LLM call failed after {max_retries} attempts: {last_error}")
