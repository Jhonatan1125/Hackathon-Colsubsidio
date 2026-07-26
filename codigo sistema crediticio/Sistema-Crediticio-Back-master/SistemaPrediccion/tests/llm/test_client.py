"""Unit tests for ``credit_engine.llm.client`` — OllamaClient, response parsing, retries."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

import pytest

from credit_engine.llm.client import (
    LLMClientError,
    LLMConnectionError,
    LLMEmptyResponseError,
    OllamaClient,
)


def _mock_ollama_response(content: str, finish_reason: str = "stop") -> MagicMock:
    """Build a mock that behaves like ``urlopen()`` return value in a ``with`` block."""
    payload = json.dumps(
        {"choices": [{"message": {"content": content}, "finish_reason": finish_reason}]}
    ).encode("utf-8")
    response_mock = MagicMock()
    response_mock.read.return_value = payload
    context_mock = MagicMock()
    context_mock.__enter__.return_value = response_mock
    return context_mock


class TestOllamaClientInit:
    def test_default_values(self):
        client = OllamaClient()

        assert client._base_url == "http://localhost:12434"
        assert client._endpoint == "http://localhost:12434/v1/chat/completions"
        assert client._model == "docker.io/ai/qwen2.5:latest"
        assert client._timeout == 30.0
        assert client._max_retries == 2

    def test_custom_values(self):
        client = OllamaClient(
            base_url="http://10.0.0.1:9999",
            model="custom-model",
            timeout=60.0,
            max_retries=5,
        )

        assert client._base_url == "http://10.0.0.1:9999"
        assert client._endpoint == "http://10.0.0.1:9999/v1/chat/completions"
        assert client._model == "custom-model"
        assert client._timeout == 60.0
        assert client._max_retries == 5

    def test_trailing_slash_stripped_from_base_url(self):
        client = OllamaClient(base_url="http://localhost:12434/")

        assert client._base_url == "http://localhost:12434"
        assert client._endpoint == "http://localhost:12434/v1/chat/completions"

    def test_negative_max_retries_raises_value_error(self):
        with pytest.raises(ValueError, match="max_retries must be >= 0"):
            OllamaClient(max_retries=-1)


class TestOllamaClientGenerate:
    @patch("credit_engine.llm.client.urlopen")
    def test_returns_text_from_response(self, mock_urlopen):
        mock_urlopen.return_value = _mock_ollama_response("Hola Carlos")
        client = OllamaClient()

        result = client.generate("system", "user")

        assert result == "Hola Carlos"

    @patch("credit_engine.llm.client.urlopen")
    def test_retries_on_urlerror_and_succeeds(self, mock_urlopen):
        mock_urlopen.side_effect = [
            URLError("timeout"),
            URLError("timeout"),
            _mock_ollama_response("Final success"),
        ]
        client = OllamaClient(max_retries=2)

        result = client.generate("system", "user")

        assert result == "Final success"
        assert mock_urlopen.call_count == 3

    @patch("credit_engine.llm.client.urlopen")
    def test_raises_connection_error_when_all_urlerror_retries_exhausted(self, mock_urlopen):
        mock_urlopen.side_effect = [URLError("timeout"), URLError("timeout"), URLError("timeout")]
        client = OllamaClient(max_retries=2)

        with pytest.raises(LLMConnectionError, match="All 3 attempts failed"):
            client.generate("system", "user")

        assert mock_urlopen.call_count == 3

    @patch("credit_engine.llm.client.urlopen")
    def test_retries_on_5xx_error_and_succeeds(self, mock_urlopen):
        mock_urlopen.side_effect = [
            HTTPError("url", 500, "Internal Error", {}, None),  # type: ignore[arg-type]
            _mock_ollama_response("Recovered"),
        ]
        client = OllamaClient(max_retries=1)

        result = client.generate("system", "user")

        assert result == "Recovered"
        assert mock_urlopen.call_count == 2

    @patch("credit_engine.llm.client.urlopen")
    def test_raises_connection_error_after_all_5xx_retries_exhausted(self, mock_urlopen):
        mock_urlopen.side_effect = HTTPError("url", 503, "Down", {}, None)  # type: ignore[arg-type]
        client = OllamaClient(max_retries=1)

        with pytest.raises(LLMConnectionError, match="All 2 attempts failed"):
            client.generate("system", "user")

        assert mock_urlopen.call_count == 2

    @patch("credit_engine.llm.client.urlopen")
    def test_raises_client_error_on_4xx_no_retry(self, mock_urlopen):
        mock_urlopen.side_effect = HTTPError("url", 400, "Bad Request", {}, None)  # type: ignore[arg-type]
        client = OllamaClient(max_retries=2)

        with pytest.raises(LLMClientError, match="Client error 400"):
            client.generate("system", "user")

        assert mock_urlopen.call_count == 1

    @patch("credit_engine.llm.client.urlopen")
    def test_retries_on_connection_reset_and_succeeds(self, mock_urlopen):
        mock_urlopen.side_effect = [
            ConnectionResetError("connection reset by peer"),
            _mock_ollama_response("Recovered"),
        ]
        client = OllamaClient(max_retries=1)

        result = client.generate("system", "user")

        assert result == "Recovered"
        assert mock_urlopen.call_count == 2

    @patch("credit_engine.llm.client.urlopen")
    def test_converts_incomplete_read_to_connection_error(self, mock_urlopen):
        from http.client import IncompleteRead

        mock_urlopen.side_effect = IncompleteRead(b"partial body")
        client = OllamaClient(max_retries=0)

        with pytest.raises(LLMConnectionError, match="All 1 attempts failed"):
            client.generate("system", "user")

    @patch("credit_engine.llm.client.urlopen")
    def test_max_retries_zero_attempts_once(self, mock_urlopen):
        mock_urlopen.return_value = _mock_ollama_response("Ok")
        client = OllamaClient(max_retries=0)

        result = client.generate("system", "user")

        assert result == "Ok"
        assert mock_urlopen.call_count == 1

    @patch("credit_engine.llm.client.urlopen")
    def test_max_retries_zero_fails_immediately_on_urlerror(self, mock_urlopen):
        mock_urlopen.side_effect = URLError("timeout")
        client = OllamaClient(max_retries=0)

        with pytest.raises(LLMConnectionError, match="All 1 attempts failed"):
            client.generate("system", "user")

    @patch("credit_engine.llm.client.urlopen")
    def test_sends_correct_payload_to_api(self, mock_urlopen):
        mock_urlopen.return_value = _mock_ollama_response("ok")
        client = OllamaClient(model="test-model")

        client.generate("sys prompt", "user prompt")

        call_args = mock_urlopen.call_args[0][0]
        body = json.loads(call_args.data.decode("utf-8"))
        assert body["model"] == "test-model"
        assert body["messages"][0] == {"role": "system", "content": "sys prompt"}
        assert body["messages"][1] == {"role": "user", "content": "user prompt"}


class TestParseResponse:
    def test_valid_response_returns_content(self):
        payload = json.dumps({"choices": [{"message": {"content": "Hello"}}]}).encode()

        result = OllamaClient._parse_response(payload)

        assert result == "Hello"

    def test_strips_surrounding_whitespace_from_content(self):
        payload = json.dumps({"choices": [{"message": {"content": "  Hello  "}}]}).encode()

        result = OllamaClient._parse_response(payload)

        assert result == "Hello"

    def test_invalid_json_raises_client_error(self):
        with pytest.raises(LLMClientError, match="invalid JSON"):
            OllamaClient._parse_response(b"not json")

    def test_non_dict_top_level_raises_client_error(self):
        with pytest.raises(LLMClientError, match="not a JSON object"):
            OllamaClient._parse_response(b'["list"]')

    def test_missing_choices_key_raises_empty_response_error(self):
        with pytest.raises(LLMEmptyResponseError, match="no choices"):
            OllamaClient._parse_response(b"{}")

    def test_empty_choices_list_raises_empty_response_error(self):
        payload = json.dumps({"choices": []}).encode()

        with pytest.raises(LLMEmptyResponseError, match="no choices"):
            OllamaClient._parse_response(payload)

    def test_first_choice_not_a_dict_raises_client_error(self):
        payload = json.dumps({"choices": ["invalid"]}).encode()

        with pytest.raises(LLMClientError, match="not a JSON object"):
            OllamaClient._parse_response(payload)

    def test_missing_message_key_in_choice_raises_client_error(self):
        payload = json.dumps({"choices": [{"finish_reason": "stop"}]}).encode()

        with pytest.raises(LLMClientError, match="not a JSON object"):
            OllamaClient._parse_response(payload)

    def test_message_not_a_dict_raises_client_error(self):
        payload = json.dumps({"choices": [{"message": "not dict"}]}).encode()

        with pytest.raises(LLMClientError, match="not a JSON object"):
            OllamaClient._parse_response(payload)

    def test_content_missing_from_message_raises_empty_response_error(self):
        payload = json.dumps({"choices": [{"message": {}}]}).encode()

        with pytest.raises(LLMEmptyResponseError, match="empty content"):
            OllamaClient._parse_response(payload)

    def test_empty_string_content_raises_empty_response_error(self):
        payload = json.dumps({"choices": [{"message": {"content": ""}}]}).encode()

        with pytest.raises(LLMEmptyResponseError, match="empty content"):
            OllamaClient._parse_response(payload)

    def test_whitespace_only_content_raises_empty_response_error(self):
        payload = json.dumps({"choices": [{"message": {"content": "   "}}]}).encode()

        with pytest.raises(LLMEmptyResponseError, match="empty content"):
            OllamaClient._parse_response(payload)

    def test_length_finish_reason_raises_empty_response_error(self):
        payload = json.dumps(
            {"choices": [{"message": {"content": "x"}, "finish_reason": "length"}]}
        ).encode()

        with pytest.raises(LLMEmptyResponseError, match="token limit"):
            OllamaClient._parse_response(payload)

    def test_content_filter_finish_reason_raises_empty_response_error(self):
        payload = json.dumps(
            {"choices": [{"message": {"content": "x"}, "finish_reason": "content_filter"}]}
        ).encode()

        with pytest.raises(LLMEmptyResponseError, match="content filter"):
            OllamaClient._parse_response(payload)
