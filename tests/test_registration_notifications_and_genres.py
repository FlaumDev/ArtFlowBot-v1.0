import importlib
import os
import sys
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch


os.environ.setdefault("TOKEN", "123456:TEST")
sys.modules.setdefault("psycopg2", SimpleNamespace(connect=Mock()))
registration_callbacks = importlib.import_module("callbacks.registration_callbacks")
user_keyboards = importlib.import_module("keyboards.user_keyboards")


def callback(data, chat_id=100):
    return SimpleNamespace(
        id="callback-id",
        data=data,
        from_user=SimpleNamespace(id=777, username="real_user", first_name="Real"),
        message=SimpleNamespace(
            chat=SimpleNamespace(id=chat_id),
            message_id=55,
            text=""
        )
    )


def registration_data(genre="ИЗО"):
    return {
        "city": "Москва",
        "team": "Команда",
        "name": "Номер",
        "genre": genre,
        "participant_count": 2,
        "age": "Средняя 10-14",
        "performance_time": 3,
        "supervisor": "Руководитель",
        "WhatsApp": "+79990000000",
        "email": "artist@example.com",
        "music_file_id": None,
        "music_file_name": "Не используется",
        "selected_competition": "competition_5",
        "competition_name": "ArtFlow",
        "participants": ["Иван", "Мария"],
    }


def flatten_buttons(markup):
    return [button for row in markup.keyboard for button in row]


class FakeCursor:
    def __init__(self, events):
        self.events = events
        self.queries = []

    def execute(self, query, params=None):
        self.queries.append((query, params))
        if "INSERT INTO ArtFlow_bid" in query:
            self.events.append("insert_application")
        elif "INSERT INTO participants" in query:
            self.events.append("insert_participant")

    def fetchone(self):
        return (321, datetime(2026, 7, 29, 12, 0))

    def close(self):
        self.events.append("cursor_close")


class FakeConnection:
    def __init__(self, events):
        self.events = events
        self.cursor_obj = FakeCursor(events)

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.events.append("commit")

    def close(self):
        self.events.append("connection_close")


class RegistrationNotificationsAndGenresTest(unittest.TestCase):
    def tearDown(self):
        registration_callbacks.user_data.clear()

    def test_izo_button_is_present(self):
        buttons = {
            button.callback_data: button.text
            for button in flatten_buttons(user_keyboards.genre_menu())
        }

        self.assertEqual(buttons["genre_4"], "🎨 ИЗО")

    def test_genre_4_saves_izo(self):
        chat_id = 100
        registration_callbacks.user_data[chat_id] = {}

        with patch.object(registration_callbacks.bot, "answer_callback_query"):
            with patch.object(registration_callbacks.bot, "send_message", return_value=SimpleNamespace()):
                with patch.object(registration_callbacks.bot, "register_next_step_handler"):
                    registration_callbacks.registration_callback_message(callback("genre_4", chat_id))

        self.assertEqual(registration_callbacks.user_data[chat_id]["genre"], "ИЗО")

    def test_old_genres_still_work(self):
        expected = {
            "genre_1": "Хореография",
            "genre_2": "Вокал",
            "genre_3": "Инструментальный",
        }

        for genre_callback, genre_name in expected.items():
            with self.subTest(genre_callback=genre_callback):
                chat_id = 100
                registration_callbacks.user_data[chat_id] = {}

                with patch.object(registration_callbacks.bot, "answer_callback_query"):
                    with patch.object(registration_callbacks.bot, "send_message", return_value=SimpleNamespace()):
                        with patch.object(registration_callbacks.bot, "register_next_step_handler"):
                            registration_callbacks.registration_callback_message(callback(genre_callback, chat_id))

                self.assertEqual(registration_callbacks.user_data[chat_id]["genre"], genre_name)
                registration_callbacks.user_data.clear()

    def test_notification_is_called_after_commit_once_and_uses_callback_from_user(self):
        chat_id = 100
        events = []
        fake_connection = FakeConnection(events)
        cb = callback("confirm_reg", chat_id)
        data = registration_data()
        registration_callbacks.user_data[chat_id] = data

        with patch.object(registration_callbacks.bot, "answer_callback_query"):
            with patch("database.get_connection", return_value=fake_connection):
                with patch.object(registration_callbacks, "send_application_notifications", side_effect=lambda *args: events.append("notify")) as notify:
                    with patch.object(registration_callbacks, "end_registration", side_effect=lambda message: events.append("end")):
                        registration_callbacks.registration_callback_message(cb)

        self.assertLess(events.index("commit"), events.index("notify"))
        self.assertLess(events.index("connection_close"), events.index("notify"))
        notify.assert_called_once_with(
            registration_callbacks.bot,
            cb.from_user,
            chat_id,
            321,
            data
        )

    def test_izo_value_is_written_to_number_genre_position(self):
        chat_id = 100
        events = []
        fake_connection = FakeConnection(events)
        registration_callbacks.user_data[chat_id] = registration_data(genre="ИЗО")

        with patch.object(registration_callbacks.bot, "answer_callback_query"):
            with patch("database.get_connection", return_value=fake_connection):
                with patch.object(registration_callbacks, "send_application_notifications"):
                    with patch.object(registration_callbacks, "end_registration"):
                        registration_callbacks.registration_callback_message(callback("confirm_reg", chat_id))

        application_insert = fake_connection.cursor_obj.queries[0]
        params = application_insert[1]
        self.assertIn("number_genre", application_insert[0])
        self.assertEqual(params[4], "ИЗО")


if __name__ == "__main__":
    unittest.main()
