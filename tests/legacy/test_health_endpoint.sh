#!/bin/bash
# Test script for the new /health-check endpoint

echo "🚀 Starting MTG NLP Search server..."
cd mtg-nlp-search
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

# Wait for server to start
sleep 3

echo "🔍 Testing /health-check endpoint..."
curl -s http://localhost:8000/health-check | python3 -m json.tool

echo -e "\n⏱️  Waiting 5 seconds and testing again to see uptime change..."
sleep 5

curl -s http://localhost:8000/health-check | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'✅ Server uptime: {data[\"uptime\"][\"formatted\"]}')
print(f'📝 Git commit: {data[\"deployment\"][\"git_commit\"]}')
print(f'🌿 Git branch: {data[\"deployment\"][\"git_branch\"]}')
print(f'🏠 Environment: {data[\"deployment\"][\"environment\"]}')
print(f'👥 Commanders loaded: {data[\"services\"][\"commanders_loaded\"]} ({data[\"services\"][\"commander_count\"]} total)')
"

echo -e "\n🛑 Stopping server..."
kill $SERVER_PID
wait $SERVER_PID 2>/dev/null

echo "✅ Test complete!"
