
#!/usr/bin/env bash
set -e

echo "[start] Launching botai.py in background..."
python3 botai.py &
BOTAI_PID=$!

echo "[start] Launching bot.py (foreground)..."
python3 bot.py
BOT_EXIT=$?

echo "[start] bot.py exited with code $BOT_EXIT — stopping botai.py (pid $BOTAI_PID)"
kill "$BOTAI_PID" 2>/dev/null || true
exit "$BOT_EXIT"
