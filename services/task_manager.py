from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path


TASK_ROOT = Path("tasks")


def ensure_task_root():

    TASK_ROOT.mkdir(
        parents=True,
        exist_ok=True
    )


def create_task(
    total_products: int,
    filename: str,
):

    ensure_task_root()


    task_id = (
        datetime.now()
        .strftime("%Y%m%d_%H%M%S")
        +
        "_"
        +
        uuid.uuid4()
        .hex[:6]
    )


    task_dir = TASK_ROOT / task_id

    task_dir.mkdir(
        parents=True,
        exist_ok=True
    )


    status = {

        "task_id": task_id,

        "filename": filename,

        "total_products":
            total_products,

        "completed": 0,

        "success": 0,

        "failed": 0,

        "status":
            "created",

        "created_at":
            datetime.now()
            .isoformat(),

    }


    save_json(
        task_dir / "status.json",
        status
    )


    return task_id



def get_task_dir(
    task_id: str
):

    return (
        TASK_ROOT
        /
        task_id
    )



def save_status(
    task_id: str,
    status: dict
):

    task_dir = get_task_dir(
        task_id
    )

    save_json(
        task_dir / "status.json",
        status
    )



def load_status(
    task_id: str
):

    path = (
        get_task_dir(task_id)
        /
        "status.json"
    )


    if not path.exists():

        return {}


    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )



def save_json(
    path: Path,
    data: dict
):

    path.write_text(

        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),

        encoding="utf-8"

    )
