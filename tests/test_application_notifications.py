import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch

import application_notifications as notifications


def valid_env(**overrides):
    env = {
        "APPLICATION_RECIPIENT_CHAT_ID": "555",
        "APPLICATION_RECIPIENT_EMAIL": "organizer@example.com",
        "RESEND_API_KEY": "re_secret_123456",
        "RESEND_FROM_EMAIL": "ArtFlow <noreply@artflowfest.com>",
        "RESEND_REPLY_TO_EMAIL": "reply@example.com",
        "TOKEN": "123456:ABCDEF",
    }
    env.update(overrides)
    return env


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


def sample_user(username="artist"):
    return SimpleNamespace(id=98765, username=username, first_name="Artist")


class FakeBot:
    def __init__(self, should_fail=False, error=None):
        self.should_fail = should_fail
        self.error = error or RuntimeError("telegram failed")
        self.messages = []

    def send_message(self, chat_id, text, parse_mode=None):
        if self.should_fail:
            raise self.error

        self.messages.append({
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
        })


class FakeEmails:
    sent = []
    error = None
    response = {"id": "email-id"}

    @classmethod
    def send(cls, params):
        if cls.error:
            raise cls.error

        cls.sent.append(params)
        return cls.response


class FakeResend:
    api_key = None
    Emails = FakeEmails


class ApplicationNotificationsTest(unittest.TestCase):
    def setUp(self):
        FakeResend.api_key = None
        FakeEmails.sent = []
        FakeEmails.error = None
        FakeEmails.response = {"id": "email-id"}

    def build_notification(self, **overrides):
        return notifications.build_application_notification_data(
            123,
            sample_registration_data(**overrides),
            sample_user(),
            1000
        )

    def test_telegram_message_uses_real_data_and_escapes_html(self):
        notification = self.build_notification()

        text = notifications.format_application_telegram_message(notification)

        self.assertIn("🎉 Новая заявка ArtFlow", text)
        self.assertIn("🆔 Заявка: №123", text)
        self.assertIn("🏆 Конкурс: ArtFlow &lt;Final&gt;", text)
        self.assertIn("🎵 Номер: Танец &lt;script&gt;", text)
        self.assertIn("👤 Telegram: @artist", text)
        self.assertIn("🆔 Telegram ID: 98765", text)
        self.assertIn("💬 Chat ID: 1000", text)
        self.assertIn("🕒 Дата подачи: 24.07.2026 15:30", text)
        self.assertNotIn("Танец <script>", text)

    def test_email_format_returns_subject_text_and_html(self):
        notification = self.build_notification()

        subject, text_body, html_body = notifications.format_application_email(notification)

        self.assertEqual(subject, "Новая заявка ArtFlow №123 — ArtFlow <Final>")
        self.assertIn("Заявка: №123", text_body)
        self.assertIn("Конкурс: ArtFlow <Final>", text_body)
        self.assertIn("Коллектив: Коллектив & Co", text_body)
        self.assertIn("Telegram ID: 98765", text_body)
        self.assertIn("Chat ID: 1000", text_body)
        self.assertIn("Дата подачи: 24.07.2026 15:30", text_body)
        self.assertIn("<h1>Новая заявка ArtFlow</h1>", html_body)
        self.assertIn("ArtFlow &lt;Final&gt;", html_body)
        self.assertIn("Коллектив &amp; Co", html_body)

    def test_email_html_escapes_unsafe_user_values(self):
        notification = self.build_notification(name="</script><b>unsafe</b>")

        _, _, html_body = notifications.format_application_email(notification)

        self.assertIn("&lt;/script&gt;&lt;b&gt;unsafe&lt;/b&gt;", html_body)
        self.assertNotIn("</script><b>unsafe</b>", html_body)

    def test_email_subject_crlf_is_sanitized(self):
        notification = self.build_notification(competition_name="ArtFlow\r\nBcc: bad@example.com")

        subject, _, _ = notifications.format_application_email(notification)

        self.assertNotIn("\r", subject)
        self.assertNotIn("\n", subject)
        self.assertIn("Bcc: bad@example.com", subject)

    def test_telegram_config_enabled_with_valid_chat_id(self):
        with patch.dict("os.environ", valid_env(), clear=True):
            config = notifications.validate_application_notification_config()

        self.assertTrue(config["telegram"]["configured"])
        self.assertEqual(config["telegram"]["missing"], [])
        self.assertEqual(config["telegram"]["errors"], [])

    def test_empty_chat_id_is_detected(self):
        with patch.dict("os.environ", valid_env(APPLICATION_RECIPIENT_CHAT_ID=""), clear=True):
            config = notifications.validate_application_notification_config()

        self.assertFalse(config["telegram"]["configured"])
        self.assertIn("APPLICATION_RECIPIENT_CHAT_ID", config["telegram"]["missing"])

    def test_invalid_chat_id_is_detected(self):
        with patch.dict("os.environ", valid_env(APPLICATION_RECIPIENT_CHAT_ID="abc"), clear=True):
            config = notifications.validate_application_notification_config()

        self.assertFalse(config["telegram"]["configured"])
        self.assertIn("APPLICATION_RECIPIENT_CHAT_ID must be an integer", config["telegram"]["errors"])

    def test_resend_config_is_valid_with_from_display_name(self):
        with patch.dict("os.environ", valid_env(), clear=True):
            config = notifications.validate_application_notification_config()

        self.assertTrue(config["email"]["configured"])
        self.assertEqual(config["email"]["missing"], [])
        self.assertEqual(config["email"]["errors"], [])

    def test_empty_resend_api_key_is_detected(self):
        with patch.dict("os.environ", valid_env(RESEND_API_KEY=""), clear=True):
            config = notifications.validate_application_notification_config()

        self.assertFalse(config["email"]["configured"])
        self.assertIn("RESEND_API_KEY", config["email"]["missing"])

    def test_empty_resend_from_email_is_detected(self):
        with patch.dict("os.environ", valid_env(RESEND_FROM_EMAIL=""), clear=True):
            config = notifications.validate_application_notification_config()

        self.assertFalse(config["email"]["configured"])
        self.assertIn("RESEND_FROM_EMAIL", config["email"]["missing"])

    def test_invalid_email_is_detected(self):
        with patch.dict("os.environ", valid_env(APPLICATION_RECIPIENT_EMAIL="not-an-email"), clear=True):
            config = notifications.validate_application_notification_config()

        self.assertFalse(config["email"]["configured"])
        self.assertIn("APPLICATION_RECIPIENT_EMAIL must be an email address", config["email"]["errors"])

    def test_invalid_resend_reply_to_email_is_detected(self):
        with patch.dict("os.environ", valid_env(RESEND_REPLY_TO_EMAIL="not-an-email"), clear=True):
            config = notifications.validate_application_notification_config()

        self.assertFalse(config["email"]["configured"])
        self.assertIn("RESEND_REPLY_TO_EMAIL must be an email address", config["email"]["errors"])

    def test_crlf_in_from_is_rejected(self):
        with patch.dict("os.environ", valid_env(RESEND_FROM_EMAIL="ArtFlow\r\nBcc: bad@example.com"), clear=True):
            config = notifications.validate_application_notification_config()

        self.assertFalse(config["email"]["configured"])
        self.assertIn("RESEND_FROM_EMAIL must not contain CR or LF", config["email"]["errors"])

    def test_crlf_in_reply_to_is_rejected(self):
        with patch.dict("os.environ", valid_env(RESEND_REPLY_TO_EMAIL="reply@example.com\nBcc: bad@example.com"), clear=True):
            config = notifications.validate_application_notification_config()

        self.assertFalse(config["email"]["configured"])
        self.assertIn("RESEND_REPLY_TO_EMAIL must not contain CR or LF", config["email"]["errors"])

    def test_crlf_in_recipient_is_rejected(self):
        with patch.dict("os.environ", valid_env(APPLICATION_RECIPIENT_EMAIL="organizer@example.com\r\nBcc: bad@example.com"), clear=True):
            config = notifications.validate_application_notification_config()

        self.assertFalse(config["email"]["configured"])
        self.assertIn("APPLICATION_RECIPIENT_EMAIL must not contain CR or LF", config["email"]["errors"])

    def test_recipient_tail_after_email_is_rejected(self):
        with patch.dict("os.environ", valid_env(APPLICATION_RECIPIENT_EMAIL="organizer@example.com extra"), clear=True):
            config = notifications.validate_application_notification_config()

        self.assertFalse(config["email"]["configured"])
        self.assertIn("APPLICATION_RECIPIENT_EMAIL must be an email address", config["email"]["errors"])

    def test_startup_logs_do_not_include_api_key(self):
        with patch.dict("os.environ", valid_env(), clear=True):
            lines = notifications.get_application_notification_startup_lines()

        output = "\n".join(lines)
        self.assertIn("Email: enabled, provider=Resend HTTPS", output)
        self.assertNotIn("re_secret_123456", output)
        self.assertNotIn("api_key=", output)
        self.assertNotIn("re_", output)

    def test_chat_id_is_sent_to_telegram_as_int(self):
        bot = FakeBot()
        notification = self.build_notification()

        with patch.dict("os.environ", valid_env(APPLICATION_RECIPIENT_CHAT_ID="-100555"), clear=True):
            result = notifications.send_application_telegram_notification(bot, notification)

        self.assertTrue(result["sent"])
        self.assertIsInstance(bot.messages[0]["chat_id"], int)
        self.assertEqual(bot.messages[0]["chat_id"], -100555)
        self.assertEqual(bot.messages[0]["parse_mode"], "HTML")

    def test_telegram_success_returns_sent_true(self):
        bot = FakeBot()

        with patch.dict("os.environ", valid_env(), clear=True):
            result = notifications.send_application_telegram_notification(bot, self.build_notification())

        self.assertEqual(result, {
            "configured": True,
            "sent": True,
            "error_type": None,
            "error_message": None
        })

    def test_telegram_error_returns_sent_false(self):
        bot = FakeBot(should_fail=True, error=RuntimeError("chat not found"))

        with patch.dict("os.environ", valid_env(), clear=True):
            result = notifications.send_application_telegram_notification(bot, self.build_notification())

        self.assertTrue(result["configured"])
        self.assertFalse(result["sent"])
        self.assertEqual(result["error_type"], "ChatNotFound")

    def test_telegram_error_does_not_block_email(self):
        with patch.object(notifications, "send_application_telegram_notification", return_value={"configured": True, "sent": False, "error_type": "ChatNotFound", "error_message": "Chat not found"}) as telegram:
            with patch.object(notifications, "send_application_email_notification", return_value={"configured": True, "sent": True, "error_type": None, "error_message": None, "provider": "resend", "provider_message_id": "email-id"}) as email:
                result = notifications.send_application_notifications(
                    Mock(),
                    sample_user(),
                    1000,
                    123,
                    sample_registration_data()
                )

        telegram.assert_called_once()
        email.assert_called_once()
        self.assertFalse(result["telegram"]["sent"])
        self.assertTrue(result["email"]["sent"])

    def test_resend_error_does_not_block_telegram(self):
        with patch.object(notifications, "send_application_telegram_notification", return_value={"configured": True, "sent": True, "error_type": None, "error_message": None}) as telegram:
            with patch.object(notifications, "send_application_email_notification", return_value={"configured": True, "sent": False, "error_type": "ResendAPIError", "error_message": "resend", "provider": "resend", "provider_message_id": None}) as email:
                result = notifications.send_application_notifications(
                    Mock(),
                    sample_user(),
                    1000,
                    123,
                    sample_registration_data()
                )

        telegram.assert_called_once()
        email.assert_called_once()
        self.assertTrue(result["telegram"]["sent"])
        self.assertFalse(result["email"]["sent"])

    def test_resend_success_sends_email_over_sdk_once_with_text_and_html(self):
        with patch.dict("os.environ", valid_env(), clear=True):
            with patch.object(notifications, "resend", FakeResend):
                result = notifications.send_application_email_notification(self.build_notification())

        self.assertEqual(result, {
            "configured": True,
            "sent": True,
            "provider": "resend",
            "provider_message_id": "email-id",
            "error_type": None,
            "error_message": None,
        })
        self.assertEqual(FakeResend.api_key, "re_secret_123456")
        self.assertEqual(len(FakeEmails.sent), 1)
        params = FakeEmails.sent[0]
        self.assertEqual(params["from"], "ArtFlow <noreply@artflowfest.com>")
        self.assertEqual(params["to"], ["organizer@example.com"])
        self.assertEqual(params["reply_to"], "reply@example.com")
        self.assertEqual(params["subject"], "Новая заявка ArtFlow №123 — ArtFlow <Final>")
        self.assertIn("Заявка: №123", params["text"])
        self.assertIn("<h1>Новая заявка ArtFlow</h1>", params["html"])

    def test_resend_dict_response_id_is_returned(self):
        FakeEmails.response = {"id": "dict-id"}

        with patch.dict("os.environ", valid_env(), clear=True):
            with patch.object(notifications, "resend", FakeResend):
                result = notifications.send_application_email_notification(self.build_notification())

        self.assertTrue(result["sent"])
        self.assertEqual(result["provider_message_id"], "dict-id")

    def test_resend_object_response_id_is_returned(self):
        FakeEmails.response = SimpleNamespace(id="object-id")

        with patch.dict("os.environ", valid_env(), clear=True):
            with patch.object(notifications, "resend", FakeResend):
                result = notifications.send_application_email_notification(self.build_notification())

        self.assertTrue(result["sent"])
        self.assertEqual(result["provider_message_id"], "object-id")

    def test_resend_response_without_id_is_error(self):
        FakeEmails.response = {}

        with patch.dict("os.environ", valid_env(), clear=True):
            with patch.object(notifications, "resend", FakeResend):
                result = notifications.send_application_email_notification(self.build_notification())

        self.assertEqual(result, {
            "configured": True,
            "sent": False,
            "provider": "resend",
            "provider_message_id": None,
            "error_type": "InvalidProviderResponse",
            "error_message": "Resend response does not contain an email id",
        })

    def test_resend_reply_to_is_optional(self):
        with patch.dict("os.environ", valid_env(RESEND_REPLY_TO_EMAIL=""), clear=True):
            with patch.object(notifications, "resend", FakeResend):
                result = notifications.send_application_email_notification(self.build_notification())

        self.assertTrue(result["sent"])
        self.assertNotIn("reply_to", FakeEmails.sent[0])

    def test_resend_authentication_error_is_reflected_in_result(self):
        FakeEmails.error = RuntimeError("Unauthorized re_secret_123456 401")

        with patch.dict("os.environ", valid_env(), clear=True):
            with patch.object(notifications, "resend", FakeResend):
                result = notifications.send_application_email_notification(self.build_notification())

        self.assertFalse(result["sent"])
        self.assertEqual(result["error_type"], "ResendAuthenticationError")
        self.assertEqual(result["error_message"], "Resend authentication failed")

    def test_missing_resend_package_returns_dependency_error(self):
        with patch.dict("os.environ", valid_env(), clear=True):
            with patch.object(notifications, "resend", None):
                result = notifications.send_application_email_notification(self.build_notification())

        self.assertTrue(result["configured"])
        self.assertFalse(result["sent"])
        self.assertEqual(result["provider"], "resend")
        self.assertEqual(result["error_type"], "DependencyError")

    def test_logs_do_not_include_api_key_or_token(self):
        bot = FakeBot(should_fail=True, error=RuntimeError("re_secret_123456 123456:ABCDEF bot123456:ABCDEF"))

        with patch.dict("os.environ", valid_env(), clear=True):
            with self.assertLogs(notifications.logger, level="ERROR") as logs:
                notifications.send_application_telegram_notification(bot, self.build_notification())

        output = "\n".join(logs.output)
        self.assertNotIn("re_secret_123456", output)
        self.assertNotIn("123456:ABCDEF", output)
        self.assertNotIn("bot123456:ABCDEF", output)
        self.assertIn("[secret]", output)

    def test_resend_api_key_is_not_in_exception_logs(self):
        FakeEmails.error = RuntimeError("Unauthorized re_secret_123456 401")

        with patch.dict("os.environ", valid_env(), clear=True):
            with patch.object(notifications, "resend", FakeResend):
                with self.assertLogs(notifications.logger, level="ERROR") as logs:
                    notifications.send_application_email_notification(self.build_notification())

        output = "\n".join(logs.output)
        self.assertNotIn("re_secret_123456", output)
        self.assertIn("ResendAuthenticationError", output)

    def test_both_disabled_channels_return_structured_result(self):
        with patch.dict("os.environ", {}, clear=True):
            result = notifications.send_application_notifications(
                Mock(),
                sample_user(),
                1000,
                123,
                sample_registration_data()
            )

        self.assertFalse(result["telegram"]["configured"])
        self.assertFalse(result["email"]["configured"])
        self.assertFalse(result["telegram"]["sent"])
        self.assertFalse(result["email"]["sent"])

    def test_empty_optional_fields_do_not_break_formatting(self):
        notification = notifications.build_application_notification_data(
            124,
            sample_registration_data(participants=[], music_file_name=None),
            sample_user(username=None),
            1000
        )

        telegram_text = notifications.format_application_telegram_message(notification)
        subject, text_body, html_body = notifications.format_application_email(notification)

        self.assertIn("👤 Telegram: не указан", telegram_text)
        self.assertIn("🎧 Музыкальный файл: Не используется", telegram_text)
        self.assertIn("№124", subject)
        self.assertIn("Музыкальный файл: Не используется", text_body)
        self.assertIn("Не используется", html_body)


if __name__ == "__main__":
    unittest.main()
