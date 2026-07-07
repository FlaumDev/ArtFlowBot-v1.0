from loader import bot
from keyboards.user_keyboards import main_menu
from telebot import types
from keyboards.admin_keyboards import admin_requests_menu
from database import is_admin, save_user


@bot.message_handler(commands=['start', 'info'])
def main(message):
    save_user(message)


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

    if not is_admin(message.chat.id):
        bot.send_message(
            message.chat.id,
            "❌ У вас нет доступа к панели администратора."
        )
        return

    bot.send_message(
        message.chat.id,
        "🛠 Панель администратора",
        reply_markup=admin_requests_menu()
    )
