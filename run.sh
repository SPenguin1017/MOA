#!/bin/bash

# 定義路徑
INI_FILE="CSConfig.ini"
PYTHON_SCRIPT_PATH="./MOA.py"
ERROR_LOG="error.log"

# 紀錄錯誤函數
log_error() {
    echo "$(date "+%Y-%m-%d %H:%M:%S") - 錯誤: $1" >> $ERROR_LOG
}

# 從 .ini 文件中提取時間
get_next_time() {
    grep "^time" $INI_FILE | sed 's/time = //'
}

# 更新排程
update_cron() {
    local next_time=$1

    # 計算時間（cron 格式）
    CRON_TIME=$(date -d "$next_time" "+%M %H %d %m *")
    if [ $? -ne 0 ]; then
        log_error "無法解析時間格式：$next_time"
        exit 1
    fi

    # 更新 crontab
    (crontab -l 2>/dev/null | grep -v "$0"; echo "$CRON_TIME $PWD/$0 start >> $ERROR_LOG 2>&1") | crontab -
    echo "已添加新的排程：$CRON_TIME 執行 $0 start"
}

# 執行主任務並設置下一次排程
run_task() {
    echo "執行 $PYTHON_SCRIPT_PATH..."
    python3 $PYTHON_SCRIPT_PATH >> $ERROR_LOG 2>&1
    if [ $? -ne 0 ]; then
        log_error "執行 $PYTHON_SCRIPT_PATH 時發生錯誤"
        exit 1
    fi

    # 從 .ini 文件中獲取下一次時間
    NEXT_TIME=$(get_next_time)
    if [ -z "$NEXT_TIME" ]; then
        log_error "未能從 $INI_FILE 中提取時間"
        exit 1
    fi
    echo "下一次排程時間為：$NEXT_TIME"

    # 設置新的排程
    update_cron "$NEXT_TIME"
}

# 停止排程
stop_scheduler() {
    (crontab -l 2>/dev/null | grep -v "$0") | crontab -
    echo "已移除排程"
}

# API 控制功能
case $1 in
    start)
        run_task
        ;;
    stop)
        stop_scheduler
        ;;
    *)
        echo "用法: $0 {start|stop}"
        exit 1
        ;;
esac
