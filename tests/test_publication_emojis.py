import importlib
import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch


os.environ.setdefault("TOKEN", "123456:TEST")
sys.modules.setdefault("psycopg2", SimpleNamespace(connect=Mock()))
admin_keyboards = importlib.import_module("keyboards.admin_keyboards")
competition_callbacks = importlib.import_module("callbacks.competition_callbacks")


def flatten_buttons(markup):
    return [button for row in markup.keyboard for button in row]


class PublicationEmojiTest(unittest.TestCase):
    def test_publication_buttons_keep_callback_data(self):
        buttons = flatten_buttons(admin_keyboards.admin_competition_publication_menu())
        by_callback = {button.callback_data: button.text for button in buttons}

        self.assertEqual(by_callback["admin_web_publish"], "🚀 Опубликовать на сайте")
        self.assertEqual(by_callback["admin_web_unpublish"], "🙈 Снять с сайта")
        self.assertEqual(by_callback["admin_web_cancel"], "❌ Отмена")

    def test_admin_competitions_menu_keeps_web_callback_data(self):
        buttons = flatten_buttons(admin_keyboards.admin_competitions_menu())
        by_callback = {button.callback_data: button.text for button in buttons}

        self.assertEqual(by_callback["admin_competition_web_data"], "📝 Изменить данные для сайта")
        self.assertEqual(by_callback["admin_competition_publication"], "👁 Публикация на сайте")

    def test_publication_status_text_has_emojis(self):
        self.assertEqual(competition_callbacks.publication_status_text(True), "🚀 опубликован")
        self.assertEqual(competition_callbacks.publication_status_text(False), "🙈 не опубликован")

    def test_publish_and_unpublish_messages_still_use_existing_database_functions(self):
        chat_id = 777
        competition_callbacks.user_data[chat_id] = {
            "admin_competition_publication": {"competition_id": 12}
        }
        web_data = {
            "id": 12,
            "name": "ArtFlow",
            "event_date": object(),
            "application_deadline": object(),
            "city": "Москва",
            "short_description": "Описание",
            "directions": "Вокал",
            "is_published": False,
        }

        with patch.object(competition_callbacks, "admin_web_schema_ready", return_value=True):
            with patch.object(competition_callbacks, "get_competition_web_data_by_id", return_value=web_data) as get_web_data:
                with patch.object(competition_callbacks, "set_competition_publication_by_id", return_value=1) as set_publication:
                    with patch.object(competition_callbacks, "send_admin_competitions_panel") as send_panel:
                        competition_callbacks.change_admin_publication(chat_id, True)

        get_web_data.assert_called_once_with(12)
        set_publication.assert_called_once_with(12, True)
        send_panel.assert_called_with(chat_id, "✅ Конкурс опубликован на сайте.")

        competition_callbacks.user_data[chat_id] = {
            "admin_competition_publication": {"competition_id": 12}
        }

        with patch.object(competition_callbacks, "admin_web_schema_ready", return_value=True):
            with patch.object(competition_callbacks, "get_competition_web_data_by_id", return_value=web_data):
                with patch.object(competition_callbacks, "set_competition_publication_by_id", return_value=1) as set_publication:
                    with patch.object(competition_callbacks, "send_admin_competitions_panel") as send_panel:
                        competition_callbacks.change_admin_publication(chat_id, False)

        set_publication.assert_called_once_with(12, False)
        send_panel.assert_called_with(chat_id, "🙈 Конкурс снят с сайта.")
        competition_callbacks.user_data.pop(chat_id, None)


if __name__ == "__main__":
    unittest.main()
