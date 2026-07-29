import importlib
import os
import sys
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch


os.environ.setdefault("TOKEN", "123456:TEST")
sys.modules.setdefault("psycopg2", SimpleNamespace(connect=Mock()))
competition_callbacks = importlib.import_module("callbacks.competition_callbacks")
admin_keyboards = importlib.import_module("keyboards.admin_keyboards")


def callback(data="admin_competition_participants_1_1"):
    return SimpleNamespace(
        id="callback-id",
        data=data,
        message=SimpleNamespace(
            chat=SimpleNamespace(id=100),
            message_id=55,
            text=""
        )
    )


def request_data(**overrides):
    data = {
        "id": 123,
        "telegram_id": 777,
        "city": "Москва",
        "name_team": "Ансамбль <Радуга>",
        "number_name": "Весенний танец",
        "number_genre": "Хореография",
        "number_of_participants": 12,
        "age": "Средняя 10-14",
        "performance_time": 4,
        "SFP_supervisor": "Елена Иванова",
        "WhatsApp_number": "+79990000000",
        "email": "team@example.com",
        "status": "На рассмотрении",
        "create_at": datetime(2026, 7, 26, 12, 30),
        "music_file_id": "file-id",
        "music_file_name": "music.mp3",
        "competition_id": 5,
        "competition_name": "ArtFlow",
        "username": "leader",
        "first_name": "Елена",
        "participants": ["Иван <script>", "Мария"],
    }
    data.update(overrides)
    return data


def button_callbacks(markup):
    return [button.callback_data for row in markup.keyboard for button in row]


class AdminCompetitionParticipantsTest(unittest.TestCase):
    def test_participants_button_is_visible_in_admin_competitions_menu(self):
        buttons = {
            button.callback_data: button.text
            for row in admin_keyboards.admin_competitions_menu().keyboard
            for button in row
        }

        self.assertEqual(buttons["admin_competition_participants"], "👥 Участники")

    def test_regular_user_cannot_open_fake_participants_callback(self):
        with patch.object(competition_callbacks.bot, "answer_callback_query"):
            with patch.object(competition_callbacks, "admin_check", return_value=False) as admin_check:
                with patch.object(competition_callbacks, "show_admin_competition_participants") as show_list:
                    competition_callbacks.competition_callback_message(
                        callback("admin_competition_participants_5_1")
                    )

        admin_check.assert_called()
        show_list.assert_not_called()

    def test_list_loads_only_selected_competition_requests(self):
        competition = {"title": "ArtFlow"}

        with patch.object(competition_callbacks, "get_competition_by_id", return_value=competition):
            with patch.object(competition_callbacks, "get_competition_requests_count", return_value=2):
                with patch.object(competition_callbacks, "get_competition_requests", return_value=[request_data(id=1), request_data(id=2)]) as get_requests:
                    with patch.object(competition_callbacks.bot, "edit_message_text") as edit_message:
                        competition_callbacks.show_admin_competition_participants(100, 55, 5, 1)

        get_requests.assert_called_once_with(5, competition_callbacks.ADMIN_COMPETITION_REQUESTS_PER_PAGE, 0)
        self.assertIn("📋 Всего заявок: 2", edit_message.call_args.args[0])

    def test_empty_competition_shows_empty_state(self):
        competition = {"title": "ArtFlow"}

        with patch.object(competition_callbacks, "get_competition_by_id", return_value=competition):
            with patch.object(competition_callbacks, "get_competition_requests_count", return_value=0):
                with patch.object(competition_callbacks.bot, "edit_message_text") as edit_message:
                    competition_callbacks.show_admin_competition_participants(100, 55, 5, 1)

        self.assertIn("👥 Участников пока нет", edit_message.call_args.args[0])
        self.assertIn("На этот конкурс ещё не подано ни одной заявки.", edit_message.call_args.args[0])

    def test_pagination_calculates_offset(self):
        competition = {"title": "ArtFlow"}

        with patch.object(competition_callbacks, "get_competition_by_id", return_value=competition):
            with patch.object(competition_callbacks, "get_competition_requests_count", return_value=25):
                with patch.object(competition_callbacks, "get_competition_requests", return_value=[]) as get_requests:
                    with patch.object(competition_callbacks.bot, "edit_message_text"):
                        competition_callbacks.show_admin_competition_participants(100, 55, 5, 3)

        get_requests.assert_called_once_with(5, competition_callbacks.ADMIN_COMPETITION_REQUESTS_PER_PAGE, 16)

    def test_first_page_does_not_go_below_one(self):
        markup = competition_callbacks.admin_competition_participants_menu(
            5,
            [request_data(id=1)],
            1,
            3
        )

        self.assertIn("none", button_callbacks(markup))
        self.assertIn("admin_competition_participants_5_2", button_callbacks(markup))

    def test_last_page_does_not_open_missing_page(self):
        markup = competition_callbacks.admin_competition_participants_menu(
            5,
            [request_data(id=1)],
            3,
            3
        )

        self.assertIn("admin_competition_participants_5_2", button_callbacks(markup))
        self.assertEqual(button_callbacks(markup).count("none"), 2)

    def test_application_card_opens_specific_request(self):
        data = request_data()

        with patch.object(competition_callbacks, "get_competition_request_by_id", return_value=data) as get_request:
            with patch.object(competition_callbacks.bot, "edit_message_text") as edit_message:
                competition_callbacks.show_admin_competition_application(100, 55, 5, 123, 2)

        get_request.assert_called_once_with(5, 123)
        self.assertIn("🆔 Заявка: №123", edit_message.call_args.args[0])
        self.assertIn("⬅️ К участникам", edit_message.call_args.kwargs["reply_markup"].keyboard[0][0].text)

    def test_empty_optional_fields_do_not_break_card(self):
        text = competition_callbacks.admin_competition_application_text(
            request_data(
                name_team=None,
                WhatsApp_number=None,
                email=None,
                username=None,
                music_file_name=None,
                participants=[]
            )
        )

        self.assertIn("👥 Коллектив: Не указано", text)
        self.assertIn("👤 Telegram: Не указано", text)
        self.assertIn("🎧 Музыкальный файл: Не используется", text)
        self.assertIn("👥 Участники:\nНе указано", text)

    def test_html_in_participant_name_is_escaped(self):
        text = competition_callbacks.admin_competition_application_text(request_data())

        self.assertIn("Ансамбль &lt;Радуга&gt;", text)
        self.assertIn("Иван &lt;script&gt;", text)
        self.assertNotIn("Иван <script>", text)

    def test_missing_application_is_handled(self):
        with patch.object(competition_callbacks, "get_competition_request_by_id", return_value=None):
            with patch.object(competition_callbacks.bot, "edit_message_text") as edit_message:
                competition_callbacks.show_admin_competition_application(100, 55, 5, 999, 1)

        self.assertIn("⚠️ Заявка не найдена или была удалена.", edit_message.call_args.args[0])

    def test_existing_admin_competitions_callback_still_opens_panel(self):
        with patch.object(competition_callbacks.bot, "answer_callback_query"):
            with patch.object(competition_callbacks, "admin_check", return_value=True):
                with patch.object(competition_callbacks, "admin_competitions_text", return_value="competitions"):
                    with patch.object(competition_callbacks.bot, "edit_message_text") as edit_message:
                        competition_callbacks.competition_callback_message(
                            callback("admin_competitions")
                        )

        self.assertEqual(edit_message.call_args.args[0], "competitions")


if __name__ == "__main__":
    unittest.main()
