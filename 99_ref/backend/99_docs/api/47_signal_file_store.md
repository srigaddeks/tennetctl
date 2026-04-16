# Signal File Store

**Priority:** P1 — cleaner code management
**Status:** New module
**Module:** `backend/10_sandbox/signal_store/`

---

## Overview

Generated signal Python code is stored in both DB (EAV, source of truth for execution) and filesystem (for review, git tracking, IDE access). The file store provides a clean directory structure per org/signal/version.

---

## Directory Structure

```text
{SIGNAL_STORE_ROOT}/
  {org_id}/
    {signal_code}/
      v{version}/
        evaluate.py          — the Python evaluate() function
        spec.md              — the Markdown signal spec
        args_schema.json     — configurable arguments: [{name, type, default, label, description}]
        test_bundle.json     — test cases with expected outputs
        metadata.json        — signal_id, org_id, created_at, codegen_iterations, status
```

**Config:** `SIGNAL_STORE_ROOT` env var (default: `./signal_store` for dev, `/data/signals` for prod)

---

## Writer Service

```python
class SignalFileWriter:
    def __init__(self, store_root: str):
        self._root = Path(store_root)

    async def write_signal(
        self,
        org_id: str,
        signal_code: str,
        version: int,
        python_code: str,
        spec_markdown: str,
        args_schema: list[dict],
        test_bundle: list[dict],
        metadata: dict,
    ) -> Path:
        """Write all signal files atomically (temp dir → rename)."""

    async def read_signal(self, org_id: str, signal_code: str, version: int) -> dict:
        """Read all signal files. Returns dict with code, spec, args_schema, test_bundle, metadata."""

    async def list_signals(self, org_id: str) -> list[dict]:
        """List all signals for an org. Returns [{signal_code, versions: [1, 2, ...]}]."""

    async def list_versions(self, org_id: str, signal_code: str) -> list[int]:
        """List all versions for a signal."""
```

**Atomic writes:** Write to temp dir first, then `os.rename()` to final path. Prevents partial writes on crash.

---

## Integration Points

| When | Who Calls Writer |
|------|-----------------|
| Codegen success | `write_files` node in codegen graph |
| Spec approved | `approve_spec()` in signal spec service (writes spec.md) |
| Test dataset generated | Test dataset gen handler (writes test_bundle.json) |
| Manual signal edit | Signal service `update_signal()` |

---

## Settings

Add to `backend/00_config/settings.py`:

```python
signal_store_root: str  # Env: SIGNAL_STORE_ROOT, default ./signal_store
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `backend/10_sandbox/signal_store/__init__.py` | Module init |
| `backend/10_sandbox/signal_store/writer.py` | SignalFileWriter class |

---

## Verification

1. Generate signal → verify files exist at `{root}/{org_id}/{signal_code}/v1/`
2. Read back `evaluate.py` → verify matches `python_source` EAV property
3. Create v2 of signal → verify v1 and v2 directories both exist
4. Atomic write: simulate crash during write → verify no partial files
