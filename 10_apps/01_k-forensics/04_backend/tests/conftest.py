"""Shared test configuration for kbio scoring engine tests.

Inserts the backend directory onto sys.path so that importlib can
resolve modules with numeric-prefix directories (03_kbio, etc.).
Also adds 03_kbio itself for direct _signals/_threats imports.
"""
import sys
import os

_backend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _backend)
sys.path.insert(0, os.path.join(_backend, "03_kbio"))
