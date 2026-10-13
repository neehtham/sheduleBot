import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
os.environ.setdefault("Telegram_Token", "test-token")

import bot
import reader


class TomorrowScheduleTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.update = SimpleNamespace(
            effective_user=SimpleNamespace(id=123),
            message=SimpleNamespace(reply_text=AsyncMock()),
        )
        self.context = SimpleNamespace()

    async def test_registered_user_receives_tomorrows_schedule(self):
        details = {"code": "APD1F2309SE", "group": "G1", "accommodation": "Maple"}
        with (
            patch.object(bot, "read_users", new_callable=AsyncMock, return_value={"123": details}),
            patch.object(bot, "getting", new_callable=AsyncMock, return_value=True) as refresh,
            patch.object(bot, "finder", return_value="Tomorrow's classes") as finder,
        ):
            await bot.tomorrow_schedule(self.update, self.context)

        refresh.assert_awaited_once()
        args = finder.call_args.args
        self.assertEqual(args[:3], ("APD1F2309SE", "G1", "Maple"))
        self.assertEqual(args[3], datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).date() + timedelta(days=1))
        self.update.message.reply_text.assert_awaited_once_with("Tomorrow's classes")

    async def test_unregistered_user_is_prompted_to_register(self):
        with (
            patch.object(bot, "read_users", new_callable=AsyncMock, return_value={}),
            patch.object(bot, "getting", new_callable=AsyncMock) as refresh,
        ):
            await bot.tomorrow_schedule(self.update, self.context)

        refresh.assert_not_awaited()
        self.update.message.reply_text.assert_awaited_once_with(
            "You are not registered. Use /register first."
        )

    async def test_fetch_failure_does_not_send_stale_schedule(self):
        with (
            patch.object(bot, "read_users", new_callable=AsyncMock, return_value={"123": {"code": "A"}}),
            patch.object(bot, "getting", new_callable=AsyncMock, return_value=False),
            patch.object(bot, "finder") as finder,
        ):
            await bot.tomorrow_schedule(self.update, self.context)

        finder.assert_not_called()
        self.update.message.reply_text.assert_awaited_once_with(
            "Could not fetch the schedule right now. Please try again later."
        )


class ReaderDateTests(unittest.TestCase):
    def test_finder_filters_by_requested_date_and_labels_tomorrow(self):
        today = datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).date()
        tomorrow = today + timedelta(days=1)
        with tempfile.TemporaryDirectory() as temp:
            data_dir = Path(temp)
            intake_dir = data_dir / "intake"
            intake_dir.mkdir()
            lectures = [
                {"name": name, "date": day.strftime("%d, %m, %Y"), "group": group,
                 "room": room, "start": "09:00 AM", "end": "10:00 AM"}
                for name, day, group, room in (
                    ("Today's lecture", today, "G1", "Room 1"),
                    ("Tomorrow's lecture", tomorrow, "G1", "Room 2"),
                    ("Another group's lecture", tomorrow, "G2", "Room 3"),
                    ("Online tomorrow", tomorrow, "G1", "ONLINE"),
                )
            ]
            (intake_dir / "TEST.json").write_text(json.dumps(lectures), encoding="utf-8")
            (data_dir / "busShedule.json").write_text("[]", encoding="utf-8")

            with (
                patch.object(reader, "DATA_DIR", data_dir),
                patch.object(reader, "get_intake_dir", return_value=intake_dir),
            ):
                result = reader.finder("TEST", "G1", "Maple", tomorrow)
                empty_result = reader.finder("TEST", "G3", "Maple", tomorrow)
                today_result = reader.finder("TEST", "G1", "Maple")

        self.assertIn("1 physical classes tomorrow", result)
        self.assertIn("Tomorrow's lecture", result)
        self.assertIn("Online tomorrow", result)
        self.assertNotIn("Today's lecture", result)
        self.assertNotIn("Another group's lecture", result)
        self.assertIn("No physical classes tomorrow", empty_result)
        self.assertIn("No online classes tomorrow", empty_result)
        self.assertIn("Today's lecture", today_result)
        self.assertIn("1 physical classes today", today_result)
        self.assertNotIn("Tomorrow's lecture", today_result)


if __name__ == "__main__":
    unittest.main()
