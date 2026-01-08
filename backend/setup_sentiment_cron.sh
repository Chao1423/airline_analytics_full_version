#!/bin/bash

# ============================================
# Setup Sentiment Analysis Pipeline Cron Job
# ============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/../venv"
PYTHON_SCRIPT="$SCRIPT_DIR/sentiment_pipeline.py"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Virtual environment not found at $VENV_PATH"
    exit 1
fi

# Create cron job command (runs daily at 3:00 AM, processes 1000 reviews)
CRON_COMMAND="0 3 * * * cd $SCRIPT_DIR && $VENV_PATH/bin/python $PYTHON_SCRIPT --batch-size 100 --max-reviews 1000 >> $SCRIPT_DIR/sentiment_pipeline.log 2>&1"

# Check if same cron job already exists
if crontab -l 2>/dev/null | grep -q "$PYTHON_SCRIPT"; then
    echo "⚠️  Cron job already exists. Removing old entry..."
    crontab -l 2>/dev/null | grep -v "$PYTHON_SCRIPT" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_COMMAND") | crontab -

echo "✅ Sentiment pipeline cron job added successfully!"
echo ""
echo "Schedule: Daily at 3:00 AM"
echo "Command: $CRON_COMMAND"
echo ""
echo "To view cron jobs: crontab -l"
echo "To remove this cron job: crontab -e (then delete the line)"
echo ""
echo "Log file: $SCRIPT_DIR/sentiment_pipeline.log"

