import json
from pathlib import Path


TASK_FILE = Path("current_task.json")


def save_current_task(task_id):

    TASK_FILE.write_text(
        json.dumps(
            {
                "task_id": task_id
            },
            ensure_ascii=False
        ),
        encoding="utf-8"
    )


def load_current_task():

    if not TASK_FILE.exists():

        return ""


    data = json.loads(
        TASK_FILE.read_text(
            encoding="utf-8"
        )
    )


    return data.get(
        "task_id",
        ""
    )
