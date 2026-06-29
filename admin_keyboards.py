from telebot import types
from loader import bot



def admin_requests_menu(): # кнопки админ меню
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            "📋 Заявки",
            callback_data="admin_requests"
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            '📊 Статистика',
            callback_data="admin_stats"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            '📤 Рассылка',
            callback_data='admin_spam'
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            '📄 Выгрузить заявки',
            callback_data='admin_choice_request'
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            '👱‍♂️ Добавить администратора',
            callback_data='admin_add_admin'
        )
    )
    return markup

def admin_requests_menu_menu(current, total):#кнопки с пагинации админ списка заявок
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            '🔎 Поиск заявки',
            callback_data="admin_search"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            '🔍 Поиск участника',
            callback_data="admin_participants_search"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            '🗑 Удалить заявку',
            callback_data="admin_delete_request"
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            '🔉 Скачать музыку',
            callback_data='admin_save_music'
        )
    )

    buttons = []

    if current > 1:
        buttons.append(
            types.InlineKeyboardButton(
                "⬅️",
                callback_data=f"admin_request_page_{current - 1}"
            )
        )

    buttons.append(
        types.InlineKeyboardButton(
            f"Заявка {current}/{total}",
            callback_data="none"
        )
    )

    if current < total:
        buttons.append(
            types.InlineKeyboardButton(
                "➡️",
                callback_data=f"admin_request_page_{current + 1}"
            )
        )

    markup.row(*buttons)

    return markup


def admin_request_navigation(current, total):

    markup = types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton(
            "🏠 Главное меню",
            callback_data="back_to_info"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            '🔎 Поиск заявки',
            callback_data="admin_search"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            '🔍 Поиск участника',
            callback_data="admin_participants_search"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            '🗑 Удалить заявку',
            callback_data="admin_delete_request"
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            '🔉 Скачать музыку',
            callback_data='admin_save_music'
        )
    )

    buttons = []

    if current > 1:
        buttons.append(
            types.InlineKeyboardButton(
                "⬅️",
                callback_data=f"admin_request_page_{current - 1}"
            )
        )

    buttons.append(
        types.InlineKeyboardButton(
            f"Заявка {current}/{total}",
            callback_data="none"
        )
    )

    if current < total:
        buttons.append(
            types.InlineKeyboardButton(
                "➡️",
                callback_data=f"admin_request_page_{current + 1}"
            )
        )

    markup.row(*buttons)

    return markup