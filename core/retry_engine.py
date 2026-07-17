from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any


def run_with_retries(operation: Callable[[str], tuple[dict[str, Any], bool, str, int]], attempts: int = 4) -> tuple[dict[str, Any], bool, str, int]:
    reason = ""
    last: dict[str, Any] = {}
    score = 0
    for _ in range(attempts):
        last, ok, reason, score = operation(reason)
        if ok:
            return last, True, "", score
        time.sleep(0.35)
    return last, False, reason or "未知质检失败", score
