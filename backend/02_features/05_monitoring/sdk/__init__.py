"""Monitoring SDK — in-process handles for metrics."""

from importlib import import_module

metrics = import_module("backend.02_features.05_monitoring.sdk.metrics")

__all__ = ["metrics"]
