#!/usr/bin/env python3
"""
Automated Verification & Quality Test Suite for 19.GYM Bot
Validates:
1. Security & Authentication Lock (Chat ID Hijack Prevention)
2. Indian Standard Time (IST) Localization across all schedulers
3. Atomic File Writes, Thread Locking, and Automated Daily Backups
4. Intent Classification Engine (Zero accidental meal logging)
5. Dynamic Tesseract OCR Discovery & Fallback
6. CLI Tracker Integration
"""

import os
import sys
import json
import shutil
import unittest
from datetime import datetime, timezone, timedelta

# Import modules under test
import telegram_bot
import tracker

class TestGymCoachProductionReadiness(unittest.TestCase):

    def setUp(self):
        self.test_dir = os.path.join(telegram_bot.BASE_DIR, "test_scratch")
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_security_lock_unauthorized_user_blocked(self):
        """Verify SEC-01: Stranger cannot hijack Darshan's chat ID or access logs."""
        bot = telegram_bot.TelegramBot(token="MOCK_TOKEN:MOCK_SECRET", authorized_chat_id=8650465749)
        self.assertEqual(bot.authorized_chat_id, 8650465749)

        # Mock an unauthorized user trying to message the bot
        unauthorized_update = {
            "update_id": 1001,
            "message": {
                "message_id": 55,
                "chat": {"id": 123456789},  # Stranger's ID
                "text": "Hello coach, what is my status?"
            }
        }

        # Mock send_message so it doesn't make real network calls
        sent_messages = []
        bot.send_message = lambda cid, txt, parse_mode="Markdown": sent_messages.append((cid, txt))

        # Handle stranger's update
        bot.handle_update(unauthorized_update)

        # 1. Profile must NOT be overwritten
        profile = telegram_bot.load_profile()
        self.assertEqual(profile.get("telegram_chat_id"), 8650465749, "Master Chat ID was corrupted!")

        # 2. Stranger must receive Access Denied
        self.assertEqual(len(sent_messages), 1)
        self.assertEqual(sent_messages[0][0], 123456789)
        self.assertIn("Access Denied", sent_messages[0][1])

    def test_02_timezone_strict_ist_localization(self):
        """Verify REL-02: All schedulers and timestamps operate strictly in IST (UTC+5:30)."""
        now = telegram_bot.now_ist()
        self.assertIsNotNone(now.tzinfo)
        utc_offset = now.utcoffset()
        self.assertEqual(utc_offset, timedelta(hours=5, minutes=30), "Timezone is not IST UTC+5:30!")

        tracker_now = tracker.now_ist()
        self.assertEqual(tracker_now.utcoffset(), timedelta(hours=5, minutes=30))

    def test_03_atomic_persistence_and_daily_backups(self):
        """Verify REL-01 & CONC-01: File writes are atomic (.tmp + os.replace) and create daily backups."""
        test_file = os.path.join(self.test_dir, "test_data.json")
        test_data = {"key": "production_value", "timestamp": telegram_bot.now_ist().isoformat()}

        # Test atomic dump
        telegram_bot._atomic_json_dump(test_file, test_data, make_backup=True)

        # File must exist and be readable
        self.assertTrue(os.path.exists(test_file))
        with open(test_file, "r") as f:
            loaded = json.load(f)
        self.assertEqual(loaded["key"], "production_value")

        # Daily backup must exist in backups directory
        today_str = telegram_bot.now_ist().strftime("%Y%m%d")
        expected_backup = os.path.join(telegram_bot.BACKUPS_DIR, f"test_data.json.{today_str}.bak")
        self.assertTrue(os.path.exists(expected_backup), "Daily rolling backup was not created!")

        # Clean up test backup
        if os.path.exists(expected_backup):
            os.remove(expected_backup)

    def test_04_thread_locking_file_io(self):
        """Verify CONC-01: Reentrant lock FILE_LOCK allows safe thread locking."""
        with telegram_bot.FILE_LOCK:
            profile = telegram_bot.load_profile()
            self.assertIn("targets", profile)

    def test_05_intent_classifier_accuracies(self):
        """Verify intent classifier prevents conversational pings from logging as food."""
        self.assertEqual(telegram_bot.classify_intent("Live?"), "GREETING")
        self.assertEqual(telegram_bot.classify_intent("Are you live?"), "GREETING")
        self.assertEqual(telegram_bot.classify_intent("hi"), "GREETING")
        self.assertEqual(telegram_bot.classify_intent("status"), "STATUS")
        self.assertEqual(telegram_bot.classify_intent("Can I eat peanut butter?"), "QUESTION")
        self.assertEqual(telegram_bot.classify_intent("search optimum nutrition"), "SEARCH")
        self.assertEqual(telegram_bot.classify_intent("Incline dumbbell press 28kg 10 reps"), "WORKOUT")
        self.assertEqual(telegram_bot.classify_intent("I ate 150g low fat paneer and 2 rotis"), "MEAL")

    def test_06_tesseract_dynamic_path_resolution(self):
        """Verify DEP-01: Tesseract binary discovery resolves or falls back cleanly."""
        tess = telegram_bot.find_tesseract()
        self.assertTrue(isinstance(tess, str))
        self.assertTrue(len(tess) > 0)

        # Run OCR on a non-existent file: must not crash, must return empty string
        res = telegram_bot.run_ocr("/invalid/non_existent_image.jpg")
        self.assertEqual(res, "")

    def test_07_interactive_tracker_cli_compilation(self):
        """Verify UX-01: Tracker CLI compiles and loads targets properly."""
        profile = tracker.load_profile()
        self.assertEqual(profile["targets"]["protein_g"], 145)
        self.assertEqual(profile["targets"]["daily_calories"], 2050)

if __name__ == "__main__":
    unittest.main()
