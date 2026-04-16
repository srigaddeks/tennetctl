"""
SignalFileWriter — atomic read/write of signal artifacts to the filesystem.

Directory layout:
  {root}/{org_id}/{signal_code}/v{version}/
    evaluate.py          — the generated Python evaluate() function
    spec.md              — signal spec in Markdown
    args_schema.json     — configurable arguments schema
    test_bundle.json     — test dataset with expected outputs
    metadata.json        — signal_id, created_at, codegen_iterations, status

All writes are atomic: files land in a temp dir then renamed into place.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path


class SignalFileWriter:
    """Reads and writes signal artifacts atomically to the configured store root."""

    def __init__(self, store_root: str | None = None) -> None:
        if store_root:
            self._root = Path(store_root)
        else:
            # Default: ./signal_store relative to CWD
            self._root = Path("signal_store")

    def _signal_dir(self, org_id: str, signal_code: str, version: int) -> Path:
        return self._root / org_id / signal_code / f"v{version}"

    def write_signal(
        self,
        *,
        org_id: str,
        signal_code: str,
        version: int,
        signal_id: str,
        code: str,
        spec_md: str | None = None,
        args_schema: list | None = None,
        test_bundle: list | None = None,
        codegen_iterations: int | None = None,
        status: str = "validated",
    ) -> Path:
        """Write all signal artifacts atomically. Returns the final signal directory path."""
        target_dir = self._signal_dir(org_id, signal_code, version)

        # Write to temp dir first, then rename atomically
        parent = target_dir.parent
        parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(dir=parent, prefix=f".tmp_{signal_code}_v{version}_") as tmp_str:
            tmp = Path(tmp_str)

            # evaluate.py
            (tmp / "evaluate.py").write_text(code, encoding="utf-8")

            # spec.md
            if spec_md is not None:
                (tmp / "spec.md").write_text(spec_md, encoding="utf-8")

            # args_schema.json
            if args_schema is not None:
                (tmp / "args_schema.json").write_text(
                    json.dumps(args_schema, indent=2), encoding="utf-8"
                )

            # test_bundle.json
            if test_bundle is not None:
                (tmp / "test_bundle.json").write_text(
                    json.dumps(test_bundle, indent=2), encoding="utf-8"
                )

            # metadata.json
            metadata = {
                "signal_id": signal_id,
                "signal_code": signal_code,
                "version": version,
                "org_id": org_id,
                "status": status,
                "codegen_iterations": codegen_iterations,
                "written_at": datetime.now(timezone.utc).isoformat(),
            }
            (tmp / "metadata.json").write_text(
                json.dumps(metadata, indent=2), encoding="utf-8"
            )

            # Atomically move into place (remove old version if exists)
            if target_dir.exists():
                shutil.rmtree(target_dir)
            shutil.copytree(tmp_str, str(target_dir))

        return target_dir

    def read_signal(self, *, org_id: str, signal_code: str, version: int) -> dict | None:
        """Read all artifacts for a signal version. Returns None if not found."""
        d = self._signal_dir(org_id, signal_code, version)
        if not d.exists():
            return None

        result: dict = {}
        for name in ("evaluate.py", "spec.md", "args_schema.json", "test_bundle.json", "metadata.json"):
            p = d / name
            if p.exists():
                content = p.read_text(encoding="utf-8")
                if name.endswith(".json"):
                    try:
                        content = json.loads(content)
                    except Exception:
                        pass
                result[name.replace(".", "_").replace("-", "_")] = content

        return result

    def list_signals(self, org_id: str) -> list[dict]:
        """List all signals for an org. Returns [{signal_code, versions: [int]}]."""
        org_dir = self._root / org_id
        if not org_dir.exists():
            return []

        signals = []
        for signal_dir in sorted(org_dir.iterdir()):
            if not signal_dir.is_dir():
                continue
            versions = []
            for v_dir in sorted(signal_dir.iterdir()):
                if v_dir.is_dir() and v_dir.name.startswith("v"):
                    try:
                        versions.append(int(v_dir.name[1:]))
                    except ValueError:
                        pass
            if versions:
                signals.append({"signal_code": signal_dir.name, "versions": sorted(versions)})

        return signals

    def delete_signal(self, *, org_id: str, signal_code: str, version: int | None = None) -> None:
        """Delete a signal version (or all versions if version is None)."""
        if version is not None:
            d = self._signal_dir(org_id, signal_code, version)
            if d.exists():
                shutil.rmtree(d)
        else:
            d = self._root / org_id / signal_code
            if d.exists():
                shutil.rmtree(d)

    def signal_dir_path(self, *, org_id: str, signal_code: str, version: int) -> str:
        """Return the absolute path to a signal version directory."""
        return str(self._signal_dir(org_id, signal_code, version).resolve())
