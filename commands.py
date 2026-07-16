import logging

from loader import bot
from keyboards.user_keyboards import main_menu
from keyboards.user_keyboards import competition_1_menu
from keyboards.admin_keyboards import admin_requests_menu
from storage import user_data
from deep_links import parse_competition_deep_link
from competition_messages import competition_text
from database import is_admin, save_user, get_competition_by_id, get_competition_web_data_by_id


logger = logging.getLogger(__name__)

WELCOME_TEXT = '''👋 Добро пожаловать в ArtFlow!

🎨 Здесь вы можете подать заявку на участие в конкурсах, ознакомиться с положениями, узнать стоимость участия и получить ответы на популярные вопросы.

🏆 В настоящее время открыта регистрация на международные конкурсы по различным направлениям искусства:
• Хореография
• Вокал
• Инструментальное творчество

👇 Выберите интересующий вас раздел в меню ниже:'''


def save_user_safely(message):
    try:
        save_user(message)
    except Exception:
        logger.error("Failed to save Telegram user")


def send_main_menu(message, prefix=None):
    text = WELCOME_TEXT

    if prefix:
        text = f"{prefix}\n\n{text}"

    bot.send_message(message.chat.id, text, reply_markup=main_menu())


def open_competition_from_deep_link(message, competition_number):
    competition_id = f"competition_{competition_number}"

    try:
        competition = get_competition_by_id(competition_id)
        web_data = get_competition_web_data_by_id(competition_number)
    except Exception:
        logger.error("Failed to open competition from Telegram deep link")
        send_main_menu(
            message,
            "Конкурс по этой ссылке не найден или больше недоступен."
        )
        return

    if not competition or not web_data or web_data.get("is_published") is not True:
        send_main_menu(
            message,
            "Конкурс по этой ссылке не найден или больше недоступен."
        )
        return

    user_data.setdefault(message.chat.id, {})
    user_data[message.chat.id]["selected_competition"] = competition_id

    bot.send_message(
        message.chat.id,
        competition_text(competition),
        reply_markup=competition_1_menu()
    )


@bot.message_handler(commands=['start'])
def start(message):
    save_user_safely(message)

    competition_number = parse_competition_deep_link(message.text)

    if competition_number is None:
        send_main_menu(message)
        return

    open_competition_from_deep_link(message, competition_number)


@bot.message_handler(commands=['info'])
def info(message):
    save_user_safely(message)
    send_main_menu(message)


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
