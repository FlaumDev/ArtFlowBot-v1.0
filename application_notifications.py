import logging
import os
import re
import socket
from email.utils import parseaddr
from html import escape

try:
    import resend
except ImportError:
    resend = None


logger = logging.getLogger(__name__)

APPLICATION_RECIPIENT_CHAT_ID = "APPLICATION_RECIPIENT_CHAT_ID"
APPLICATION_RECIPIENT_EMAIL = "APPLICATION_RECIPIENT_EMAIL"
RESEND_API_KEY = "RESEND_API_KEY"
RESEND_FROM_EMAIL = "RESEND_FROM_EMAIL"
RESEND_REPLY_TO_EMAIL = "RESEND_REPLY_TO_EMAIL"

TEST_NOTIFICATION_TEXT = "Тестовое уведомление ArtFlow.\nКанал уведомлений настроен правильно."
_SENSITIVE_ENV_NAMES = (
    "TOKEN",
    "BOT_TOKEN",
    "RESEND_API_KEY",
    "SMTP_PASSWORD",
    "DB_PASSWORD",
    "DATABASE_URL"
)


def _clean(value):
    if value is None:
        return ""

    return str(value).strip()


def _display(value, empty="Не указано"):
    value = _clean(value)

    if not value:
        return empty

    return value


def _email_value(value, empty="Не указано"):
    value = _clean(value)

    if not value:
        return empty

    return value


def _env(name):
    value = os.getenv(name)

    if value is None:
        return ""

    return value.strip()


def _join_participants(participants):
    if not participants:
        return ""

    values = [_clean(participant) for participant in participants]
    values = [participant for participant in values if participant]

    return ", ".join(values)


def _format_datetime(value):
    if not value:
        return ""

    if hasattr(value, "strftime"):
        return value.strftime("%d.%m.%Y %H:%M")

    return _clean(value)


def _telegram_username(user):
    username = getattr(user, "username", None)

    if username:
        return f"@{username}"

    return "не указан"


def _telegram_user_id(user):
    user_id = getattr(user, "id", None)

    if user_id is None:
        return ""

    return str(user_id)


def _extract_user_and_chat(user_or_message=None, chat_id=None):
    user = user_or_message

    if hasattr(user_or_message, "from_user"):
        message = user_or_message
        user = getattr(message, "from_user", None)

        if chat_id is None:
            chat = getattr(message, "chat", None)
            chat_id = getattr(chat, "id", None)

    return user, chat_id


def _has_header_break(value):
    return "\r" in value or "\n" in value


def _looks_like_email_address(value):
    value = _clean(value)

    if not value or _has_header_break(value):
        return False

    if any(symbol in value for symbol in ("<", ">", " ", "\t")):
        return False

    if value.count("@") != 1:
        return False

    local, domain = value.rsplit("@", 1)

    return bool(local and domain and "." in domain)


def _validate_email_header_value(name, value, allow_display_name=False):
    value = _clean(value)

    if _has_header_break(value):
        return f"{name} must not contain CR or LF"

    display_name, email_address = parseaddr(value)
    email_address = _clean(email_address)

    if not _looks_like_email_address(email_address):
        return f"{name} must be an email address"

    if allow_display_name:
        if value == email_address:
            return None

        if "<" in value or ">" in value:
            parsed_suffix = value.rsplit("<", 1)[-1]
            if value.endswith(">") and parsed_suffix.rstrip(">").strip() == email_address:
                return None

        return f"{name} must be an email address"

    if display_name or value != email_address:
        return f"{name} must be an email address"

    return None


def _sanitize_header_text(value):
    return _clean(value).replace("\r", " ").replace("\n", " ")


def validate_application_notification_config():
    telegram_missing = []
    telegram_errors = []
    email_missing = []
    email_errors = []

    chat_id = _env(APPLICATION_RECIPIENT_CHAT_ID)

    if not chat_id:
        telegram_missing.append(APPLICATION_RECIPIENT_CHAT_ID)
    else:
        try:
            parsed_chat_id = int(chat_id)

            if parsed_chat_id == 0:
                telegram_errors.append(
                    f"{APPLICATION_RECIPIENT_CHAT_ID} must be a positive private chat ID or a negative group ID"
                )
        except ValueError:
            telegram_errors.append(f"{APPLICATION_RECIPIENT_CHAT_ID} must be an integer")

    recipient_email = _env(APPLICATION_RECIPIENT_EMAIL)
    api_key = _env(RESEND_API_KEY)
    from_email = _env(RESEND_FROM_EMAIL)
    reply_to_email = _env(RESEND_REPLY_TO_EMAIL)

    if not recipient_email:
        email_missing.append(APPLICATION_RECIPIENT_EMAIL)
    else:
        recipient_error = _validate_email_header_value(APPLICATION_RECIPIENT_EMAIL, recipient_email)
        if recipient_error:
            email_errors.append(recipient_error)

    if not api_key:
        email_missing.append(RESEND_API_KEY)

    if not from_email:
        email_missing.append(RESEND_FROM_EMAIL)
    else:
        from_error = _validate_email_header_value(RESEND_FROM_EMAIL, from_email, allow_display_name=True)
        if from_error:
            email_errors.append(from_error)

    if reply_to_email:
        reply_to_error = _validate_email_header_value(RESEND_REPLY_TO_EMAIL, reply_to_email)
        if reply_to_error:
            email_errors.append(reply_to_error)

    return {
        "telegram": {
            "configured": not telegram_missing and not telegram_errors,
            "missing": telegram_missing,
            "errors": telegram_errors
        },
        "email": {
            "configured": not email_missing and not email_errors,
            "missing": email_missing,
            "errors": email_errors
        }
    }


def _mask_chat_id(chat_id):
    value = _clean(chat_id)

    if not value:
        return "not set"

    sign = "-" if value.startswith("-") else ""
    digits = value[1:] if sign else value

    if len(digits) <= 4:
        return f"{sign}{'*' * len(digits)}"

    return f"{sign}{'*' * max(6, len(digits) - 4)}{digits[-4:]}"


def _mask_email(email):
    value = _clean(email)

    if not value:
        return "not set"

    if "@" not in value:
        return "***"

    local, domain = value.split("@", 1)

    if not local:
        masked_local = "***"
    else:
        masked_local = f"{local[0]}***"

    return f"{masked_local}@{domain}"



def _format_config_issue(status):
    parts = []

    if status["missing"]:
        parts.append("missing " + ", ".join(status["missing"]))

    if status["errors"]:
        parts.append("errors " + "; ".join(status["errors"]))

    return "; ".join(parts) or "not configured"


def get_application_notification_startup_lines():
    config = validate_application_notification_config()
    lines = ["Application notifications:"]

    if config["telegram"]["configured"]:
        lines.append(f"Telegram: enabled, recipient={_mask_chat_id(_env(APPLICATION_RECIPIENT_CHAT_ID))}")
    else:
        lines.append(f"Telegram: disabled, {_format_config_issue(config['telegram'])}")

    if config["email"]["configured"]:
        lines.append("Email: enabled, provider=Resend HTTPS")
    else:
        lines.append(f"Email: disabled, {_format_config_issue(config['email'])}")

    return lines


def log_application_notification_startup_status():
    logger.info("\n".join(get_application_notification_startup_lines()))


def _sanitize_error_message(error):
    message = _clean(error)

    if not message:
        return type(error).__name__

    for name in _SENSITIVE_ENV_NAMES:
        secret = os.getenv(name)

        if secret:
            message = message.replace(secret, "[secret]")

    message = re.sub(r"bot\d+:[A-Za-z0-9_-]+", "bot[secret]", message)
    message = re.sub(r"re_[A-Za-z0-9_-]+", "re_[secret]", message)

    if len(message) > 300:
        message = f"{message[:297]}..."

    return message


def _result(configured, sent, error_type=None, error_message=None, provider=None, provider_message_id=None):
    result = {
        "configured": configured,
        "sent": sent,
        "error_type": error_type,
        "error_message": error_message
    }

    if provider is not None:
        result["provider"] = provider
        result["provider_message_id"] = provider_message_id

    return result


def _email_result(configured, sent, error_type=None, error_message=None, provider_message_id=None):
    return {
        "configured": configured,
        "sent": sent,
        "provider": "resend",
        "provider_message_id": provider_message_id,
        "error_type": error_type,
        "error_message": error_message
    }

def _config_error_result(channel_status):
    return _result(
        False,
        False,
        "ConfigurationError",
        _format_config_issue(channel_status)
    )


def _log_sanitized_exception(message, application_id, error_type, error_message, error):
    original_args = getattr(error, "args", None)

    try:
        if original_args is not None:
            error.args = (error_message,)

        logger.exception(
            message,
            application_id,
            error_type,
            error_message
        )
    finally:
        if original_args is not None:
            error.args = original_args


def _classify_telegram_error(error):
    error_type = type(error).__name__
    safe_message = _sanitize_error_message(error)
    normalized = safe_message.lower()

    if isinstance(error, (TimeoutError, socket.timeout)) or "timeout" in normalized:
        return "TimeoutError", "Telegram request timed out"

    if "chat not found" in normalized:
        return "ChatNotFound", "Chat not found"

    if "bot was blocked" in normalized or "blocked by the user" in normalized:
        return "BotBlocked", "Bot was blocked by the user"

    if "forbidden" in normalized or "403" in normalized:
        return "Forbidden", "Telegram request is forbidden"

    if "invalid chat" in normalized or "chat_id" in normalized:
        return "InvalidChatID", "Invalid chat ID"

    if "telegram" in error_type.lower() or "api" in error_type.lower():
        return "TelegramAPIError", safe_message

    return error_type, safe_message


def _classify_resend_error(error):
    error_type = type(error).__name__
    safe_message = _sanitize_error_message(error)
    normalized = safe_message.lower()

    if isinstance(error, (TimeoutError, socket.timeout)) or "timeout" in normalized:
        return "TimeoutError", "Resend request timed out"

    if "api key" in normalized or "unauthorized" in normalized or "401" in normalized:
        return "ResendAuthenticationError", "Resend authentication failed"

    if "rate" in normalized and "limit" in normalized:
        return "ResendRateLimitError", safe_message

    if "validation" in normalized or "invalid" in normalized or "422" in normalized:
        return "ResendValidationError", safe_message

    if "resend" in error_type.lower() or "api" in error_type.lower():
        return "ResendAPIError", safe_message

    return error_type, safe_message


def build_application_notification_data(application_id, registration_data, user=None, chat_id=None):
    user, chat_id = _extract_user_and_chat(user, chat_id)

    return {
        "application_id": application_id,
        "competition_name": registration_data.get("competition_name"),
        "city": registration_data.get("city"),
        "team": registration_data.get("team"),
        "number_name": registration_data.get("name"),
        "genre": registration_data.get("genre"),
        "participant_count": registration_data.get("participant_count"),
        "participants": _join_participants(registration_data.get("participants")),
        "age": registration_data.get("age"),
        "performance_time": registration_data.get("performance_time"),
        "supervisor": registration_data.get("supervisor"),
        "whatsapp": registration_data.get("WhatsApp"),
        "email": registration_data.get("email"),
        "music_file_name": registration_data.get("music_file_name"),
        "create_at": _format_datetime(registration_data.get("create_at")),
        "telegram_username": _telegram_username(user),
        "telegram_id": _telegram_user_id(user),
        "telegram_user_id": _telegram_user_id(user),
        "telegram_chat_id": _clean(chat_id),
    }


def format_application_telegram_message(notification_data):
    lines = [
        "<b>🎉 Новая заявка ArtFlow</b>",
        "",
        f"🆔 Заявка: №{escape(_display(notification_data.get('application_id')))}",
        f"🏆 Конкурс: {escape(_display(notification_data.get('competition_name')))}",
        f"🏙 Город: {escape(_display(notification_data.get('city')))}",
        f"🏫 Коллектив: {escape(_display(notification_data.get('team')))}",
        f"🎵 Номер: {escape(_display(notification_data.get('number_name')))}",
        f"🎭 Номинация: {escape(_display(notification_data.get('genre')))}",
        f"👥 Количество участников: {escape(_display(notification_data.get('participant_count')))}",
        f"👥 Участники: {escape(_display(notification_data.get('participants')))}",
        f"🎂 Возраст: {escape(_display(notification_data.get('age')))}",
        f"⏱ Хронометраж: {escape(_display(notification_data.get('performance_time')))}",
        f"👤 Руководитель: {escape(_display(notification_data.get('supervisor')))}",
        f"📱 WhatsApp: {escape(_display(notification_data.get('whatsapp')))}",
        f"📧 Email: {escape(_display(notification_data.get('email')))}",
        f"👤 Telegram: {escape(_display(notification_data.get('telegram_username')))}",
        f"🆔 Telegram ID: {escape(_display(notification_data.get('telegram_user_id')))}",
        f"💬 Chat ID: {escape(_display(notification_data.get('telegram_chat_id')))}",
        f"🎧 Музыкальный файл: {escape(_display(notification_data.get('music_file_name'), 'Не используется'))}",
        f"🕒 Дата подачи: {escape(_display(notification_data.get('create_at')))}",
    ]

    return "\n".join(lines)


def _application_email_fields(notification_data):
    return [
        ("Заявка", f"№{_email_value(notification_data.get('application_id'))}"),
        ("Конкурс", _email_value(notification_data.get("competition_name"))),
        ("Город", _email_value(notification_data.get("city"))),
        ("Коллектив", _email_value(notification_data.get("team"))),
        ("Номер", _email_value(notification_data.get("number_name"))),
        ("Номинация", _email_value(notification_data.get("genre"))),
        ("Количество участников", _email_value(notification_data.get("participant_count"))),
        ("Участники", _email_value(notification_data.get("participants"))),
        ("Возраст", _email_value(notification_data.get("age"))),
        ("Хронометраж", _email_value(notification_data.get("performance_time"))),
        ("Руководитель", _email_value(notification_data.get("supervisor"))),
        ("WhatsApp", _email_value(notification_data.get("whatsapp"))),
        ("Email", _email_value(notification_data.get("email"))),
        ("Telegram", _email_value(notification_data.get("telegram_username"))),
        ("Telegram ID", _email_value(notification_data.get("telegram_user_id"))),
        ("Chat ID", _email_value(notification_data.get("telegram_chat_id"))),
        ("Музыкальный файл", _email_value(notification_data.get("music_file_name"), "Не используется")),
        ("Дата подачи", _email_value(notification_data.get("create_at"))),
    ]


def _format_application_email_html(fields):
    rows = []

    for label, value in fields:
        rows.append(
            "<tr>"
            f"<th>{escape(label)}</th>"
            f"<td>{escape(value)}</td>"
            "</tr>"
        )

    return "".join([
        "<!doctype html>",
        "<html>",
        "<body style=\"font-family: Arial, sans-serif; color: #111827; line-height: 1.45;\">",
        "<h1>Новая заявка ArtFlow</h1>",
        "<table cellpadding=\"6\" cellspacing=\"0\" style=\"border-collapse: collapse;\">",
        "".join(rows),
        "</table>",
        "</body>",
        "</html>",
    ])


def format_application_email(notification_data):
    application_id = _email_value(notification_data.get("application_id"))
    competition_name = _email_value(notification_data.get("competition_name"))
    subject = _sanitize_header_text(f"Новая заявка ArtFlow №{application_id} — {competition_name}")
    fields = _application_email_fields(notification_data)

    text_body = "\n".join(
        [
            "Новая заявка ArtFlow",
            "",
        ]
        + [f"{label}: {value}" for label, value in fields]
    )
    html_body = _format_application_email_html(fields)

    return subject, text_body, html_body


def _send_telegram_message(bot, text, application_id=None):
    config = validate_application_notification_config()["telegram"]

    if not config["configured"]:
        logger.warning("Application Telegram notification skipped: %s", _format_config_issue(config))
        return _config_error_result(config)

    try:
        recipient_chat_id = int(_env(APPLICATION_RECIPIENT_CHAT_ID))
        bot.send_message(
            recipient_chat_id,
            text,
            parse_mode="HTML"
        )

        return _result(True, True)
    except Exception as error:
        error_type, error_message = _classify_telegram_error(error)
        _log_sanitized_exception(
            "Application Telegram notification failed: application_id=%s error_type=%s error_message=%s",
            application_id,
            error_type,
            error_message,
            error
        )
        return _result(True, False, error_type, error_message)


def _resend_params(subject, text_body, html_body):
    params = {
        "from": _env(RESEND_FROM_EMAIL),
        "to": [_env(APPLICATION_RECIPIENT_EMAIL)],
        "subject": _sanitize_header_text(subject),
        "text": text_body,
        "html": html_body,
    }

    reply_to_email = _env(RESEND_REPLY_TO_EMAIL)

    if reply_to_email:
        params["reply_to"] = reply_to_email

    return params


def _extract_resend_email_id(response):
    if isinstance(response, dict):
        message_id = response.get("id")
    else:
        message_id = getattr(response, "id", None)

    message_id = _clean(message_id)

    if not message_id:
        return None

    return message_id


def _send_email_message(subject, text_body, html_body, application_id=None):
    config = validate_application_notification_config()["email"]

    if not config["configured"]:
        logger.warning("Application email notification skipped: %s", _format_config_issue(config))
        return _email_result(False, False, "ConfigurationError", _format_config_issue(config))

    if resend is None:
        logger.error("Application email notification failed: resend package is not installed")
        return _email_result(True, False, "DependencyError", "resend package is not installed")

    try:
        resend.api_key = _env(RESEND_API_KEY)
        response = resend.Emails.send(_resend_params(subject, text_body, html_body))
        provider_message_id = _extract_resend_email_id(response)

        if not provider_message_id:
            error_message = "Resend response does not contain an email id"
            logger.error(
                "Application email notification failed: application_id=%s error_type=%s error_message=%s",
                application_id,
                "InvalidProviderResponse",
                error_message
            )
            return _email_result(True, False, "InvalidProviderResponse", error_message)

        return _email_result(True, True, provider_message_id=provider_message_id)
    except Exception as error:
        error_type, error_message = _classify_resend_error(error)
        _log_sanitized_exception(
            "Application email notification failed: application_id=%s error_type=%s error_message=%s",
            application_id,
            error_type,
            error_message,
            error
        )
        return _email_result(True, False, error_type, error_message)


def send_application_telegram_notification(bot, notification_data):
    return _send_telegram_message(
        bot,
        format_application_telegram_message(notification_data),
        notification_data.get("application_id")
    )


def send_application_email_notification(notification_data):
    subject, text_body, html_body = format_application_email(notification_data)
    return _send_email_message(subject, text_body, html_body, notification_data.get("application_id"))


def send_application_notifications(bot, user, chat_id=None, application_id=None, registration_data=None):
    if registration_data is None and isinstance(application_id, dict):
        message = user
        registration_data = application_id
        application_id = chat_id
        user, chat_id = _extract_user_and_chat(message)

    notification_data = build_application_notification_data(
        application_id,
        registration_data or {},
        user,
        chat_id
    )

    result = {
        "telegram": send_application_telegram_notification(bot, notification_data),
        "email": send_application_email_notification(notification_data)
    }

    logger.info(
        "Application notification result: application_id=%s telegram_sent=%s telegram_error=%s email_sent=%s email_error=%s",
        application_id,
        result["telegram"].get("sent"),
        result["telegram"].get("error_type"),
        result["email"].get("sent"),
        result["email"].get("error_type")
    )

    return result


def send_test_notifications(bot):
    result = {
        "telegram": _send_telegram_message(
            bot,
            f"🔔 {escape(TEST_NOTIFICATION_TEXT)}",
            "test"
        ),
        "email": _send_email_message(
            "Тестовое уведомление ArtFlow",
            TEST_NOTIFICATION_TEXT,
            "<h1>Тестовое уведомление ArtFlow</h1><p>Канал уведомлений настроен правильно.</p>",
            "test"
        )
    }

    logger.info(
        "Application test notification result: telegram_sent=%s telegram_error=%s email_sent=%s email_error=%s",
        result["telegram"].get("sent"),
        result["telegram"].get("error_type"),
        result["email"].get("sent"),
        result["email"].get("error_type")
    )

    return result
