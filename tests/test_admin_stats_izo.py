import importlib
import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch


os.environ.setdefault("TOKEN", "123456:TEST")
sys.modules.setdefault("psycopg2", SimpleNamespace(connect=Mock()))
admin_callbacks = importlib.import_module("callbacks.admin_callbacks")


def callback(data="admin_stats"):
    return SimpleNamespace(
        id="callback-id",
        data=data,
        message=SimpleNamespace(
            chat=SimpleNamespace(id=100),
            message_id=55,
            text=""
        )
    )


def request_with_genre(genre):
    request = [None] * 18
    request[5] = genre
    request[12] = "На рассмотрении"
    return request


class AdminStatsIzoTest(unittest.TestCase):
    def test_admin_stats_counts_izo_genre(self):
        with patch.object(admin_callbacks.bot, "answer_callback_query"):
            with patch.object(admin_callbacks, "admin_check", return_value=True):
                with patch.object(admin_callbacks, "all_count", return_value=1):
                    with patch.object(admin_callbacks, "all_participants", return_value=1):
                        with patch.object(admin_callbacks, "requests_status", return_value=[request_with_genre("ИЗО")]):
                            with patch.object(admin_callbacks, "request_time", return_value=1):
                                with patch.object(admin_callbacks.bot, "edit_message_text") as edit_message:
                                    admin_callbacks.admin_callback_message(callback())

        self.assertIn("• ИЗО — 1", edit_message.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
