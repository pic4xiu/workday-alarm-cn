#!/usr/bin/env bash
set -euo pipefail

TIME_VALUE="${1:-07:30}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}"
LABEL="com.local.workday-alarm-cn"
PLIST_PATH="$HOME/Library/LaunchAgents/${LABEL}.plist"
LOG_DIR="$HOME/Library/Logs"
LOG_PREFIX="workday-alarm-cn"
USER_ID="$(id -u)"
LAUNCHD_DOMAIN="gui/${USER_ID}"

if [[ ! "$TIME_VALUE" =~ ^([01][0-9]|2[0-3]):[0-5][0-9]$ ]]; then
  echo "时间格式应为 HH:MM，例如 07:30" >&2
  exit 1
fi

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
    <string>--check-time</string>
  </array>
  <key>WorkingDirectory</key>
  <string>${SCRIPT_DIR}</string>
  <key>StartInterval</key>
  <integer>60</integer>
  <key>StandardOutPath</key>
  <string>${LOG_DIR}/${LOG_PREFIX}.out.log</string>
  <key>StandardErrorPath</key>
  <string>${LOG_DIR}/${LOG_PREFIX}.err.log</string>
  <key>RunAtLoad</key>
  <false/>
</dict>
</plist>
PLIST

CONFIG_PATH="${SCRIPT_DIR}/config.json"
EXAMPLE_CONFIG_PATH="${SCRIPT_DIR}/config.example.json"
if [[ ! -f "$CONFIG_PATH" && -f "$EXAMPLE_CONFIG_PATH" ]]; then
  cp "$EXAMPLE_CONFIG_PATH" "$CONFIG_PATH"
fi

if [[ -f "$CONFIG_PATH" ]]; then
  "$PYTHON_BIN" - "$CONFIG_PATH" "$TIME_VALUE" <<'PY'
import json
import sys
from pathlib import Path

config_path = Path(sys.argv[1])
alarm_time = sys.argv[2]
config = json.loads(config_path.read_text(encoding="utf-8"))
config["alarm_time"] = alarm_time
config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
else
  echo "未找到 config.json 或 config.example.json，请先创建配置文件。" >&2
  exit 1
fi

launchctl bootout "${LAUNCHD_DOMAIN}" "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl bootstrap "${LAUNCHD_DOMAIN}" "$PLIST_PATH"
launchctl enable "${LAUNCHD_DOMAIN}/${LABEL}"

echo "已安装 ${LABEL}，每 60 秒检查一次，每天 ${TIME_VALUE} 符合条件时推送。"
echo "配置文件：${SCRIPT_DIR}/config.json"
echo "日志：${LOG_DIR}/${LOG_PREFIX}.out.log"
