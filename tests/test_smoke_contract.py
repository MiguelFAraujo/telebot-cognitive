# registro: 2026-10-19 | autor: Miguel (via OpenCode) | modelo: opencode/big-pickle
"""R007-D: transport contract + smoke, no real Telegram/gateway messages."""
import asyncio
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import telebot_cognitive as tc


class TransportContractTest(unittest.TestCase):
    def test_telethon_is_lazy_not_imported(self):
        # module-level import must not pull the Telegram transport
        self.assertNotIn("telethon", sys.modules)

    def test_send_disabled_by_default(self):
        # dry-run default: process_cycle never reaches send_telegram
        self.assertFalse(os.environ.get("AGENT_SEND_ENABLED"))
        self.assertFalse(tc.SEND_ENABLED)

    def test_import_has_no_side_effects(self):
        # no state DB or audit log merely from import
        self.assertFalse(Path(tc.STATE_DB).exists())
        self.assertFalse(Path(tc.AUDIT_LOG).exists())

    def test_send_telegram_fails_closed_without_transport(self):
        # no local transport/credentials -> local exception, zero network
        saved = os.environ.pop("TELEGRAM_SESSION", None)
        try:
            with self.assertRaises((KeyError, ImportError)):
                asyncio.run(tc.send_telegram({"chat_id": "-100", "msg_id": 1}, "x"))
        finally:
            if saved is not None:
                os.environ["TELEGRAM_SESSION"] = saved

    def test_race_gate_not_applicable_single_threaded(self):
        # process_cycle is a serial loop; no shared mutable state across threads
        src = Path(tc.__file__).read_text(encoding="utf-8")
        self.assertNotIn("threading", src)
        self.assertNotIn("multiprocessing", src)


if __name__ == "__main__":
    unittest.main()
