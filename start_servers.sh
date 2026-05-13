#!/bin/bash
cd /Users/leooh/Desktop/Matchy

# Kill existing
pkill -f "uvicorn api.main" 2>/dev/null
pkill -f "next dev" 2>/dev/null
sleep 1

# API server
nohup /Users/leooh/Desktop/Matchy/.venv/bin/python -m uvicorn api.main:app \
  --host 0.0.0.0 --port 8000 \
  > /tmp/matchy_api.log 2>&1 &
echo "API PID: $!"

# Frontend
cd /Users/leooh/Desktop/Matchy/frontend
nohup node node_modules/next/dist/bin/next dev --port 3001 \
  > /tmp/matchy_frontend.log 2>&1 &
echo "Frontend PID: $!"

echo "Starting... check logs:"
echo "  API:      tail -f /tmp/matchy_api.log"
echo "  Frontend: tail -f /tmp/matchy_frontend.log"
