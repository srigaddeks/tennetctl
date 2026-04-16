from __future__ import annotations

from importlib import import_module

_dimensions_router_module = import_module("backend.10_sandbox.01_dimensions.router")
_connectors_router_module = import_module("backend.10_sandbox.02_connectors.router")
_datasets_router_module = import_module("backend.10_sandbox.03_datasets.router")
_signals_router_module = import_module("backend.10_sandbox.04_signals.router")
_threat_types_router_module = import_module("backend.10_sandbox.05_threat_types.router")
_policies_router_module = import_module("backend.10_sandbox.06_policies.router")
_execution_router_module = import_module("backend.10_sandbox.07_execution.router")
_live_sessions_router_module = import_module("backend.10_sandbox.08_live_sessions.router")
_libraries_router_module = import_module("backend.10_sandbox.09_libraries.router")
_promotions_router_module = import_module("backend.10_sandbox.10_promotions.router")
_ssf_transmitter_router_module = import_module("backend.10_sandbox.12_ssf_transmitter.router")
_assets_router_module = import_module("backend.10_sandbox.14_assets.router")
_collection_runs_router_module = import_module("backend.10_sandbox.15_collection_runs.router")
_providers_router_module = import_module("backend.10_sandbox.16_providers.router")
_asset_connectors_router_module = import_module("backend.10_sandbox.17_asset_connectors.router")
_promoted_tests_router_module = import_module("backend.10_sandbox.35_promoted_tests.router")
_global_library_router_module = import_module("backend.10_sandbox.21_global_library.router")
_global_datasets_router_module = import_module("backend.10_sandbox.22_global_datasets.router")
_global_control_tests_router_module = import_module("backend.10_sandbox.23_global_control_tests.router")
_live_test_router_module = import_module("backend.10_sandbox.36_live_test.router")

dimensions_router = _dimensions_router_module.router
connectors_router = _connectors_router_module.router
datasets_router = _datasets_router_module.router
signals_router = _signals_router_module.router
threat_types_router = _threat_types_router_module.router
policies_router = _policies_router_module.router
execution_runs_router = _execution_router_module.runs_router
execution_threat_eval_router = _execution_router_module.threat_eval_router
execution_policy_exec_router = _execution_router_module.policy_exec_router
live_sessions_router = _live_sessions_router_module.router
libraries_router = _libraries_router_module.router
promotions_router = _promotions_router_module.router
ssf_transmitter_router = _ssf_transmitter_router_module.router
ssf_wellknown_router = _ssf_transmitter_router_module.wellknown_router
assets_router = _assets_router_module.router
collection_runs_router = _collection_runs_router_module.router
providers_router = _providers_router_module.router
asset_connectors_router = _asset_connectors_router_module.router
promoted_tests_router = _promoted_tests_router_module.router
global_library_router = _global_library_router_module.router
global_datasets_router = _global_datasets_router_module.router
global_control_tests_router = _global_control_tests_router_module.router
live_test_router = _live_test_router_module.router
