from telebot import types

def main_menu():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('🏆 Конкурсы', callback_data='competition')
    btn2 = types.InlineKeyboardButton('📝 Подать заявку', callback_data='apply')
    markup.row(btn1, btn2)
    btn3 = types.InlineKeyboardButton('📋 Мои заявки', callback_data='my_requests')
    btn4 = types.InlineKeyboardButton('❓ Частые вопросы', callback_data='faq')
    markup.row(btn3, btn4)
    markup.add(types.InlineKeyboardButton('📞 Связаться с организатором', callback_data='contact'))

    return markup



def end_registration_menu():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('🏠 Главное меню', callback_data='back_to_info')
    btn2 = types.InlineKeyboardButton('📋 Мои заявки', callback_data='my_requests')
    btn3 = types.InlineKeyboardButton('📞 Связаться с организатором', callback_data='contact')
    markup.row(btn1, btn2)
    markup.row(btn3)
    return markup



def exit_registration_menu():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('✅ Подтвердить', callback_data='confirm_reg')
    btn2 = types.InlineKeyboardButton('🔙 Вернуться на главную', callback_data='back_to_info')
    markup.row(btn1, btn2)
    return markup



def age_menu():
    markup = types.InlineKeyboardMarkup()

    btn1 = types.InlineKeyboardButton(
        '👶 Малыши 3-4',
        callback_data="age_3_4"
    )

    btn2 = types.InlineKeyboardButton(
        '🧒 Дошкольная 5-6',
        callback_data="age_5_6"
    )

    btn3 = types.InlineKeyboardButton(
        '👦 Младшая 7-9',
        callback_data="age_7_9"
    )

    btn4 = types.InlineKeyboardButton(
        '👧 Средняя 10-14',
        callback_data="age_10_14"
    )

    btn5 = types.InlineKeyboardButton(
        '🧑 Старшая 15-18',
        callback_data="age_15_18"
    )

    markup.row(btn1, btn2)
    markup.row(btn3, btn4)
    markup.row(btn5)
    return markup



def competition_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            '🏆 СОДРУЖЕСТВО ТАЛАНТОВ г.Павлодар', callback_data='competition_1'
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            '🔙 Назад', callback_data='back_to_info'
        )
    )
    return markup



def back_to_info_menu():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('🏆 Конкурсы', callback_data='competition')
    btn2 = types.InlineKeyboardButton('📝 Подать заявку', callback_data='apply')
    markup.row(btn1, btn2)
    btn3 = types.InlineKeyboardButton('📋 Мои заявки', callback_data='my_requests')
    btn4 = types.InlineKeyboardButton('❓ Частые вопросы', callback_data='faq')
    markup.row(btn3, btn4)
    markup.add(types.InlineKeyboardButton('📞 Связаться с организатором', callback_data='contact'))
    return markup



def competition_1_menu():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('📄 Положение', callback_data='rules')
    btn2 = types.InlineKeyboardButton('📝 Подать заявку', callback_data='bid')
    markup.row(btn1, btn2)
    btn3 = types.InlineKeyboardButton('🔙 Назад', callback_data='back_to_competition')
    markup.add(btn3)
    return markup



def back_to_competition_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            '🏆 СОДРУЖЕСТВО ТАЛАНТОВ г.Павлодар', callback_data='competition_1'
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            '🔙 Назад', callback_data='back_to_info'
        )
    )
    return markup



def bid_menu():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('✅ Начать', callback_data='registration')
    btn2 = types.InlineKeyboardButton('🔙 Назад', callback_data='back_to_competition1')
    markup.row(btn1, btn2)
    return markup



def back_to_competition1_menu():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('📄 Положение', callback_data='rules')
    btn2 = types.InlineKeyboardButton('📝 Подать заявку', callback_data='bid')
    markup.row(btn1, btn2)
    btn3 = types.InlineKeyboardButton('🔙 Назад', callback_data='back_to_competition')
    markup.add(btn3)
    return markup



def apply_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            '🏆 СОДРУЖЕСТВО ТАЛАНТОВ г.Павлодар', callback_data='competition_1'
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            '🔙 Назад', callback_data='back_to_info'
        )
    )
    return markup

def request_navigation(current, total):

    markup = types.InlineKeyboardMarkup()

    buttons = []

    if current > 1:
        buttons.append(
            types.InlineKeyboardButton(
                "⬅️",
                callback_data=f"request_page_{current-1}"
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
                callback_data=f"request_page_{current+1}"
            )
        )


    markup.row(*buttons)


    markup.add(
        types.InlineKeyboardButton(
            "🏠 Главное меню",
            callback_data="back_to_info"
        )
    )

    return markup

def contact_menu():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('WhatsApp', callback_data = 'wa')
    btn2 = types.InlineKeyboardButton('Telegram', callback = 'tg')
    btn3 = types.InlineKeyboardButton('Почта', callback = 'em')
    markup.row(btn2, btn3)

def faq_menu():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('', callback_data = 'q1')
    btn2 = types.InlineKeyboardButton('', callback_data = 'q2')
    btn3 = types.InlineKeyboardButton('', callback_data = 'q3')
    btn4 = types.InlineKeyboardButton('', callback_data = 'q4')
    btn5 = types.InlineKeyboardButton('', callback_data = 'q5')
    btn6 = types.InlineKeyboardButton('', callback_data = 'q6')
    btn7 = types.InlineKeyboardButton('', callback_data = 'q7')
    btn8 = types.InlineKeyboardButton('', callback_data = 'q8')
    btn9 = types.InlineKeyboardButton('', callback_data = 'q9')
    btn10 = types.InlineKeyboardButton('', callback_data = 'q10')

