from __future__ import annotations

import json
from pathlib import Path


from services.task_manager import get_task_dir


def get_result_path(task_id: str):
    """
    获取结果文件路径
    """

    task_dir = get_task_dir(task_id)

    return task_dir / "profiles.json"



def get_failed_path(task_id: str):

    task_dir = get_task_dir(task_id)

    return task_dir / "failed.json"



def save_profiles(
    task_id: str,
    profiles: list,
):
    """
    保存已经成功生成的产品结果
    """

    path = get_result_path(task_id)

    path.write_text(

        json.dumps(
            profiles,
            ensure_ascii=False,
            indent=2
        ),

        encoding="utf-8"

    )



def load_profiles(
    task_id: str,
):
    """
    读取任务结果
    """

    path = get_result_path(task_id)


    if not path.exists():

        return []


    return json.loads(

        path.read_text(
            encoding="utf-8"
        )

    )



def save_failed_items(
    task_id: str,
    failed_items: list,
):
    """
    保存失败产品
    """

    path = get_failed_path(task_id)


    path.write_text(

        json.dumps(
            failed_items,
            ensure_ascii=False,
            indent=2
        ),

        encoding="utf-8"

    )



def load_failed_items(
    task_id: str,
):

    path = get_failed_path(task_id)


    if not path.exists():

        return []


    return json.loads(

        path.read_text(
            encoding="utf-8"
        )

    )
