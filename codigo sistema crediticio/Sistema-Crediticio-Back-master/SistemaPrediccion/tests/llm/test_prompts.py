"""Unit tests for ``credit_engine.llm.prompts`` — channel wrappers, sanitization, prompt building."""

from __future__ import annotations

import pytest

from credit_engine.llm.prompts import (
    CHANNEL_WRAPPERS,
    SYSTEM_PROMPT,
    _build_prompt,
    _sanitize,
    wrap_email,
    wrap_sms,
    wrap_whatsapp,
)


class TestSanitize:
    def test_replaces_curly_braces_with_parentheses(self):
        result = _sanitize("text {key} more {another}")

        assert result == "text (key) more (another)"

    def test_replaces_newlines_with_spaces(self):
        result = _sanitize("line1\nline2\nline3")

        assert result == "line1 line2 line3"

    def test_replaces_carriage_return_with_space(self):
        result = _sanitize("line1\rline2")

        assert result == "line1 line2"

    def test_returns_clean_input_unchanged(self):
        result = _sanitize("texto sin caracteres especiales")

        assert result == "texto sin caracteres especiales"

    def test_strips_surrounding_whitespace(self):
        result = _sanitize("  texto  ")

        assert result == "texto"


class TestBuildPrompt:
    def test_includes_sanitized_persona_tag(self):
        result = _build_prompt("WhatsApp", "Maria", "Credito", "Beneficio")

        assert "<persona>Maria</persona>" in result

    def test_includes_sanitized_producto_tag(self):
        result = _build_prompt("WhatsApp", "Maria", "Credito", "Beneficio")

        assert "<producto>Credito</producto>" in result

    def test_includes_sanitized_beneficios_tag(self):
        result = _build_prompt("WhatsApp", "Maria", "Credito", "Beneficio")

        assert "<beneficios>Beneficio</beneficios>" in result

    def test_includes_template_name_in_instruction(self):
        result = _build_prompt("WhatsApp", "Maria", "Credito", "Beneficio")

        assert "Crea un mensaje de WhatsApp" in result

    def test_template_name_appears_in_tag_order(self):
        result = _build_prompt("SMS", "Maria", "Credito", "Beneficio")

        persona_pos = result.index("<persona>")
        producto_pos = result.index("<producto>")
        beneficios_pos = result.index("<beneficios>")
        assert persona_pos < producto_pos < beneficios_pos

    def test_includes_reglas_heading_at_end(self):
        result = _build_prompt("WhatsApp", "Maria", "Credito", "Beneficio")

        assert result.endswith("Reglas:\n")


class TestSystemPrompt:
    def test_is_non_empty_string(self):
        assert isinstance(SYSTEM_PROMPT, str)
        assert len(SYSTEM_PROMPT) > 0

    def test_mentions_colombian_assistant(self):
        assert "colombiano" in SYSTEM_PROMPT.lower()

    def test_instructs_no_markdown_or_extra_commentary(self):
        assert "sin markdown" in SYSTEM_PROMPT.lower()
        assert "sin comillas alrededor" in SYSTEM_PROMPT.lower()


class TestWrapWhatsapp:
    def test_contains_emoji_rule(self):
        result = wrap_whatsapp("Carlos", "Credito Libre", "Tasa 1.2%")

        assert "Puedes usar emojis" in result

    def test_contains_short_sentences_rule(self):
        result = wrap_whatsapp("Carlos", "Credito Libre", "Tasa 1.2%")

        assert "1 a 3 oraciones cortas" in result

    def test_contains_conversational_tone_rule(self):
        result = wrap_whatsapp("Carlos", "Credito Libre", "Tasa 1.2%")

        assert "Tono conversacional" in result

    def test_contains_only_message_output_rule(self):
        result = wrap_whatsapp("Carlos", "Credito Libre", "Tasa 1.2%")

        assert "Solo el texto del mensaje, nada más." in result

    def test_sanitizes_name_containing_newlines(self):
        result = wrap_whatsapp("Car\nlos", "Producto", "Beneficios")

        assert "<persona>Car los</persona>" in result
        assert "Car\nlos" not in result

    def test_sanitizes_product_containing_curly_braces(self):
        result = wrap_whatsapp("Carlos", "Prod{test}ucto", "Beneficios")

        assert "<producto>Prod(test)ucto</producto>" in result
        assert "{test}" not in result

    def test_generated_prompt_is_a_string(self):
        result = wrap_whatsapp("Carlos", "Credito", "Tasa 1.2%")

        assert isinstance(result, str)
        assert len(result) > 0


class TestWrapSms:
    def test_contains_character_limit_rule(self):
        result = wrap_sms("Carlos", "Credito", "Tasa 1.2%")

        assert "160 caracteres" in result

    def test_contains_no_emoji_rule(self):
        result = wrap_sms("Carlos", "Credito", "Tasa 1.2%")

        assert "Sin emojis" in result

    def test_contains_direct_and_concise_rule(self):
        result = wrap_sms("Carlos", "Credito", "Tasa 1.2%")

        assert "Directo y conciso" in result

    def test_contains_only_message_output_rule(self):
        result = wrap_sms("Carlos", "Credito Libre", "Tasa 1.2%")

        assert "Solo el texto del mensaje, nada más." in result

    def test_sanitizes_inputs_with_curly_braces(self):
        result = wrap_sms("Carlos", "Prod{test}ucto", "Benef{fit}")

        assert "<producto>Prod(test)ucto</producto>" in result
        assert "<beneficios>Benef(fit)</beneficios>" in result

    def test_generated_prompt_is_a_string(self):
        result = wrap_sms("Carlos", "Credito", "Tasa 1.2%")

        assert isinstance(result, str)
        assert len(result) > 0


class TestWrapEmail:
    def test_contains_greeting_rule(self):
        result = wrap_email("Carlos", "Credito", "Tasa 1.2%")

        assert "saludo inicial" in result

    def test_contains_farewell_rule(self):
        result = wrap_email("Carlos", "Credito", "Tasa 1.2%")

        assert "despedida cordial" in result

    def test_contains_detailed_tone_rule(self):
        result = wrap_email("Carlos", "Credito", "Tasa 1.2%")

        assert "más detallado" in result.lower()

    def test_contains_no_subject_rule(self):
        result = wrap_email("Carlos", "Credito", "Tasa 1.2%")

        assert "Sin asunto" in result

    def test_contains_only_message_output_rule(self):
        result = wrap_email("Carlos", "Credito Libre", "Tasa 1.2%")

        assert "Solo el texto del mensaje, nada más." in result

    def test_sanitizes_inputs_with_newlines_and_braces(self):
        result = wrap_email("Car\nlos", "Prod{ucto}", "Ben\r\neficio")

        assert "<persona>Car los</persona>" in result
        assert "Ben  eficio" in result

    def test_generated_prompt_is_a_string(self):
        result = wrap_email("Carlos", "Credito", "Tasa 1.2%")

        assert isinstance(result, str)
        assert len(result) > 0


class TestChannelWrappers:
    def test_contains_whatsapp_key(self):
        assert "whatsapp" in CHANNEL_WRAPPERS

    def test_contains_sms_key(self):
        assert "sms" in CHANNEL_WRAPPERS

    def test_contains_email_key(self):
        assert "email" in CHANNEL_WRAPPERS

    def test_has_exactly_three_channels(self):
        assert len(CHANNEL_WRAPPERS) == 3

    def test_whatsapp_key_maps_to_wrap_whatsapp(self):
        assert CHANNEL_WRAPPERS["whatsapp"] is wrap_whatsapp

    def test_sms_key_maps_to_wrap_sms(self):
        assert CHANNEL_WRAPPERS["sms"] is wrap_sms

    def test_email_key_maps_to_wrap_email(self):
        assert CHANNEL_WRAPPERS["email"] is wrap_email

    def test_all_wrappers_are_callable(self):
        for key, wrapper in CHANNEL_WRAPPERS.items():
            assert callable(wrapper), f"Wrapper for '{key}' is not callable"
