from telebot import types



def admin_requests_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            ' Список всех заявок', callback_data='admin_requests'
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
            '🔉 Скачать музыку',
            callback_data='admin_save_music'
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
            "📋 Заявки",
            callback_data="admin_requests"
        )
    )