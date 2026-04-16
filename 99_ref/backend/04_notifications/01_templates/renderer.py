from __future__ import annotations

import logging

from jinja2 import Undefined
from jinja2.sandbox import SandboxedEnvironment

_logger = logging.getLogger("backend.notifications.renderer")


class _LoggingUndefined(Undefined):
    """Undefined that logs a warning and renders as empty string.

    Unlike ChainableUndefined which is completely silent, this logs a warning
    so template typos (e.g. ``{{ user.frist_name }}``) are discoverable in logs
    without breaking email delivery.
    """

    def __str__(self) -> str:
        _logger.warning(
            "template_undefined_variable",
            extra={"variable": self._undefined_name, "hint": self._undefined_hint},
        )
        return ""

    def __html__(self) -> str:
        return self.__str__()

    def __iter__(self):
        return iter([])

    def __bool__(self) -> bool:
        return False

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Undefined)

    def __ne__(self, other: object) -> bool:
        return not isinstance(other, Undefined)

    def __hash__(self) -> int:
        return id(type(self))

    def __getattr__(self, name: str) -> "_LoggingUndefined":
        # Allow chained access like {{ user.first_name }} without raising
        return _LoggingUndefined(
            hint=self._undefined_hint,
            obj=self._undefined_obj,
            name=f"{self._undefined_name}.{name}",
        )


class TemplateRenderer:
    def __init__(self) -> None:
        self._env = SandboxedEnvironment(
            autoescape=True,
            undefined=_LoggingUndefined,
        )

    def render(self, template_str: str, variables: dict[str, str]) -> str:
        template = self._env.from_string(template_str)
        nested = self._nest_variables(variables)
        return template.render(**nested)

    @staticmethod
    def _nest_variables(flat: dict[str, str]) -> dict:
        """Convert dotted keys to nested dicts for Jinja2.

        e.g. {"user.display_name": "John"} -> {"user": {"display_name": "John"}}
        """
        result: dict = {}
        for key, value in flat.items():
            parts = key.split(".")
            current = result
            for part in parts[:-1]:
                current = current.setdefault(part, {})
            current[parts[-1]] = value
        return result

    def render_template_version(
        self,
        *,
        subject_line: str | None,
        body_html: str | None,
        body_text: str | None,
        body_short: str | None,
        variables: dict[str, str],
        base_body_html: str | None = None,
    ) -> dict[str, str | None]:
        rendered: dict[str, str | None] = {}
        rendered["subject_line"] = self.render(subject_line, variables) if subject_line else None
        rendered_html = self.render(body_html, variables) if body_html else None

        # Base template wrapping: inject child content into {{ content }} placeholder
        if rendered_html and base_body_html:
            if "{{ content }}" not in base_body_html and "{{content}}" not in base_body_html:
                _logger.warning(
                    "base_template_missing_content_placeholder",
                    extra={"hint": "Base template HTML does not contain {{ content }} — child content will be lost"},
                )
            else:
                rendered_html = self.render(base_body_html, {**variables, "content": rendered_html})

        rendered["body_html"] = rendered_html
        rendered["body_text"] = self.render(body_text, variables) if body_text else None
        rendered["body_short"] = self.render(body_short, variables) if body_short else None
        return rendered
