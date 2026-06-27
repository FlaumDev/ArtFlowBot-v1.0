from loader import bot
from keyboards import main_menu
from telebot import types


@bot.message_handler(commands=['start', 'info'])
def main(message):


    bot.send_message(message.chat.id, '''👋 Добро пожаловать в ArtFlow!

🎨 Здесь вы можете подать заявку на участие в конкурсах, ознакомиться с положениями, узнать стоимость участия и получить ответы на популярные вопросы.

🏆 В настоящее время открыта регистрация на международные конкурсы по различным направлениям искусства:
• Хореография
• Вокал
• Инструментальное творчество

👇 Выберите интересующий вас раздел в меню ниже:''', reply_markup=main_menu())



ADMIN_IDS = [2087517047]

@bot.message_handler(commands=["admin"])
def admin(message):

    if message.chat.id not in ADMIN_IDS:
        bot.send_message(
            message.chat.id,
            "❌ У вас нет доступа к панели администратора."
        )
        return



    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            ' Список всех заявок', callback_data = 'admin_requests'
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            '📊 Статистика',
            callback_data = "admin_stats"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            '🔎 Поиск заявки',
            callback_data = "admin_search"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            '🔍 Поиск участника',
            callback_data = "admin_participants_search"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            '🗑 Удалить заявку',
            callback_data = "admin_delete_request"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            '📤 Рассылка',
            callback_data = 'admin_spam'
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            '📄 Выгрузить заявки',
            callback_data = 'admin_choice_request'
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            '🔉 Скачать музыку',
            callback_data = 'admin_save_music'
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            '👱‍♂️ Добавить администратора',
            callback_data = 'admin_add_admin'
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            "📋 Заявки",
            callback_data="admin_requests"
        )
    )

    bot.send_message(
        message.chat.id,
        "🛠 Панель администратора",
        reply_markup=markup
    )