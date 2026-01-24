#!/bin/bash

# Get project root directory (assuming script is in /scripts)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="$PROJECT_ROOT/logs/update.log"

# Create logs directory
mkdir -p "$PROJECT_ROOT/logs"

# Navigate to project root
cd "$PROJECT_ROOT"

# Activate virtual environment if it exists in 'venv' or '.venv' inside project
# Adjust this line if your venv is located elsewhere on the server
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "========================================" >> "$LOG_FILE"
echo "Starting update at $(date)" >> "$LOG_FILE"

# 1. Update historical data (CSV) - focused on current/recent seasons
# This helps ensure finished matches have final scores from CSV
echo "Running import_football_data..." >> "$LOG_FILE"
python manage.py import_football_data --min_year 2025 >> "$LOG_FILE" 2>&1

# 2. Update live matches and upcoming fixtures (API)
echo "Running update_live_matches..." >> "$LOG_FILE"
python manage.py update_live_matches >> "$LOG_FILE" 2>&1

echo "Update finished at $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
