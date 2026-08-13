from pathlib import Path
import json


def control_path(task_id):

    return Path(
        "tasks"
    ) / task_id / "control.json"



def save_control(
    task_id,
    action
):

    path = control_path(
        task_id
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    path.write_text(
        json.dumps(
            {
                "action": action
            },
            ensure_ascii=False
        ),
        encoding="utf-8"
    )



def load_control(
    task_id
):

    path = control_path(
        task_id
    )


    if not path.exists():

        return "running"


    try:

        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        return data.get(
            "action",
            "running"
        )

    except Exception:

        return "running"
