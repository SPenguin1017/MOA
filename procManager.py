from fastapi import FastAPI, HTTPException
import subprocess
import os
import uvicorn
from datetime import datetime

app = FastAPI()

# 定義路徑
SCRIPT_PATH = "./run.sh"
ERROR_LOG = "./error.log"


def log_error(message: str):
    """
    將錯誤訊息記錄到 error.log
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ERROR_LOG, "a") as log_file:
        log_file.write(f"{timestamp} - 系統啟動 - {message}\n")


def run_script(action: str):
    """
    執行 run.sh 的指定動作
    """
    try:
        result = subprocess.run(
            [SCRIPT_PATH, action],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            # 如果腳本返回非零狀態碼，記錄錯誤日誌
            log_error(f"執行腳本 '{action}' 時失敗: {result.stderr}")
            raise Exception(result.stderr)
        return result.stdout.strip()
    except Exception as e:
        # 如果執行過程中出現異常，記錄錯誤日誌
        log_error(f"執行腳本 '{action}' 時發生異常: {e}")
        raise HTTPException(status_code=500, detail=f"執行腳本錯誤: {e}")


@app.post("/start")
def start_task():
    """
    啟動 run.sh 的任務
    """
    output = run_script("start")
    return {"message": "任務已啟動", "output": output}


@app.post("/stop")
def stop_task():
    """
    停止排程
    """
    output = run_script("stop")
    return {"message": "排程已停止", "output": output}


@app.get("/log")
def get_error_log():
    """
    獲取錯誤日誌
    """
    if not os.path.exists(ERROR_LOG):
        raise HTTPException(status_code=404, detail="錯誤日誌不存在")
    with open(ERROR_LOG, "r") as file:
        logs = file.readlines()
    return {"logs": logs}


if __name__ == "__main__":
    uvicorn.run("procManager:app", host="0.0.0.0", port=2486, reload=True)
