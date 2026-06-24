import telebot
from telebot import types
from loader import bot

import commands
import registration
import callbacks

from database import create_tables

if __name__ == '__main__':
    create_tables()
    bot.infinity_polling(
        allowed_updates=['message', 'callback_query'],
    )

create_tables()

bot.infinity_polling(allowed_updates=['message', 'callback_query'])