import logging
from html import escape as html_escape
from io import BytesIO
import math
import re
from telebot import types
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from loader import bot
from keyboards.user_keyboards import request_navigation
from keyboards.admin_keyboards import admin_requests_menu_menu, admin_request_navigation, admin_requests_menu, admin_status_menu, admin_search_menu
from database import get_user_requests, get_participants, get_all_requests, get_all_users_requests, get_request_by_id, delete_request, update_request_status, search_request_by_id, search_request_by_email, search_request_by_whatsapp, search_request_by_participant, get_competitions_for_requests_export, get_requests_for_excel, get_competition_by_id
from callbacks.admin_callbacks import admin_check


logger = logging.getLogger(__name__)
EXPORT_COMPETITIONS_PER_PAGE = 8


def admin_request_text(request):
    participants = get_participants(request[0])
    participants_text = "\n".join(
        f"• {participant[0]}"
        for participant in participants
    )

    if not participants_text:
        participants_text = "—"

    return f"""📋 Заявка №{request[0]}
    🏆 Конкурс: {request[17] or "Не указан"}
    
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


def safe_caption_text(value):
    value = re.sub(r"[\r\n]+", " ", str(value or "")).strip()

    if not value:
        return "Без названия"

    return value


def format_export_competition_button_text(competition):
    name = safe_caption_text(competition.get("name") or "Без названия")
    count = competition.get("requests_count") or 0
    label = f"🏆 {competition.get('id')}. {name} ({count})"

    if len(label) > 60:
        label = f"{label[:57]}..."

    return label


def export_competitions_total_pages(competitions):
    return max(1, math.ceil(len(competitions) / EXPORT_COMPETITIONS_PER_PAGE))


def normalize_export_page(page, competitions):
    total_pages = export_competitions_total_pages(competitions)

    if not isinstance(page, int) or isinstance(page, bool):
        page = 1

    if page < 1:
        page = 1

    if page > total_pages:
        page = total_pages

    return page, total_pages


def admin_export_competitions_menu(competitions, page=1):
    page, total_pages = normalize_export_page(page, competitions)
    markup = types.InlineKeyboardMarkup()
    start = (page - 1) * EXPORT_COMPETITIONS_PER_PAGE
    end = start + EXPORT_COMPETITIONS_PER_PAGE

    markup.add(
        types.InlineKeyboardButton(
            "📚 Все конкурсы",
            callback_data="admin_export_all"
        )
    )

    for competition in competitions[start:end]:
        markup.add(
            types.InlineKeyboardButton(
                format_export_competition_button_text(competition),
                callback_data=f"admin_export_competition_{competition.get('id')}"
            )
        )

    markup.row(
        types.InlineKeyboardButton(
            "⬅️",
            callback_data=f"admin_export_page_{page - 1}" if page > 1 else "admin_export_noop"
        ),
        types.InlineKeyboardButton(
            f"Страница {page}/{total_pages}",
            callback_data="admin_export_noop"
        ),
        types.InlineKeyboardButton(
            "➡️",
            callback_data=f"admin_export_page_{page + 1}" if page < total_pages else "admin_export_noop"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "🔙 Назад",
            callback_data="back_to_admin_info"
        )
    )

    return markup


def admin_export_competitions_text(competitions, page=1):
    page, total_pages = normalize_export_page(page, competitions)
    return f"📄 Выберите конкурс для выгрузки заявок:\n\nСтраница {page}/{total_pages}"


def parse_admin_export_competition_callback(callback_data):
    prefix = "admin_export_competition_"

    if not callback_data.startswith(prefix):
        return None

    value = callback_data[len(prefix):]

    if not value.isdigit():
        return None

    competition_id = int(value)

    if competition_id <= 0:
        return None

    return competition_id


def parse_admin_export_page_callback(callback_data):
    prefix = "admin_export_page_"

    if not callback_data.startswith(prefix):
        return None

    value = callback_data[len(prefix):]

    if not value.isdigit():
        return None

    page = int(value)

    if page <= 0:
        return None

    return page


def sanitize_excel_cell(value):
    if not isinstance(value, str):
        return value

    stripped = value.lstrip()

    if stripped.startswith(("=", "+", "-", "@")):
        return f"'{value}"

    return value


def requests_excel_filename(competition_id=None):
    if competition_id is None:
        return "artflow_requests_all.xlsx"

    return f"artflow_requests_competition_{competition_id}.xlsx"


def create_requests_excel(requests, competition_id=None):
    if not requests:
        return None

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Заявки"

    headers = [
        "ID",
        "Конкурс ID",
        "Конкурс",
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
        participants_text = "\n".join(
            str(sanitize_excel_cell(participant))
            for participant in (request.get("participants") or [])
        )

        sheet.append([
            request.get("id"),
            request.get("competition_id"),
            sanitize_excel_cell(request.get("competition_name")),
            request.get("telegram_id"),
            sanitize_excel_cell(request.get("city")),
            sanitize_excel_cell(request.get("name_team")),
            sanitize_excel_cell(request.get("number_name")),
            sanitize_excel_cell(request.get("number_genre")),
            request.get("number_of_participants"),
            sanitize_excel_cell(request.get("age")),
            request.get("performance_time"),
            sanitize_excel_cell(request.get("SFP_supervisor")),
            sanitize_excel_cell(request.get("WhatsApp_number")),
            sanitize_excel_cell(request.get("email")),
            sanitize_excel_cell(request.get("status")),
            request.get("create_at"),
            sanitize_excel_cell(request.get("music_file_name")),
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
        "P": 38,
        "Q": 32,
        "R": 38
    }

    for column, width in widths.items():
        sheet.column_dimensions[column].width = width

    sheet.freeze_panes = "A2"

    excel_file = BytesIO()
    workbook.save(excel_file)
    excel_file.seek(0)
    excel_file.name = requests_excel_filename(competition_id)

    return excel_file


def safe_competition_name_for_html_message(competition):
    return html_escape(
        safe_caption_text(competition.get("title") or competition.get("name")),
        quote=True
    )


def build_export_caption(requests_count, competition=None):
    if competition is None:
        return f"📄 Все заявки ArtFlow\n\n📋 Количество заявок: {requests_count}"

    competition_name = safe_competition_name_for_html_message(competition)
    return f"📄 Заявки конкурса\n\n🏆 {competition_name}\n📋 Количество заявок: {requests_count}"


def empty_export_message(competition=None):
    if competition is None:
        return "📋 Заявок пока нет."

    competition_name = safe_competition_name_for_html_message(competition)
    return f"📋 На конкурс “{competition_name}” пока нет заявок."

def send_requests_excel(callback, competition_id=None):
    competition = None
    excel_file = None

    try:
        if competition_id is not None:
            competition = get_competition_by_id(f"competition_{competition_id}")

            if not competition:
                bot.send_message(
                    callback.message.chat.id,
                    "❌ Конкурс не найден."
                )
                return

        requests = get_requests_for_excel(competition_id)

        if not requests:
            bot.send_message(
                callback.message.chat.id,
                empty_export_message(competition)
            )
            return

        excel_file = create_requests_excel(requests, competition_id)

        if not excel_file:
            bot.send_message(
                callback.message.chat.id,
                empty_export_message(competition)
            )
            return

        bot.send_document(
            callback.message.chat.id,
            excel_file,
            caption=build_export_caption(len(requests), competition)
        )
    except Exception:
        logger.exception(
            "Admin requests Excel export failed: competition_id=%s",
            competition_id
        )
        bot.send_message(
            callback.message.chat.id,
            "❌ Не удалось создать Excel-файл. Попробуйте позже."
        )
    finally:
        if excel_file is not None:
            excel_file.close()

def admin_request_func(callback):
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
        🏆 Конкурс: {request[17] or "Не указан"}
        
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


def admin_request_page_func(callback):
    page = int(callback.data.split("_")[-1])

    requests = get_all_users_requests()

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

    requests = search_request_by_participant(participant_name)

    admin_send_found_requests(
        message,
        requests,
        "🔍 Результаты поиска участника"
    )


@bot.callback_query_handler(func=lambda callback: (
    callback.data in (
        "my_requests",
        "admin_choice_request",
        "admin_search",
        "admin_search_id",
        "admin_search_email",
        "admin_search_whatsapp",
        "admin_participants_search",
        "admin_requests",
        "admin_delete_request",
        "admin_save_music",
        "admin_change_status",
        "admin_export_all",
        "admin_export_noop",
    )
    or callback.data.startswith("request_page_")
    or callback.data.startswith("request_participants_")
    or callback.data.startswith("admin_request_page_")
    or callback.data.startswith("admin_open_request_")
    or callback.data.startswith("admin_export_competition_")
    or callback.data.startswith("admin_export_page_")
    or callback.data.startswith("admin_status_")
))
def requests_callback_message(callback):
    bot.answer_callback_query(callback.id)
    if callback.data.startswith("admin") or callback.data == "back_to_admin_info":
        if not admin_check(callback.message):
            return

    if callback.data == "my_requests":

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
                🏆 Конкурс: {request[17] or "Не указан"}

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
            🏆 Конкурс: {request[17] or "Не указан"}

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



    elif callback.data.startswith("request_participants_"):
        page = int(callback.data.split("_")[-1])

        requests = get_user_requests(callback.message.chat.id)

        if not requests:
            bot.send_message(callback.message.chat.id, "📋 У вас пока нет заявок")
            return

        if page > len(requests):
            page = len(requests)

        if page < 1:
            page = 1

        request = requests[page - 1]

        participants = get_participants(request[0])

        if not participants:
            participants_text = "Участники не указаны"
        else:
            participants_text = "\n".join(
                f"• {participant[0]}"
                for participant in participants
            )

        bot.send_message(
            callback.message.chat.id,
            f"""👥 Участники заявки №{request[0]}

    {participants_text}"""
        )



    elif callback.data == 'admin_choice_request':
        competitions = get_competitions_for_requests_export()

        if not competitions:
            bot.send_message(
                callback.message.chat.id,
                "🏆 Конкурсов пока нет"
            )
            return

        bot.edit_message_text(
            admin_export_competitions_text(competitions, 1),
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=admin_export_competitions_menu(competitions, 1)
        )

    elif callback.data.startswith("admin_export_page_"):
        page = parse_admin_export_page_callback(callback.data) or 1
        competitions = get_competitions_for_requests_export()

        if not competitions:
            bot.send_message(
                callback.message.chat.id,
                "🏆 Конкурсов пока нет"
            )
            return

        bot.edit_message_text(
            admin_export_competitions_text(competitions, page),
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=admin_export_competitions_menu(competitions, page)
        )

    elif callback.data == "admin_export_noop":
        return

    elif callback.data == "admin_export_all":
        send_requests_excel(callback)

    elif callback.data.startswith("admin_export_competition_"):
        competition_id = parse_admin_export_competition_callback(callback.data)

        if not competition_id:
            bot.send_message(
                callback.message.chat.id,
                "❌ Не удалось определить конкурс для выгрузки."
            )
            return

        send_requests_excel(callback, competition_id)
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
        admin_request_func(callback)

    elif callback.data.startswith("admin_request_page_"):
        admin_request_page_func(callback)

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

        if not request[14] or request[14] == 'Не используется':
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
