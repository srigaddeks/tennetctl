"""
LangFuse Tracer
===============
Unified observability layer for all AI agents. Every LLM call, every iteration,
every validation result flows through here to LangFuse.

Usage:
    tracer = LangFuseTracer.from_settings(settings)

    # Start a root trace for the entire job/session
    trace = tracer.trace(name="signal_codegen", job_id="...", user_id="...", metadata={...})

    # Nested generation span (each LLM call)
    with tracer.generation(trace, name="generate_code", model="gpt-4o", input=messages) as gen:
        response = await llm.chat_completion(...)
        gen.end(output=response.content, usage={"input": response.input_tokens, "output": response.output_tokens})

    # Log a structured event
    tracer.event(trace, name="compile_check", metadata={"error": "...", "iteration": 2})

    # Score the trace (e.g. pass rate)
    tracer.score(trace, name="test_pass_rate", value=0.85)

    # Flush before process exit (optional — auto-flushes on GC)
    tracer.flush()

When LangFuse is disabled (ai_langfuse_enabled=False), all operations are
no-ops — zero overhead, no imports loaded.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from importlib import import_module
from typing import Any, Generator

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.langfuse_tracer")


class _NoopTrace:
    """Zero-overhead trace when LangFuse is disabled."""
    id = "noop"

    def update(self, **kwargs) -> None: pass
    def score(self, **kwargs) -> None: pass
    def generation(self, **kwargs) -> "_NoopGeneration": return _NoopGeneration()
    def span(self, **kwargs) -> "_NoopSpan": return _NoopSpan()
    def event(self, **kwargs) -> None: pass


class _NoopGeneration:
    def end(self, **kwargs) -> None: pass
    def __enter__(self): return self
    def __exit__(self, *args): pass


class _NoopSpan:
    def end(self, **kwargs) -> None: pass
    def __enter__(self): return self
    def __exit__(self, *args): pass


class _LiveGeneration:
    """Wraps a LangFuse generation object, records timing on exit."""

    def __init__(self, generation_obj, *, start_ms: float) -> None:
        self._gen = generation_obj
        self._start_ms = start_ms

    def end(
        self,
        *,
        output: str | None = None,
        usage: dict | None = None,
        level: str = "DEFAULT",
        status_message: str | None = None,
    ) -> None:
        latency_ms = int((time.perf_counter() * 1000) - self._start_ms)
        kwargs: dict[str, Any] = {
            "end_time": None,  # LangFuse records NOW() internally
            "level": level,
        }
        if output is not None:
            kwargs["output"] = output[:8000] if isinstance(output, str) else output
        if usage:
            kwargs["usage"] = usage
        if status_message:
            kwargs["status_message"] = status_message
        try:
            self._gen.end(**kwargs)
        except Exception as exc:
            _logger.debug("langfuse.generation_end_failed: %s", exc)

    def __enter__(self) -> "_LiveGeneration":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            self.end(level="ERROR", status_message=str(exc_val)[:500])
        else:
            self.end()


class LangFuseTracer:
    """
    Thread-safe, async-compatible LangFuse tracer.

    All public methods are synchronous (LangFuse SDK is sync/fire-and-forget).
    Heavy LLM calls are async; tracing is a synchronous side channel.
    """

    def __init__(self, *, langfuse_client) -> None:
        self._client = langfuse_client
        self._enabled = True

    @classmethod
    def from_settings(cls, settings) -> "LangFuseTracer":
        """
        Build a tracer from app settings.
        Returns a no-op tracer if LangFuse is disabled or not configured.
        """
        if not getattr(settings, "ai_langfuse_enabled", False):
            return cls._noop()

        public_key = getattr(settings, "ai_langfuse_public_key", None)
        secret_key = getattr(settings, "ai_langfuse_secret_key", None)
        if not public_key or not secret_key:
            _logger.warning(
                "langfuse.missing_keys: ai_langfuse_enabled=true but public/secret keys not set"
            )
            return cls._noop()

        try:
            langfuse_mod = import_module("langfuse")
            host = getattr(settings, "ai_langfuse_host", None)
            init_kwargs: dict[str, Any] = {
                "public_key": public_key,
                "secret_key": secret_key,
                "enabled": True,
                "debug": False,
            }
            if host:
                init_kwargs["host"] = host

            client = langfuse_mod.Langfuse(**init_kwargs)
            _logger.info("langfuse.initialized", extra={"host": host or "cloud.langfuse.com"})
            return cls(langfuse_client=client)

        except ImportError:
            _logger.warning("langfuse.not_installed: pip install langfuse to enable tracing")
            return cls._noop()
        except Exception as exc:
            _logger.warning("langfuse.init_failed: %s", exc)
            return cls._noop()

    @classmethod
    def _noop(cls) -> "LangFuseTracer":
        instance = cls.__new__(cls)
        instance._client = None
        instance._enabled = False
        return instance

    # ── Root trace ─────────────────────────────────────────────────────────────

    def trace(
        self,
        *,
        name: str,
        job_id: str | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
        metadata: dict | None = None,
        tags: list[str] | None = None,
    ) -> Any:
        """
        Create a root-level LangFuse trace. Returns a trace object (or noop).

        Use job_id as session_id to correlate all spans in one job execution.
        """
        if not self._enabled:
            return _NoopTrace()
        try:
            kwargs: dict[str, Any] = {"name": name}
            if session_id or job_id:
                kwargs["session_id"] = session_id or job_id
            if user_id:
                kwargs["user_id"] = user_id
            if metadata:
                kwargs["metadata"] = metadata
            if tags:
                kwargs["tags"] = tags
            return self._client.trace(**kwargs)
        except Exception as exc:
            _logger.debug("langfuse.trace_failed: %s", exc)
            return _NoopTrace()

    # ── Generation (LLM call) ──────────────────────────────────────────────────

    def generation(
        self,
        trace,
        *,
        name: str,
        model: str,
        input: list[dict] | str,
        metadata: dict | None = None,
        level: str = "DEFAULT",
    ) -> _LiveGeneration | _NoopGeneration:
        """
        Open a generation span for one LLM call.

        Returns a context manager. Call .end(output=..., usage=...) when done,
        or use as `with tracer.generation(...) as gen:`.

        Example:
            gen = tracer.generation(trace, name="generate", model="gpt-4o", input=messages)
            response = await llm.chat_completion(...)
            gen.end(output=response.content, usage={"input": response.input_tokens, "output": response.output_tokens})
        """
        if not self._enabled:
            return _NoopGeneration()
        try:
            start_ms = time.perf_counter() * 1000
            kwargs: dict[str, Any] = {
                "name": name,
                "model": model,
                "input": input,
                "level": level,
            }
            if metadata:
                kwargs["metadata"] = metadata
            gen_obj = trace.generation(**kwargs)
            return _LiveGeneration(gen_obj, start_ms=start_ms)
        except Exception as exc:
            _logger.debug("langfuse.generation_failed: %s", exc)
            return _NoopGeneration()

    # ── Span (non-LLM step) ────────────────────────────────────────────────────

    def span(
        self,
        trace,
        *,
        name: str,
        input: dict | str | None = None,
        metadata: dict | None = None,
    ) -> Any:
        """Open a non-LLM span (e.g. compile check, structural diff, DB write)."""
        if not self._enabled:
            return _NoopSpan()
        try:
            kwargs: dict[str, Any] = {"name": name}
            if input is not None:
                kwargs["input"] = input
            if metadata:
                kwargs["metadata"] = metadata
            span_obj = trace.span(**kwargs)

            class _LiveSpan:
                def end(self_, *, output=None, level="DEFAULT", **kw):
                    try:
                        end_kwargs = {"level": level}
                        if output is not None:
                            end_kwargs["output"] = output
                        end_kwargs.update(kw)
                        span_obj.end(**end_kwargs)
                    except Exception:
                        pass
                def __enter__(self_): return self_
                def __exit__(self_, *args): self_.end()

            return _LiveSpan()
        except Exception as exc:
            _logger.debug("langfuse.span_failed: %s", exc)
            return _NoopSpan()

    # ── Event (point-in-time log) ──────────────────────────────────────────────

    def event(
        self,
        trace,
        *,
        name: str,
        metadata: dict | None = None,
        level: str = "DEFAULT",
        input: dict | None = None,
        output: dict | None = None,
    ) -> None:
        """Log a point-in-time event (no duration)."""
        if not self._enabled:
            return
        try:
            kwargs: dict[str, Any] = {"name": name, "level": level}
            if metadata:
                kwargs["metadata"] = metadata
            if input is not None:
                kwargs["input"] = input
            if output is not None:
                kwargs["output"] = output
            trace.event(**kwargs)
        except Exception as exc:
            _logger.debug("langfuse.event_failed: %s", exc)

    # ── Score ──────────────────────────────────────────────────────────────────

    def score(
        self,
        trace,
        *,
        name: str,
        value: float,
        comment: str | None = None,
    ) -> None:
        """Attach a numeric score to a trace (e.g. test pass rate, confidence)."""
        if not self._enabled:
            return
        try:
            kwargs: dict[str, Any] = {"trace_id": trace.id, "name": name, "value": value}
            if comment:
                kwargs["comment"] = comment
            self._client.score(**kwargs)
        except Exception as exc:
            _logger.debug("langfuse.score_failed: %s", exc)

    # ── Flush ──────────────────────────────────────────────────────────────────

    def flush(self) -> None:
        """Flush all pending events. Call before process shutdown."""
        if not self._enabled or not self._client:
            return
        try:
            self._client.flush()
        except Exception as exc:
            _logger.debug("langfuse.flush_failed: %s", exc)

    @property
    def enabled(self) -> bool:
        return self._enabled
