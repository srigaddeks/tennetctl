# Signal Pipeline — Enterprise Policy Engine

**Version:** 1.0
**Status:** Feature Spec (implementation in progress)
**Last Updated:** 2026-03-20

---

## Vision

K-Control Sandbox is a Python-based, data-consistent compliance policy engine competing with Vanta/Sprinto. The differentiator: customers create their own control tests using AI-assisted signal generation, or use platform-curated control test libraries.

**You don't need to be a developer** — the AI pipeline generates Python functions from natural language descriptions, creates test datasets with expected outputs, and validates everything automatically.

---

## End-to-End Flow

```text
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Connector    │────▶│  Steampipe   │────▶│   Assets     │
│  (data src)   │     │  Collection  │     │  (PG props)  │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                                                  ▼
                                          ┌──────────────┐
                                          │   Dataset    │  ◄── Source of Truth
                                          │  (composed)  │
                                          └──────┬───────┘
                                                  │
                     ┌────────────────────────────┼────────────────────────────┐
                     ▼                            ▼                            ▼
             ┌──────────────┐            ┌──────────────┐            ┌──────────────┐
             │ Signal Spec  │───────────▶│ Test Dataset │───────────▶│   Codegen    │
             │  (Markdown)  │            │ (AI + expect)│            │  (LangGraph) │
             └──────────────┘            └──────────────┘            └──────┬───────┘
                                                                           │
                     ┌─────────────────────────────────────────────────────┘
                     ▼                            ▼                            ▼
             ┌──────────────┐            ┌──────────────┐            ┌──────────────┐
             │   Signals    │───────────▶│ Threat Types │───────────▶│  Libraries   │
             │  (Python fn) │            │ (AND/OR/NOT) │            │ (ctrl packs) │
             └──────────────┘            └──────────────┘            └──────┬───────┘
                     │                                                      │
                     ▼                                                      ▼
             ┌──────────────┐                                      ┌──────────────┐
             │  Test Suite  │                                      │   Global     │
             │  + Live Exec │                                      │   Library    │
             └──────────────┘                                      └──────────────┘
```

---

## Pipeline Stages

| Stage | Module | Job Type | Auto-chains To |
|-------|--------|----------|----------------|
| 1. Signal Spec | `20_ai/22_signal_spec` | (SSE streaming) | → Test Dataset Gen |
| 2. Test Dataset | `20_ai/23_test_dataset_gen` | `signal_test_dataset_gen` | → Signal Codegen |
| 3. Signal Codegen | `20_ai/24_signal_codegen` | `signal_codegen` | → Threat Composer (planned) |
| 4. Threat Composer | `20_ai/25_threat_composer` | `threat_composer` | → Library Builder (planned) |
| 5. Library Builder | `20_ai/26_library_builder` | `library_builder` | (end) |

**Job Queue:** `20_ai/15_job_queue` — `SELECT FOR UPDATE SKIP LOCKED`, configurable per-type concurrency.

---

## Core Principles

1. **Datasets are the source of truth** — Signal specs reference exact JSON field paths from datasets. Schema changes cascade to new signals/tests.
2. **Testing datasets include expected outputs** — Each test case has `dataset_input` + `expected_output`. Control tests compare actual vs expected.
3. **Signals are Python functions with configurable arguments** — `evaluate(dataset, **kwargs)` where kwargs are user-configurable (e.g., `dormant_days=90`).
4. **LangGraph StateGraph** for codegen — Checkpointing (resume on crash), per-node observability, iteration control.
5. **Generated code stored in DB + files** — EAV for execution, filesystem for review/git/IDE.
6. **Sequential queue with configurable parallelism** — 1000 signals run cleanly; max parallel configurable per job type.

---

## Implementation Order (Incremental)

Each step: build API → test API → build UI → test UI with Playwright → next step.

### Step 1: LangGraph Infrastructure + Signal Codegen Refactor
- See: [41_langgraph_infrastructure.md](41_langgraph_infrastructure.md)

### Step 2: Signal Spec Agent (Markdown, Dataset-Grounded)
- See: [42_signal_spec_agent.md](42_signal_spec_agent.md)

### Step 3: Test Dataset Generator (with Expected Outputs)
- See: [43_test_dataset_generator.md](43_test_dataset_generator.md)

### Step 4: Signal Codegen (LangGraph Deep Agent)
- See: [44_signal_codegen_agent.md](44_signal_codegen_agent.md)

### Step 5: Test Suite Execution + Live Execution
- See: [45_signal_test_suite.md](45_signal_test_suite.md)

### Step 6: Threat Composer + Library Builder + Auto-Chaining
- See: [46_threat_library_pipeline.md](46_threat_library_pipeline.md)

### Step 7: File-Based Signal Store
- See: [47_signal_file_store.md](47_signal_file_store.md)

### Step 8: Per-Type Job Concurrency
- See: [48_job_queue_concurrency.md](48_job_queue_concurrency.md)

### Step 9: Dataset Composition + Schema Drift
- See: [49_dataset_composition.md](49_dataset_composition.md)

### Step 10: Global Library + Clone-on-Subscribe
- See: [50_global_library.md](50_global_library.md)
