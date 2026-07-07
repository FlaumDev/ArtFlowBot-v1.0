from loader import bot

from database import create_tables

if __name__ == '__main__':
    create_tables()
    bot.infinity_polling(
        allowed_updates=['message', 'callback_query'],
    )

