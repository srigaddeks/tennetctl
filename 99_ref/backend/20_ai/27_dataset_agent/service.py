"""Dataset AI Agent Service — explains, composes, and enhances datasets."""
from __future__ import annotations

import json
from importlib import import_module

_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")

get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods


def _parse_json_response(raw: str) -> dict:
    """Strip markdown fences and parse JSON from LLM response."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        end = len(lines) - 1
        while end > 0 and lines[end].strip() in ("```", ""):
            end -= 1
        text = "\n".join(lines[1:end + 1])
    return json.loads(text)


@instrument_class_methods(
    namespace="ai.dataset_agent.service",
    logger_name="backend.ai.dataset_agent.instrumentation",
)
class DatasetAgentService:
    """AI-powered dataset explanation, composition, and enhancement."""

    def __init__(self, *, database_pool, settings) -> None:
        self._database_pool = database_pool
        self._settings = settings
        self._logger = get_logger("backend.ai.dataset_agent")
        # Build tracer once per service instance
        _tracer_mod = import_module("backend.20_ai.14_llm_providers.langfuse_tracer")
        self._tracer = _tracer_mod.LangFuseTracer.from_settings(settings)

    async def _get_provider(self, org_id: str | None = None):
        """Resolve LLM config and create provider."""
        _resolver_mod = import_module("backend.20_ai.12_agent_config.resolver")
        _config_repo_mod = import_module("backend.20_ai.12_agent_config.repository")
        _factory_mod = import_module("backend.20_ai.14_llm_providers.factory")

        config_repo = _config_repo_mod.AgentConfigRepository()
        resolver = _resolver_mod.AgentConfigResolver(
            repository=config_repo,
            database_pool=self._database_pool,
            settings=self._settings,
        )
        config = await resolver.resolve(
            agent_type_code="dataset_agent",
            org_id=org_id,
        )

        provider = _factory_mod.get_provider(
            provider_type=config.provider_type,
            provider_base_url=config.provider_base_url,
            api_key=config.api_key,
            model_id=config.model_id,
            temperature=config.temperature,
        )
        return provider, config

    async def explain_record(
        self,
        *,
        user_id: str,
        record_data: dict,
        asset_type_hint: str | None = None,
        connector_type: str | None = None,
        org_id: str | None = None,
    ) -> dict:
        """
        Explain every field in a JSON record — what it means, its compliance
        relevance, and what signals could check it.
        """
        from .prompts import SCHEMA_EXPLAINER_SYSTEM

        provider, config = await self._get_provider(org_id)

        trace = self._tracer.trace(
            name="dataset_agent.explain_record",
            user_id=user_id,
            metadata={
                "asset_type": asset_type_hint,
                "connector_type": connector_type,
                "field_count": len(record_data),
            },
            tags=["dataset_agent", "explain_record"],
        )

        context_parts = []
        if asset_type_hint:
            context_parts.append(f"Asset type: {asset_type_hint}")
        if connector_type:
            context_parts.append(f"Connector/Integration: {connector_type}")

        messages = [
            {"role": "system", "content": SCHEMA_EXPLAINER_SYSTEM},
            {"role": "user", "content": f"""Explain this JSON record:

{json.dumps(record_data, indent=2, default=str)[:8000]}

{chr(10).join(context_parts)}"""},
        ]

        gen = self._tracer.generation(
            trace,
            name="explain_record",
            model=config.model_id,
            input=messages,
            metadata={"field_count": len(record_data), "asset_type": asset_type_hint},
        )

        try:
            response = await provider.chat_completion(
                messages=messages,
                temperature=1.0,
                max_tokens=None,
            )
            gen.end(
                output=response.content,
                usage={"input": response.input_tokens, "output": response.output_tokens},
            )
        except Exception as exc:
            gen.end(level="ERROR", status_message=str(exc)[:500])
            raise

        try:
            result = _parse_json_response(response.content)
            self._tracer.score(trace, name="field_count",
                               value=len(result.get("fields", [])) / max(len(record_data), 1))
            return result
        except (json.JSONDecodeError, AttributeError) as exc:
            self._logger.warning("explain_record: failed to parse LLM response: %s", exc)
            self._tracer.event(trace, name="parse_failed", level="WARNING",
                               metadata={"error": str(exc)[:300]})
            return {
                "asset_type": asset_type_hint or "unknown",
                "record_summary": "Failed to generate explanation",
                "total_fields": len(record_data),
                "fields": [
                    {"field_name": k, "data_type": type(v).__name__, "description": "",
                     "compliance_relevance": "unknown", "example_signal_uses": [], "anomaly_indicators": []}
                    for k, v in record_data.items()
                ],
                "recommended_signals": [],
            }

    async def compose_test_data(
        self,
        *,
        user_id: str,
        property_keys: list[str],
        sample_records: list[dict],
        asset_type: str,
        connector_type: str | None = None,
        record_count: int = 10,
        org_id: str | None = None,
    ) -> dict:
        """
        Generate varied, realistic test dataset records from a schema.
        Covers compliant, non-compliant, mixed, and edge case scenarios.
        """
        from .prompts import DATASET_COMPOSER_SYSTEM

        provider, config = await self._get_provider(org_id)

        trace = self._tracer.trace(
            name="dataset_agent.compose_test_data",
            user_id=user_id,
            metadata={
                "asset_type": asset_type,
                "connector_type": connector_type,
                "record_count": record_count,
                "field_count": len(property_keys),
            },
            tags=["dataset_agent", "compose_test_data"],
        )

        schema_info = f"Asset type: {asset_type}\n"
        if connector_type:
            schema_info += f"Connector: {connector_type}\n"
        schema_info += f"Fields ({len(property_keys)}): {', '.join(property_keys[:50])}\n"

        if sample_records:
            schema_info += f"\nSample records ({len(sample_records)}):\n"
            for i, rec in enumerate(sample_records[:3]):
                schema_info += f"\n--- Sample {i+1} ---\n{json.dumps(rec, indent=2, default=str)[:3000]}\n"

        user_message = f"""Generate {record_count} varied test records for this asset type.

{schema_info}

Generate records that cover ALL compliance scenarios: fully secure, fully insecure, mixed, edge cases.
Each record MUST have all the fields listed above plus _scenario_name, _expected_result, _explanation."""

        messages = [
            {"role": "system", "content": DATASET_COMPOSER_SYSTEM},
            {"role": "user", "content": user_message},
        ]

        gen = self._tracer.generation(
            trace,
            name="compose_test_data",
            model=config.model_id,
            input=messages,
            metadata={"record_count": record_count, "asset_type": asset_type},
        )

        try:
            response = await provider.chat_completion(
                messages=messages,
                temperature=1.0,
                max_tokens=None,
            )
            gen.end(
                output=response.content,
                usage={"input": response.input_tokens, "output": response.output_tokens},
            )
        except Exception as exc:
            gen.end(level="ERROR", status_message=str(exc)[:500])
            raise

        try:
            result = _parse_json_response(response.content)
            generated = result.get("generated_records", [])
            self._tracer.score(trace, name="record_yield",
                               value=len(generated) / max(record_count, 1))
            return result
        except (json.JSONDecodeError, AttributeError) as exc:
            self._logger.warning("compose_test_data: failed to parse LLM response: %s", exc)
            self._tracer.event(trace, name="parse_failed", level="WARNING",
                               metadata={"error": str(exc)[:300]})
            return {
                "asset_type": asset_type,
                "schema_summary": "Failed to generate test data",
                "generated_records": [],
                "coverage_notes": f"Error: {exc}",
            }

    async def enhance_dataset(
        self,
        *,
        user_id: str,
        records: list[dict],
        asset_type: str = "",
        connector_type: str | None = None,
        org_id: str | None = None,
    ) -> dict:
        """
        Analyze an existing dataset and suggest improvements —
        missing scenarios, poor field coverage, quality gaps.
        """
        from .prompts import DATASET_ENHANCE_SYSTEM

        provider, config = await self._get_provider(org_id)

        trace = self._tracer.trace(
            name="dataset_agent.enhance_dataset",
            user_id=user_id,
            metadata={
                "asset_type": asset_type,
                "connector_type": connector_type,
                "record_count": len(records),
            },
            tags=["dataset_agent", "enhance_dataset"],
        )

        records_text = json.dumps(records[:50], indent=2, default=str)[:10000]
        user_message = f"""Analyze this dataset and suggest improvements.

Asset type: {asset_type or 'unknown'}
Connector: {connector_type or 'unknown'}
Records ({len(records)} total, showing up to 50):

{records_text}

Identify gaps, missing scenarios, and suggest specific improvements."""

        messages = [
            {"role": "system", "content": DATASET_ENHANCE_SYSTEM},
            {"role": "user", "content": user_message},
        ]

        gen = self._tracer.generation(
            trace,
            name="enhance_dataset",
            model=config.model_id,
            input=messages,
            metadata={"record_count": len(records), "asset_type": asset_type},
        )

        try:
            response = await provider.chat_completion(
                messages=messages,
                temperature=1.0,
                max_tokens=None,
            )
            gen.end(
                output=response.content,
                usage={"input": response.input_tokens, "output": response.output_tokens},
            )
        except Exception as exc:
            gen.end(level="ERROR", status_message=str(exc)[:500])
            raise

        try:
            result = _parse_json_response(response.content)
            quality_score = result.get("quality_score", 0)
            if isinstance(quality_score, (int, float)):
                self._tracer.score(trace, name="quality_score",
                                   value=min(quality_score / 100, 1.0))
            return result
        except (json.JSONDecodeError, AttributeError) as exc:
            self._logger.warning("enhance_dataset: failed to parse LLM response: %s", exc)
            return {
                "quality_score": 0,
                "strengths": [],
                "gaps": [{"gap": f"Analysis failed: {exc}", "severity": "high", "suggestion": "Retry"}],
                "missing_scenarios": [],
                "field_coverage": {},
            }

    async def explain_dataset_batch(
        self,
        *,
        user_id: str,
        records: list[dict],
        asset_type: str = "",
        connector_type: str | None = None,
        org_id: str | None = None,
    ) -> dict:
        """
        Batch-explain all records in a dataset. Each record gets a summary
        explanation attached. Also generates a dataset-level schema overview.
        """
        provider, config = await self._get_provider(org_id)

        trace = self._tracer.trace(
            name="dataset_agent.explain_batch",
            user_id=user_id,
            metadata={
                "asset_type": asset_type,
                "connector_type": connector_type,
                "record_count": len(records),
            },
            tags=["dataset_agent", "explain_batch"],
        )

        all_keys = set()
        for r in records:
            all_keys.update(r.keys())

        system = f"""You are a data schema expert for compliance automation.

Analyze this dataset of {len(records)} records (asset type: {asset_type or 'unknown'}, connector: {connector_type or 'unknown'}).

Return JSON:
{{
  "dataset_summary": "What this dataset represents overall",
  "asset_type": "{asset_type}",
  "schema_fields": [
    {{
      "field_name": "...",
      "data_type": "...",
      "description": "What this field means",
      "compliance_relevance": "high|medium|low|none",
      "value_distribution": "Brief note on value variety across records"
    }}
  ],
  "record_explanations": [
    {{
      "record_index": 0,
      "summary": "One-line explanation of what this specific record represents",
      "compliance_status": "compliant|non_compliant|mixed|edge_case",
      "key_observations": ["observation1", "observation2"]
    }}
  ],
  "overall_quality": "good|fair|poor",
  "improvement_suggestions": ["suggestion1", "suggestion2"]
}}

Explain EVERY record (up to 30). Be specific about WHY each record matters for testing."""

        records_text = json.dumps(records[:30], indent=2, default=str)[:12000]
        user_message = f"All fields across dataset: {', '.join(sorted(all_keys))}\n\nRecords:\n{records_text}"

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ]

        gen = self._tracer.generation(
            trace,
            name="explain_batch",
            model=config.model_id,
            input=messages,
            metadata={"record_count": len(records), "field_count": len(all_keys)},
        )

        try:
            response = await provider.chat_completion(
                messages=messages,
                temperature=1.0,
                max_tokens=None,
            )
            gen.end(
                output=response.content,
                usage={"input": response.input_tokens, "output": response.output_tokens},
            )
        except Exception as exc:
            gen.end(level="ERROR", status_message=str(exc)[:500])
            raise

        try:
            result = _parse_json_response(response.content)
            explained_count = len(result.get("record_explanations", []))
            self._tracer.score(trace, name="explain_coverage",
                               value=explained_count / max(len(records), 1))
            return result
        except (json.JSONDecodeError, AttributeError) as exc:
            self._logger.warning("explain_dataset_batch: failed to parse: %s", exc)
            return {
                "dataset_summary": "Analysis failed",
                "schema_fields": [],
                "record_explanations": [],
                "overall_quality": "unknown",
                "improvement_suggestions": [str(exc)],
            }
