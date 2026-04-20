"""Jinja2 sandboxed template renderer with bounds checking and deterministic output."""

import hashlib
import asyncio
from typing import Optional
import json

from jinja2 import (
    SandboxedEnvironment,
    TemplateError,
    TemplateSyntaxError,
)
from jinja2.sandbox import SandboxedEnvironment as SandboxEnv


class Renderer:
    """Sandboxed Jinja2 template renderer with security + performance bounds."""

    # Maximum template output size (64KB)
    MAX_OUTPUT_SIZE = 64 * 1024

    # Maximum render time (50ms wall-clock)
    MAX_RENDER_TIME_MS = 50

    # Allow-listed filter names
    ALLOWED_FILTERS = {
        "tojson": json.dumps,
        "length": len,
        "upper": str.upper,
        "lower": str.lower,
        "default": lambda x, d=None: x if x is not None else d,
        "replace": str.replace,
        "round": round,
        "int": int,
        "float": float,
    }

    def __init__(self):
        """Initialize the sandboxed Jinja2 environment."""
        self.env = SandboxedEnvironment()
        # Remove all filters and re-add only allowed ones
        self.env.filters = {}
        for name, fn in self.ALLOWED_FILTERS.items():
            self.env.filters[name] = fn

    def validate_template(self, template_str: str) -> None:
        """Validate template syntax without rendering. Raises on error."""
        try:
            self.env.from_string(template_str)
        except (TemplateSyntaxError, TemplateError) as e:
            raise ValueError(f"Template syntax error at line {e.lineno}: {e.message}")

    def render(
        self,
        template_id: str,
        template_str: str,
        variables: dict,
    ) -> dict:
        """
        Render a template with variables.

        Args:
            template_id: Template identifier (for logging/caching)
            template_str: Jinja2 template string
            variables: Context variables dict

        Returns:
            {rendered_body, rendered_headers, payload_hash}

        Raises:
            ValueError: If render exceeds bounds or has syntax error
        """
        # Validate template syntax first
        try:
            template = self.env.from_string(template_str)
        except TemplateError as e:
            raise ValueError(f"Template parse error: {str(e)}")

        # Run render with timeout (simplified; real impl would use signal-free approach)
        try:
            rendered_body = template.render(**variables)
        except Exception as e:
            raise ValueError(f"Render error: {str(e)}")

        # Check output size
        if len(rendered_body) > self.MAX_OUTPUT_SIZE:
            raise ValueError(
                f"Rendered output exceeds {self.MAX_OUTPUT_SIZE} bytes: {len(rendered_body)}"
            )

        # Compute payload hash
        payload_hash = hashlib.sha256(rendered_body.encode()).hexdigest()

        # Parse headers (if template contains them in YAML/JSON)
        rendered_headers = {}
        try:
            # Placeholder: real impl would parse headers from template blocks
            # For now, return empty headers dict
            pass
        except Exception:
            pass

        return {
            "rendered_body": rendered_body,
            "rendered_headers": rendered_headers,
            "payload_hash": payload_hash,
        }

    async def render_async(
        self,
        template_id: str,
        template_str: str,
        variables: dict,
    ) -> dict:
        """
        Async version of render with timeout enforcement.

        Args:
            template_id: Template identifier
            template_str: Jinja2 template string
            variables: Context variables dict

        Returns:
            {rendered_body, rendered_headers, payload_hash}

        Raises:
            ValueError: If render exceeds bounds or times out
        """
        # Run render in executor to avoid blocking
        loop = asyncio.get_event_loop()
        return await asyncio.wait_for(
            loop.run_in_executor(
                None,
                self.render,
                template_id,
                template_str,
                variables,
            ),
            timeout=self.MAX_RENDER_TIME_MS / 1000.0,
        )
