from __future__ import annotations

from importlib import import_module

_base_module = import_module("backend.10_sandbox.18_drivers.base")
AssetDriver = _base_module.AssetDriver

_DRIVER_MAP: dict[str, str] = {
    "github": "backend.10_sandbox.18_drivers.github.GitHubDriver",
    "azure_storage": "backend.10_sandbox.18_drivers.azure_storage.AzureStorageDriver",
}


def get_driver(provider_code: str) -> AssetDriver:
    """Return an instantiated driver for the given provider code."""
    driver_path = _DRIVER_MAP.get(provider_code)
    if not driver_path:
        raise ValueError(f"No driver registered for provider '{provider_code}'")
    module_path, class_name = driver_path.rsplit(".", 1)
    module = import_module(module_path)
    driver_class: type[AssetDriver] = getattr(module, class_name)
    return driver_class()
