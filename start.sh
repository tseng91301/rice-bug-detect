#!/bin/bash

# 取得目前腳本 (start.sh) 所在的絕對路徑
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$SCRIPT_DIR"

SESSION="rice-bug-detect"

# 檢查 tmux 是否已安裝
if ! command -v tmux &> /dev/null; then
    echo "錯誤: 未安裝 tmux。請先安裝再執行此腳本。"
    exit 1
fi

# 如果 session 已存在，則先殺掉
tmux kill-session -t $SESSION 2>/dev/null

# 建立新的 tmux session，直接啟動 Backend，並指定工作目錄
tmux new-session -d -s $SESSION -n "FastAPI-Backend" -c "$SCRIPT_DIR"

# 在第一個視窗啟動 Backend
tmux send-keys -t $SESSION:0 "source venv/bin/activate && python -m backend.main" C-m

echo "已在 tmux 會話 '$SESSION' 中啟動服務。"
echo "FastAPI Backend: 視窗口 0 (http://localhost:13984)"
