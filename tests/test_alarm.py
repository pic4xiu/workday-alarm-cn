import unittest
from datetime import date
from datetime import datetime
from datetime import time
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from alarm import (
    already_sent,
    build_bark_url,
    decide,
    load_holiday_days,
    mark_sent,
    mask_bark_url,
    parse_positive_int,
    should_run_in_alarm_window,
)


HOLIDAYS = load_holiday_days(Path(__file__).resolve().parents[1] / "holidays.cn.2026.json")


class AlarmDecisionTests(unittest.TestCase):
    def test_makeup_workday_notifies(self):
        decision = decide(date(2026, 5, 9), HOLIDAYS, "workdays")
        self.assertTrue(decision.should_notify)
        self.assertTrue(decision.is_workday)
        self.assertTrue(decision.is_override)
        self.assertEqual(decision.reason, "调休补班日")

    def test_holiday_does_not_notify(self):
        decision = decide(date(2026, 5, 1), HOLIDAYS, "workdays")
        self.assertFalse(decision.should_notify)
        self.assertFalse(decision.is_workday)
        self.assertTrue(decision.is_override)

    def test_normal_weekday_notifies_in_workdays_mode(self):
        decision = decide(date(2026, 5, 12), HOLIDAYS, "workdays")
        self.assertTrue(decision.should_notify)
        self.assertEqual(decision.reason, "普通工作日")

    def test_normal_weekday_silent_in_makeup_only_mode(self):
        decision = decide(date(2026, 5, 12), HOLIDAYS, "makeup_only")
        self.assertFalse(decision.should_notify)
        self.assertTrue(decision.is_workday)

    def test_makeup_workday_notifies_in_makeup_only_mode(self):
        decision = decide(date(2026, 5, 9), HOLIDAYS, "makeup_only")
        self.assertTrue(decision.should_notify)
        self.assertEqual(decision.reason, "调休补班日")

    def test_normal_weekend_does_not_notify(self):
        decision = decide(date(2026, 5, 10), HOLIDAYS, "workdays")
        self.assertFalse(decision.should_notify)
        self.assertEqual(decision.reason, "普通周末")

    def test_should_run_in_alarm_window(self):
        self.assertFalse(should_run_in_alarm_window(datetime(2026, 5, 13, 9, 9, 59), time(9, 10), 10))
        self.assertTrue(should_run_in_alarm_window(datetime(2026, 5, 13, 9, 10, 0), time(9, 10), 10))
        self.assertTrue(should_run_in_alarm_window(datetime(2026, 5, 13, 9, 19, 59), time(9, 10), 10))
        self.assertFalse(should_run_in_alarm_window(datetime(2026, 5, 13, 9, 20, 0), time(9, 10), 10))

    def test_mask_bark_url_hides_key(self):
        config = {
            "bark_key": "secret-key",
            "bark_base_url": "https://api.day.app",
            "title": "调休闹钟",
            "body": "{date} {reason}",
        }
        url = build_bark_url(config, date(2026, 5, 9), "调休补班日")
        masked = mask_bark_url(url, config)
        self.assertIn("/***/", masked)
        self.assertNotIn("secret-key", masked)

    def test_mark_sent_and_already_sent(self):
        with TemporaryDirectory() as tmp_dir:
            state_path = Path(tmp_dir) / "state.json"
            target = date(2026, 5, 13)
            self.assertFalse(already_sent(state_path, target))
            mark_sent(state_path, target, datetime(2026, 5, 13, 9, 10))
            self.assertTrue(already_sent(state_path, target))
            self.assertFalse(already_sent(state_path, date(2026, 5, 14)))

    def test_parse_positive_int(self):
        self.assertEqual(parse_positive_int("10", "alarm_window_minutes"), 10)
        with self.assertRaisesRegex(ValueError, "alarm_window_minutes"):
            parse_positive_int("abc", "alarm_window_minutes")
        with self.assertRaisesRegex(ValueError, "alarm_window_minutes"):
            parse_positive_int(0, "alarm_window_minutes")

    def test_holiday_data_shape(self):
        self.assertTrue(HOLIDAYS)
        for day, kind in HOLIDAYS.items():
            parsed = date.fromisoformat(day)
            self.assertEqual(parsed.year, 2026)
            self.assertIn(kind, {"holiday", "workday"})


if __name__ == "__main__":
    unittest.main()
