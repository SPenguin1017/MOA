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

# 更新 .ini 文件中的時間
update_ini_time() {
    local new_time=$1
    sed -i "s/^time = .*/time = $new_time/" $INI_FILE
}

# 啟動排程
start_scheduler() {
    NEXT_TIME=$(get_next_time)
    if [ -z "$NEXT_TIME" ]; then
        log_error "未能從 $INI_FILE 中提取時間"
        exit 1
    fi

    # 執行一次 MOA.py
    echo "執行 $PYTHON_SCRIPT_PATH..."
    python3 $PYTHON_SCRIPT_PATH >> $ERROR_LOG 2>&1
    if [ $? -ne 0 ]; then
        log_error "執行 $PYTHON_SCRIPT_PATH 時發生錯誤"
        exit 1
    fi

    # 計算新時間（加 3 小時）
    NEW_TIME=$(date -d "$NEXT_TIME" "+%Y-%m-%d %H:%M:%S")

    # 更新 .ini 文件中的時間
    update_ini_time "$NEW_TIME"
    echo "已將新時間更新到 $INI_FILE：$NEW_TIME"

    # 生成新的 cron 表達式
    NEW_CRON_TIME=$(date -d "$NEW_TIME" "+%M %H %d %m *")

    # 更新 crontab
    (crontab -l 2>/dev/null | grep -v "$PYTHON_SCRIPT_PATH"; echo "$NEW_CRON_TIME python3 $PYTHON_SCRIPT_PATH >> $ERROR_LOG 2>&1") | crontab -

    echo "新的 cron 排程已添加：$NEW_CRON_TIME 執行 $PYTHON_SCRIPT_PATH"
}

# 停止排程
stop_scheduler() {
    (crontab -l 2>/dev/null | grep -v "$PYTHON_SCRIPT_PATH") | crontab -
    echo "已移除 $PYTHON_SCRIPT_PATH 的排程"
}

# API 控制功能
case $1 in
    start)
        echo "啟動排程..."
        start_scheduler
        ;;
    stop)
        echo "停止排程..."
        stop_scheduler
        ;;
    *)
        echo "用法: $0 {start|stop}"
        exit 1
        ;;
esac
