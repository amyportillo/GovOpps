#!/bin/bash
# Starts the full GovOpps project:
# 1. Activates the virtual environment
# 2. Runs the ETL to pull fresh contracts from SAM.gov
# 3. Starts the API in the background
# 4. Starts the dashboard in the background
# 5. Opens both in your browser

cd /Users/amyportillo/Documents/GovOpps/GovOpps

source venv/bin/activate

# Kill anything already running on our ports so we always start fresh
echo "Clearing ports 8000 and 8501..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:8501 | xargs kill -9 2>/dev/null
sleep 1

echo ""
echo "Running ETL..."
python3 run.py etl

echo ""
echo "Starting API..."
uvicorn api:app --host 0.0.0.0 --port 8000 &
API_PID=$!

echo "Starting dashboard..."
uvicorn dashboard:app --host 0.0.0.0 --port 8501 &
DASH_PID=$!

# Give the servers a moment to start before opening the browser
sleep 2

open http://localhost:8000/docs
open http://localhost:8501

echo ""
echo "Everything is running!"
echo "  API       -> http://localhost:8000/docs  (PID $API_PID)"
echo "  Dashboard -> http://localhost:8501       (PID $DASH_PID)"
echo ""
echo "Press Ctrl+C to stop everything."

# Wait and clean up both processes when you hit Ctrl+C
trap "kill $API_PID $DASH_PID 2>/dev/null; echo 'Stopped.'" INT
wait
