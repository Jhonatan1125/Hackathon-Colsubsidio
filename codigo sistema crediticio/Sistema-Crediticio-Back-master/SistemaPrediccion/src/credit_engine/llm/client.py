"""Ollama HTTP client wrapper — Adapter pattern isolating HTTP details from business logic."""

from __future__ import annotations

import json
import os
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from credit_engine.config import LLM_BASE_URL_ENV_VAR, LLM_MODEL_ENV_VAR


class LLMClientError(Exception):
    """Base exception for LLM client failures."""


class LLMConnectionError(LLMClientError):
    """Raised when the LLM endpoint is unreachable or times out."""


class LLMEmptyResponseError(LLMClientError):
    """Raised when the LLM returns no usable content."""


class OllamaClient:
    """Adapter wrapping the Ollama OpenAI-compatible chat completions API.

    Isolates HTTP transport, retries, and response parsing from the
    rest of the module.  If the LLM backend changes, only this file
    needs to change.
    """

    _DEFAULT_MODEL: str = "docker.io/ai/qwen2.5:latest"
    _DEFAULT_BASE_URL: str = "http://localhost:12434"

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 2,
    ) -> None:
        """Initialise the Ollama client.

        Args:
            base_url: Base URL of the Ollama server. Falls back to the
                ``LLM_BASE_URL`` env var, then to ``http://localhost:12434``.
            model: Model name to use. Falls back to the ``LLM_MODEL`` env
                var, then to ``_DEFAULT_MODEL``.
            timeout: HTTP request timeout in seconds.
            max_retries: Number of retries after the first attempt fails.
        """
        if max_retries < 0:
            raise ValueError(f"max_retries must be >= 0, got {max_retries}")

        self._base_url: str = (
            base_url
            or os.environ.get(LLM_BASE_URL_ENV_VAR)
            or self._DEFAULT_BASE_URL
        ).rstrip("/")
        self._endpoint: str = f"{self._base_url}/v1/chat/completions"
        self._model: str = (
            model
            or os.environ.get(LLM_MODEL_ENV_VAR)
            or self._DEFAULT_MODEL
        )
        self._timeout: float = timeout
        self._max_retries: int = max_retries

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Send a chat completion request and return the model's text.

        Args:
            system_prompt: The system-level instruction for the model.
            user_prompt: The user-level prompt with the specific request.

        Returns:
            The model's text response, stripped of surrounding whitespace.

        Raises:
            LLMConnectionError: If the endpoint cannot be reached after all retries.
            LLMEmptyResponseError: If the model returns no usable content.
            LLMClientError: If the returned payload is malformed.
        """
        payload: dict[str, object] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        for attempt in range(1, self._max_retries + 2):
            body: bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            request = Request(
                self._endpoint,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urlopen(request, timeout=self._timeout) as response:
                    raw: bytes = response.read()
                    return self._parse_response(raw)
            except HTTPError as exc:
                if 400 <= exc.code < 500:
                    raise LLMClientError(
                        f"Client error {exc.code} from {self._endpoint}: {exc.reason}"
                    ) from exc
                if attempt == self._max_retries + 1:
                    raise LLMConnectionError(
                        f"All {self._max_retries + 1} attempts failed with server error {exc.code}"
                    ) from exc
            except (OSError, HTTPException) as exc:
                # Covers URLError, TimeoutError, ConnectionResetError,
                # IncompleteRead, etc. — any transport failure during the
                # request or while reading the response body. Nothing
                # untyped may escape this method (the delivery pipeline's
                # fallback depends on it).
                if attempt == self._max_retries + 1:
                    raise LLMConnectionError(
                        f"All {self._max_retries + 1} attempts failed: cannot reach {self._endpoint}"
                    ) from exc
        raise AssertionError("Unreachable: the loop always raises or returns")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_response(raw: bytes) -> str:
        """Extract ``choices[0].message.content`` from the JSON response."""

        try:
            data: object = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMClientError("LLM returned invalid JSON") from exc

        if not isinstance(data, dict):
            raise LLMClientError(f"LLM response is not a JSON object (got {type(data).__name__})")

        choices: object = data.get("choices")
        if not isinstance(choices, list) or len(choices) == 0:
            raise LLMEmptyResponseError("LLM response contains no choices")

        first_choice: object = choices[0]
        if not isinstance(first_choice, dict):
            raise LLMClientError(f"LLM choice is not a JSON object (got {type(first_choice).__name__})")

        message: object = first_choice.get("message")
        if not isinstance(message, dict):
            raise LLMClientError(f"LLM message is not a JSON object (got {type(message).__name__})")

        content: object = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise LLMEmptyResponseError("LLM returned empty content")

        finish_reason: object = first_choice.get("finish_reason")
        if finish_reason == "length":
            raise LLMEmptyResponseError("LLM response truncated (token limit)")
        if finish_reason == "content_filter":
            raise LLMEmptyResponseError("LLM response blocked by content filter")

        return content.strip()
