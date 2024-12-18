#!/bin/bash
# 獲取當前腳本所在的目錄
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 定義變數（使用相對路徑）
PYTHON_SCRIPT_PATH="$BASE_DIR/MOA.py"
INI_FILE="$BASE_DIR/CSConfig.ini"
LOG_FILE="$BASE_DIR/log.txt"

# 記錄錯誤日誌
log_error() {
    echo "$(date "+%Y-%m-%d %H:%M:%S") - sh錯誤: $1" >> "$LOG_FILE"
}

# 儲存 PID 到 INI 文件
save_pid_to_ini() {
    local pid=$1
    sed -i "/^pid =/c\pid = $pid" "$INI_FILE"
    echo "PID 已儲存到 $INI_FILE"
}

# 從 INI 文件中讀取 PID
read_pid_from_ini() {
    grep "^pid =" "$INI_FILE" | awk -F' = ' '{print $2}'
}

# 啟動 Python 任務
start_task() {
    local current_pid=$(read_pid_from_ini)
    if [ -n "$current_pid" ] && ps -p "$current_pid" > /dev/null 2>&1; then
        echo "服務已經在運行中，PID: $current_pid"
        exit 0
    fi

    echo "啟動 $PYTHON_SCRIPT_PATH ..."
    cd "$BASE_DIR"
    nohup python3 "$PYTHON_SCRIPT_PATH" --MOA >> "$LOG_FILE" 2>&1 &
    new_pid=$!
    save_pid_to_ini "$new_pid"
    echo "服務已啟動，PID: $new_pid"
}

# 停止 Python 任務
stop_task() {
    local current_pid=$(read_pid_from_ini)
    if [ -n "$current_pid" ]; then
        if ps -p "$current_pid" > /dev/null 2>&1; then
            echo "停止服務，PID: $current_pid"
            kill "$current_pid"
            sed -i "/^pid =/c\pid = " "$INI_FILE"  # 清空 PID
            echo "服務已停止"
        else
            echo "PID $current_pid 不存在，清理 INI 文件的 PID 設定"
            sed -i "/^pid =/c\pid = " "$INI_FILE"
        fi
    else
        echo "服務未在運行"
    fi
}

# 查看日誌
show_log() {
    if [ -f "$LOG_FILE" ]; then
        echo "顯示日誌內容："
        tail -n 20 "$LOG_FILE"
    else
        echo "日誌文件不存在"
    fi
}

# 主程式邏輯
case $1 in
    start)
        start_task
        ;;
    stop)
        stop_task
        ;;
    log)
        show_log
        ;;
    *)
        echo "用法: $0 {start|stop|log}"
        exit 1
        ;;
esac
