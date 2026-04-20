"""
Manifest parser + Pydantic models — the NCP v1 §3 grammar.

Pydantic models ARE the schema. No separate JSON Schema file.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

# ── Error hierarchy ─────────────────────────────────────────────────

class CatalogError(Exception):
    """Base class for catalog errors. Every subclass carries a stable error code."""
    code: str = "CAT_UNKNOWN"

    def __init__(self, message: str, *, path: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.path = path

    def __str__(self) -> str:
        if self.path:
            return f"[{self.code}] {self.message} (at {self.path})"
        return f"[{self.code}] {self.message}"


class ManifestInvalid(CatalogError):
    code = "CAT_MANIFEST_INVALID"


class KeyConflict(CatalogError):
    code = "CAT_KEY_CONFLICT"


class HandlerUnresolved(CatalogError):
    code = "CAT_HANDLER_UNRESOLVED"


class ParentMissing(CatalogError):
    code = "CAT_PARENT_MISSING"


class HandlerContractMismatch(CatalogError):
    code = "CAT_HANDLER_CONTRACT_MISMATCH"


# ── Constants (mirror dim_* seeds) ──────────────────────────────────

_KEY_SEGMENT = r"[a-z][a-z0-9_]*"
_FEATURE_KEY_RE = re.compile(rf"^{_KEY_SEGMENT}$")
_SUB_FEATURE_KEY_RE = re.compile(rf"^{_KEY_SEGMENT}\.{_KEY_SEGMENT}$")
_NODE_KEY_RE = re.compile(rf"^{_KEY_SEGMENT}(\.{_KEY_SEGMENT}){{2,}}$")

_VALID_MODULES = {"core", "iam", "audit", "monitoring", "vault", "notify", "billing", "llmops", "featureflags"}


# ── Manifest models ─────────────────────────────────────────────────

class ExecutionPolicy(BaseModel):
    """Per-node execution policy (NCP v1 §8)."""
    model_config = ConfigDict(extra="forbid")

    timeout_ms: int = Field(default=5000, ge=100, le=600000)
    retries: int = Field(default=0, ge=0, le=3)
    tx: Literal["caller", "own", "none"] = "caller"


class OwnsBlock(BaseModel):
    """What a sub-feature owns in terms of DB objects + seeds."""
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    db_schema: str = Field(default="", alias="schema")
    tables: list[str] = Field(default_factory=list)
    views: list[str] = Field(default_factory=list)
    seeds: list[str] = Field(default_factory=list)


class NodeManifest(BaseModel):
    """Single node entry in a sub-feature's `nodes:` list."""
    model_config = ConfigDict(extra="forbid")

    key: str
    kind: Literal["request", "effect", "control"]
    handler: str
    label: str
    description: str = ""
    emits_audit: bool = False
    version: int = Field(default=1, ge=1)
    tags: list[str] = Field(default_factory=list)
    execution: ExecutionPolicy = Field(default_factory=ExecutionPolicy)
    deprecated_at: datetime | None = None

    @field_validator("key")
    @classmethod
    def _key_shape(cls, v: str) -> str:
        if not _NODE_KEY_RE.match(v):
            raise ValueError(
                f"Node key {v!r} must match '{_KEY_SEGMENT}(.{_KEY_SEGMENT}){{2,}}' "
                f"(feature.sub.action at minimum)."
            )
        return v

    @model_validator(mode="after")
    def _effect_must_emit_audit(self) -> "NodeManifest":
        if self.kind == "effect" and not self.emits_audit:
            raise ValueError(
                f"Node {self.key!r} is kind=effect but emits_audit=false. "
                f"Effect nodes MUST emit audit (NCP v1 §4 + DB CHECK constraint)."
            )
        return self


class RouteManifest(BaseModel):
    """Route entry — kept loose for v1 (not upserted into catalog this plan)."""
    model_config = ConfigDict(extra="allow")

    method: str
    path: str
    handler: str | None = None
    node_chain: list[str] = Field(default_factory=list)


class UIPageManifest(BaseModel):
    """UI page entry — kept loose for v1."""
    model_config = ConfigDict(extra="allow")

    path: str
    component: str | None = None
    label: str | None = None


class SubFeatureManifest(BaseModel):
    """Sub-feature entry under `spec.sub_features`."""
    model_config = ConfigDict(extra="forbid")

    key: str
    number: int = Field(ge=1, le=99)
    label: str
    description: str = ""
    owns: OwnsBlock = Field(default_factory=OwnsBlock)
    nodes: list[NodeManifest] = Field(default_factory=list)
    routes: list[RouteManifest] = Field(default_factory=list)
    ui_pages: list[UIPageManifest] = Field(default_factory=list)
    deprecated_at: datetime | None = None

    @field_validator("key")
    @classmethod
    def _key_shape(cls, v: str) -> str:
        if not _SUB_FEATURE_KEY_RE.match(v):
            raise ValueError(
                f"Sub-feature key {v!r} must match '{_KEY_SEGMENT}.{_KEY_SEGMENT}'."
            )
        return v

    @model_validator(mode="after")
    def _node_keys_belong_to_this_sub_feature(self) -> "SubFeatureManifest":
        prefix = f"{self.key}."
        for node in self.nodes:
            if not node.key.startswith(prefix):
                raise ValueError(
                    f"Node key {node.key!r} does not start with sub-feature prefix {prefix!r}."
                )
        return self


class FeatureMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    number: int = Field(ge=1, le=99)
    module: Literal["core", "iam", "audit", "monitoring", "vault", "notify", "billing", "llmops", "featureflags"]
    always_on: bool = False
    label: str
    description: str = ""
    icon: str | None = None
    manifest_version: int = Field(default=1, ge=1)

    @field_validator("key")
    @classmethod
    def _key_shape(cls, v: str) -> str:
        if not _FEATURE_KEY_RE.match(v):
            raise ValueError(
                f"Feature key {v!r} must match '{_KEY_SEGMENT}' (single word, lowercase snake_case)."
            )
        return v

    @model_validator(mode="after")
    def _key_matches_module_in_v1(self) -> "FeatureMetadata":
        # In v1 NCP says feature.key == module code (one feature per module).
        if self.key != self.module:
            raise ValueError(
                f"Feature key {self.key!r} must equal module {self.module!r} in NCP v1 "
                f"(one feature per module). If you need distinction, wait for NCP v2."
            )
        return self


class FeatureSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    depends_on_modules: list[str] = Field(default_factory=list)
    sub_features: list[SubFeatureManifest] = Field(default_factory=list)


class FeatureManifest(BaseModel):
    """Top-level feature manifest — whole YAML file."""
    model_config = ConfigDict(extra="forbid")

    apiVersion: Literal["tennetctl/v1"]
    kind: Literal["Feature"]
    metadata: FeatureMetadata
    spec: FeatureSpec

    @model_validator(mode="after")
    def _sub_feature_keys_belong_to_feature(self) -> "FeatureManifest":
        prefix = f"{self.metadata.key}."
        for sub in self.spec.sub_features:
            if not sub.key.startswith(prefix):
                raise ValueError(
                    f"Sub-feature key {sub.key!r} does not start with feature prefix {prefix!r}."
                )
        # No duplicate sub-feature keys/numbers within a feature.
        keys = [s.key for s in self.spec.sub_features]
        numbers = [s.number for s in self.spec.sub_features]
        if len(set(keys)) != len(keys):
            raise ValueError(f"Duplicate sub-feature keys within feature {self.metadata.key!r}.")
        if len(set(numbers)) != len(numbers):
            raise ValueError(f"Duplicate sub-feature numbers within feature {self.metadata.key!r}.")
        # No duplicate node keys across the whole feature.
        node_keys: list[str] = [n.key for sub in self.spec.sub_features for n in sub.nodes]
        if len(set(node_keys)) != len(node_keys):
            raise ValueError(f"Duplicate node keys within feature {self.metadata.key!r}.")
        # depends_on_modules must be valid module codes.
        for dep in self.spec.depends_on_modules:
            if dep not in _VALID_MODULES:
                raise ValueError(f"depends_on_modules entry {dep!r} is not a valid module.")
        return self


# ── Public API ──────────────────────────────────────────────────────

def parse_manifest(path: Path | str) -> FeatureManifest:
    """Load + validate a single feature.manifest.yaml file."""
    path = Path(path)
    try:
        raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise ManifestInvalid(f"YAML parse failed: {e}", path=str(path)) from e
    if not isinstance(raw, dict):
        raise ManifestInvalid(
            f"Manifest must be a mapping at top level, got {type(raw).__name__}.",
            path=str(path),
        )
    try:
        return FeatureManifest(**raw)
    except ValidationError as e:
        raise ManifestInvalid(str(e), path=str(path)) from e


def discover_manifests(root: Path | str, *, include_fixtures: bool = False) -> list[Path]:
    """
    Find every feature.manifest.yaml under:
    - {root}/backend/02_features/*/feature.manifest.yaml
    - {root}/tests/fixtures/features/*/feature.manifest.yaml (if include_fixtures=True)
    """
    root = Path(root)
    found: list[Path] = []
    features_dir = root / "backend" / "02_features"
    if features_dir.exists():
        found.extend(sorted(features_dir.glob("*/feature.manifest.yaml")))
    if include_fixtures:
        fixtures_dir = root / "tests" / "fixtures" / "features"
        if fixtures_dir.exists():
            found.extend(sorted(fixtures_dir.glob("*/feature.manifest.yaml")))
    return found
