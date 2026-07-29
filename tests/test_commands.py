import importlib
import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch


os.environ.setdefault("TOKEN", "123456:TEST")
sys.modules.setdefault("psycopg2", SimpleNamespace(connect=Mock()))
commands = importlib.import_module("commands")


def message(text="/start"):
    return SimpleNamespace(
        text=text,
        chat=SimpleNamespace(id=100),
        from_user=SimpleNamespace(id=100, username="artist", first_name="Artist")
    )


class CommandHandlersTest(unittest.TestCase):
    def test_start_opens_main_menu_without_deep_link(self):
        with patch.object(commands, "save_user_safely") as save_user:
            with patch.object(commands, "parse_competition_deep_link", return_value=None):
                with patch.object(commands, "send_main_menu") as send_main_menu:
                    commands.start(message("/start"))

        save_user.assert_called_once()
        send_main_menu.assert_called_once()

    def test_start_deep_link_still_opens_competition(self):
        with patch.object(commands, "save_user_safely"):
            with patch.object(commands, "parse_competition_deep_link", return_value=7):
                with patch.object(commands, "open_competition_from_deep_link") as open_competition:
                    commands.start(message("/start competition_7"))

        open_competition.assert_called_once()
        self.assertEqual(open_competition.call_args.args[1], 7)

    def test_competitions_command_uses_existing_competition_menu(self):
        with patch.object(commands, "save_user_safely"):
            with patch.object(commands, "competition_menu", return_value="competition-markup"):
                with patch.object(commands.bot, "send_message") as send_message:
                    commands.competitions(message("/competitions"))

        send_message.assert_called_once_with(
            100,
            commands.COMPETITIONS_TEXT,
            reply_markup="competition-markup"
        )

    def test_faq_command_uses_existing_faq_menu(self):
        with patch.object(commands, "save_user_safely"):
            with patch.object(commands, "faq_menu", return_value="faq-markup"):
                with patch.object(commands.bot, "send_message") as send_message:
                    commands.faq(message("/faq"))

        send_message.assert_called_once_with(
            100,
            commands.FAQ_TEXT,
            reply_markup="faq-markup"
        )

    def test_contact_command_uses_existing_contact_menu(self):
        with patch.object(commands, "save_user_safely"):
            with patch.object(commands, "contact_menu", return_value="contact-markup"):
                with patch.object(commands.bot, "send_message") as send_message:
                    commands.contact(message("/contact"))

        send_message.assert_called_once_with(
            100,
            commands.CONTACT_TEXT,
            reply_markup="contact-markup"
        )

    def test_help_command_shows_public_commands(self):
        with patch.object(commands, "save_user_safely"):
            with patch.object(commands.bot, "send_message") as send_message:
                commands.help_command(message("/help"))

        send_message.assert_called_once_with(100, commands.HELP_TEXT)
        self.assertIn("/competitions", commands.HELP_TEXT)
        self.assertNotIn("/admin", commands.HELP_TEXT)


    def test_help_command_does_not_show_test_notifications(self):
        self.assertNotIn("/test_notifications", commands.HELP_TEXT)

    def test_welcome_text_contains_izo(self):
        self.assertIn("• ИЗО", commands.WELCOME_TEXT)

    def test_test_notifications_is_available_for_admin(self):
        result = {
            "telegram": {"configured": True, "sent": True, "error_type": None, "error_message": None},
            "email": {"configured": True, "sent": True, "error_type": None, "error_message": None},
        }
        config = {
            "telegram": {"configured": True, "missing": [], "errors": []},
            "email": {"configured": True, "missing": [], "errors": []},
        }

        with patch.object(commands, "is_admin", return_value=True) as is_admin:
            with patch.object(commands, "save_user_safely") as save_user:
                with patch.object(commands, "validate_application_notification_config", return_value=config):
                    with patch.object(commands, "send_test_notifications", return_value=result) as send_test:
                        with patch.object(commands.bot, "send_message") as send_message:
                            commands.test_notifications(message("/test_notifications"))

        is_admin.assert_called_once_with(100)
        save_user.assert_not_called()
        send_test.assert_called_once_with(commands.bot)
        self.assertIn("Telegram: ✅ отправлено", send_message.call_args.args[1])
        self.assertIn("Email: ✅ отправлено", send_message.call_args.args[1])

    def test_test_notifications_is_denied_for_regular_user(self):
        with patch.object(commands, "is_admin", return_value=False):
            with patch.object(commands, "send_test_notifications") as send_test:
                with patch.object(commands.bot, "send_message") as send_message:
                    commands.test_notifications(message("/test_notifications"))

        send_test.assert_not_called()
        self.assertIn("нет доступа", send_message.call_args.args[1])

    def test_test_notifications_shows_missing_variable_names_only(self):
        result = {
            "telegram": {"configured": False, "sent": False, "error_type": "ConfigurationError", "error_message": "missing APPLICATION_RECIPIENT_CHAT_ID"},
            "email": {"configured": False, "sent": False, "error_type": "ConfigurationError", "error_message": "missing RESEND_API_KEY"},
        }
        config = {
            "telegram": {"configured": False, "missing": ["APPLICATION_RECIPIENT_CHAT_ID"], "errors": []},
            "email": {"configured": False, "missing": ["RESEND_API_KEY"], "errors": []},
        }

        with patch.object(commands, "is_admin", return_value=True):
            with patch.object(commands, "validate_application_notification_config", return_value=config):
                with patch.object(commands, "send_test_notifications", return_value=result):
                    with patch.object(commands.bot, "send_message") as send_message:
                        commands.test_notifications(message("/test_notifications"))

        text = send_message.call_args.args[1]
        self.assertIn("APPLICATION_RECIPIENT_CHAT_ID", text)
        self.assertIn("RESEND_API_KEY", text)
        self.assertNotIn("smtp-secret", text)
    def test_test_notifications_shows_safe_config_errors(self):
        result = {
            "telegram": {"configured": False, "sent": False, "error_type": "ConfigurationError", "error_message": "errors APPLICATION_RECIPIENT_CHAT_ID must be an integer"},
            "email": {"configured": False, "sent": False, "error_type": "ConfigurationError", "error_message": "errors RESEND_FROM_EMAIL must be an email address"},
        }
        config = {
            "telegram": {"configured": False, "missing": [], "errors": ["APPLICATION_RECIPIENT_CHAT_ID must be an integer"]},
            "email": {"configured": False, "missing": [], "errors": ["RESEND_FROM_EMAIL must be an email address"]},
        }

        with patch.object(commands, "is_admin", return_value=True):
            with patch.object(commands, "validate_application_notification_config", return_value=config):
                with patch.object(commands, "send_test_notifications", return_value=result):
                    with patch.object(commands.bot, "send_message") as send_message:
                        commands.test_notifications(message("/test_notifications"))

        text = send_message.call_args.args[1]
        self.assertIn("APPLICATION_RECIPIENT_CHAT_ID must be an integer", text)
        self.assertIn("RESEND_FROM_EMAIL must be an email address", text)
        self.assertNotIn("smtp-secret", text)

    def test_test_notifications_shows_resend_error_safely(self):
        result = {
            "telegram": {"configured": True, "sent": True, "error_type": None, "error_message": None},
            "email": {"configured": True, "sent": False, "error_type": "ResendAuthenticationError", "error_message": "re_secret_123456", "provider": "resend", "provider_message_id": None},
        }
        config = {
            "telegram": {"configured": True, "missing": [], "errors": []},
            "email": {"configured": True, "missing": [], "errors": []},
        }

        with patch.object(commands, "is_admin", return_value=True):
            with patch.object(commands, "validate_application_notification_config", return_value=config):
                with patch.object(commands, "send_test_notifications", return_value=result):
                    with patch.object(commands.bot, "send_message") as send_message:
                        commands.test_notifications(message("/test_notifications"))

        text = send_message.call_args.args[1]
        self.assertIn("Email: ❌ ResendAuthenticationError", text)
        self.assertNotIn("re_secret_123456", text)
if __name__ == "__main__":
    unittest.main()
