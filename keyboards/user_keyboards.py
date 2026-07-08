from telebot import types, callback_data
from database import get_all_faq, get_all_competitions


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
    competitions = get_all_competitions()

    for competition_id, competition in competitions.items():
        markup.add(
            types.InlineKeyboardButton(
                competition["title"], callback_data=competition_id
            )
        )

    if not competitions:
        markup.add(
            types.InlineKeyboardButton(
                'Конкурсов пока нет', callback_data='none'
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
    return competition_menu()



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
    competitions = get_all_competitions()

    for competition_id, competition in competitions.items():
        markup.add(
            types.InlineKeyboardButton(
                competition["title"], callback_data=competition_id
            )
        )

    if not competitions:
        markup.add(
            types.InlineKeyboardButton(
                'Конкурсов пока нет', callback_data='none'
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

    markup.add(types.InlineKeyboardButton('👥 Участники', callback_data = f'request_participants_{current}'))


    markup.add(
        types.InlineKeyboardButton(
            "🏠 Главное меню",
            callback_data="back_to_info"
        )
    )

    return markup

def contact_menu1():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('🟢 WhatsApp', callback_data = 'wa_1')
    btn2 = types.InlineKeyboardButton('🔵 Telegram', url = 'https://t.me/elenaflaum')
    btn3 = types.InlineKeyboardButton('📩 Почта', callback_data = 'em')
    markup.row(btn1)
    markup.row(btn2, btn3)
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data = 'back_to_contact'))
    return markup



def contact_menu2():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('🟢 WhatsApp', callback_data = 'wa_1')
    btn2 = types.InlineKeyboardButton('🔵 Telegram', url = 'https://t.me/Marishka_060483')
    btn3 = types.InlineKeyboardButton('📩 Почта', callback_data = 'em')
    markup.row(btn1)
    markup.row(btn2, btn3)
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data='back_to_contact'))
    return markup



def faq_menu():
    return faq_page_menu(1)

def faq_menu2():
    return faq_page_menu(2)

def faq_page_menu(page):
    markup = types.InlineKeyboardMarkup()

    faq = get_all_faq()
    per_page = 5

    if not faq:
        markup.add(types.InlineKeyboardButton('Вопросов пока нет', callback_data = 'none'))
        return markup

    total_pages = (len(faq) + per_page - 1) // per_page

    if page > total_pages:
        page = total_pages

    if page < 1:
        page = 1

    start = (page - 1) * per_page
    end = start + per_page

    for item in faq[start:end]:
        markup.add(types.InlineKeyboardButton(item[1], callback_data = f'faq_{item[0]}'))

    if page > 1:
        btn_left = types.InlineKeyboardButton('⬅️', callback_data = f'faqpage_{page - 1}')
    else:
        btn_left = types.InlineKeyboardButton('⬅️', callback_data = 'none')

    btn_middle = types.InlineKeyboardButton(f'Стр. {page}/{total_pages}', callback_data = 'none')

    if page < total_pages:
        btn_right = types.InlineKeyboardButton('➡️', callback_data = f'faqpage_{page + 1}')
    else:
        btn_right = types.InlineKeyboardButton('➡️', callback_data = 'none')

    markup.row(btn_left, btn_middle, btn_right)
    return markup



def contact_menu(): #вернуться в меню с связи орг
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('👩 Елена', callback_data = 'contact_1')
    btn2 = types.InlineKeyboardButton('👩‍🦰 Марина', callback_data = 'contact_2')
    markup.row(btn1, btn2)
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data='back_to_info'))
    return markup



def genre_menu():
    markup = types.InlineKeyboardMarkup()

    btn1 = types.InlineKeyboardButton(
        "💃 Хореография",
        callback_data = 'genre_1'
    )

    btn2 = types.InlineKeyboardButton(
        "🎤 Вокал",
        callback_data = 'genre_2'
    )

    btn3 = types.InlineKeyboardButton(
        "🎻 Инструментальный",
        callback_data = 'genre_3'
    )

    markup.row(btn1, btn2)
    markup.row(btn3)

    return markup
