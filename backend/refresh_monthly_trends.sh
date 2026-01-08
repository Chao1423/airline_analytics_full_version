#!/bin/bash

# Shell script to refresh monthly trends materialized view
# Can be called via cron job

cd "$(dirname "$0")"
source ../venv/bin/activate

echo "🔄 Refreshing monthly trends materialized view..."
python3 refresh_monthly_trends.py

