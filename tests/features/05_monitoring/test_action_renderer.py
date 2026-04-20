"""Tests for template rendering with sandboxing and bounds."""

import pytest
from backend.02_features.05_monitoring.sub_features.09_action_templates.renderer import Renderer


class TestRendererSandboxing:
    """Test Jinja2 sandbox restrictions."""

    def test_render_simple_template(self):
        """Test basic template rendering."""
        renderer = Renderer()
        result = renderer.render(
            template_id="test",
            template_str='Alert {{rule_name}} with value {{value}}',
            variables={"rule_name": "cpu_high", "value": 0.92},
        )

        assert result["rendered_body"] == "Alert cpu_high with value 0.92"
        assert "payload_hash" in result

    def test_render_with_tojson_filter(self):
        """Test tojson filter (allowed)."""
        renderer = Renderer()
        result = renderer.render(
            template_id="test",
            template_str='{"labels": {{labels|tojson}}}',
            variables={"labels": {"host": "x", "service": "api"}},
        )

        assert '"host": "x"' in result["rendered_body"]

    def test_render_with_upper_filter(self):
        """Test upper filter (allowed)."""
        renderer = Renderer()
        result = renderer.render(
            template_id="test",
            template_str='{{severity|upper}}',
            variables={"severity": "critical"},
        )

        assert result["rendered_body"] == "CRITICAL"

    def test_reject_import_statement(self):
        """Test that {% import %} is rejected."""
        renderer = Renderer()

        with pytest.raises(ValueError):
            renderer.render(
                template_id="test",
                template_str='{% import "os" as os %}',
                variables={},
            )

    def test_reject_class_attribute_access(self):
        """Test that __class__ access is blocked."""
        renderer = Renderer()

        with pytest.raises(ValueError):
            renderer.render(
                template_id="test",
                template_str='{{obj.__class__}}',
                variables={"obj": "test"},
            )

    def test_reject_mro_chain(self):
        """Test that MRO chain is blocked."""
        renderer = Renderer()

        with pytest.raises(ValueError):
            renderer.render(
                template_id="test",
                template_str="{{''.__class__.__mro__}}",
                variables={},
            )

    def test_output_size_bound(self):
        """Test that output exceeding MAX_OUTPUT_SIZE raises error."""
        renderer = Renderer()
        huge_var = "x" * (65 * 1024)  # 65KB > 64KB limit

        with pytest.raises(ValueError) as exc_info:
            renderer.render(
                template_id="test",
                template_str='{{data}}',
                variables={"data": huge_var},
            )

        assert "exceeds" in str(exc_info.value)

    def test_deterministic_output(self):
        """Test that same input produces same output."""
        renderer = Renderer()
        variables = {"rule_name": "cpu", "value": 0.92}

        result1 = renderer.render(
            template_id="test",
            template_str='{{rule_name}}={{value}}',
            variables=variables,
        )
        result2 = renderer.render(
            template_id="test",
            template_str='{{rule_name}}={{value}}',
            variables=variables,
        )

        assert result1["rendered_body"] == result2["rendered_body"]
        assert result1["payload_hash"] == result2["payload_hash"]

    def test_validate_template_syntax(self):
        """Test pre-validation of template syntax."""
        renderer = Renderer()

        # Valid
        renderer.validate_template('{{var}}')
        renderer.validate_template('{% if true %}x{% endif %}')

        # Invalid
        with pytest.raises(ValueError):
            renderer.validate_template('{{unclosed')

    def test_allowed_filters_only(self):
        """Test that only allow-listed filters are available."""
        renderer = Renderer()

        # These should work (allow-listed)
        renderer.render(
            template_id="test",
            template_str='{{value|round}}',
            variables={"value": 3.14},
        )
        renderer.render(
            template_id="test",
            template_str='{{name|lower}}',
            variables={"name": "TEST"},
        )

        # This should fail (not allow-listed)
        with pytest.raises(ValueError):
            renderer.render(
                template_id="test",
                template_str='{{name|reverse}}',  # not allowed
                variables={"name": "test"},
            )
