"""Unit tests for ``credit_engine.llm.generator`` — MessageGenerator facade, output cleaning, channel dispatch."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from credit_engine.llm.generator import (
    GenerationError,
    MessageGenerator,
    UnknownChannelError,
)
from credit_engine.llm.prompts import SYSTEM_PROMPT


def _mock_llm_client(response: str = "Mensaje generado") -> Mock:
    """Create a mock that satisfies the ``LLMClient`` protocol."""
    client = Mock()
    client.generate.return_value = response
    return client


class TestMessageGeneratorInit:
    def test_stores_client_reference(self):
        client = Mock()
        generator = MessageGenerator(client)

        assert generator._client is client


class TestGenerateMessage:
    def test_whatsapp_channel_returns_string(self):
        client = _mock_llm_client("Hola Carlos, te tenemos esta oferta 😊")
        generator = MessageGenerator(client)

        result = generator.generate_message("Carlos", "Credito Libre", "Tasa 1.2%", "whatsapp")

        assert isinstance(result, str)
        assert client.generate.called

    def test_sms_channel_returns_cleaned_message(self):
        client = _mock_llm_client("Hola Carlos, tasa 1.2% sin codeudor.")
        generator = MessageGenerator(client)

        result = generator.generate_message("Carlos", "Credito Libre", "Tasa 1.2%", "sms")

        assert result == "Hola Carlos, tasa 1.2% sin codeudor."

    def test_email_channel_returns_cleaned_message(self):
        client = _mock_llm_client("Hola Carlos,\n\nTe ofrecemos el credito con grandes beneficios.\n\nSaludos cordiales")
        generator = MessageGenerator(client)

        result = generator.generate_message("Carlos", "Credito", "Beneficio", "email")

        assert "Hola Carlos" in result

    def test_empty_person_name_raises_generation_error(self):
        generator = MessageGenerator(Mock())

        with pytest.raises(GenerationError, match="person_name must not be empty"):
            generator.generate_message("", "Producto", "Beneficios", "whatsapp")

    def test_whitespace_only_person_name_raises(self):
        generator = MessageGenerator(Mock())

        with pytest.raises(GenerationError, match="person_name must not be empty"):
            generator.generate_message("   ", "Producto", "Beneficios", "whatsapp")

    def test_empty_product_raises_generation_error(self):
        generator = MessageGenerator(Mock())

        with pytest.raises(GenerationError, match="product must not be empty"):
            generator.generate_message("Carlos", "", "Beneficios", "whatsapp")

    def test_whitespace_only_product_raises(self):
        generator = MessageGenerator(Mock())

        with pytest.raises(GenerationError, match="product must not be empty"):
            generator.generate_message("Carlos", "   ", "Beneficios", "whatsapp")

    def test_unknown_channel_raises_unknown_channel_error(self):
        generator = MessageGenerator(Mock())

        with pytest.raises(UnknownChannelError, match="Unknown channel"):
            generator.generate_message("Carlos", "Producto", "Beneficios", "telegram")  # type: ignore[arg-type]

    def test_unknown_channel_error_lists_valid_options(self):
        generator = MessageGenerator(Mock())

        with pytest.raises(UnknownChannelError, match="email, sms, whatsapp"):
            generator.generate_message("Carlos", "Producto", "Beneficios", "invalid")  # type: ignore[arg-type]

    def test_calls_client_with_system_prompt(self):
        client = _mock_llm_client("Mensaje")
        generator = MessageGenerator(client)

        generator.generate_message("Maria", "Credito Libre", "Tasa 1.2%, sin codeudor", "whatsapp")

        client.generate.assert_called_once()
        args = client.generate.call_args[0]
        assert args[0] == SYSTEM_PROMPT

    def test_calls_client_with_user_prompt_containing_inputs(self):
        client = _mock_llm_client("Mensaje")
        generator = MessageGenerator(client)

        generator.generate_message("Maria", "Credito Libre", "Tasa 1.2%, sin codeudor", "whatsapp")

        args = client.generate.call_args[0]
        user_prompt = args[1]
        assert "Maria" in user_prompt
        assert "Credito Libre" in user_prompt
        assert "Tasa 1.2%, sin codeudor" in user_prompt

    def test_accepts_any_object_with_generate_method(self):
        class CustomClient:
            def generate(self, system_prompt: str, user_prompt: str) -> str:
                return "custom response"

        generator = MessageGenerator(CustomClient())
        result = generator.generate_message("Carlos", "Credito", "Beneficio", "whatsapp")

        assert result == "custom response"

    def test_strips_whitespace_from_input_before_use(self):
        client = _mock_llm_client("Mensaje")
        generator = MessageGenerator(client)

        generator.generate_message("  Carlos  ", "  Credito  ", "  Beneficio  ", "whatsapp")

        args = client.generate.call_args[0]
        assert "  Carlos  " not in args[1]
        assert "<persona>Carlos</persona>" in args[1]

    def test_cleans_output_before_returning(self):
        client = _mock_llm_client("```\nMensaje limpio\n```")
        generator = MessageGenerator(client)

        result = generator.generate_message("Carlos", "Credito", "Beneficio", "whatsapp")

        assert result == "Mensaje limpio"


class TestCleanOutput:
    def test_removes_code_fence_without_language(self):
        result = MessageGenerator._clean_output("```\nHola\n```")

        assert result == "Hola"

    def test_removes_code_fence_with_language_tag(self):
        result = MessageGenerator._clean_output("```python\nHola\n```")

        assert result == "Hola"

    def test_removes_inline_fence_markers(self):
        result = MessageGenerator._clean_output("```\nHola\n```")

        assert result == "Hola"

    def test_removes_bold_markdown(self):
        result = MessageGenerator._clean_output("Hola **Carlos**!")

        assert result == "Hola Carlos!"

    def test_removes_multiple_bold_spans(self):
        result = MessageGenerator._clean_output("**Hola** **Carlos**!")

        assert result == "Hola Carlos!"

    def test_strips_mensaje_prefix(self):
        result = MessageGenerator._clean_output("Mensaje: Hola Carlos")

        assert result == "Hola Carlos"

    def test_strips_aqui_tienes_prefix(self):
        result = MessageGenerator._clean_output("Aquí tienes el mensaje: Hola Carlos")

        assert result == "Hola Carlos"

    def test_strips_claro_prefix(self):
        result = MessageGenerator._clean_output("¡Claro! Hola Carlos")

        assert result == "Hola Carlos"

    def test_strips_por_supuesto_prefix(self):
        result = MessageGenerator._clean_output("Por supuesto: Hola Carlos")

        assert result == "Hola Carlos"

    def test_strips_channel_specific_prefix(self):
        result = MessageGenerator._clean_output("Mensaje de WhatsApp: Hola Carlos")

        assert result == "Hola Carlos"

    def test_prefix_stripping_is_case_insensitive(self):
        result = MessageGenerator._clean_output("mensaje: Hola Carlos")

        assert result == "Hola Carlos"

    def test_strips_only_first_matching_prefix(self):
        result = MessageGenerator._clean_output("Mensaje: Aquí tienes el mensaje: Hola Carlos")

        assert result == "Aquí tienes el mensaje: Hola Carlos"

    def test_removes_surrounding_double_quotes(self):
        result = MessageGenerator._clean_output('"Hola Carlos"')

        assert result == "Hola Carlos"

    def test_removes_surrounding_single_quotes(self):
        result = MessageGenerator._clean_output("'Hola Carlos'")

        assert result == "Hola Carlos"

    def test_preserves_inner_quotes(self):
        result = MessageGenerator._clean_output('Hola "Carlos"')

        assert result == 'Hola "Carlos"'

    def test_does_not_remove_unbalanced_quotes(self):
        result = MessageGenerator._clean_output('"Hola Carlos')

        assert result == '"Hola Carlos'

    def test_strips_leading_and_trailing_whitespace(self):
        result = MessageGenerator._clean_output("  Hola Carlos  ")

        assert result == "Hola Carlos"

    def test_raises_generation_error_when_result_is_empty(self):
        with pytest.raises(GenerationError, match="empty after cleanup"):
            MessageGenerator._clean_output("Mensaje:")

    def test_raises_generation_error_when_only_fences(self):
        with pytest.raises(GenerationError, match="empty after cleanup"):
            MessageGenerator._clean_output("``` ```")

    def test_handles_model_preamble_with_cleaned_text(self):
        result = MessageGenerator._clean_output("Aquí está el mensaje: ¡Hola Carlos!")

        assert result == "¡Hola Carlos!"
