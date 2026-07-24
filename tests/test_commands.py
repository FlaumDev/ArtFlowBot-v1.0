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


if __name__ == "__main__":
    unittest.main()
