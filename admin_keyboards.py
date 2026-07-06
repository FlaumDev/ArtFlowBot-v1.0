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
            '🏆 Конкурсы',
            callback_data="admin_competitions"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            '❓ FAQ',
            callback_data="admin_faq"
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

    markup.add(
        types.InlineKeyboardButton(
            '🗑 Удалить администратора',
            callback_data='admin_delete_admin'
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            '📋 Список администраторов',
            callback_data='admin_list_admins'
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
    markup.add(
        types.InlineKeyboardButton(
            '✏️ Изменить статус',
            callback_data='admin_change_status'
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            '🔙 Назад',
            callback_data="back_to_admin_info"
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
    markup.add(
        types.InlineKeyboardButton(
            '✏️ Изменить статус',
            callback_data='admin_change_status'
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            '🔙 Назад',
            callback_data="back_to_admin_info"
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



def admin_stats_menu():
    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton('Назад', callback_data="back_to_admin_info"))

    return markup

def admin_status_menu(request_id):
    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton('На рассмотрении', callback_data=f"admin_status_{request_id}_review"))
    markup.add(types.InlineKeyboardButton('Подтверждено', callback_data=f"admin_status_{request_id}_approved"))
    markup.add(types.InlineKeyboardButton('Отклонено', callback_data=f"admin_status_{request_id}_rejected"))
    markup.add(types.InlineKeyboardButton('Ожидает оплаты', callback_data=f"admin_status_{request_id}_payment"))
    markup.add(types.InlineKeyboardButton('Назад', callback_data=f"admin_open_request_{request_id}"))

    return markup

def admin_faq_menu():
    markup = types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton(
            '📋 Обновить список',
            callback_data='admin_faq'
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            '➕ Добавить вопрос',
            callback_data='admin_add_faq'
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            '✏️ Изменить вопрос',
            callback_data='admin_change_faq'
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            '🗑 Удалить вопрос',
            callback_data='admin_delete_faq'
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            '🔙 Назад',
            callback_data='back_to_admin_info'
        )
    )

    return markup

def admin_competitions_menu():
    markup = types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton(
            '📋 Обновить список',
            callback_data='admin_competitions'
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            '➕ Добавить конкурс',
            callback_data='admin_add_competition'
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            '✏️ Изменить конкурс',
            callback_data='admin_change_competition'
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            '🗑 Удалить конкурс',
            callback_data='admin_delete_competition'
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            '🔙 Назад',
            callback_data='back_to_admin_info'
        )
    )

    return markup
