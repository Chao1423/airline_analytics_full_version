#!/bin/bash

# Script to run sentiment pipeline in background
# Usage: ./run_pipeline_background.sh [batch_size] [log_file]

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

# Activate virtual environment
VENV_ACTIVATE="$PROJECT_ROOT/venv/bin/activate"
PIPELINE_SCRIPT="$SCRIPT_DIR/sentiment_pipeline.py"

# Parameters
BATCH_SIZE=${1:-100}
LOG_FILE=${2:-"$PROJECT_ROOT/pipeline.log"}

# Check virtual environment
if [ ! -f "$VENV_ACTIVATE" ]; then
    echo "❌ Error: Python virtual environment not found at $VENV_ACTIVATE"
    exit 1
fi

# Check script
if [ ! -f "$PIPELINE_SCRIPT" ]; then
    echo "❌ Error: Pipeline script not found at $PIPELINE_SCRIPT"
    exit 1
fi

echo "🚀 Starting sentiment pipeline in background..."
echo "   Batch size: $BATCH_SIZE"
echo "   Log file: $LOG_FILE"
echo ""
echo "To view logs: tail -f $LOG_FILE"
echo "To stop: pkill -f sentiment_pipeline.py"
echo ""

# Run in background
nohup bash -c "source $VENV_ACTIVATE && python3 $PIPELINE_SCRIPT --batch-size $BATCH_SIZE" > "$LOG_FILE" 2>&1 &

PID=$!
echo "✅ Pipeline started with PID: $PID"
echo "   Check status: ps aux | grep $PID"

