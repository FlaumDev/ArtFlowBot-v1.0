from telebot import types
from io import BytesIO
import re
from html import escape
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from loader import  bot
from storage import user_data, WhatsApp, COMPETITIONS
from registration import end_registration, performance_time, city, number_of_participants, exit_registration, music_file
from keyboards import competition_menu, contact_menu, competition_1_menu,back_to_info_menu, back_to_competition_menu, bid_menu, back_to_competition1_menu, apply_menu, request_navigation, contact_menu1, contact_menu2, faq_menu, faq_page_menu
from database import get_user_requests, get_participants, get_all_requests, get_all_users_requests, all_count, all_participants, requests_status, request_time, get_connection, search_requests, search_requests_by_participant, get_request_by_id, delete_request, update_request_status, get_all_faq, get_faq_by_id, add_faq, update_faq, delete_faq, get_all_telegram_ids, get_all_admins, is_admin, add_admin, delete_admin, search_request_by_id, search_request_by_email, search_request_by_whatsapp, search_requests_by_participant
from admin_keyboards import admin_requests_menu_menu, admin_request_navigation, admin_requests_menu, admin_stats_menu, admin_status_menu, admin_faq_menu, admin_competitions_menu, admin_search_menu




                       #        обработчики поиска заявок и участников!!!

def admin_search_request_by_id(message):
    if message.content_type != "text":
        msg = bot.send_message(message.chat.id, "❌ Введите ID заявки текстом")
        bot.register_next_step_handler(msg, admin_search_request_by_id)
        return

    search_text = message.text.strip()

    if not search_text.isdigit():
        msg = bot.send_message(message.chat.id, "❌ ID должен быть числом")
        bot.register_next_step_handler(msg, admin_search_request_by_id)
        return

    requests = search_request_by_id(int(search_text))

    admin_send_found_requests(
        message,
        requests,
        "🆔 Результаты поиска по ID"
    )


def admin_search_request_by_email(message):
    if message.content_type != "text":
        msg = bot.send_message(message.chat.id, "❌ Введите e-mail текстом")
        bot.register_next_step_handler(msg, admin_search_request_by_email)
        return

    email = message.text.strip()

    if not email:
        msg = bot.send_message(message.chat.id, "❌ E-mail не может быть пустым")
        bot.register_next_step_handler(msg, admin_search_request_by_email)
        return

    requests = search_request_by_email(email)

    admin_send_found_requests(
        message,
        requests,
        "📧 Результаты поиска по e-mail"
    )


def admin_search_request_by_whatsapp(message):
    if message.content_type != "text":
        msg = bot.send_message(message.chat.id, "❌ Введите WhatsApp текстом")
        bot.register_next_step_handler(msg, admin_search_request_by_whatsapp)
        return

    phone = message.text.strip()

    if not phone:
        msg = bot.send_message(message.chat.id, "❌ WhatsApp не может быть пустым")
        bot.register_next_step_handler(msg, admin_search_request_by_whatsapp)
        return

    requests = search_request_by_whatsapp(phone)

    admin_send_found_requests(
        message,
        requests,
        "📱 Результаты поиска по WhatsApp"
    )


def admin_search_participant(message):
    if not admin_check(message):
        return

    if message.content_type != "text":
        msg = bot.send_message(
            message.chat.id,
            "❌ Введите ФИО участника текстом"
        )
        bot.register_next_step_handler(msg, admin_search_participant)
        return

    participant_name = message.text.strip()

    if not participant_name:
        msg = bot.send_message(
            message.chat.id,
            "❌ ФИО участника не может быть пустым"
        )
        bot.register_next_step_handler(msg, admin_search_participant)
        return

    requests = search_requests_by_participant(participant_name)

    admin_send_found_requests(
        message,
        requests,
        "🔍 Результаты поиска участника"
    )










def admin_request_text(request):
    participants = get_participants(request[0])
    participants_text = "\n".join(
        f"• {participant[0]}"
        for participant in participants
    )

    if not participants_text:
        participants_text = "—"

    return f"""📋 Заявка №{request[0]}
🏙 Город: {request[2]}
🏫 Коллектив: {request[3]}
🎵 Номер: {request[4]}
🎭 Жанр: {request[5]}
👥 Участников: {request[6]} чел.
🎂 Возрастная категория: {request[7]}        
⏱️ Хронометраж {request[8]} мин.
👨‍🏫 Руководитель: {request[9]}
📞 WhatsApp: {request[10]}
📧 E-mail: {request[11]}        
🎵 Музыкальный файл: {request[15]}

👥 Участники:
{participants_text}

📊 Статус: {request[12]}
    """

def get_admin_request_id(text):
    result = re.search(r"Заявка №(\d+)", text or "")

    if result:
        return int(result.group(1))

    return None

def admin_send_found_requests(message, requests, title):
    if not requests:
        bot.send_message(
            message.chat.id,
            "❌ Заявки не найдены"
        )
        return

    if len(requests) == 1:
        bot.send_message(
            message.chat.id,
            admin_request_text(requests[0]),
            reply_markup=admin_requests_menu_menu(1, 1)
        )
        return

    markup = types.InlineKeyboardMarkup()

    for request in requests[:30]:
        markup.add(
            types.InlineKeyboardButton(
                f"Заявка №{request[0]} — {request[11]}",
                callback_data=f"admin_open_request_{request[0]}"
            )
        )

    if len(requests) > 30:
        markup.add(
            types.InlineKeyboardButton(
                "Показаны первые 30 заявок",
                callback_data="none"
            )
        )

    bot.send_message(
        message.chat.id,
        f"{title}\nНайдено заявок: {len(requests)}\nВыберите заявку:",
        reply_markup=markup
    )

def create_requests_excel():
    requests = get_all_requests()

    if not requests:
        return None

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Заявки"

    headers = [
        "ID",
        "Telegram ID",
        "Город",
        "Коллектив",
        "Название номера",
        "Жанр",
        "Количество участников",
        "Возраст",
        "Хронометраж",
        "Руководитель",
        "WhatsApp",
        "Email",
        "Статус",
        "Дата создания",
        "Название музыкального файла",
        "Участники"
    ]

    sheet.append(headers)

    for cell in sheet[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(wrap_text=True, vertical="top")

    for request in requests:
        participants = get_participants(request[0])
        participants_text = "\n".join(
            participant[0]
            for participant in participants
        )

        sheet.append([
            request[0],
            request[1],
            request[2],
            request[3],
            request[4],
            request[5],
            request[6],
            request[7],
            request[8],
            request[9],
            request[10],
            request[11],
            request[12],
            request[13],
            request[15],
            participants_text
        ])

    for row in sheet.iter_rows():
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    widths = {
        "A": 8,
        "B": 16,
        "C": 18,
        "D": 28,
        "E": 28,
        "F": 20,
        "G": 14,
        "H": 18,
        "I": 14,
        "J": 28,
        "K": 18,
        "L": 28,
        "M": 18,
        "N": 22,
        "O": 32,
        "P": 38
    }

    for column, width in widths.items():
        sheet.column_dimensions[column].width = width

    sheet.freeze_panes = "A2"

    excel_file = BytesIO()
    workbook.save(excel_file)
    excel_file.seek(0)
    excel_file.name = "artflow_requests.xlsx"

    return excel_file

def admin_list_text():
    admins = get_all_admins()

    if not admins:
        return "📋 Администраторов пока нет"

    text = "📋 Администраторы\n\n"

    for admin in admins:
        text += f"ID: {admin[1]}\n"

    return text

def admin_add_admin_id(message):
    if not admin_check(message):
        return

    if message.content_type != "text":
        bot.send_message(
            message.chat.id,
            "❌ Введите Telegram ID числом"
        )
        bot.register_next_step_handler(message, admin_add_admin_id)
        return

    admin_id = message.text.strip()

    if not admin_id.isdigit():
        bot.send_message(
            message.chat.id,
            "❌ Введите Telegram ID числом"
        )
        bot.register_next_step_handler(message, admin_add_admin_id)
        return

    admin = add_admin(int(admin_id))

    if not admin:
        bot.send_message(
            message.chat.id,
            "✅ Администратор уже добавлен"
        )
    else:
        bot.send_message(
            message.chat.id,
            "✅ Администратор добавлен"
        )

    bot.send_message(
        message.chat.id,
        admin_list_text(),
        reply_markup=admin_requests_menu()
    )

def admin_delete_admin_id(message):
    if not admin_check(message):
        return

    if message.content_type != "text":
        bot.send_message(
            message.chat.id,
            "❌ Введите Telegram ID числом"
        )
        bot.register_next_step_handler(message, admin_delete_admin_id)
        return

    admin_id = message.text.strip()

    if not admin_id.isdigit():
        bot.send_message(
            message.chat.id,
            "❌ Введите Telegram ID числом"
        )
        bot.register_next_step_handler(message, admin_delete_admin_id)
        return

    count = delete_admin(int(admin_id))

    if not count:
        bot.send_message(
            message.chat.id,
            "❌ Администратор не найден"
        )
    else:
        bot.send_message(
            message.chat.id,
            "🗑 Администратор удален"
        )

    bot.send_message(
        message.chat.id,
        admin_list_text(),
        reply_markup=admin_requests_menu()
    )

def admin_send_spam(message):
    if not admin_check(message):
        return

    users = get_all_telegram_ids()

    if not users:
        bot.send_message(
            message.chat.id,
            "📋 Нет пользователей для рассылки"
        )
        return

    success = 0
    errors = 0

    for user in users:
        telegram_id = user[0]

        try:
            bot.copy_message(
                telegram_id,
                message.chat.id,
                message.message_id
            )
            success += 1
        except Exception:
            errors += 1

    bot.send_message(
        message.chat.id,
        f"""📤 Рассылка завершена

✅ Успешно: {success}
❌ Ошибок: {errors}"""
    )

def admin_faq_text(faq):
    if not faq:
        return "❓ FAQ пока пуст\n\nДобавьте первый вопрос через админ-панель."

    text = "❓ FAQ\n\n"

    for item in faq:
        text += f"""ID {item[0]}
{escape(item[1] or "")}

💬 {escape(item[2] or "")}

"""

    return text

def admin_check(message):
    if not is_admin(message.chat.id):
        bot.send_message(
            message.chat.id,
            "❌ У вас нет доступа к панели администратора."
        )
        return False

    return True

def get_current_competition(user_id):
    competition_id = "competition_1"

    if user_id in user_data:
        competition_id = user_data[user_id].get("selected_competition", competition_id)

    if competition_id not in COMPETITIONS and COMPETITIONS:
        competition_id = next(iter(COMPETITIONS))

    return competition_id, COMPETITIONS.get(competition_id)

def competition_text(competition):
    price = competition.get("price") or "Не указана"

    return f"""🏆 {escape(competition.get("name") or competition.get("title") or "")}

📍 Место проведения:
{escape(competition.get("place") or "Не указано")}

📅 Дата проведения:
{escape(competition.get("date") or "Не указана")}

{escape(competition.get("description") or "")}

💳 Стоимость участия:
{escape(price)}

👇 Выберите дальнейшее действие:"""

def bid_info_text(competition):
    title = competition.get("title") if competition else "конкурс"

    return f"""📝 Регистрация участника(-ов)

Для подачи заявки на конкурс "{escape(title)}" подготовьте следующую информацию:

📌 Данные, которые потребуются:
🏙 Город
🏫 Название коллектива / школы / учреждения
🎵 Название номера
🎭 Жанр номера
👥 Количество участников в номере
🎂 Возрастная категория
⏱ Хронометраж выступления(в минутах)
👤 ФИО руководителя / хореографа
📞 Контактный номер WhatsApp
📞 Ваш e-mail
👥 Список участников (ФИО каждого участника)
🎧 Музыкальный файл номера (формат MP3)

После начала регистрации бот последовательно запросит все необходимые данные. Пожалуйста, подготовьте информацию заранее.

Готовы начать регистрацию?"""

def admin_competitions_text():
    if not COMPETITIONS:
        return "🏆 Конкурсов пока нет\n\nДобавьте первый конкурс через админ-панель."

    text = "🏆 Конкурсы\n\n"

    for competition_id, competition in COMPETITIONS.items():
        price = competition.get("price") or "Не указана"
        rules_file = competition.get("rules_file") or "Не загружено"

        text += f"""ID: {escape(competition_id)}
Название: {escape(competition.get("title") or "")}
Дата: {escape(competition.get("date") or "Не указана")}
Место: {escape(competition.get("place") or "Не указано")}
Стоимость: {escape(price)}
Положение: {escape(rules_file)}

"""

    return text






def get_next_competition_id():
    numbers = []

    for competition_id in COMPETITIONS:
        number = competition_id.split("_")[-1]

        if number.isdigit():
            numbers.append(int(number))

    return f"competition_{max(numbers, default=0) + 1}"

def admin_add_competition_title(message):
    if not admin_check(message):
        return

    if message.content_type != "text":
        bot.send_message(
            message.chat.id,
            "❌ Введите название конкурса текстом"
        )
        bot.register_next_step_handler(message, admin_add_competition_title)
        return

    title = message.text.strip()

    if not title:
        bot.send_message(
            message.chat.id,
            "❌ Название конкурса не может быть пустым"
        )
        bot.register_next_step_handler(message, admin_add_competition_title)
        return

    user_data.setdefault(message.chat.id, {})
    user_data[message.chat.id]["admin_competition"] = {
        "title": title,
        "name": title
    }

    msg = bot.send_message(
        message.chat.id,
        "📝 Введите описание конкурса:"
    )
    bot.register_next_step_handler(msg, admin_add_competition_description)

def admin_add_competition_description(message):
    if not admin_check(message):
        return

    if message.content_type != "text":
        bot.send_message(
            message.chat.id,
            "❌ Введите описание конкурса текстом"
        )
        bot.register_next_step_handler(message, admin_add_competition_description)
        return

    description = message.text.strip()

    if not description:
        bot.send_message(
            message.chat.id,
            "❌ Описание конкурса не может быть пустым"
        )
        bot.register_next_step_handler(message, admin_add_competition_description)
        return

    user_data[message.chat.id]["admin_competition"]["description"] = description

    msg = bot.send_message(
        message.chat.id,
        "📄 Введите путь к положению или отправьте - если положения нет:"
    )
    bot.register_next_step_handler(msg, admin_add_competition_rules)

def admin_add_competition_rules(message):
    if not admin_check(message):
        return

    if message.content_type != "text":
        bot.send_message(
            message.chat.id,
            "❌ Введите путь к положению текстом"
        )
        bot.register_next_step_handler(message, admin_add_competition_rules)
        return

    rules_file = message.text.strip()

    if rules_file == "-":
        rules_file = None

    user_data[message.chat.id]["admin_competition"]["rules_file"] = rules_file

    msg = bot.send_message(
        message.chat.id,
        "📅 Введите дату проведения:"
    )
    bot.register_next_step_handler(msg, admin_add_competition_date)

def admin_add_competition_date(message):
    if not admin_check(message):
        return

    if message.content_type != "text":
        bot.send_message(
            message.chat.id,
            "❌ Введите дату проведения текстом"
        )
        bot.register_next_step_handler(message, admin_add_competition_date)
        return

    date = message.text.strip()

    if not date:
        bot.send_message(
            message.chat.id,
            "❌ Дата проведения не может быть пустой"
        )
        bot.register_next_step_handler(message, admin_add_competition_date)
        return

    user_data[message.chat.id]["admin_competition"]["date"] = date

    msg = bot.send_message(
        message.chat.id,
        "📍 Введите место проведения:"
    )
    bot.register_next_step_handler(msg, admin_add_competition_place)

def admin_add_competition_place(message):
    if not admin_check(message):
        return

    if message.content_type != "text":
        bot.send_message(
            message.chat.id,
            "❌ Введите место проведения текстом"
        )
        bot.register_next_step_handler(message, admin_add_competition_place)
        return

    place = message.text.strip()

    if not place:
        bot.send_message(
            message.chat.id,
            "❌ Место проведения не может быть пустым"
        )
        bot.register_next_step_handler(message, admin_add_competition_place)
        return

    user_data[message.chat.id]["admin_competition"]["place"] = place

    msg = bot.send_message(
        message.chat.id,
        "💳 Введите стоимость участия или отправьте - если стоимости нет:"
    )
    bot.register_next_step_handler(msg, admin_add_competition_price)

def admin_add_competition_price(message):
    if not admin_check(message):
        return

    if message.content_type != "text":
        bot.send_message(
            message.chat.id,
            "❌ Введите стоимость участия текстом"
        )
        bot.register_next_step_handler(message, admin_add_competition_price)
        return

    price = message.text.strip()

    if price == "-":
        price = ""

    user_data[message.chat.id]["admin_competition"]["price"] = price

    competition_id = get_next_competition_id()
    COMPETITIONS[competition_id] = user_data[message.chat.id]["admin_competition"]
    user_data[message.chat.id].pop("admin_competition", None)

    bot.send_message(
        message.chat.id,
        f"✅ Конкурс {competition_id} добавлен"
    )

    bot.send_message(
        message.chat.id,
        admin_competitions_text(),
        reply_markup=admin_competitions_menu()
    )

def admin_change_competition_id(message):
    if not admin_check(message):
        return

    if message.content_type != "text":
        bot.send_message(
            message.chat.id,
            "❌ Введите ID конкурса текстом"
        )
        bot.register_next_step_handler(message, admin_change_competition_id)
        return

    competition_id = message.text.strip()

    if competition_id not in COMPETITIONS:
        bot.send_message(
            message.chat.id,
            "❌ Конкурс не найден"
        )
        return

    user_data.setdefault(message.chat.id, {})
    user_data[message.chat.id]["admin_competition_id"] = competition_id
    user_data[message.chat.id]["admin_competition"] = COMPETITIONS[competition_id].copy()

    msg = bot.send_message(
        message.chat.id,
        f"Текущее название:\n{escape(COMPETITIONS[competition_id].get('title') or '')}\n\nВведите новое название или отправьте - чтобы оставить текущее:"
    )
    bot.register_next_step_handler(msg, admin_change_competition_title)

def admin_change_competition_title(message):
    if not admin_check(message):
        return

    if message.content_type != "text":
        bot.send_message(
            message.chat.id,
            "❌ Введите название конкурса текстом"
        )
        bot.register_next_step_handler(message, admin_change_competition_title)
        return

    title = message.text.strip()

    if title != "-":
        if not title:
            bot.send_message(
                message.chat.id,
                "❌ Название конкурса не может быть пустым"
            )
            bot.register_next_step_handler(message, admin_change_competition_title)
            return

        user_data[message.chat.id]["admin_competition"]["title"] = title
        user_data[message.chat.id]["admin_competition"]["name"] = title

    msg = bot.send_message(
        message.chat.id,
        f"Текущее описание:\n{escape(user_data[message.chat.id]['admin_competition'].get('description') or '')}\n\nВведите новое описание или отправьте - чтобы оставить текущее:"
    )
    bot.register_next_step_handler(msg, admin_change_competition_description)

def admin_change_competition_description(message):
    if not admin_check(message):
        return

    if message.content_type != "text":
        bot.send_message(
            message.chat.id,
            "❌ Введите описание конкурса текстом"
        )
        bot.register_next_step_handler(message, admin_change_competition_description)
        return

    description = message.text.strip()

    if description != "-":
        if not description:
            bot.send_message(
                message.chat.id,
                "❌ Описание конкурса не может быть пустым"
            )
            bot.register_next_step_handler(message, admin_change_competition_description)
            return

        user_data[message.chat.id]["admin_competition"]["description"] = description

    msg = bot.send_message(
        message.chat.id,
        f"Текущее положение:\n{escape(user_data[message.chat.id]['admin_competition'].get('rules_file') or 'Не загружено')}\n\nВведите новый путь к положению или отправьте - чтобы оставить текущее:"
    )
    bot.register_next_step_handler(msg, admin_change_competition_rules)

def admin_change_competition_rules(message):
    if not admin_check(message):
        return

    if message.content_type != "text":
        bot.send_message(
            message.chat.id,
            "❌ Введите путь к положению текстом"
        )
        bot.register_next_step_handler(message, admin_change_competition_rules)
        return

    rules_file = message.text.strip()

    if rules_file != "-":
        user_data[message.chat.id]["admin_competition"]["rules_file"] = rules_file or None

    msg = bot.send_message(
        message.chat.id,
        f"Текущая дата:\n{escape(user_data[message.chat.id]['admin_competition'].get('date') or '')}\n\nВведите новую дату или отправьте - чтобы оставить текущую:"
    )
    bot.register_next_step_handler(msg, admin_change_competition_date)

def admin_change_competition_date(message):
    if not admin_check(message):
        return

    if message.content_type != "text":
        bot.send_message(
            message.chat.id,
            "❌ Введите дату проведения текстом"
        )
        bot.register_next_step_handler(message, admin_change_competition_date)
        return

    date = message.text.strip()

    if date != "-":
        if not date:
            bot.send_message(
                message.chat.id,
                "❌ Дата проведения не может быть пустой"
            )
            bot.register_next_step_handler(message, admin_change_competition_date)
            return

        user_data[message.chat.id]["admin_competition"]["date"] = date

    msg = bot.send_message(
        message.chat.id,
        f"Текущее место:\n{escape(user_data[message.chat.id]['admin_competition'].get('place') or '')}\n\nВведите новое место или отправьте - чтобы оставить текущее:"
    )
    bot.register_next_step_handler(msg, admin_change_competition_place)

def admin_change_competition_place(message):
    if not admin_check(message):
        return

    if message.content_type != "text":
        bot.send_message(
            message.chat.id,
            "❌ Введите место проведения текстом"
        )
        bot.register_next_step_handler(message, admin_change_competition_place)
        return

    place = message.text.strip()

    if place != "-":
        if not place:
            bot.send_message(
                message.chat.id,
                "❌ Место проведения не может быть пустым"
            )
            bot.register_next_step_handler(message, admin_change_competition_place)
            return

        user_data[message.chat.id]["admin_competition"]["place"] = place

    msg = bot.send_message(
        message.chat.id,
        f"Текущая стоимость:\n{escape(user_data[message.chat.id]['admin_competition'].get('price') or 'Не указана')}\n\nВведите новую стоимость или отправьте - чтобы оставить текущую:"
    )
    bot.register_next_step_handler(msg, admin_change_competition_price)

def admin_change_competition_price(message):
    if not admin_check(message):
        return

    if message.content_type != "text":
        bot.send_message(
            message.chat.id,
            "❌ Введите стоимость участия текстом"
        )
        bot.register_next_step_handler(message, admin_change_competition_price)
        return

    price = message.text.strip()

    if price != "-":
        user_data[message.chat.id]["admin_competition"]["price"] = price

    competition_id = user_data[message.chat.id]["admin_competition_id"]
    COMPETITIONS[competition_id] = user_data[message.chat.id]["admin_competition"]

    user_data[message.chat.id].pop("admin_competition_id", None)
    user_data[message.chat.id].pop("admin_competition", None)

    bot.send_message(
        message.chat.id,
        f"✅ Конкурс {competition_id} изменен"
    )

    bot.send_message(
        message.chat.id,
        admin_competitions_text(),
        reply_markup=admin_competitions_menu()
    )

def admin_delete_competition_id(message):
    if not admin_check(message):
        return

    if message.content_type != "text":
        bot.send_message(
            message.chat.id,
            "❌ Введите ID конкурса текстом"
        )
        bot.register_next_step_handler(message, admin_delete_competition_id)
        return

    competition_id = message.text.strip()

    if competition_id not in COMPETITIONS:
        bot.send_message(
            message.chat.id,
            "❌ Конкурс не найден"
        )
        return

    del COMPETITIONS[competition_id]

    bot.send_message(
        message.chat.id,
        f"🗑 Конкурс {competition_id} удален"
    )

    bot.send_message(
        message.chat.id,
        admin_competitions_text(),
        reply_markup=admin_competitions_menu()
    )

def admin_add_faq_question(message):
    if not admin_check(message):
        return

    if message.content_type != "text":
        bot.send_message(
            message.chat.id,
            "❌ Введите вопрос текстом"
        )
        bot.register_next_step_handler(message, admin_add_faq_question)
        return

    question = message.text.strip()

    if not question:
        bot.send_message(
            message.chat.id,
            "❌ Вопрос не может быть пустым"
        )
        bot.register_next_step_handler(message, admin_add_faq_question)
        return

    user_data.setdefault(message.chat.id, {})
    user_data[message.chat.id]["admin_faq_question"] = question

    msg = bot.send_message(
        message.chat.id,
        "💬 Введите ответ на вопрос:"
    )
    bot.register_next_step_handler(msg, admin_add_faq_answer)

def admin_add_faq_answer(message):
    if not admin_check(message):
        return

    if message.content_type != "text":
        bot.send_message(
            message.chat.id,
            "❌ Введите ответ текстом"
        )
        bot.register_next_step_handler(message, admin_add_faq_answer)
        return

    answer = message.text.strip()

    if not answer:
        bot.send_message(
            message.chat.id,
            "❌ Ответ не может быть пустым"
        )
        bot.register_next_step_handler(message, admin_add_faq_answer)
        return

    if message.chat.id not in user_data or "admin_faq_question" not in user_data[message.chat.id]:
        bot.send_message(
            message.chat.id,
            "❌ Данные вопроса не найдены"
        )
        return

    question = user_data[message.chat.id]["admin_faq_question"]
    faq_id = add_faq(question, answer)
    user_data[message.chat.id].pop("admin_faq_question", None)

    bot.send_message(
        message.chat.id,
        f"✅ FAQ №{faq_id} добавлен"
    )

    bot.send_message(
        message.chat.id,
        admin_faq_text(get_all_faq()),
        reply_markup=admin_faq_menu()
    )

def admin_change_faq_id(message):
    if not admin_check(message):
        return

    if message.content_type != "text":
        bot.send_message(
            message.chat.id,
            "❌ Введите ID вопроса числом"
        )
        bot.register_next_step_handler(message, admin_change_faq_id)
        return

    if not message.text.strip().isdigit():
        bot.send_message(
            message.chat.id,
            "❌ Введите ID вопроса числом"
        )
        bot.register_next_step_handler(message, admin_change_faq_id)
        return

    faq_id = int(message.text.strip())
    faq = get_faq_by_id(faq_id)

    if not faq:
        bot.send_message(
            message.chat.id,
            "❌ Вопрос не найден"
        )
        return

    user_data.setdefault(message.chat.id, {})
    user_data[message.chat.id]["admin_faq_id"] = faq_id

    msg = bot.send_message(
        message.chat.id,
        f"Текущий вопрос:\n{escape(faq[1] or '')}\n\nВведите новый вопрос или отправьте - чтобы оставить текущий:"
    )
    bot.register_next_step_handler(msg, admin_change_faq_question)

def admin_change_faq_question(message):
    if not admin_check(message):
        return

    if message.content_type != "text":
        bot.send_message(
            message.chat.id,
            "❌ Введите вопрос текстом"
        )
        bot.register_next_step_handler(message, admin_change_faq_question)
        return

    if message.chat.id not in user_data or "admin_faq_id" not in user_data[message.chat.id]:
        bot.send_message(
            message.chat.id,
            "❌ Данные вопроса не найдены"
        )
        return

    faq_id = user_data[message.chat.id]["admin_faq_id"]
    faq = get_faq_by_id(faq_id)

    if not faq:
        bot.send_message(
            message.chat.id,
            "❌ Вопрос не найден"
        )
        return

    question = message.text.strip()

    if question == "-":
        question = faq[1]

    if not question:
        bot.send_message(
            message.chat.id,
            "❌ Вопрос не может быть пустым"
        )
        bot.register_next_step_handler(message, admin_change_faq_question)
        return

    user_data[message.chat.id]["admin_faq_question"] = question

    msg = bot.send_message(
        message.chat.id,
        f"Текущий ответ:\n{escape(faq[2] or '')}\n\nВведите новый ответ или отправьте - чтобы оставить текущий:"
    )
    bot.register_next_step_handler(msg, admin_change_faq_answer)

def admin_change_faq_answer(message):
    if not admin_check(message):
        return

    if message.content_type != "text":
        bot.send_message(
            message.chat.id,
            "❌ Введите ответ текстом"
        )
        bot.register_next_step_handler(message, admin_change_faq_answer)
        return

    if message.chat.id not in user_data or "admin_faq_id" not in user_data[message.chat.id]:
        bot.send_message(
            message.chat.id,
            "❌ Данные вопроса не найдены"
        )
        return

    faq_id = user_data[message.chat.id]["admin_faq_id"]
    faq = get_faq_by_id(faq_id)

    if not faq:
        bot.send_message(
            message.chat.id,
            "❌ Вопрос не найден"
        )
        return

    answer = message.text.strip()

    if answer == "-":
        answer = faq[2]

    if not answer:
        bot.send_message(
            message.chat.id,
            "❌ Ответ не может быть пустым"
        )
        bot.register_next_step_handler(message, admin_change_faq_answer)
        return

    question = user_data[message.chat.id].get("admin_faq_question", faq[1])
    update_faq(faq_id, question, answer)

    user_data[message.chat.id].pop("admin_faq_id", None)
    user_data[message.chat.id].pop("admin_faq_question", None)

    bot.send_message(
        message.chat.id,
        f"✅ FAQ №{faq_id} изменен"
    )

    bot.send_message(
        message.chat.id,
        admin_faq_text(get_all_faq()),
        reply_markup=admin_faq_menu()
    )

def admin_delete_faq_id(message):
    if not admin_check(message):
        return

    if message.content_type != "text":
        bot.send_message(
            message.chat.id,
            "❌ Введите ID вопроса числом"
        )
        bot.register_next_step_handler(message, admin_delete_faq_id)
        return

    if not message.text.strip().isdigit():
        bot.send_message(
            message.chat.id,
            "❌ Введите ID вопроса числом"
        )
        bot.register_next_step_handler(message, admin_delete_faq_id)
        return

    faq_id = int(message.text.strip())
    faq = get_faq_by_id(faq_id)

    if not faq:
        bot.send_message(
            message.chat.id,
            "❌ Вопрос не найден"
        )
        return

    delete_faq(faq_id)

    bot.send_message(
        message.chat.id,
        f"🗑 FAQ №{faq_id} удален"
    )

    bot.send_message(
        message.chat.id,
        admin_faq_text(get_all_faq()),
        reply_markup=admin_faq_menu()
    )

@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):

    bot.answer_callback_query(callback.id)

    if callback.data.startswith("admin") or callback.data == "back_to_admin_info":
        if not admin_check(callback.message):
            return

    if callback.data == 'competition':

        bot.edit_message_text(
            '🏆 Актуальные конкурсы ArtFlow\n\nВыберите интересующий вас конкурс для просмотра подробной информации и подачи заявки.\n\n👇 Список доступных конкурсов:',
            callback.message.chat.id,
            callback.message.message_id, reply_markup = competition_menu())
    elif callback.data == 'back_to_info':
            bot.edit_message_text(
                '''👋 Добро пожаловать в ArtFlow!

        🎨 Здесь вы можете подать заявку на участие в конкурсах, ознакомиться с положениями, узнать стоимость участия и получить ответы на популярные вопросы.

        🏆 В настоящее время открыта регистрация на международные конкурсы по различным направлениям искусства:
        • Хореография
        • Вокал
        • Инструментальное творчество

        👇 Выберите интересующий вас раздел в меню ниже:''',
                callback.message.chat.id,
                callback.message.message_id, reply_markup= back_to_info_menu())
    elif callback.data.startswith('competition_'):
        competition = COMPETITIONS.get(callback.data)

        if not competition:
            bot.send_message(
                callback.message.chat.id,
                "❌ Конкурс не найден"
            )
            return

        user_data.setdefault(callback.message.chat.id, {})
        user_data[callback.message.chat.id]["selected_competition"] = callback.data

        bot.edit_message_text(
            competition_text(competition),
            callback.message.chat.id,
            callback.message.message_id, reply_markup = competition_1_menu()
        )
    elif callback.data == 'back_to_competition':

        bot.edit_message_text(
            '🏆 Актуальные конкурсы ArtFlow\n\nВыберите интересующий вас конкурс для просмотра подробной информации и подачи заявки.\n\n👇 Список доступных конкурсов:',
            callback.message.chat.id,
            callback.message.message_id, reply_markup = back_to_competition_menu())

    elif callback.data  == 'bid':
        competition_id, competition = get_current_competition(callback.message.chat.id)

        if not competition:
            bot.send_message(
                callback.message.chat.id,
                "❌ Конкурс не найден"
            )
            return

        user_data.setdefault(callback.message.chat.id, {})
        user_data[callback.message.chat.id]["selected_competition"] = competition_id

        bot.edit_message_text(
            bid_info_text(competition),
            callback.message.chat.id,
            callback.message.message_id,
        reply_markup= bid_menu()
        )

    elif callback.data == 'back_to_competition1':
        competition_id, competition = get_current_competition(callback.message.chat.id)

        if not competition:
            bot.send_message(
                callback.message.chat.id,
                "❌ Конкурс не найден"
            )
            return

        bot.edit_message_text(
            competition_text(competition),
            callback.message.chat.id,
            callback.message.message_id, reply_markup = back_to_competition1_menu())
    elif callback.data == 'apply':

        bot.edit_message_text(
            '📄 Перед подачей заявки на конкурс ArtFlow,\nВыберите интересующий вас конкурс для просмотра подробной информации и подачи заявки.\n\n👇 Список доступных конкурсов:',
            callback.message.chat.id,
            callback.message.message_id, reply_markup = apply_menu())
    elif callback.data == 'rules':
        competition_id, competition = get_current_competition(callback.message.chat.id)

        if not competition:
            bot.send_message(
                callback.message.chat.id,
                "❌ Конкурс не найден"
            )
            return

        rules_file = competition.get("rules_file")

        if not rules_file:
            bot.send_message(
                callback.message.chat.id,
                "❌ Положение конкурса не загружено"
            )
            return

        try:
            with open(rules_file, 'rb') as file:
                bot.send_document(
                    callback.message.chat.id,
                    file,
                    caption=f'📄 Положение конкурса "{escape(competition.get("title") or "")}"'
                )
        except FileNotFoundError:
            bot.send_message(
                callback.message.chat.id,
                "❌ Файл положения не найден"
            )



    elif callback.data=='registration':
        competition_id, competition = get_current_competition(callback.message.chat.id)

        if not competition:
            bot.send_message(
                callback.message.chat.id,
                "❌ Конкурс не найден"
            )
            return

        user_data[callback.message.chat.id] = {
            "participants": [],
            "current_participant": 1,
            "music_file_id": None,
            "music_file_name": "Не используется",
            "selected_competition": competition_id,
            "competition_name": competition.get("title"),
            "competition_date": competition.get("date")
        }

        bot.send_message(
            callback.message.chat.id,
            "🏙 Шаг 1 из 12\nВведите город:"
        )

        bot.register_next_step_handler(callback.message, city)



    elif callback.data.startswith("age_"):

        user_id = callback.message.chat.id

        ages = {
            "age_3_4": "Малыши 3-4",
            "age_5_6": "Дошкольная 5-6",
            "age_7_9": "Младшая 7-9",
            "age_10_14": "Средняя 10-14",
            "age_15_18": "Старшая 15-18",
        }

        user_data[user_id]["age"] = ages[callback.data]

        bot.send_message(
            user_id, "⏱️ Шаг 7 из 12\nВведите хронометраж выступления (в минутах):"
        )

        bot.register_next_step_handler(
            callback.message,
            performance_time
        )


    elif callback.data.startswith("genre_"):

        user_id = callback.message.chat.id

        genres = {
            "genre_1": "Хореография",
            "genre_2": "Вокал",
            "genre_3": "Инструментальный",
        }

        user_data[user_id]["genre"] = genres[callback.data]

        bot.send_message(
            user_id,
            "👥 Шаг 5 из 12\nВведите количество участников в номере"
        )

        bot.register_next_step_handler(callback.message, number_of_participants)



    elif callback.data  == 'confirm_reg':
        if callback.message.chat.id not in user_data:
            bot.send_message(
                callback.message.chat.id, "❌ Данные заявки не найдены. Пожалуйста, заполните заявку заново."
            )
            return

        data = user_data[callback.message.chat.id]

        from database import get_connection

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            '''
            INSERT INTO ArtFlow_bid (telegram_id,
                                     city,
                                     name_team,
                                     number_name,
                                     number_genre,
                                     number_of_participants,
                                     age,
                                     performance_time,
                                     SFP_supervisor,
                                     WhatsApp_number,
                                     email,
                                     music_file_id,
                                     music_file_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            ''',
            (
                callback.message.chat.id,
                data['city'],
                data['team'],
                data['name'],
                data['genre'],
                data['participant_count'],
                data['age'],
                data['performance_time'],
                data['supervisor'],
                data['WhatsApp'],
                data['email'],
                data['music_file_id'],
                data['music_file_name']
            )
        )

        bid_id = cur.fetchone()[0]


        for participant in data['participants']:
            cur.execute("""
                        INSERT INTO participants (bid_id, participant_name)
                        VALUES (%s, %s)
                        """, (bid_id, participant))

        conn.commit()
        cur.close()
        conn.close()
        end_registration(callback.message)

        user_data.pop(callback.message.chat.id, None)

    elif callback.data == "my_requests":

        requests = get_user_requests(
            callback.message.chat.id
        )

        if not requests:
            bot.send_message(callback.message.chat.id, "📋 У вас пока нет заявок")
            return

        request = requests[0]
        participants = get_participants(request[0])
        participants_text = "\n".join(
            f"• {participant[0]}"
            for participant in participants
        )
        bot.send_message(
                callback.message.chat.id,
                f"""📋 Заявка №{request[0]}

📊 Статус: {request[12]}

🏙 Город: {request[2]}
🏫 Коллектив: {request[3]}
🎵 Номер: {request[4]}
🎭 Жанр: {request[5]}
👥 Участников: {request[6]} чел.
🎂 Возрастная категория: {request[7]}        
⏱️ Хронометраж {request[8]} мин.
👨‍🏫 Руководитель: {request[9]}
📞 WhatsApp: {request[10]}
📧 E-mail: {request[11]} 
🎵 Музыкальный файл: {request[15]}       
    """, reply_markup = request_navigation(1, len(requests)
        )
        )
    elif callback.data.startswith("request_page_"):

        page = int(callback.data.split("_")[-1])

        requests  = get_user_requests(callback.message.chat.id)

        if not requests:
            bot.send_message(callback.message.chat.id, "📋 У вас пока нет заявок")
            return

        if page > len(requests):
            page = len(requests)

        if page < 1:
            page = 1

        request = requests[page - 1]
        participants = get_participants(request[0])
        participants_text = "\n".join(
            f"• {participant[0]}"
            for participant in participants
        )
        bot.edit_message_text(
            f"""📋 Заявка №{request[0]}

📊 Статус: {request[12]}

🏙 Город: {request[2]}
🏫 Коллектив: {request[3]}
🎵 Номер: {request[4]}
🎭 Жанр: {request[5]}
👥 Участников: {request[6]} чел.
🎂 Возрастная категория: {request[7]}        
⏱️ Хронометраж {request[8]} мин.
👨‍🏫 Руководитель: {request[9]}
📞 WhatsApp: {request[10]}
📧 E-mail: {request[11]}
🎵 Музыкальный файл: {request[15]}        
    """,    callback.message.chat.id,
            callback.message.message_id,
            reply_markup = request_navigation(page, len(requests)
        )
    )

    elif callback.data == "contact":
        bot.edit_message_text(
            """📞 Связаться с организаторами

Выберите организатора, с которым хотите связаться:

👩 Елена
📋 Организационные вопросы
📝 Подача заявок
💳 Оплата участия

👩‍🦰 Мария
🎭 Конкурсная программа
📅 Расписание мероприятий
🏆 Награждение участников

👇 Нажмите на нужную кнопку ниже.""",
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup = contact_menu()
        )

    elif callback.data == "faq":
        bot.edit_message_text(
            """❓ Часто задаваемые вопросы

В этом разделе собраны ответы на самые популярные вопросы участников и руководителей коллективов.

Если вы не нашли нужную информацию, вы всегда можете связаться с организаторами конкурса через соответствующий раздел меню.

👇 Выберите интересующий вас вопрос:""",
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup = faq_menu()
        )



    elif callback.data.startswith("faq_") and callback.data.split("_")[-1].isdigit():
        faq_id = int(callback.data.split("_")[-1])
        faq = get_faq_by_id(faq_id)

        if not faq:
            bot.send_message(
                callback.message.chat.id,
                "❌ Вопрос не найден"
            )
            return

        bot.send_message(
            callback.message.chat.id,
            f"{escape(faq[1] or '')}\n\n💬 {escape(faq[2] or '')}"
        )

    elif callback.data == "wa_1":
        bot.send_message(
            callback.message.chat.id,
            f"📞 Елена Фляум: {WhatsApp['wa_1']['number']}"
        )

    elif callback.data == "wa_2":
        bot.send_message(
            callback.message.chat.id,
            f"📞 Марина Михаиловна: {WhatsApp['wa_2']['number']}"
        )

    elif callback.data == "em":
        bot.send_message(
            callback.message.chat.id,
            "lemani1974@mail.ru"
        )

    elif callback.data.startswith("faqpage_"):
        page = int(callback.data.split("_")[-1])

        bot.edit_message_text(
            """❓ Часто задаваемые вопросы

В этом разделе собраны ответы на самые популярные вопросы участников и руководителей коллективов.

Если вы не нашли нужную информацию, вы всегда можете связаться с организаторами конкурса через соответствующий раздел меню.

👇 Выберите интересующий вас вопрос:""",
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=faq_page_menu(page)
        )

    elif callback.data == "contact_1":
        bot.edit_message_text(
            """👩 Елена Фляум

По всем организационным вопросам вы можете обратиться к Елене.

Она поможет вам, если необходимо:

📋 Подать заявку на конкурс
💳 Получить информацию об оплате
📄 Уточнить статус вашей заявки
📞 Получить консультацию по участию

👇 Выберите удобный способ связи:""",
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=contact_menu1()
        )

    elif callback.data == 'contact_2':
        bot.edit_message_text(
            """👩‍🦰 Мария

По вопросам проведения конкурса вы можете обратиться к Марии.

Она поможет вам, если необходимо:

🎭 Уточнить конкурсную программу
📅 Узнать расписание конкурса
🏆 Получить информацию о награждении
❓ Задать вопросы по проведению мероприятия

👇 Выберите удобный способ связи:""",
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup = contact_menu2()
        )

    elif callback.data == 'back_to_contact':
        bot.edit_message_text(
            """📞 Связаться с организаторами

Выберите организатора, с которым хотите связаться:

👩 Елена
📋 Организационные вопросы
📝 Подача заявок
💳 Оплата участия

👩‍🦰 Мария
🎭 Конкурсная программа
📅 Расписание мероприятий
🏆 Награждение участников

👇 Нажмите на нужную кнопку ниже.""",
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=contact_menu()
        )
    elif callback.data == 'admin_competitions':
        if not admin_check(callback.message):
            return

        bot.edit_message_text(
            admin_competitions_text(),
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=admin_competitions_menu()
        )

    elif callback.data == 'admin_add_competition':
        if not admin_check(callback.message):
            return

        msg = bot.send_message(
            callback.message.chat.id,
            "🏆 Введите название конкурса:"
        )
        bot.register_next_step_handler(msg, admin_add_competition_title)

    elif callback.data == 'admin_change_competition':
        if not admin_check(callback.message):
            return

        msg = bot.send_message(
            callback.message.chat.id,
            "✏️ Введите ID конкурса для изменения:"
        )
        bot.register_next_step_handler(msg, admin_change_competition_id)

    elif callback.data == 'admin_delete_competition':
        if not admin_check(callback.message):
            return

        msg = bot.send_message(
            callback.message.chat.id,
            "🗑 Введите ID конкурса для удаления:"
        )
        bot.register_next_step_handler(msg, admin_delete_competition_id)

    elif callback.data == 'admin_faq':
        if not admin_check(callback.message):
            return

        bot.edit_message_text(
            admin_faq_text(get_all_faq()),
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=admin_faq_menu()
        )

    elif callback.data == 'admin_add_faq':
        if not admin_check(callback.message):
            return

        msg = bot.send_message(
            callback.message.chat.id,
            "❓ Введите новый вопрос:"
        )
        bot.register_next_step_handler(msg, admin_add_faq_question)

    elif callback.data == 'admin_change_faq':
        if not admin_check(callback.message):
            return

        msg = bot.send_message(
            callback.message.chat.id,
            "✏️ Введите ID вопроса для изменения:"
        )
        bot.register_next_step_handler(msg, admin_change_faq_id)

    elif callback.data == 'admin_delete_faq':
        msg = bot.send_message(
            callback.message.chat.id,
            "🗑 Введите ID вопроса для удаления:"
        )
        bot.register_next_step_handler(msg, admin_delete_faq_id)

    elif callback.data == 'admin_spam':
        msg = bot.send_message(
            callback.message.chat.id,
            "📤 Отправьте сообщение для рассылки:"
        )
        bot.register_next_step_handler(msg, admin_send_spam)

    elif callback.data == 'admin_add_admin':
        msg = bot.send_message(
            callback.message.chat.id,
            "👱‍♂️ Введите Telegram ID администратора:"
        )
        bot.register_next_step_handler(msg, admin_add_admin_id)

    elif callback.data == 'admin_delete_admin':
        msg = bot.send_message(
            callback.message.chat.id,
            "🗑 Введите Telegram ID администратора:"
        )
        bot.register_next_step_handler(msg, admin_delete_admin_id)

    elif callback.data == 'admin_list_admins':
        bot.send_message(
            callback.message.chat.id,
            admin_list_text(),
            reply_markup=admin_requests_menu()
        )

    elif callback.data == 'admin_choice_request':
        excel_file = create_requests_excel()

        if not excel_file:
            bot.send_message(
                callback.message.chat.id,
                "📋 пока нет заявок"
            )
            return

        bot.send_document(
            callback.message.chat.id,
            excel_file,
            caption="📄 Выгрузка заявок ArtFlow"
        )

    elif callback.data == 'admin_search':

        bot.edit_message_text("🔎 Выберите вариант поиска заявки",
                              callback.message.chat.id,
                              callback.message.message_id,
                              reply_markup = admin_search_menu())

    elif callback.data == "admin_search_id":
        msg = bot.send_message(
            callback.message.chat.id,
            "🆔 Введите ID заявки:"
        )
        bot.register_next_step_handler(msg, admin_search_request_by_id)

    elif callback.data == "admin_search_email":
        msg = bot.send_message(
            callback.message.chat.id,
            "📧 Введите e-mail:"
        )
        bot.register_next_step_handler(msg, admin_search_request_by_email)

    elif callback.data == "admin_search_whatsapp":
        msg = bot.send_message(
            callback.message.chat.id,
            "📱 Введите WhatsApp:\n\nМожно писать так:\n+7 702 394 12 34\n87023941234\n77023941234"
        )
        bot.register_next_step_handler(msg, admin_search_request_by_whatsapp)

    elif callback.data == 'admin_participants_search':
        msg = bot.send_message(
            callback.message.chat.id,
            "🔍 Введите ФИО участника или его часть:"
        )

        bot.register_next_step_handler(msg, admin_search_participant)


    elif callback.data == 'admin_requests':
        requests = get_all_requests()

        if not requests:
            bot.send_message(
                callback.message.chat.id,
                "📋 пока нет заявок"
            )
            return
        request = requests[0]
        participants = get_participants(request[0])
        participants_text = "\n".join(
            f"• {participant[0]}"
            for participant in participants
        )
        bot.edit_message_text(
            f"""📋 Заявка №{request[0]}
🏙 Город: {request[2]}
🏫 Коллектив: {request[3]}
🎵 Номер: {request[4]}
🎭 Жанр: {request[5]}
👥 Участников: {request[6]} чел.
🎂 Возрастная категория: {request[7]}        
⏱️ Хронометраж {request[8]} мин.
👨‍🏫 Руководитель: {request[9]}
📞 WhatsApp: {request[10]}
📧 E-mail: {request[11]}    
🎵 Музыкальный файл: {request[15]}    

📊 Статус: {request[12]}
    """,
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=admin_requests_menu_menu(1, len(requests))
        )
    elif callback.data.startswith("admin_request_page_"):
        page = int(callback.data.split("_")[-1])

        requests = get_all_users_requests()

        if not requests:
            bot.send_message(callback.message.chat.id, "📋 У вас пока нет заявок")
            return

        if page > len(requests):
            page = len(requests)

        if page < 1:
            page = 1

        request = requests[page-1]



        participants = get_participants(request[0])
        participants_text = "\n".join(
            f"• {participant[0]}"
            for participant in participants
        )
        bot.edit_message_text(
            f"""📋 Заявка №{request[0]}
🏙 Город: {request[2]}
🏫 Коллектив: {request[3]}
🎵 Номер: {request[4]}
🎭 Жанр: {request[5]}
👥 Участников: {request[6]} чел.
🎂 Возрастная категория: {request[7]}        
⏱️ Хронометраж {request[8]} мин.
👨‍🏫 Руководитель: {request[9]}
📞 WhatsApp: {request[10]}
📧 E-mail: {request[11]}        
🎵 Музыкальный файл: {request[15]}

📊 Статус: {request[12]}
    """, callback.message.chat.id,
            callback.message.message_id,
            reply_markup=admin_request_navigation(page, len(requests)
                                            )
        )
    elif callback.data.startswith("admin_open_request_"):
        request_id = int(callback.data.split("_")[-1])
        request = get_request_by_id(request_id)

        if not request:
            bot.send_message(
                callback.message.chat.id,
                "❌ Заявка не найдена"
            )
            return

        bot.edit_message_text(
            admin_request_text(request),
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=admin_requests_menu_menu(1, 1)
        )
    elif callback.data == "admin_stats":
        stat1 = 0
        stat2 = 0
        stat3 = 0
        stat4 = 0
        genre1 = 0
        genre2 = 0
        genre3 = 0

        count = all_count()
        part_count = all_participants()
        requests_data = requests_status()
        today = request_time(1)
        week = request_time(7)
        month = request_time(30)

        for request in requests_data:
            status = request[12]

            if status.lower() == "на рассмотрении":
                stat1 += 1
            elif status.lower().strip() == "подтверждено":
                stat2 += 1
            elif status.lower().strip() == "отклонено":
                stat3 += 1
            elif status.lower() == "ожидает оплаты":
                stat4 += 1
            else:
                print("Неизвестный статус:", status)

        for request in requests_data:
            genre = request[5]


            if genre.lower() == "хореография":
                genre1 += 1
            elif genre.lower() == "вокал":
                genre2 += 1
            elif genre.lower() == "инструментальный":
                genre3 += 1
            else:
                print("Неизвестный статус:", genre)





        bot.edit_message_text(
            f"""
            📊 Статистика ArtFlow

📋 Всего заявок: {count}
👥 Всего участников: {part_count}

🟡 На рассмотрении: {stat1}
🟢 Подтверждено: {stat2}
🔴 Отклонено: {stat3}
💳 Ожидает оплаты: {stat4}

━━━━━━━━━━━━━━

🎭 По жанрам
• Хореография — {genre1}
• Вокал — {genre2}
• Инструментальное — {genre3}

━━━━━━━━━━━━━━

📅 За сегодня: {today} заявки
📅 За неделю: {week} заявок
📅 За месяц: {month} заявки
            """,


            callback.message.chat.id,
            callback.message.message_id,
            reply_markup = admin_stats_menu()
        )
    elif callback.data == "back_to_admin_info":
        bot.edit_message_text(

            "🛠 Панель администратора",
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=admin_requests_menu()
        )


    elif callback.data.startswith("mus_"):

        user_id = callback.message.chat.id

        if callback.data.endswith("yes"):
            msg = bot.send_message(user_id, "🎵 Прикрепите музыкальный файл")
            bot.register_next_step_handler(msg, music_file)
        elif callback.data.endswith("no"):
            user_data[user_id]["music_file_id"] = None
            user_data[user_id]["music_file_name"] = "Не используется"
            exit_registration(callback.message)



    elif callback.data == 'admin_delete_request':
        request_id = get_admin_request_id(callback.message.text)

        if not request_id:
            bot.send_message(
                callback.message.chat.id,
                "❌ Не удалось определить ID заявки"
            )
            return

        request = get_request_by_id(request_id)

        if not request:
            bot.send_message(
                callback.message.chat.id,
                "❌ Заявка не найдена"
            )
            return

        delete_request(request_id)

        bot.edit_message_text(
            f"🗑 Заявка №{request_id} удалена",
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=admin_requests_menu()
        )

    elif callback.data == 'admin_save_music':
        request_id = get_admin_request_id(callback.message.text)

        if not request_id:
            bot.send_message(
                callback.message.chat.id,
                "❌ Не удалось определить ID заявки"
            )
            return

        request = get_request_by_id(request_id)

        if not request:
            bot.send_message(
                callback.message.chat.id,
                "❌ Заявка не найдена"
            )
            return

        if not request[14]:
            bot.send_message(
                callback.message.chat.id,
                "❌ Музыкальный файл не прикреплен"
            )
            return

        try:
            bot.send_document(
                callback.message.chat.id,
                request[14],
                caption=f"🎵 Музыкальный файл заявки №{request_id}\n{request[15]}"
            )
        except Exception:
            try:
                bot.send_audio(
                    callback.message.chat.id,
                    request[14],
                    caption=f"🎵 Музыкальный файл заявки №{request_id}\n{request[15]}"
                )
            except Exception:
                try:
                    file_info = bot.get_file(request[14])
                    downloaded_file = bot.download_file(file_info.file_path)
                    music_file_obj = BytesIO(downloaded_file)
                    music_file_obj.name = request[15] or f"music_{request_id}"

                    bot.send_document(
                        callback.message.chat.id,
                        music_file_obj,
                        caption=f"🎵 Музыкальный файл заявки №{request_id}\n{request[15]}"
                    )
                except Exception:
                    bot.send_message(
                        callback.message.chat.id,
                        "❌ Не удалось отправить музыкальный файл"
                    )

    elif callback.data == 'admin_change_status':
        request_id = get_admin_request_id(callback.message.text)

        if not request_id:
            bot.send_message(
                callback.message.chat.id,
                "❌ Не удалось определить ID заявки"
            )
            return

        bot.edit_message_reply_markup(
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=admin_status_menu(request_id)
        )

    elif callback.data.startswith("admin_status_"):
        status_list = {
            "review": "На рассмотрении",
            "approved": "Подтверждено",
            "rejected": "Отклонено",
            "payment": "Ожидает оплаты"
        }

        try:
            _, _, request_id, status_key = callback.data.split("_")
            request_id = int(request_id)
        except ValueError:
            bot.send_message(callback.message.chat.id, "❌ Ошибка статуса")
            return

        status = status_list.get(status_key)

        if not status:
            bot.send_message(
                callback.message.chat.id,
                "❌ Неизвестный статус"
            )
            return

        update_request_status(request_id, status)
        request = get_request_by_id(request_id)

        if not request:
            bot.send_message(
                callback.message.chat.id,
                "❌ Заявка не найдена"
            )
            return

        bot.edit_message_text(
            admin_request_text(request),
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=admin_requests_menu_menu(1, 1)
        )
