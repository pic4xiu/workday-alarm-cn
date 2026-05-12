# workday-alarm-cn

一个跑在 Mac mini 上的中国调休闹钟：每天固定时间判断今天是否需要上班，如果需要，就通过 Bark HTTP API 推送到 iPhone。

当前内置 2026 年中国法定节假日和调休补班数据。

## 文件说明

- `alarm.py`：主程序，负责判断日期并调用 Bark。
- `config.example.json`：配置示例。
- `holidays.cn.2026.json`：2026 年中国法定节假日和调休补班表。
- `install_launchd.sh`：生成并加载 macOS launchd 定时任务。
- `tests/test_alarm.py`：核心判断逻辑测试。
- `LICENSE`：MIT License。

## 快速开始

复制配置文件：

```bash
cp config.example.json config.json
```

编辑 `config.json`，填入你的 Bark key：

```json
{
  "bark_key": "你的BarkKey"
}
```

`config.json` 包含个人 Bark key，已被 `.gitignore` 忽略，请不要提交到公开仓库。

也可以不写入配置文件，改用环境变量：

```bash
export BARK_KEY="你的BarkKey"
```

## 手动测试

只判断，不真正推送：

```bash
python3 alarm.py --date 2026-05-09 --dry-run
```

测试普通休息日：

```bash
python3 alarm.py --date 2026-05-10 --dry-run
```

真正发送一条测试推送：

```bash
python3 alarm.py --date 2026-05-09
```

强制发送测试推送：

```bash
python3 alarm.py --date 2026-05-10 --force
```

`--force` 会忽略日期判断并发送推送，适合测试 Bark；输出里的原因仍然会保留原始判断结果，例如“普通周末”。

运行测试：

```bash
python3 -m unittest discover
```

## 安装定时任务

默认每天 `07:30` 执行：

```bash
./install_launchd.sh
```

指定时间：

```bash
./install_launchd.sh 07:15
```

安装后会生成：

```text
~/Library/LaunchAgents/com.local.workday-alarm-cn.plist
```

日志在：

```text
~/Library/Logs/workday-alarm-cn.out.log
~/Library/Logs/workday-alarm-cn.err.log
```

卸载定时任务：

```bash
launchctl unload ~/Library/LaunchAgents/com.local.workday-alarm-cn.plist
rm ~/Library/LaunchAgents/com.local.workday-alarm-cn.plist
```

## 运行策略

判断优先级：

1. 如果日期在 `holidays.cn.2026.json` 中：
   - `workday`：需要上班，推送。
   - `holiday`：休息，不推送。
2. 如果日期不在节假日表中：
   - 周一到周五：需要上班，推送。
   - 周六周日：休息，不推送。

默认会在所有“应上班日”推送。如果你只想在周末调休补班时推送，把 `config.json` 中的 `notify_mode` 改成：

```json
{
  "notify_mode": "makeup_only"
}
```

## Bark 提醒参数

示例配置默认开启：

```json
{
  "level": "critical",
  "volume": "5",
  "call": "1"
}
```

含义：

- `level=critical`：使用 Bark 关键提醒，可能绕过静音和专注模式，需要 iPhone 上允许 Bark 的关键提醒权限。
- `volume=5`：关键提醒音量，范围通常为 `0` 到 `10`。
- `call=1`：连续播放提醒音，适合闹钟场景。

如果不想使用关键提醒，可以从 `config.json` 中删除 `level`、`volume` 和 `call`。

## 数据来源

2026 年节假日数据来自中国政府网：

https://www.gov.cn/zhengce/zhengceku/202511/content_7047091.htm

后续年份需要新增或替换对应年份的节假日数据文件，并在 `config.json` 中调整 `holiday_file`。
