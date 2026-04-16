"""
Node Catalog Protocol v1 implementation.

See: 03_docs/00_main/protocols/001_node_catalog_protocol_v1.md
See: 03_docs/00_main/08_decisions/027_node_catalog_and_runner.md

Public surface:
- parse_manifest(path) -> FeatureManifest
- discover_manifests(root, include_fixtures=False) -> list[Path]
- upsert_all(pool, enabled_modules, fixtures=False) -> LoaderReport
- FeatureManifest, SubFeatureManifest, NodeManifest, ExecutionPolicy
- CatalogError + subclasses (ManifestInvalid, KeyConflict, HandlerUnresolved, ParentMissing, HandlerContractMismatch)
"""

from importlib import import_module
from typing import Any

_manifest: Any = import_module("backend.01_catalog.manifest")
_loader: Any = import_module("backend.01_catalog.loader")
_context: Any = import_module("backend.01_catalog.context")
_node: Any = import_module("backend.01_catalog.node")
_errors: Any = import_module("backend.01_catalog.errors")
_authz: Any = import_module("backend.01_catalog.authz")
_runner: Any = import_module("backend.01_catalog.runner")

parse_manifest = _manifest.parse_manifest
discover_manifests = _manifest.discover_manifests

FeatureManifest = _manifest.FeatureManifest
SubFeatureManifest = _manifest.SubFeatureManifest
NodeManifest = _manifest.NodeManifest
ExecutionPolicy = _manifest.ExecutionPolicy

CatalogError = _manifest.CatalogError
ManifestInvalid = _manifest.ManifestInvalid
KeyConflict = _manifest.KeyConflict
HandlerUnresolved = _manifest.HandlerUnresolved
ParentMissing = _manifest.ParentMissing
HandlerContractMismatch = _manifest.HandlerContractMismatch

upsert_all = _loader.upsert_all
LoaderReport = _loader.LoaderReport

# Runner + context + node base
NodeContext = _context.NodeContext
Node = _node.Node
run_node = _runner.run_node

# Authorization hook
register_checker = _authz.register_checker
clear_checkers = _authz.clear_checkers

# Runtime error classes
RunnerError = _errors.RunnerError
NodeNotFound = _errors.NodeNotFound
NodeTombstoned = _errors.NodeTombstoned
NodeAuthDenied = _errors.NodeAuthDenied
NodeTimeout = _errors.NodeTimeout
IdempotencyRequired = _errors.IdempotencyRequired
TransientError = _errors.TransientError
DomainError = _errors.DomainError

__all__ = [
    # Manifest + loader
    "parse_manifest",
    "discover_manifests",
    "upsert_all",
    "FeatureManifest",
    "SubFeatureManifest",
    "NodeManifest",
    "ExecutionPolicy",
    "LoaderReport",
    # Manifest/boot error classes
    "CatalogError",
    "ManifestInvalid",
    "KeyConflict",
    "HandlerUnresolved",
    "ParentMissing",
    "HandlerContractMismatch",
    # Runner + context + node
    "NodeContext",
    "Node",
    "run_node",
    "register_checker",
    "clear_checkers",
    # Runtime error classes
    "RunnerError",
    "NodeNotFound",
    "NodeTombstoned",
    "NodeAuthDenied",
    "NodeTimeout",
    "IdempotencyRequired",
    "TransientError",
    "DomainError",
]
