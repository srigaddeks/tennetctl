from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvidenceReference:
    document_filename: str
    page_number: int | None
    section_or_sheet: str | None
    excerpt: str  # capped at 150 chars
    confidence: float  # 0.0–1.0


@dataclass
class CriterionResult:
    criterion_id: str | None
    criterion_text: str
    verdict: str  # MET | PARTIALLY_MET | NOT_MET | INSUFFICIENT_EVIDENCE
    threshold_met: bool | None
    justification: str
    gap_analysis: str | None = None  # What specific evidence is missing (for non-MET verdicts)
    evidence_references: list[EvidenceReference] = field(default_factory=list)
    conflicting_references: list[EvidenceReference] = field(default_factory=list)
    agent_run_id: str | None = None
    langfuse_trace_id: str | None = None


@dataclass
class EvidenceReport:
    job_id: str
    task_id: str
    overall_verdict: str  # ALL_MET | PARTIALLY_MET | NOT_MET | INCONCLUSIVE
    attachment_count: int
    total_pages_analyzed: int
    tokens_consumed: int
    duration_seconds: float
    langfuse_trace_id: str | None
    criteria_results: list[CriterionResult] = field(default_factory=list)


@dataclass
class Criterion:
    id: str | None
    text: str
    threshold: str | None = None


@dataclass
class ChunkResult:
    text: str
    document_filename: str
    page_number: int | None
    section_or_sheet: str | None
    attachment_id: str
    chunk_index: int
    score: float  # similarity score from Qdrant


@dataclass
class IngestionResult:
    attachment_id: str
    pages_processed: int
    chunks_indexed: int
    error: str | None = None
