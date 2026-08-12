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

        "task_id":
            task_id,


        "filename":
            filename,


        # 统一字段
        "total":
            total_products,


        "completed":
            0,


        "success":
            0,


        "failed":
            0,


        "status":
            "created",


        "message":
            "任务已创建",


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


    old_status = load_status(
        task_id
    )


    if old_status:

        old_status.update(
            status
        )

        status = old_status



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



    try:

        content = path.read_text(
            encoding="utf-8"
        )
    
    
        if not content.strip():
    
            return {}
    
    
        return json.loads(
            content
        )
    
    
    except json.JSONDecodeError:
    
        return {}
    
    
    except Exception:

        return {}





def save_json(
    path: Path,
    data: dict
):


    temp_path = path.with_suffix(".tmp")


    temp_path.write_text(
        json.dumps(
            status,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )
    
    
    temp_path.replace(path)
