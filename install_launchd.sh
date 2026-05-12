#!/usr/bin/env bash
set -euo pipefail

TIME_VALUE="${1:-07:30}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}"
LABEL="com.local.shift-alarm"
PLIST_PATH="$HOME/Library/LaunchAgents/${LABEL}.plist"
LOG_DIR="$HOME/Library/Logs"

if [[ ! "$TIME_VALUE" =~ ^([01][0-9]|2[0-3]):[0-5][0-9]$ ]]; then
  echo "时间格式应为 HH:MM，例如 07:30" >&2
  exit 1
fi

HOUR="${TIME_VALUE%:*}"
MINUTE="${TIME_VALUE#*:}"
HOUR="$((10#$HOUR))"
MINUTE="$((10#$MINUTE))"

mkdir -p "$HOME/Library/LaunchAgents" "$LOG_DIR"

cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${PYTHON_BIN}</string>
    <string>${SCRIPT_DIR}/alarm.py</string>
  </array>
  <key>WorkingDirectory</key>
  <string>${SCRIPT_DIR}</string>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>${HOUR}</integer>
    <key>Minute</key>
    <integer>${MINUTE}</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>${LOG_DIR}/shift-alarm.out.log</string>
  <key>StandardErrorPath</key>
  <string>${LOG_DIR}/shift-alarm.err.log</string>
  <key>RunAtLoad</key>
  <false/>
</dict>
</plist>
PLIST

launchctl unload "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl load "$PLIST_PATH"

echo "已安装 ${LABEL}，每天 ${TIME_VALUE} 执行。"
echo "配置文件：${SCRIPT_DIR}/config.json"
echo "日志：${LOG_DIR}/shift-alarm.out.log"
