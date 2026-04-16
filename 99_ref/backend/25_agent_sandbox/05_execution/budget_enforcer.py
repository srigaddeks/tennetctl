"""
Budget enforcer — tracks and enforces per-run budget limits.

Checked before every ctx.llm() and ctx.tool() call.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field


class BudgetExceededError(Exception):
    """Raised when a budget limit is exceeded."""

    def __init__(self, limit_name: str, current: int | float, maximum: int | float) -> None:
        self.limit_name = limit_name
        self.current = current
        self.maximum = maximum
        super().__init__(f"budget_exceeded:{limit_name} (current={current}, max={maximum})")


@dataclass
class BudgetState:
    """Mutable budget state tracked during execution."""
    tokens_used: int = 0
    tool_calls_made: int = 0
    llm_calls_made: int = 0
    cost_usd: float = 0.0
    iterations_used: int = 0
    start_time: float = field(default_factory=time.time)


class BudgetEnforcer:
    """Enforces budget limits for an agent run."""

    def __init__(
        self,
        *,
        max_tokens_budget: int,
        max_tool_calls: int,
        max_iterations: int,
        max_duration_ms: int,
        max_cost_usd: float,
    ) -> None:
        self._max_tokens = max_tokens_budget
        self._max_tool_calls = max_tool_calls
        self._max_iterations = max_iterations
        self._max_duration_ms = max_duration_ms
        self._max_cost_usd = max_cost_usd
        self._state = BudgetState()

    @property
    def state(self) -> BudgetState:
        return self._state

    def check_all(self) -> None:
        """Check all budget limits. Raises BudgetExceededError if any exceeded."""
        self._check_tokens()
        self._check_tool_calls()
        self._check_iterations()
        self._check_duration()
        self._check_cost()

    def check_before_llm(self) -> None:
        """Check limits before making an LLM call."""
        self._check_tokens()
        self._check_duration()
        self._check_cost()

    def check_before_tool(self) -> None:
        """Check limits before making a tool call."""
        self._check_tool_calls()
        self._check_duration()
        self._check_cost()

    def check_before_iteration(self) -> None:
        """Check limits before a new graph node transition."""
        self._check_iterations()
        self._check_duration()

    def record_llm_call(self, tokens: int, cost_usd: float) -> None:
        """Record an LLM call's token usage and cost."""
        self._state.tokens_used += tokens
        self._state.cost_usd += cost_usd
        self._state.llm_calls_made += 1

    def record_tool_call(self) -> None:
        """Record a tool call."""
        self._state.tool_calls_made += 1

    def record_iteration(self) -> None:
        """Record a graph node transition."""
        self._state.iterations_used += 1

    def elapsed_ms(self) -> int:
        """Return elapsed time since start in milliseconds."""
        return int((time.time() - self._state.start_time) * 1000)

    def pct_tokens(self) -> float:
        return (self._state.tokens_used / self._max_tokens * 100) if self._max_tokens > 0 else 0

    def pct_cost(self) -> float:
        return (self._state.cost_usd / self._max_cost_usd * 100) if self._max_cost_usd > 0 else 0

    def _check_tokens(self) -> None:
        if self._state.tokens_used >= self._max_tokens:
            raise BudgetExceededError("max_tokens_budget", self._state.tokens_used, self._max_tokens)

    def _check_tool_calls(self) -> None:
        if self._state.tool_calls_made >= self._max_tool_calls:
            raise BudgetExceededError("max_tool_calls", self._state.tool_calls_made, self._max_tool_calls)

    def _check_iterations(self) -> None:
        if self._state.iterations_used >= self._max_iterations:
            raise BudgetExceededError("max_iterations", self._state.iterations_used, self._max_iterations)

    def _check_duration(self) -> None:
        elapsed = self.elapsed_ms()
        if elapsed >= self._max_duration_ms:
            raise BudgetExceededError("max_duration_ms", elapsed, self._max_duration_ms)

    def _check_cost(self) -> None:
        if self._state.cost_usd >= self._max_cost_usd:
            raise BudgetExceededError("max_cost_usd", self._state.cost_usd, self._max_cost_usd)
