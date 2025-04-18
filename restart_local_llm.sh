#!/bin/bash

echo "🔪 Killing old Ollama + MCP processes..."
pkill -f ollama
pkill -f ollama-mcp
sleep 1

echo "✅ Checking for port zombies on 11434 and 3456..."
for port in 11434 3456; do
    pid=$(lsof -ti tcp:$port)
    if [ -n "$pid" ]; then
        echo "⚠️ Port $port in use by PID $pid — killing..."
        kill -9 $pid
    fi
done

echo "🧠 Starting Ollama backend..."
OLLAMA_NUM_PARALLEL=1 \
OLLAMA_CONTEXT_LENGTH=512 \
ollama serve > /tmp/ollama.log 2>&1 &

sleep 2  # Give it a sec to boot

echo "🌐 Starting MCP server (port 3456)..."
PORT=3456 npx @rawveg/ollama-mcp > /tmp/mcp.log 2>&1 &

sleep 2

echo "🎯 Checking health..."

curl -s http://localhost:11434 >/dev/null && echo "✅ Ollama running on :11434" || echo "❌ Ollama failed"
curl -s http://localhost:3456/models && echo "✅ MCP server live on :3456" || echo "❌ MCP failed"

echo "🚀 You're good to go. Hit it with your agent now."
