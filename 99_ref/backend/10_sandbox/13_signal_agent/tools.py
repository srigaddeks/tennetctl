from __future__ import annotations

from importlib import import_module

_engine_module = import_module("backend.10_sandbox.07_execution.engine")
SignalExecutionEngine = _engine_module.SignalExecutionEngine


class AgentTools:
    """Toolbox for the signal generation agent — compile checks and sandbox execution."""

    def __init__(self, *, execution_engine: SignalExecutionEngine) -> None:
        self._engine = execution_engine

    async def compile_signal(self, code: str) -> dict:
        """Check if code compiles with RestrictedPython. Returns {success: bool, errors: list}."""
        try:
            from RestrictedPython import compile_restricted

            result = compile_restricted(code, filename="<signal>", mode="exec")
            if result.errors:
                return {"success": False, "errors": list(result.errors)}
            return {"success": True, "errors": []}
        except ImportError:
            # Fallback: basic compile check (dev mode without RestrictedPython)
            try:
                compile(code, "<signal>", "exec")
                return {"success": True, "errors": []}
            except SyntaxError as e:
                return {"success": False, "errors": [str(e)]}

    async def execute_signal(
        self, code: str, dataset: dict, configurable_args: dict | None = None
    ) -> dict:
        """Execute signal in sandbox and return result."""
        result = await self._engine.execute(
            python_source=code,
            dataset=dataset,
            configurable_args=configurable_args or {},
        )
        return {
            "status": result.status,
            "result_code": result.result_code,
            "result_summary": result.result_summary,
            "result_details": result.result_details,
            "metadata": result.metadata,
            "error_message": result.error_message,
            "execution_time_ms": result.execution_time_ms,
        }

    @staticmethod
    def extract_rich_schema(records: list[dict], max_records: int = 5) -> dict:
        """
        Extract a rich schema from up to max_records real dataset records.
        Returns {field_path: {type, example, nullable}} for use by SignalSpecAgent.
        Richer than infer_dataset_schema — includes actual example values.
        """
        sample = records[:max_records]

        def _collect(obj: object, path: str, acc: dict) -> None:
            if isinstance(obj, dict):
                for k, v in obj.items():
                    _collect(v, f"{path}.{k}" if path else k, acc)
            elif isinstance(obj, list):
                if obj:
                    _collect(obj[0], f"{path}[]", acc)
                else:
                    acc[f"{path}[]"] = {"type": "array", "example": None, "nullable": True}
            else:
                if path not in acc:
                    acc[path] = {"type": _infer_leaf_type(obj), "example": obj, "nullable": obj is None}
                else:
                    if obj is None:
                        acc[path]["nullable"] = True

        def _infer_leaf_type(value: object) -> str:
            if value is None:
                return "null"
            if isinstance(value, bool):
                return "boolean"
            if isinstance(value, int):
                return "integer"
            if isinstance(value, float):
                return "number"
            if isinstance(value, str):
                return "string"
            return "unknown"

        result: dict = {}
        for record in sample:
            _collect(record, "", result)
        return result

    @staticmethod
    def infer_dataset_schema(dataset: dict) -> dict:
        """Infer a simplified JSON schema from a dataset sample."""

        def _infer_type(value: object) -> str:
            if isinstance(value, bool):
                return "boolean"
            if isinstance(value, int):
                return "integer"
            if isinstance(value, float):
                return "number"
            if isinstance(value, str):
                return "string"
            if isinstance(value, list):
                return "array"
            if isinstance(value, dict):
                return "object"
            return "unknown"

        def _infer_schema(obj: object) -> object:
            if isinstance(obj, dict):
                return {k: _infer_schema(v) for k, v in obj.items()}
            if isinstance(obj, list) and obj:
                return [_infer_schema(obj[0])]
            return _infer_type(obj)

        return _infer_schema(dataset)  # type: ignore[return-value]
