
from __future__ import annotations

import random
import re
import time
from typing import Any

_LAST_REQUEST_AT = 0.0


def _retry_wait_from_error(exc: Exception, fallback: float) -> float:
    message = str(exc)
    patterns = [
        r"try again in\s*([0-9.]+)\s*s",
        r"retry after\s*([0-9.]+)",
        r"Please try again in\s*([0-9.]+)\s*s",
    ]
    for pattern in patterns:
        match = re.search(pattern, message, flags=re.I)
        if match:
            try:
                return max(float(match.group(1)) + 0.5, fallback)
            except ValueError:
                pass
    return fallback


def create_response_with_backoff(
    client: Any,
    *,
    model: str,
    input_text: str,
    max_output_tokens: int,
    attempts: int = 5,
    min_interval: float = 1.25,
) -> str:
    """Serializes requests and retries 429/temporary API errors with backoff."""
    global _LAST_REQUEST_AT

    last_error: Exception | None = None
    for attempt in range(max(1, attempts)):
        elapsed = time.monotonic() - _LAST_REQUEST_AT
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)

        try:
            response = client.responses.create(
                model=model,
                input=input_text,
                max_output_tokens=max_output_tokens,
            )
            _LAST_REQUEST_AT = time.monotonic()
            return str(response.output_text or "").strip()
        except Exception as exc:
            _LAST_REQUEST_AT = time.monotonic()
            last_error = exc
            message = str(exc).casefold()
            retryable = any(
                marker in message
                for marker in [
                    "429", "rate limit", "tpm", "temporarily",
                    "timeout", "timed out", "connection",
                    "server error", "500", "502", "503", "504",
                ]
            )
            if not retryable or attempt >= attempts - 1:
                raise

            fallback = min(30.0, 4.0 * (2 ** attempt))
            wait_seconds = _retry_wait_from_error(exc, fallback)
            wait_seconds += random.uniform(0.2, 0.8)
            time.sleep(wait_seconds)

    raise last_error or RuntimeError("API调用失败")
