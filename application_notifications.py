import logging
import os
import smtplib
import ssl
from email.message import EmailMessage
from html import escape


logger = logging.getLogger(__name__)

APPLICATION_RECIPIENT_CHAT_ID = "APPLICATION_RECIPIENT_CHAT_ID"
APPLICATION_RECIPIENT_EMAIL = "APPLICATION_RECIPIENT_EMAIL"
SMTP_HOST = "SMTP_HOST"
SMTP_PORT = "SMTP_PORT"
SMTP_USER = "SMTP_USER"
SMTP_PASSWORD = "SMTP_PASSWORD"
SMTP_FROM_EMAIL = "SMTP_FROM_EMAIL"
SMTP_USE_SSL = "SMTP_USE_SSL"
SMTP_USE_STARTTLS = "SMTP_USE_STARTTLS"


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


def _telegram_username(message):
    user = getattr(message, "from_user", None)
    username = getattr(user, "username", None)

    if username:
        return f"@{username}"

    return "не указан"


def _telegram_id(message):
    chat = getattr(message, "chat", None)
    chat_id = getattr(chat, "id", None)

    if chat_id is None:
        return ""

    return str(chat_id)


def _env(name):
    value = os.getenv(name)

    if value is None:
        return ""

    return value.strip()


def _env_bool(name, default=False):
    value = _env(name)

    if not value:
        return default

    return value.lower() in ("1", "true", "yes", "y", "on")


def build_application_notification_data(application_id, registration_data, message=None):
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
        "telegram_username": _telegram_username(message),
        "telegram_id": _telegram_id(message),
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
        f"🆔 Telegram ID: {escape(_display(notification_data.get('telegram_id')))}",
        f"🎧 Музыкальный файл: {escape(_display(notification_data.get('music_file_name'), 'Не используется'))}",
        f"🕒 Дата подачи: {escape(_display(notification_data.get('create_at')))}",
    ]

    return "\n".join(lines)


def format_application_email(notification_data):
    application_id = _email_value(notification_data.get("application_id"))
    competition_name = _email_value(notification_data.get("competition_name"))
    safe_competition_name = competition_name.replace("\r", " ").replace("\n", " ")
    subject = f"Новая заявка ArtFlow №{application_id} — {safe_competition_name}"

    body = "\n".join([
        "Новая заявка ArtFlow",
        "",
        f"Заявка: №{application_id}",
        f"Конкурс: {competition_name}",
        f"Город: {_email_value(notification_data.get('city'))}",
        f"Коллектив: {_email_value(notification_data.get('team'))}",
        f"Номер: {_email_value(notification_data.get('number_name'))}",
        f"Номинация: {_email_value(notification_data.get('genre'))}",
        f"Количество участников: {_email_value(notification_data.get('participant_count'))}",
        f"Участники: {_email_value(notification_data.get('participants'))}",
        f"Возраст: {_email_value(notification_data.get('age'))}",
        f"Хронометраж: {_email_value(notification_data.get('performance_time'))}",
        f"Руководитель: {_email_value(notification_data.get('supervisor'))}",
        f"WhatsApp: {_email_value(notification_data.get('whatsapp'))}",
        f"Email: {_email_value(notification_data.get('email'))}",
        f"Telegram: {_email_value(notification_data.get('telegram_username'))}",
        f"Telegram ID: {_email_value(notification_data.get('telegram_id'))}",
        f"Музыкальный файл: {_email_value(notification_data.get('music_file_name'), 'Не используется')}",
        f"Дата подачи: {_email_value(notification_data.get('create_at'))}",
    ])

    return subject, body


def send_application_telegram_notification(bot, notification_data):
    recipient_chat_id = _env(APPLICATION_RECIPIENT_CHAT_ID)

    if not recipient_chat_id:
        logger.warning("Application Telegram notification skipped: recipient chat id is not configured")
        return False

    bot.send_message(
        recipient_chat_id,
        format_application_telegram_message(notification_data),
        parse_mode="HTML"
    )

    return True


def send_application_email_notification(notification_data):
    recipient_email = _env(APPLICATION_RECIPIENT_EMAIL)
    smtp_host = _env(SMTP_HOST)
    smtp_user = _env(SMTP_USER)
    smtp_password = _env(SMTP_PASSWORD)
    from_email = _env(SMTP_FROM_EMAIL) or smtp_user

    if not recipient_email or not smtp_host or not from_email:
        logger.warning("Application email notification skipped: SMTP settings are not configured")
        return False

    use_ssl = _env_bool(SMTP_USE_SSL, False)
    use_starttls = _env_bool(SMTP_USE_STARTTLS, not use_ssl)
    default_port = 465 if use_ssl else 587
    smtp_port = int(_env(SMTP_PORT) or default_port)
    subject, body = format_application_email(notification_data)

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_email
    message["To"] = recipient_email
    message.set_content(body)

    context = ssl.create_default_context()

    if use_ssl:
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as smtp:
            if smtp_user and smtp_password:
                smtp.login(smtp_user, smtp_password)
            smtp.send_message(message)
    else:
        with smtplib.SMTP(smtp_host, smtp_port) as smtp:
            if use_starttls:
                smtp.starttls(context=context)
            if smtp_user and smtp_password:
                smtp.login(smtp_user, smtp_password)
            smtp.send_message(message)

    return True


def send_application_notifications(bot, message, application_id, registration_data):
    notification_data = build_application_notification_data(
        application_id,
        registration_data,
        message
    )

    try:
        send_application_telegram_notification(bot, notification_data)
    except Exception as error:
        logger.error("Application Telegram notification failed: %s", type(error).__name__)

    try:
        send_application_email_notification(notification_data)
    except Exception as error:
        logger.error("Application email notification failed: %s", type(error).__name__)
