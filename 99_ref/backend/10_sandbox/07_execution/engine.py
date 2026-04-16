from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

from .models import ExecutionResult


class SignalExecutionEngine:
    """Executes signal Python code in a sandboxed subprocess."""

    def __init__(self, *, timeout_ms: int = 10000, max_memory_mb: int = 256, max_concurrent: int = 10) -> None:
        self._timeout_ms = timeout_ms
        self._max_memory_mb = max_memory_mb
        self._max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._worker_path = str(Path(__file__).parent / "_sandbox_worker.py")

    async def execute(
        self,
        *,
        python_source: str,
        dataset: dict,
        configurable_args: dict | None = None,
        timeout_ms: int | None = None,
        max_memory_mb: int | None = None,
    ) -> ExecutionResult:
        """Execute signal code against dataset in subprocess sandbox."""
        async with self._semaphore:
            return await self._execute_inner(
                python_source=python_source,
                dataset=dataset,
                configurable_args=configurable_args,
                timeout_ms=timeout_ms,
                max_memory_mb=max_memory_mb,
            )

    async def _execute_inner(
        self,
        *,
        python_source: str,
        dataset: dict,
        configurable_args: dict | None = None,
        timeout_ms: int | None = None,
        max_memory_mb: int | None = None,
    ) -> ExecutionResult:
        """Inner execution logic, called under semaphore."""
        timeout = (timeout_ms or self._timeout_ms) / 1000.0
        effective_memory_mb = max_memory_mb or self._max_memory_mb

        payload = {
            "code": python_source,
            "dataset": dataset,
            "max_memory_mb": effective_memory_mb,
        }
        if configurable_args:
            payload["configurable_args"] = configurable_args

        # Guard: reject oversized payloads before spawning subprocess
        input_data = json.dumps(payload)
        if len(input_data) > 2 * 1024 * 1024:  # 2 MB
            return ExecutionResult(
                status="failed",
                error_message=f"Payload too large ({len(input_data) // 1024}KB) — reduce dataset size or configurable_args",
            )

        started_at = time.monotonic()
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, self._worker_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=input_data.encode()),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            proc.kill()  # type: ignore[union-attr]
            await proc.wait()  # type: ignore[union-attr]
            return ExecutionResult(
                status="timeout",
                error_message=f"Execution timed out after {timeout}s",
                execution_time_ms=int((time.monotonic() - started_at) * 1000),
            )
        except Exception as e:
            return ExecutionResult(
                status="failed",
                error_message=str(e),
                execution_time_ms=int((time.monotonic() - started_at) * 1000),
            )

        execution_time_ms = int((time.monotonic() - started_at) * 1000)

        if proc.returncode != 0:
            error_data = stderr.decode() if stderr else "Unknown error"
            try:
                error_json = json.loads(error_data)
                error_msg = error_json.get("error", error_data)
                stdout_capture = error_json.get("stdout", "")
            except json.JSONDecodeError:
                error_msg = error_data
                stdout_capture = ""
            return ExecutionResult(
                status="failed",
                error_message=error_msg,
                stdout_capture=stdout_capture,
                execution_time_ms=execution_time_ms,
            )

        # Parse output
        try:
            output = json.loads(stdout.decode())
        except json.JSONDecodeError:
            return ExecutionResult(
                status="failed",
                error_message="Worker produced invalid JSON output",
                execution_time_ms=execution_time_ms,
            )

        return ExecutionResult(
            status="completed",
            result_code=output.get("result"),
            result_summary=output.get("summary", ""),
            result_details=output.get("details", []),
            metadata=output.get("metadata", {}),
            stdout_capture=output.get("stdout", ""),
            execution_time_ms=execution_time_ms,
        )
