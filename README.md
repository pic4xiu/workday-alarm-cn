# workday-alarm-cn

China holiday-aware workday alarm for macOS, powered by Bark.

`workday-alarm-cn` solves a small but annoying problem: iPhone weekday alarms do not understand China makeup workdays. This project runs on a Mac mini or any macOS machine, checks whether today should be treated as a workday, and sends a Bark notification when it is time to wake up.

Current bundled holiday data covers China's 2026 public holidays and makeup workdays.

## Features

- China holiday and makeup workday aware.
- Bark notification support.
- macOS launchd installer.
- 10-minute alarm window to tolerate delayed wakeups.
- Once-per-day state file to avoid duplicate notifications.
- Secret-safe dry runs: Bark key is masked by default.
- No third-party Python dependency.

## Requirements

- macOS.
- Python 3.
- Bark app and Bark key.

## Quick Start

Clone or copy the project, then keep the runnable copy outside macOS privacy-protected folders such as `~/Documents`, `~/Desktop`, and `~/Downloads`:

```bash
mkdir -p ~/.local/share
rsync -a --exclude .git ./ ~/.local/share/workday-alarm-cn/
cd ~/.local/share/workday-alarm-cn
```

Create local config:

```bash
cp config.example.json config.json
```

Edit `config.json` and set your Bark key:

```json
{
  "bark_key": "your-bark-key"
}
```

Install the launchd job. This example checks every minute and sends the alarm during the `09:10` alarm window when today is a workday:

```bash
./install_launchd.sh 09:10
```

## Manual Testing

Check a makeup workday without sending:

```bash
python3 alarm.py --date 2026-05-09 --dry-run
```

`--dry-run` masks the Bark key by default. To print the full URL:

```bash
python3 alarm.py --date 2026-05-09 --dry-run --show-secret-url
```

Send a real test notification:

```bash
python3 alarm.py --date 2026-05-09
```

Force a notification even on a non-workday:

```bash
python3 alarm.py --date 2026-05-10 --force
```

Run tests:

```bash
python3 -m unittest discover
```

## Configuration

`config.example.json` contains all supported options:

```json
{
  "bark_key": "",
  "bark_base_url": "https://api.day.app",
  "title": "调休闹钟",
  "body": "今天需要上班，别睡过啦",
  "alarm_time": "09:10",
  "alarm_window_minutes": 10,
  "notify_mode": "workdays",
  "sound": "chime",
  "level": "critical",
  "volume": "5",
  "call": "1",
  "group": "shift-alarm",
  "timezone": "Asia/Shanghai",
  "holiday_file": "holidays.cn.2026.json"
}
```

Important options:

- `alarm_time`: Alarm window start time in `HH:MM`.
- `alarm_window_minutes`: Window length. With `09:10` and `10`, any run from `09:10` to `09:19` can send the notification.
- `notify_mode`: `workdays` sends on all workdays; `makeup_only` sends only on makeup workdays.
- `level`, `volume`, `call`: Bark critical-alert options. Remove them for normal notifications.

Manual tests can use `BARK_KEY`, but launchd jobs do not automatically inherit shell exports. For scheduled alarms, write `bark_key` into `config.json`.

## How Scheduling Works

The installer writes a user LaunchAgent:

```text
~/Library/LaunchAgents/com.local.workday-alarm-cn.plist
```

The job runs every 60 seconds:

```bash
python3 alarm.py --check-time
```

Most runs exit silently. The script only continues when:

1. Current time is inside the configured alarm window.
2. Today's notification has not already been sent.
3. Today is considered a workday.

This interval-based design avoids `StartCalendarInterval` reliability issues observed in some macOS user sessions.

Logs:

```text
~/Library/Logs/workday-alarm-cn.out.log
~/Library/Logs/workday-alarm-cn.err.log
```

Verbose debugging:

```bash
python3 alarm.py --check-time --verbose
```

## Workday Rules

The decision order is:

1. If the date is in `holidays.cn.2026.json`:
   - `workday`: send.
   - `holiday`: do not send.
2. Otherwise:
   - Monday to Friday: send.
   - Saturday or Sunday: do not send.

The script writes `.workday-alarm-state.json` locally after a successful scheduled notification to prevent duplicate sends on the same day.

## Uninstall

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.local.workday-alarm-cn.plist
rm ~/Library/LaunchAgents/com.local.workday-alarm-cn.plist
```

## Troubleshooting

If nothing happens:

- Keep the project outside `~/Documents`, `~/Desktop`, and `~/Downloads`.
- Check `~/Library/Logs/workday-alarm-cn.err.log`.
- Run `python3 alarm.py --date 2026-05-09 --dry-run`.
- Confirm Bark critical alerts are allowed on iPhone if using `level=critical`.
- Confirm the LaunchAgent is loaded:

```bash
launchctl print gui/$(id -u)/com.local.workday-alarm-cn
```

## Security And Privacy

- `config.json` contains your Bark key and is ignored by Git.
- `--dry-run` masks the Bark key by default.
- `--show-secret-url` prints the full Bark URL. Avoid sharing that output.
- Default logs do not include the Bark key.

## Holiday Data

2026 holiday data comes from the State Council notice published on gov.cn:

https://www.gov.cn/zhengce/zhengceku/202511/content_7047091.htm

Future years require adding or replacing the corresponding holiday data file and updating `holiday_file` in `config.json`.

## License

MIT
