# workday-alarm-cn

中国调休工作日闹钟。运行在 macOS 上，通过 Bark 给 iPhone 推送提醒。

这个项目解决一个很具体的问题：iPhone 的工作日闹钟不理解中国调休和周末补班。`workday-alarm-cn` 会在 Mac mini 或其他 macOS 设备上定时检查今天是否应当上班，并在提醒时间通过 Bark 推送到 iPhone。

当前内置数据覆盖 **2026 年中国法定节假日和调休补班安排**。

## 功能

- 识别中国法定节假日和调休补班日。
- 支持 Bark 推送。
- 提供 macOS launchd 安装脚本。
- 默认 10 分钟提醒窗口，容忍机器唤醒或调度延迟。
- 使用本地状态文件避免同一天重复推送。
- `--dry-run` 默认隐藏 Bark key，方便安全调试。
- Python 标准库实现，无第三方依赖。

## 环境要求

- macOS
- Python 3
- Bark App 和 Bark key

## 快速开始

建议把项目放在非 `~/Documents`、`~/Desktop`、`~/Downloads` 的目录中运行，因为 macOS 可能会限制 launchd 后台任务访问这些隐私保护目录。

从项目根目录复制运行副本：

```bash
mkdir -p ~/.local/share
rsync -a --exclude .git ./ ~/.local/share/workday-alarm-cn/
cd ~/.local/share/workday-alarm-cn
```

创建本地配置：

```bash
cp config.example.json config.json
```

编辑 `config.json`，填入你的 Bark key：

```json
{
  "bark_key": "你的BarkKey"
}
```

安装定时任务。下面示例表示：每 60 秒检查一次，如果当前时间落在 `09:10` 开始的提醒窗口内，并且今天需要上班，就发送提醒。

```bash
./install_launchd.sh 09:10
```

## 手动测试

只判断，不真正推送：

```bash
python3 alarm.py --date 2026-05-09 --dry-run
```

`--dry-run` 默认会隐藏 Bark key。如果确实需要查看完整 URL：

```bash
python3 alarm.py --date 2026-05-09 --dry-run --show-secret-url
```

测试普通休息日：

```bash
python3 alarm.py --date 2026-05-10 --dry-run
```

真实发送一条测试推送：

```bash
python3 alarm.py --date 2026-05-09
```

强制发送一条测试推送，即使当天不是工作日：

```bash
python3 alarm.py --date 2026-05-10 --force
```

运行测试：

```bash
python3 -m unittest discover
```

## 配置说明

`config.example.json` 包含所有支持的配置项：

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

关键配置：

- `bark_key`：你的 Bark key。定时任务建议写入 `config.json`。
- `alarm_time`：提醒窗口开始时间，格式为 `HH:MM`。
- `alarm_window_minutes`：提醒窗口长度。比如 `09:10` 和 `10` 表示 `09:10` 到 `09:19` 之间都可以触发。
- `notify_mode`：`workdays` 表示所有应上班日都提醒；`makeup_only` 表示只在调休补班日提醒。
- `level`、`volume`、`call`：Bark 关键提醒参数。不想使用关键提醒时，可以删除这些字段。

手动测试时可以临时使用环境变量：

```bash
export BARK_KEY="你的BarkKey"
```

但 launchd 后台任务不会自动继承你在 shell 里临时 `export` 的环境变量，所以正式定时任务推荐写入 `config.json`。

## 定时任务原理

安装脚本会创建用户级 LaunchAgent：

```text
~/Library/LaunchAgents/com.local.workday-alarm-cn.plist
```

任务每 60 秒运行一次：

```bash
python3 alarm.py --check-time
```

大多数时候脚本会静默退出。只有同时满足下面条件时才会继续判断并推送：

1. 当前时间落在 `alarm_time` 开始的提醒窗口内。
2. 今天还没有推送过。
3. 今天被判断为应上班日。

使用每分钟检查而不是 macOS 的 `StartCalendarInterval`，是为了规避部分 macOS 用户会话中日历触发不稳定的问题。

日志路径：

```text
~/Library/Logs/workday-alarm-cn.out.log
~/Library/Logs/workday-alarm-cn.err.log
```

调试静默检查：

```bash
python3 alarm.py --check-time --verbose
```

## 工作日判断规则

判断优先级：

1. 如果日期在 `holidays.cn.2026.json` 中：
   - `workday`：需要上班，推送。
   - `holiday`：休息，不推送。
2. 如果日期不在节假日表中：
   - 周一到周五：需要上班，推送。
   - 周六周日：休息，不推送。

程序会在本地写入：

```text
.workday-alarm-state.json
```

用于记录当天是否已经推送，避免同一天重复提醒。该文件已被 `.gitignore` 忽略。

## 卸载

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.local.workday-alarm-cn.plist
rm ~/Library/LaunchAgents/com.local.workday-alarm-cn.plist
```

## 常见问题

### 到点没有收到推送怎么办？

先看错误日志：

```bash
cat ~/Library/Logs/workday-alarm-cn.err.log
```

再确认任务是否已加载：

```bash
launchctl print gui/$(id -u)/com.local.workday-alarm-cn
```

也可以手动测试：

```bash
python3 alarm.py --date 2026-05-09 --dry-run
```

### 为什么不直接每天运行一次？

这个项目最初使用过 launchd 的 `StartCalendarInterval`，但在部分 macOS 用户会话中实测没有稳定触发。现在改为每 60 秒检查一次，绝大多数运行都会静默退出，只有进入提醒窗口才继续判断。

### 为什么建议不要放在 Documents 目录？

macOS 可能会限制 launchd 后台任务访问 `~/Documents`、`~/Desktop`、`~/Downloads` 等隐私保护目录。建议放在 `~/.local/share/workday-alarm-cn`。

### iPhone 静音模式下能响吗？

示例配置默认使用 Bark 的关键提醒：

```json
{
  "level": "critical",
  "volume": "5",
  "call": "1"
}
```

你还需要在 iPhone 设置里允许 Bark 的关键提醒权限。

## 安全和隐私

- `config.json` 包含 Bark key，已被 `.gitignore` 忽略，不应提交到公开仓库。
- `--dry-run` 默认隐藏 Bark key。
- `--show-secret-url` 会显示完整 Bark URL，分享日志或截图前请谨慎使用。
- 默认日志不会输出 Bark key。

## 节假日数据

2026 年节假日数据来自中国政府网：

https://www.gov.cn/zhengce/zhengceku/202511/content_7047091.htm

后续年份需要新增或替换对应年份的节假日数据文件，并在 `config.json` 中调整 `holiday_file`。

## License

MIT
