#!/usr/bin/env python3
import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import urlopen

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None


ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = {
    "bark_key": "",
    "bark_base_url": "https://api.day.app",
    "title": "调休闹钟",
    "body": "今天需要上班，别睡过啦",
    "notify_mode": "workdays",
    "sound": "chime",
    "level": "critical",
    "volume": "5",
    "call": "1",
    "group": "shift-alarm",
    "timezone": "Asia/Shanghai",
    "holiday_file": "holidays.cn.2026.json",
}


@dataclass(frozen=True)
class Decision:
    should_notify: bool
    is_workday: bool
    is_override: bool
    reason: str


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_config(config_path: Path) -> dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    if config_path.exists():
        config.update(load_json(config_path))

    env_bark_key = os.environ.get("BARK_KEY")
    if env_bark_key:
        config["bark_key"] = env_bark_key

    return config


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("日期格式应为 YYYY-MM-DD") from exc


def today_in_timezone(tz_name: str) -> date:
    if ZoneInfo is None:
        return date.today()
    return datetime.now(ZoneInfo(tz_name)).date()


def resolve_path(path_value: str, base: Path = ROOT) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path
    return base / path


def load_holiday_days(path: Path) -> dict[str, str]:
    data = load_json(path)
    days = data.get("days", data)
    if not isinstance(days, dict):
        raise ValueError(f"{path} 中缺少 days 对象")
    return {str(k): str(v) for k, v in days.items()}


def decide(target_date: date, holiday_days: dict[str, str], notify_mode: str) -> Decision:
    date_key = target_date.isoformat()
    override = holiday_days.get(date_key)
    weekday = target_date.weekday()
    is_weekday = weekday < 5

    if override == "workday":
        return Decision(
            should_notify=True,
            is_workday=True,
            is_override=True,
            reason="调休补班日",
        )

    if override == "holiday":
        return Decision(
            should_notify=False,
            is_workday=False,
            is_override=True,
            reason="法定节假日",
        )

    if override is not None:
        raise ValueError(f"{date_key} 的节假日类型无效: {override}")

    if notify_mode == "makeup_only":
        return Decision(
            should_notify=False,
            is_workday=is_weekday,
            is_override=False,
            reason="非调休补班日",
        )

    if is_weekday:
        return Decision(
            should_notify=True,
            is_workday=True,
            is_override=False,
            reason="普通工作日",
        )

    return Decision(
        should_notify=False,
        is_workday=False,
        is_override=False,
        reason="普通周末",
    )


def build_bark_url(config: dict[str, Any], target_date: date, reason: str) -> str:
    bark_key = str(config.get("bark_key", "")).strip()
    if not bark_key:
        raise ValueError("缺少 Bark key：请在 config.json 写入 bark_key，或设置 BARK_KEY 环境变量")

    base_url = str(config.get("bark_base_url", DEFAULT_CONFIG["bark_base_url"])).rstrip("/")
    title = quote(str(config.get("title", DEFAULT_CONFIG["title"])), safe="")
    body_template = str(config.get("body", DEFAULT_CONFIG["body"]))
    body = body_template.format(date=target_date.isoformat(), reason=reason)
    path = f"{base_url}/{quote(bark_key, safe='')}/{title}/{quote(body, safe='')}"

    params = []
    for key in ("sound", "group", "icon", "url", "level", "volume", "call", "badge"):
        value = str(config.get(key, "")).strip()
        if value:
            params.append(f"{quote(key)}={quote(value, safe='')}")

    if params:
        return f"{path}?{'&'.join(params)}"
    return path


def send_bark(url: str, timeout: int = 10) -> str:
    with urlopen(url, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(description="中国调休闹钟：判断今天是否上班，并通过 Bark 推送。")
    parser.add_argument("--config", default=str(ROOT / "config.json"), help="配置文件路径")
    parser.add_argument("--date", type=parse_date, help="测试指定日期，格式 YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true", help="只输出判断结果，不调用 Bark")
    parser.add_argument("--force", action="store_true", help="忽略日期判断，强制发送 Bark")
    args = parser.parse_args()

    config_path = resolve_path(args.config, Path.cwd())
    config = load_config(config_path)
    holiday_path = resolve_path(str(config.get("holiday_file", DEFAULT_CONFIG["holiday_file"])), ROOT)
    holiday_days = load_holiday_days(holiday_path)
    notify_mode = str(config.get("notify_mode", DEFAULT_CONFIG["notify_mode"]))

    if notify_mode not in {"workdays", "makeup_only"}:
        raise ValueError("notify_mode 只能是 workdays 或 makeup_only")

    target_date = args.date or today_in_timezone(str(config.get("timezone", DEFAULT_CONFIG["timezone"])))
    decision = decide(target_date, holiday_days, notify_mode)

    print(
        json.dumps(
            {
                "date": target_date.isoformat(),
                "should_notify": decision.should_notify,
                "is_workday": decision.is_workday,
                "is_override": decision.is_override,
                "reason": decision.reason,
                "notify_mode": notify_mode,
            },
            ensure_ascii=False,
        )
    )

    if not args.force and not decision.should_notify:
        return 0

    if args.dry_run:
        if str(config.get("bark_key", "")).strip():
            print(f"dry-run: {build_bark_url(config, target_date, decision.reason)}")
        else:
            print("dry-run: would send Bark notification; bark_key is not configured")
        return 0

    url = build_bark_url(config, target_date, decision.reason)
    print(send_bark(url))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
