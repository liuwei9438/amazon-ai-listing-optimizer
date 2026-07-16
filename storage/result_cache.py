from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonResultCache:
    """Small persistent JSON cache suitable for Streamlit test deployments.

    Data survives browser refreshes and normal app reruns. Streamlit Community Cloud
    may clear local files after redeploy, app migration or a full container rebuild.
    """

    def __init__(self, namespace: str = "default") -> None:
        safe = "".join(c if c.isalnum() or c in "_-" else "_" for c in namespace)
        self.root = Path.home() / ".amazon_ai_optimizer" / "cache" / safe
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self.root / f"{key}.json"

    def get(self, key: str) -> dict[str, Any] | None:
        path = self._path(key)
        if not path.exists():
            return None
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else None
        except Exception:
            return None

    def set(self, key: str, value: dict[str, Any]) -> None:
        path = self._path(key)
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        temp.replace(path)

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)
