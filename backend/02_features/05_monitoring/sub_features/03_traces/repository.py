"""Repository for monitoring traces — intentionally empty in 13-03.

Postgres writes happen in the 13-04 consumer. The OTLP receiver only
publishes to JetStream; no DB access here.
"""

from __future__ import annotations
