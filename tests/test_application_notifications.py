import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch

import application_notifications as notifications


def sample_registration_data(**overrides):
    data = {
        "competition_name": "ArtFlow <Final>",
        "city": "Москва",
        "team": "Коллектив & Co",
        "name": "Танец <script>",
        "genre": "Вокал",
        "participant_count": 2,
        "participants": ["Анна <b>", "Иван"],
        "age": "Средняя 10-14",
        "performance_time": 3,
        "supervisor": "Мария & Партнеры",
        "WhatsApp": "+79990000000",
        "email": "artist@example.com",
        "music_file_name": "track.mp3",
        "create_at": datetime(2026, 7, 24, 15, 30),
    }
    data.update(overrides)
    return data


def sample_message(username="artist"):
    return SimpleNamespace(
        chat=SimpleNamespace(id=12345),
        from_user=SimpleNamespace(username=username)
    )


class FakeBot:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail
        self.messages = []

    def send_message(self, chat_id, text, parse_mode=None):
        if self.should_fail:
            raise RuntimeError("telegram failed")

        self.messages.append({
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
        })


class FakeSMTP:
    instances = []

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.started_tls = False
        self.login_args = None
        self.sent_message = None
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def starttls(self, context=None):
        self.started_tls = True

    def login(self, user, password):
        self.login_args = (user, password)

    def send_message(self, message):
        self.sent_message = message


class ApplicationNotificationsTest(unittest.TestCase):
    def setUp(self):
        FakeSMTP.instances = []

    def build_notification(self, **overrides):
        return notifications.build_application_notification_data(
            123,
            sample_registration_data(**overrides),
            sample_message()
        )

    def test_telegram_message_uses_real_data_and_escapes_html(self):
        notification = self.build_notification()

        text = notifications.format_application_telegram_message(notification)

        self.assertIn("🎉 Новая заявка ArtFlow", text)
        self.assertIn("🆔 Заявка: №123", text)
        self.assertIn("🏆 Конкурс: ArtFlow &lt;Final&gt;", text)
        self.assertIn("🎵 Номер: Танец &lt;script&gt;", text)
        self.assertIn("👤 Telegram: @artist", text)
        self.assertIn("🕒 Дата подачи: 24.07.2026 15:30", text)
        self.assertNotIn("Танец <script>", text)

    def test_email_format_uses_application_id_and_competition_name(self):
        notification = self.build_notification()

        subject, body = notifications.format_application_email(notification)

        self.assertEqual(subject, "Новая заявка ArtFlow №123 — ArtFlow <Final>")
        self.assertIn("Заявка: №123", body)
        self.assertIn("Конкурс: ArtFlow <Final>", body)
        self.assertIn("Коллектив: Коллектив & Co", body)
        self.assertIn("Дата подачи: 24.07.2026 15:30", body)

    def test_send_telegram_success(self):
        bot = FakeBot()
        notification = self.build_notification()

        with patch.dict("os.environ", {"APPLICATION_RECIPIENT_CHAT_ID": "555"}, clear=True):
            result = notifications.send_application_telegram_notification(bot, notification)

        self.assertTrue(result)
        self.assertEqual(bot.messages[0]["chat_id"], "555")
        self.assertEqual(bot.messages[0]["parse_mode"], "HTML")
        self.assertIn("№123", bot.messages[0]["text"])

    def test_telegram_error_does_not_block_email(self):
        with patch.object(notifications, "send_application_telegram_notification", side_effect=RuntimeError("boom")) as telegram:
            with patch.object(notifications, "send_application_email_notification", return_value=True) as email:
                notifications.send_application_notifications(
                    Mock(),
                    sample_message(),
                    123,
                    sample_registration_data()
                )

        telegram.assert_called_once()
        email.assert_called_once()

    def test_send_email_success_with_starttls(self):
        notification = self.build_notification()
        env = {
            "APPLICATION_RECIPIENT_EMAIL": "organizer@example.com",
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "smtp-user",
            "SMTP_PASSWORD": "smtp-password",
            "SMTP_FROM_EMAIL": "bot@example.com",
            "SMTP_USE_SSL": "false",
            "SMTP_USE_STARTTLS": "true",
        }

        with patch.dict("os.environ", env, clear=True):
            with patch.object(notifications.smtplib, "SMTP", FakeSMTP):
                with patch.object(notifications.ssl, "create_default_context", return_value=object()):
                    result = notifications.send_application_email_notification(notification)

        self.assertTrue(result)
        self.assertEqual(FakeSMTP.instances[0].host, "smtp.example.com")
        self.assertEqual(FakeSMTP.instances[0].port, 587)
        self.assertTrue(FakeSMTP.instances[0].started_tls)
        self.assertEqual(FakeSMTP.instances[0].login_args, ("smtp-user", "smtp-password"))
        self.assertEqual(FakeSMTP.instances[0].sent_message["To"], "organizer@example.com")

    def test_smtp_error_does_not_block_telegram(self):
        with patch.object(notifications, "send_application_telegram_notification", return_value=True) as telegram:
            with patch.object(notifications, "send_application_email_notification", side_effect=RuntimeError("smtp")) as email:
                notifications.send_application_notifications(
                    Mock(),
                    sample_message(),
                    123,
                    sample_registration_data()
                )

        telegram.assert_called_once()
        email.assert_called_once()

    def test_empty_optional_fields_do_not_break_formatting(self):
        notification = notifications.build_application_notification_data(
            124,
            sample_registration_data(participants=[], music_file_name=None),
            sample_message(username=None)
        )

        telegram_text = notifications.format_application_telegram_message(notification)
        subject, body = notifications.format_application_email(notification)

        self.assertIn("👤 Telegram: не указан", telegram_text)
        self.assertIn("🎧 Музыкальный файл: Не используется", telegram_text)
        self.assertIn("№124", subject)
        self.assertIn("Музыкальный файл: Не используется", body)


if __name__ == "__main__":
    unittest.main()
