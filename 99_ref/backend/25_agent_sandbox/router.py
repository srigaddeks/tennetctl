from __future__ import annotations

from importlib import import_module

_dimensions_router_module = import_module("backend.25_agent_sandbox.01_dimensions.router")
_agents_router_module = import_module("backend.25_agent_sandbox.02_agents.router")
_tools_router_module = import_module("backend.25_agent_sandbox.03_tools.router")
_scenarios_router_module = import_module("backend.25_agent_sandbox.04_test_scenarios.router")
_execution_router_module = import_module("backend.25_agent_sandbox.05_execution.router")
_test_runner_router_module = import_module("backend.25_agent_sandbox.06_test_runner.router")
_registry_router_module = import_module("backend.25_agent_sandbox.08_registry.router")
_playground_router_module = import_module("backend.25_agent_sandbox.09_playground.router")
_tool_endpoints_router_module = import_module("backend.25_agent_sandbox.09_playground.tool_endpoints")

dimensions_router = _dimensions_router_module.router
agents_router = _agents_router_module.router
tools_router = _tools_router_module.router
scenarios_router = _scenarios_router_module.router
execution_router = _execution_router_module.router
test_runner_router = _test_runner_router_module.router
registry_router = _registry_router_module.router
playground_router = _playground_router_module.router
tool_endpoints_router = _tool_endpoints_router_module.router
