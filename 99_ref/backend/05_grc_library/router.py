from __future__ import annotations

from importlib import import_module

_dimensions_router_module = import_module("backend.05_grc_library.01_dimensions.router")
_frameworks_router_module = import_module("backend.05_grc_library.02_frameworks.router")
_versions_router_module = import_module("backend.05_grc_library.03_versions.router")
_requirements_router_module = import_module("backend.05_grc_library.04_requirements.router")
_controls_router_module = import_module("backend.05_grc_library.05_controls.router")
_tests_router_module = import_module("backend.05_grc_library.06_tests.router")
_test_mappings_router_module = import_module("backend.05_grc_library.08_test_mappings.router")
_settings_router_module = import_module("backend.05_grc_library.10_settings.router")
_test_executions_router_module = import_module("backend.05_grc_library.09_test_executions.router")
_deployments_router_module = import_module("backend.05_grc_library.11_deployments.router")
_global_risks_router_module = import_module("backend.05_grc_library.12_global_risks.router")
_dashboard_router_module = import_module("backend.05_grc_library.13_dashboard.router")

dimensions_router = _dimensions_router_module.router
frameworks_router = _frameworks_router_module.router
versions_router = _versions_router_module.router
requirements_router = _requirements_router_module.router
controls_router = _controls_router_module.router
tests_router = _tests_router_module.router
test_mappings_router = _test_mappings_router_module.router
settings_router = _settings_router_module.router
test_executions_router = _test_executions_router_module.router
deployments_router = _deployments_router_module.router
global_risks_router = _global_risks_router_module.router
dashboard_router = _dashboard_router_module.router
