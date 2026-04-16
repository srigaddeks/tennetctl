from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskTypeRecord:
    code: str
    name: str
    description: str
    sort_order: int


@dataclass(frozen=True)
class TaskPriorityRecord:
    code: str
    name: str
    description: str
    sort_order: int


@dataclass(frozen=True)
class TaskStatusRecord:
    code: str
    name: str
    description: str
    is_terminal: bool
    sort_order: int
