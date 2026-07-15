from __future__ import annotations

import json
import pickle
import time
from pathlib import Path
from typing import Any

import pandas as pd


class TaskManager:
    """Checkpoint manager for one active Streamlit optimization task."""

    def __init__(self, namespace: str = "default") -> None:
        safe = "".join(c if c.isalnum() or c in "_-" else "_" for c in namespace)
        self.root = Path.home() / ".amazon_ai_optimizer" / "tasks" / safe
        self.root.mkdir(parents=True, exist_ok=True)
        self.meta_path = self.root / "active_task.json"
        self.data_path = self.root / "active_task.pkl"

    def save(
        self,
        *,
        source_df: pd.DataFrame,
        result_df: pd.DataFrame,
        metadata: dict[str, Any],
    ) -> None:
        payload = {
            "source_df": source_df,
            "result_df": result_df,
        }
        data_tmp = self.data_path.with_suffix(".tmp")
        with data_tmp.open("wb") as f:
            pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)
        data_tmp.replace(self.data_path)

        meta = dict(metadata)
        meta["saved_at"] = time.time()
        meta_tmp = self.meta_path.with_suffix(".tmp")
        meta_tmp.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
        meta_tmp.replace(self.meta_path)

    def load(self) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]] | None:
        if not self.meta_path.exists() or not self.data_path.exists():
            return None
        try:
            meta = json.loads(self.meta_path.read_text(encoding="utf-8"))
            with self.data_path.open("rb") as f:
                payload = pickle.load(f)
            source_df = payload.get("source_df")
            result_df = payload.get("result_df")
            if not isinstance(source_df, pd.DataFrame) or not isinstance(result_df, pd.DataFrame):
                return None
            return source_df, result_df, meta
        except Exception:
            return None

    def clear(self) -> None:
        self.meta_path.unlink(missing_ok=True)
        self.data_path.unlink(missing_ok=True)
