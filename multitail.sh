#!/bin/bash

# 定义日志文件路径
LOG_FILES=("QRDATA.log" "SentINFO.log" "ERROR.log")

# 定义循环标志
RUNNING=true

# 定义一个函数用于停止 multitail 和清空日志
restart_multitail() {
    echo "Restarting multitail and clearing logs..."
    # 停止 multitail
    pkill -f "multitail"
    
    # 清空所有日志文件
    for LOG_FILE in "${LOG_FILES[@]}"; do
        if [ -f "$LOG_FILE" ]; then
            > "$LOG_FILE"
            echo "Cleared: $LOG_FILE"
        else
            echo "File not found: $LOG_FILE"
        fi
    done
}

# 捕获中断信号以停止脚本
trap "echo 'Stopping script...'; RUNNING=false; pkill -f 'multitail'; exit" SIGINT SIGTERM

# 主循环
while $RUNNING; do
    # 构建 multitail 命令参数
    MULTITAIL_CMD="multitail"
    for LOG_FILE in "${LOG_FILES[@]}"; do
        if [ -f "$LOG_FILE" ]; then
            MULTITAIL_CMD+=" $LOG_FILE"
        else
            echo "Warning: $LOG_FILE does not exist."
        fi
    done

    # 启动 multitail 查看日志文件
    echo "Starting multitail..."
    eval "$MULTITAIL_CMD &"
    
    # 等待 5 分钟
    sleep 300

    # 重启 multitail 和清空日志
    restart_multitail
done
