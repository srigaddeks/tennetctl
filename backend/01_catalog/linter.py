"""
Cross-import linter — enforces NCP v1 §10.

Sub-features cannot import from other sub-features' non-node modules.
Allowed:
  - imports within the same sub-feature
  - imports from backend.01_core.* / backend.01_catalog.*
  - imports targeting `{other_sub}.nodes.*` (node chains declared by routes)

Uses stdlib ast only — no runtime import, no new deps.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

# Matches: backend.02_features.{NN}_{feature}/sub_features/{NN}_{sub}
_OWNER_RE = re.compile(
    r"backend/02_features/(?P<feature>\d{2}_[a-z][a-z0-9_]*)/sub_features/(?P<sub>\d{2}_[a-z][a-z0-9_]*)"
)

# Matches imported dotted path: backend.02_features.{nn}_{feature}.sub_features.{nn}_{sub}(.rest)?
_FEATURES_IMPORT_RE = re.compile(
    r"^backend\.02_features\.(?P<feature>\d{2}_[a-z][a-z0-9_]*)"
    r"\.sub_features\.(?P<sub>\d{2}_[a-z][a-z0-9_]*)"
    r"(?:\.(?P<rest>.+))?$"
)


@dataclass
class Violation:
    file: Path
    line: int
    imported: str
    reason: str


def _owner_of(path: Path) -> tuple[str, str] | None:
    """Return (feature_dir, sub_dir) if path lives under a sub-feature, else None."""
    p = str(path).replace("\\", "/")
    m = _OWNER_RE.search(p)
    if not m:
        return None
    return (m.group("feature"), m.group("sub"))


def _is_allowed(imported: str, owner: tuple[str, str]) -> bool:
    """Is this import permitted from `owner` sub-feature?"""
    # Framework infrastructure — always allowed
    if imported.startswith("backend.01_core") or imported.startswith("backend.01_catalog"):
        return True
    # Non-feature imports (stdlib, pydantic, etc.) — always allowed
    if not imported.startswith("backend.02_features"):
        return True
    m = _FEATURES_IMPORT_RE.match(imported)
    if not m:
        # Matches backend.02_features.{something} but not the sub_features shape:
        # could be `backend.02_features.{feature}.feature.manifest` or similar.
        # Reject by default — keep the discipline strict.
        return False
    other_feature = m.group("feature")
    other_sub = m.group("sub")
    rest = m.group("rest") or ""
    # Same sub-feature — fine
    if (other_feature, other_sub) == owner:
        return True
    # Node imports permitted (routes declare node_chain by import; runner dispatches)
    if rest.startswith("nodes.") or rest == "nodes":
        return True
    return False


def _import_module_target(call: ast.Call) -> str | None:
    """
    If `call` is an `import_module("...")` or equivalent with a string literal arg,
    return the string. Otherwise None.
    """
    # Match call shapes:
    #   import_module("backend.x.y")                  → Name('import_module')
    #   importlib.import_module("backend.x.y")        → Attribute(value=Name('importlib'), attr='import_module')
    func = call.func
    name = None
    if isinstance(func, ast.Name):
        name = func.id
    elif isinstance(func, ast.Attribute):
        name = func.attr
    if name != "import_module":
        return None
    if not call.args:
        return None
    arg = call.args[0]
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        return arg.value
    return None


def check_file(path: Path) -> list[Violation]:
    """Return violations for a single file."""
    owner = _owner_of(path)
    if owner is None:
        return []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return []
    violations: list[Violation] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module is None or node.level != 0:
                continue
            if not _is_allowed(node.module, owner):
                violations.append(
                    Violation(
                        file=path,
                        line=node.lineno,
                        imported=node.module,
                        reason="CAT_CROSS_IMPORT",
                    )
                )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if not _is_allowed(alias.name, owner):
                    violations.append(
                        Violation(
                            file=path,
                            line=node.lineno,
                            imported=alias.name,
                            reason="CAT_CROSS_IMPORT",
                        )
                    )
        elif isinstance(node, ast.Call):
            target = _import_module_target(node)
            if target and not _is_allowed(target, owner):
                violations.append(
                    Violation(
                        file=path,
                        line=node.lineno,
                        imported=target,
                        reason="CAT_CROSS_IMPORT",
                    )
                )
    return violations


def check_tree(root: Path) -> list[Violation]:
    """Walk `root` and return all violations across .py files."""
    violations: list[Violation] = []
    for py in root.rglob("*.py"):
        # Skip __pycache__ and similar
        if "__pycache__" in py.parts:
            continue
        violations.extend(check_file(py))
    return violations
