import pytest

from app.ai.errors import PromptRenderError
from app.ai.prompt_renderer import extract_variables, render
from app.ai.prompt_templates import (
    PromptTemplate,
    get_template,
    register_template,
    render_template,
)


class TestExtractVariables:
    def test_extracts_named_variables(self) -> None:
        assert extract_variables("Hi {{ name }}, role {{role}}") == {"name", "role"}

    def test_ignores_literal_single_braces(self) -> None:
        # JSON examples in prompts must not be treated as variables.
        assert extract_variables('Return {"summary": "..."} for {{ text }}') == {"text"}

    def test_no_variables(self) -> None:
        assert extract_variables("plain text") == set()


class TestRender:
    def test_substitutes_variables(self) -> None:
        assert render("Hi {{ name }}", {"name": "Sam"}) == "Hi Sam"

    def test_preserves_literal_json_braces(self) -> None:
        out = render('Reply as {"ok": true} about {{ topic }}', {"topic": "x"})
        assert out == 'Reply as {"ok": true} about x'

    def test_stringifies_non_string_values(self) -> None:
        assert render("n={{ n }}", {"n": 42}) == "n=42"

    def test_ignores_extra_variables(self) -> None:
        assert render("Hi {{ name }}", {"name": "A", "unused": "B"}) == "Hi A"

    def test_raises_on_missing_variable(self) -> None:
        with pytest.raises(PromptRenderError, match="name"):
            render("Hi {{ name }} {{ role }}", {"role": "dev"})


class TestTemplateRegistry:
    def test_example_template_registered(self) -> None:
        template = get_template("example.echo")
        assert template.system is not None
        assert "text" in template.required_variables

    def test_unknown_template_raises(self) -> None:
        with pytest.raises(PromptRenderError, match="Unknown prompt template"):
            get_template("does.not.exist")

    def test_render_template_produces_system_and_user(self) -> None:
        rendered = render_template("example.echo", {"text": "hello world"})
        assert rendered.system is not None
        assert "hello world" in rendered.user

    def test_required_variables_derived_from_both_parts(self) -> None:
        template = PromptTemplate(
            name="test.both",
            system="System for {{ a }}",
            user="User for {{ b }}",
        )
        assert template.required_variables == {"a", "b"}

    def test_register_and_render_custom_template(self) -> None:
        register_template(
            PromptTemplate(name="test.custom", user="Value: {{ v }}")
        )
        rendered = render_template("test.custom", {"v": "123"})
        assert rendered.user == "Value: 123"
        assert rendered.system is None
