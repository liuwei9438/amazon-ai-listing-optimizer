from __future__ import annotations

import threading
import traceback


from services.batch_processor import process_batch
from services.task_manager import save_status



def run_task(
    records,
    task_id,
    api_key,
    model,
    options,
):
    """
    后台执行任务
    """

    try:

        save_status(
            task_id,
            {
                "task_id": task_id,
                "status": "running",
                "message": "AI任务开始",
                "completed":0,
                "total":len(records),
            }
        )


        profiles = process_batch(
            records,
            task_id,
            api_key,
            model,
            options,
        )


        save_status(
            task_id,
            {
                "task_id":task_id,
                "status":"completed",
                "message":"任务完成",
                "completed":len(profiles),
                "total":len(records),
            }
        )


    except Exception as e:


        save_status(
            task_id,
            {
                "task_id":task_id,
                "status":"failed",
                "message":str(e),
                "traceback":traceback.format_exc()
            }
        )



def start_worker(
    records,
    task_id,
    api_key,
    model,
    options,
):

    thread = threading.Thread(

        target=run_task,

        args=(
            records,
            task_id,
            api_key,
            model,
            options,
        ),

        daemon=True,

    )


    thread.start()


    return thread
