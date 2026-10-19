# registro: 2026-10-19 | autor: Miguel (via OpenCode) | modelo: opencode/big-pickle
"""R007-C: quiet-hour window policy tests (RED/GREEN for docs/ARCHITECTURE.md SPEC)."""
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("AGENT_STATE_DB", str(Path(tempfile.mkdtemp()) / "agent.db"))
os.environ.setdefault("AGENT_AUDIT_LOG", str(Path(tempfile.mkdtemp()) / "audit.jsonl"))

import telebot_cognitive as tc


class FakeDateTime:
    """Clock injection for rate_allowed without touching real time."""

    _now = None

    @classmethod
    def set(cls, dt):
        cls._now = dt

    @classmethod
    def now(cls, tz=None):
        return cls._now.astimezone(tz) if tz else cls._now


class QuietHoursHelperTest(unittest.TestCase):
    def test_cross_midnight_default_22_08(self):
        # spec item 2: start>end keeps the historical crossing-midnight behaviour
        for hour in (22, 23, 0, 1, 7):
            self.assertTrue(tc.quiet_hours_active(hour, 22, 8), f"hour {hour} must be quiet")
        for hour in (8, 12, 21):
            self.assertFalse(tc.quiet_hours_active(hour, 22, 8), f"hour {hour} must be active")

    def test_same_day_window_09_17(self):
        # spec item 1: start<end blocks exactly start<=hour<end (defect reproduced here)
        for hour in (9, 12, 16):
            self.assertTrue(tc.quiet_hours_active(hour, 9, 17), f"hour {hour} must be quiet")
        for hour in (0, 8, 17, 21, 23):
            self.assertFalse(tc.quiet_hours_active(hour, 9, 17), f"hour {hour} must be active")

    def test_start_equals_end_active_all_day(self):
        # spec item 3: start==end stays quiet all day (previous fail-closed behaviour)
        for hour in range(24):
            self.assertTrue(tc.quiet_hours_active(hour, 5, 5), f"hour {hour} must be quiet")

    def test_invalid_bounds_fail_closed(self):
        # spec item 3/4: invalid hour bounds fail closed (quiet = blocked)
        self.assertTrue(tc.quiet_hours_active(10, -1, 8))
        self.assertTrue(tc.quiet_hours_active(10, 22, 24))
        self.assertTrue(tc.quiet_hours_active(10, "x", 8))
        self.assertTrue(tc.quiet_hours_active(10, 22, None))


class RateAllowedQuietWindowTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self._orig_db = tc.STATE_DB
        self._orig_start = tc.QUIET_START
        self._orig_end = tc.QUIET_END
        self._orig_now = tc.datetime
        tc.STATE_DB = Path(self._tmp) / "agent.db"
        tc.QUIET_START = 9
        tc.QUIET_END = 17
        self.db = tc.connect_state()

    def tearDown(self):
        self.db.close()
        tc.STATE_DB = self._orig_db
        tc.QUIET_START = self._orig_start
        tc.QUIET_END = self._orig_end
        tc.datetime = self._orig_now

    def _at(self, hour):
        FakeDateTime.set(datetime(2026, 10, 19, hour, 0, tzinfo=tc.LOCAL_TZ))
        tc.datetime = FakeDateTime

    def test_inside_hours_blocks_before_any_other_check(self):
        self._at(10)
        ok, reason = tc.rate_allowed(self.db, "-100123")
        self.assertFalse(ok)
        self.assertEqual(reason, "quiet_hours")

    def test_after_hours_reaches_policy_checks(self):
        self._at(20)
        ok, reason = tc.rate_allowed(self.db, "-100123")
        self.assertTrue(ok, f"expected policy pass on empty state, got {reason}")

    def test_same_day_boundary_17_is_active(self):
        self._at(17)
        ok, reason = tc.rate_allowed(self.db, "-100123")
        self.assertTrue(ok, f"expected hour 17 outside 09-17 window, got {reason}")


if __name__ == "__main__":
    unittest.main()
