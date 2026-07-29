from loader import bot
import callbacks
from database import create_tables
from application_notifications import log_application_notification_startup_status

if __name__ == '__main__':
    create_tables()
    log_application_notification_startup_status()
    bot.infinity_polling(
        allowed_updates=['message', 'callback_query'],
    )
