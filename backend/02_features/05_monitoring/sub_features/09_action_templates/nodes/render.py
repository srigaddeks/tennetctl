"""Render node — control kind, pure template rendering."""

from importlib import import_module
from typing import Optional

from ..renderer import Renderer

_core_id = import_module("backend.01_core.id")


class RenderNode:
    """
    Render action template with variables.

    Input schema:
        {
            "template_id": str (UUID),
            "template_body": str (Jinja2),
            "variables": dict
        }

    Output schema:
        {
            "rendered_body": str,
            "rendered_headers": dict,
            "payload_hash": str
        }
    """

    def __init__(self):
        self.renderer = Renderer()

    async def handle(self, input_data: dict) -> dict:
        """Render a template with variables."""
        template_id = input_data.get("template_id")
        template_body = input_data.get("template_body")
        variables = input_data.get("variables", {})

        if not template_body:
            raise ValueError("template_body is required")

        try:
            result = await self.renderer.render_async(
                template_id=template_id or "",
                template_str=template_body,
                variables=variables,
            )
            return result
        except Exception as e:
            raise ValueError(f"Render failed: {str(e)}")
