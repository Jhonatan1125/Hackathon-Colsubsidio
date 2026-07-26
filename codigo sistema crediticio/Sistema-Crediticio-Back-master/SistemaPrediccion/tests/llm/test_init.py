"""Smoke tests for ``credit_engine.llm`` public API — ensures all symbols are correctly exported."""

from __future__ import annotations

import credit_engine.llm as llm


class TestPackageExports:
    def test_all_matches_public_symbols(self):
        expected = {
            "OllamaClient",
            "LLMClientError",
            "LLMConnectionError",
            "LLMEmptyResponseError",
            "Channel",
            "MessageGenerator",
            "GenerationError",
            "UnknownChannelError",
            "SYSTEM_PROMPT",
            "CHANNEL_WRAPPERS",
            "ChannelWrapper",
        }

        assert set(llm.__all__) == expected

    def test_ollama_client_is_importable(self):
        assert hasattr(llm, "OllamaClient")

    def test_message_generator_is_importable(self):
        assert hasattr(llm, "MessageGenerator")

    def test_system_prompt_is_a_non_empty_string(self):
        assert isinstance(llm.SYSTEM_PROMPT, str)
        assert len(llm.SYSTEM_PROMPT) > 0

    def test_channel_wrappers_is_a_dict(self):
        assert isinstance(llm.CHANNEL_WRAPPERS, dict)

    def test_channel_wrappers_contains_whatsapp_sms_email(self):
        assert "whatsapp" in llm.CHANNEL_WRAPPERS
        assert "sms" in llm.CHANNEL_WRAPPERS
        assert "email" in llm.CHANNEL_WRAPPERS


class TestExceptionHierarchy:
    def test_llm_client_error_is_base_for_connection_error(self):
        assert issubclass(llm.LLMConnectionError, llm.LLMClientError)

    def test_llm_client_error_is_base_for_empty_response_error(self):
        assert issubclass(llm.LLMEmptyResponseError, llm.LLMClientError)

    def test_generation_error_is_base_for_unknown_channel_error(self):
        assert issubclass(llm.UnknownChannelError, llm.GenerationError)

    def test_client_errors_are_exceptions(self):
        assert issubclass(llm.LLMClientError, Exception)

    def test_generation_errors_are_exceptions(self):
        assert issubclass(llm.GenerationError, Exception)
