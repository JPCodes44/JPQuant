#!/bin/bash

echo ""
echo "🧠 Searching for active Ollama & MCP processes..."
echo "-----------------------------------------------"

anything_killed=false
active_ports=()

kill_processes_by_name() {
    pattern="$1"
    pids=$(pgrep -f "$pattern")
    if [ -n "$pids" ]; then
        echo "🔪 Found process: '$pattern' (PID(s): $pids)"
        for pid in $pids; do
            # Capture open ports for each PID before killing
            ports=$(lsof -Pan -p "$pid" -iTCP -sTCP:LISTEN 2>/dev/null | awk '{print $9}' | grep ':')
            for port in $ports; do
                port_number=$(echo "$port" | awk -F: '{print $2}')
                active_ports+=("$port_number")
                echo "  ↪️  Listening on port $port_number"
            done
            kill -9 "$pid"
        done
        echo "✅ Killed: $pattern"
        anything_killed=true
    else
        echo "✅ No running process found for: $pattern"
    fi
}

kill_processes_by_name "ollama serve"
kill_processes_by_name "ollama-mcp"

echo ""
echo "🌐 Checking for remaining ports that might still be in use..."
echo "-------------------------------------------------------------"

# Remove duplicates from active_ports
unique_ports=($(echo "${active_ports[@]}" | tr ' ' '\n' | sort -u))

if [ ${#unique_ports[@]} -eq 0 ]; then
    echo "✅ No known LLM ports were detected."
else
    for port in "${unique_ports[@]}"; do
        if lsof -iTCP:"$port" -sTCP:LISTEN >/dev/null; then
            echo "❌ Port $port still in use!"
            lsof -iTCP:"$port" -sTCP:LISTEN
        else
            echo "✅ Port $port has been cleared."
        fi
    done
fi

echo ""
if [ "$anything_killed" = true ]; then
    echo "☠️  All matching Ollama/MCP processes have been terminated (if found)."
else
    echo "😴 Nothing was running. Everything is already clean."
fi

echo ""

