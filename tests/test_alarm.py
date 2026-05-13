import unittest
from datetime import date
from datetime import datetime
from datetime import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from alarm import decide, load_holiday_days, should_run_for_current_minute


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

    def test_normal_weekend_does_not_notify(self):
        decision = decide(date(2026, 5, 10), HOLIDAYS, "workdays")
        self.assertFalse(decision.should_notify)
        self.assertEqual(decision.reason, "普通周末")

    def test_should_run_for_current_minute(self):
        self.assertTrue(should_run_for_current_minute(datetime(2026, 5, 13, 9, 10, 59), time(9, 10)))
        self.assertFalse(should_run_for_current_minute(datetime(2026, 5, 13, 9, 11, 0), time(9, 10)))


if __name__ == "__main__":
    unittest.main()
