from datetime import datetime
from html import escape
from loader import bot
from storage import user_data
from keyboards.user_keyboards import competition_menu, competition_1_menu, back_to_competition_menu, bid_menu, back_to_competition1_menu, apply_menu
from keyboards.admin_keyboards import admin_competitions_menu, admin_competition_web_confirm_menu, admin_competition_publication_menu
from callbacks.admin_callbacks import admin_check
from competition_messages import competition_text
from database import (
    get_all_competitions,
    get_competition_by_id,
    add_competition,
    update_competition,
    delete_competition,
    competitions_web_columns_ready,
    get_competition_web_data_by_id,
    update_competition_web_data_by_id,
    set_competition_publication_by_id
)


WEB_SCHEMA_NOT_READY_MESSAGE = (
    "Веб-поля базы данных ещё не подготовлены. Сначала необходимо применить "
    "миграцию 001_add_web_fields_to_competitions.sql."
)

WEB_CANCEL_WORD = "отмена"
WEB_KEEP_WORD = "оставить"
WEB_SKIP_WORD = "пропустить"
WEB_CLEAR_WORD = "очистить"

WEB_DATA_FIELDS = (
    ("event_date", "Дата проведения", "date", True),
    ("application_deadline", "Дедлайн подачи заявок", "date", True),
    ("city", "Город", "text", True),
    ("short_description", "Краткое описание", "text", True),
    ("directions", "Направления", "text", True),
    ("poster_url", "Ссылка на афишу", "url", False),
    ("rules_url", "Ссылка на положение", "url", False),
)

WEB_REQUIRED_FOR_PUBLICATION = (
    ("event_date", "Дата проведения"),
    ("application_deadline", "Дедлайн подачи заявок"),
    ("city", "Город"),
    ("short_description", "Краткое описание"),
    ("directions", "Направления"),
)


def get_current_competition(user_id):
    competition_id = "competition_1"

    if user_id in user_data:
        competition_id = user_data[user_id].get("selected_competition", competition_id)

    competitions = get_all_competitions()

    if competition_id not in competitions and competitions:
        competition_id = next(iter(competitions))

    return competition_id, competitions.get(competition_id)


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
    competitions = get_all_competitions()

    if not competitions:
        return "🏆 Конкурсов пока нет\n\nДобавьте первый конкурс через админ-панель."

    text = "🏆 Конкурсы\n\n"

    for competition_id, competition in competitions.items():
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

    for competition_id in get_all_competitions():
        number = competition_id.split("_")[-1]

        if number.isdigit():
            numbers.append(int(number))

    return f"competition_{max(numbers, default=0) + 1}"


def clear_admin_web_state(chat_id):
    if chat_id in user_data:
        user_data[chat_id].pop("admin_competition_web", None)
        user_data[chat_id].pop("admin_competition_publication", None)


def send_admin_competitions_panel(chat_id, message_text=None):
    if message_text:
        bot.send_message(chat_id, message_text)

    try:
        bot.send_message(
            chat_id,
            admin_competitions_text(),
            reply_markup=admin_competitions_menu()
        )
    except Exception as e:
        print(f"Ошибка показа меню конкурсов: {e}")
        bot.send_message(
            chat_id,
            "Выберите действие:",
            reply_markup=admin_competitions_menu()
        )


def handle_admin_web_error(chat_id, context, error):
    print(f"Ошибка web-сценария конкурсов ({context}): {error}")
    clear_admin_web_state(chat_id)
    send_admin_competitions_panel(
        chat_id,
        "❌ Не удалось выполнить действие. Попробуйте позже."
    )


def admin_web_schema_ready(chat_id):
    try:
        is_ready = competitions_web_columns_ready()
    except Exception as e:
        handle_admin_web_error(chat_id, "проверка схемы", e)
        return False

    if not is_ready:
        clear_admin_web_state(chat_id)
        send_admin_competitions_panel(chat_id, WEB_SCHEMA_NOT_READY_MESSAGE)
        return False

    return True


def parse_positive_int(text):
    if not text.isdigit():
        return None

    value = int(text)

    if value <= 0:
        return None

    return value


def is_cancel_text(message):
    return message.content_type == "text" and message.text.strip().lower() == WEB_CANCEL_WORD


def cancel_admin_web_action(chat_id):
    clear_admin_web_state(chat_id)
    send_admin_competitions_panel(chat_id, "❌ Действие отменено.")


def format_web_value(value):
    if value is None or value == "":
        return "Не указано"

    if hasattr(value, "strftime"):
        return value.strftime("%d.%m.%Y")

    return str(value)


def publication_status_text(is_published):
    if is_published:
        return "опубликован"

    return "не опубликован"


def web_data_text(web_data, title="🌐 Данные конкурса для сайта"):
    return f"""{title}

ID: {web_data.get("id")}
Название: {escape(format_web_value(web_data.get("name")))}
Дата проведения: {escape(format_web_value(web_data.get("event_date")))}
Дедлайн подачи заявок: {escape(format_web_value(web_data.get("application_deadline")))}
Город: {escape(format_web_value(web_data.get("city")))}
Краткое описание: {escape(format_web_value(web_data.get("short_description")))}
Направления: {escape(format_web_value(web_data.get("directions")))}
Ссылка на афишу: {escape(format_web_value(web_data.get("poster_url")))}
Ссылка на положение: {escape(format_web_value(web_data.get("rules_url")))}
Статус публикации: {publication_status_text(web_data.get("is_published"))}"""


def get_field_prompt(field):
    key, label, field_type, required = field
    hint = "Введите значение"

    if field_type == "date":
        hint = "Введите дату в формате ДД.ММ.ГГГГ"
    elif field_type == "url":
        hint = "Введите ссылку, начинающуюся с http:// или https://"

    extra = f"Можно написать «{WEB_KEEP_WORD}», чтобы сохранить текущее значение."

    if not required:
        extra += f"\nДля пустого значения напишите «{WEB_SKIP_WORD}» или «{WEB_CLEAR_WORD}»."

    extra += f"\nДля отмены напишите «{WEB_CANCEL_WORD}»."

    return key, label, hint, extra


def prompt_admin_web_data_field(chat_id):
    state = user_data.get(chat_id, {}).get("admin_competition_web")

    if not state:
        send_admin_competitions_panel(
            chat_id,
            "❌ Сценарий редактирования веб-данных не найден. Начните заново."
        )
        return

    field_index = state["field_index"]

    if field_index >= len(WEB_DATA_FIELDS):
        show_admin_web_data_preview(chat_id)
        return

    field = WEB_DATA_FIELDS[field_index]
    key, label, hint, extra = get_field_prompt(field)
    current = state["current"].get(key)

    msg = bot.send_message(
        chat_id,
        f"{label}\nТекущее значение: {escape(format_web_value(current))}\n\n{hint}.\n{extra}"
    )
    bot.register_next_step_handler(msg, admin_web_data_field_step)


def get_admin_web_data_state(chat_id):
    state = user_data.get(chat_id, {}).get("admin_competition_web")

    if not state:
        return None

    data = state["current"].copy()
    data.update(state["values"])

    return state, data


def parse_admin_web_date(text):
    try:
        return datetime.strptime(text, "%d.%m.%Y").date()
    except ValueError:
        return None


def validate_admin_web_field(chat_id, field, text):
    state, data = get_admin_web_data_state(chat_id)
    key, label, field_type, required = field
    command = text.lower()

    if command == WEB_KEEP_WORD:
        value = state["current"].get(key)

        if required and not value:
            return False, f"❌ Поле «{label}» сейчас пустое. Введите значение."

        return True, value

    if command in (WEB_SKIP_WORD, WEB_CLEAR_WORD):
        if required:
            return False, f"❌ Поле «{label}» обязательно. Введите значение."

        return True, None

    if field_type == "date":
        value = parse_admin_web_date(text)

        if not value:
            return False, "❌ Введите реальную дату в формате ДД.ММ.ГГГГ."

        if key == "application_deadline":
            event_date = data.get("event_date")

            if event_date and value > event_date:
                return False, "❌ Дедлайн подачи заявок не может быть позже даты проведения."

        return True, value

    if field_type == "url":
        if not text.lower().startswith(("http://", "https://")):
            return False, "❌ Ссылка должна начинаться с http:// или https://."

        return True, text

    if not text:
        return False, f"❌ Поле «{label}» не может быть пустым."

    return True, text


def validate_admin_web_data_for_preview(chat_id):
    state, data = get_admin_web_data_state(chat_id)

    for index, field in enumerate(WEB_DATA_FIELDS):
        key, label, field_type, required = field

        if required and not data.get(key):
            state["field_index"] = index
            bot.send_message(chat_id, f"❌ Поле «{label}» обязательно.")
            prompt_admin_web_data_field(chat_id)
            return False

    event_date = data.get("event_date")
    application_deadline = data.get("application_deadline")

    if event_date and application_deadline and application_deadline > event_date:
        state["field_index"] = 1
        bot.send_message(
            chat_id,
            "❌ Дедлайн подачи заявок не может быть позже даты проведения."
        )
        prompt_admin_web_data_field(chat_id)
        return False

    state["pending"] = data

    return True


def show_admin_web_data_preview(chat_id):
    state = user_data.get(chat_id, {}).get("admin_competition_web")

    if not state:
        send_admin_competitions_panel(
            chat_id,
            "❌ Сценарий редактирования веб-данных не найден. Начните заново."
        )
        return

    if not validate_admin_web_data_for_preview(chat_id):
        return

    bot.send_message(
        chat_id,
        web_data_text(state["pending"], "🌐 Предпросмотр данных для сайта"),
        reply_markup=admin_competition_web_confirm_menu()
    )


def admin_web_data_id_step(message):
    if not admin_check(message):
        return

    if is_cancel_text(message):
        cancel_admin_web_action(message.chat.id)
        return

    if message.content_type != "text":
        msg = bot.send_message(
            message.chat.id,
            f"❌ Введите числовой ID конкурса или напишите «{WEB_CANCEL_WORD}»."
        )
        bot.register_next_step_handler(msg, admin_web_data_id_step)
        return

    competition_number = parse_positive_int(message.text.strip())

    if competition_number is None:
        msg = bot.send_message(
            message.chat.id,
            f"❌ Введите целое положительное число или напишите «{WEB_CANCEL_WORD}»."
        )
        bot.register_next_step_handler(msg, admin_web_data_id_step)
        return

    try:
        competition = get_competition_by_id(f"competition_{competition_number}")
    except Exception as e:
        handle_admin_web_error(message.chat.id, "получение конкурса", e)
        return

    if not competition:
        msg = bot.send_message(
            message.chat.id,
            f"❌ Конкурс не найден. Введите другой числовой ID или напишите «{WEB_CANCEL_WORD}»."
        )
        bot.register_next_step_handler(msg, admin_web_data_id_step)
        return

    if not admin_web_schema_ready(message.chat.id):
        return

    try:
        web_data = get_competition_web_data_by_id(competition_number)
    except Exception as e:
        handle_admin_web_error(message.chat.id, "получение web-данных", e)
        return

    if not web_data:
        msg = bot.send_message(
            message.chat.id,
            f"❌ Конкурс не найден. Введите другой числовой ID или напишите «{WEB_CANCEL_WORD}»."
        )
        bot.register_next_step_handler(msg, admin_web_data_id_step)
        return

    user_data.setdefault(message.chat.id, {})
    user_data[message.chat.id]["admin_competition_web"] = {
        "competition_id": competition_number,
        "current": web_data,
        "values": {},
        "field_index": 0
    }

    bot.send_message(message.chat.id, web_data_text(web_data))
    prompt_admin_web_data_field(message.chat.id)


def admin_web_data_field_step(message):
    if not admin_check(message):
        return

    if is_cancel_text(message):
        cancel_admin_web_action(message.chat.id)
        return

    state = user_data.get(message.chat.id, {}).get("admin_competition_web")

    if not state:
        send_admin_competitions_panel(
            message.chat.id,
            "❌ Сценарий редактирования веб-данных не найден. Начните заново."
        )
        return

    if message.content_type != "text":
        bot.send_message(message.chat.id, "❌ Введите значение текстом.")
        prompt_admin_web_data_field(message.chat.id)
        return

    field = WEB_DATA_FIELDS[state["field_index"]]
    text = message.text.strip()
    is_valid, value_or_error = validate_admin_web_field(message.chat.id, field, text)

    if not is_valid:
        bot.send_message(message.chat.id, value_or_error)
        prompt_admin_web_data_field(message.chat.id)
        return

    key = field[0]
    state["values"][key] = value_or_error
    state["field_index"] += 1

    prompt_admin_web_data_field(message.chat.id)


def save_admin_web_data(chat_id):
    state = user_data.get(chat_id, {}).get("admin_competition_web")

    if not state or "pending" not in state:
        send_admin_competitions_panel(
            chat_id,
            "❌ Данные для сохранения не найдены. Начните заново."
        )
        return

    if not admin_web_schema_ready(chat_id):
        return

    data = state["pending"]

    try:
        count = update_competition_web_data_by_id(
            data["id"],
            data.get("event_date"),
            data.get("application_deadline"),
            data.get("city"),
            data.get("short_description"),
            data.get("directions"),
            data.get("poster_url"),
            data.get("rules_url")
        )
    except Exception as e:
        handle_admin_web_error(chat_id, "сохранение web-данных", e)
        return

    clear_admin_web_state(chat_id)

    if count:
        send_admin_competitions_panel(chat_id, "✅ Данные для сайта сохранены.")
    else:
        send_admin_competitions_panel(chat_id, "❌ Конкурс не найден. Данные не сохранены.")


def admin_publication_id_step(message):
    if not admin_check(message):
        return

    if is_cancel_text(message):
        cancel_admin_web_action(message.chat.id)
        return

    if message.content_type != "text":
        msg = bot.send_message(
            message.chat.id,
            f"❌ Введите числовой ID конкурса или напишите «{WEB_CANCEL_WORD}»."
        )
        bot.register_next_step_handler(msg, admin_publication_id_step)
        return

    competition_number = parse_positive_int(message.text.strip())

    if competition_number is None:
        msg = bot.send_message(
            message.chat.id,
            f"❌ Введите целое положительное число или напишите «{WEB_CANCEL_WORD}»."
        )
        bot.register_next_step_handler(msg, admin_publication_id_step)
        return

    try:
        competition = get_competition_by_id(f"competition_{competition_number}")
    except Exception as e:
        handle_admin_web_error(message.chat.id, "получение конкурса для публикации", e)
        return

    if not competition:
        msg = bot.send_message(
            message.chat.id,
            f"❌ Конкурс не найден. Введите другой числовой ID или напишите «{WEB_CANCEL_WORD}»."
        )
        bot.register_next_step_handler(msg, admin_publication_id_step)
        return

    if not admin_web_schema_ready(message.chat.id):
        return

    try:
        web_data = get_competition_web_data_by_id(competition_number)
    except Exception as e:
        handle_admin_web_error(message.chat.id, "получение статуса публикации", e)
        return

    if not web_data:
        msg = bot.send_message(
            message.chat.id,
            f"❌ Конкурс не найден. Введите другой числовой ID или напишите «{WEB_CANCEL_WORD}»."
        )
        bot.register_next_step_handler(msg, admin_publication_id_step)
        return

    user_data.setdefault(message.chat.id, {})
    user_data[message.chat.id]["admin_competition_publication"] = {
        "competition_id": competition_number
    }

    bot.send_message(
        message.chat.id,
        f"""👁 Публикация конкурса на сайте

ID: {competition_number}
Название: {escape(format_web_value(web_data.get("name")))}
Текущий статус: {publication_status_text(web_data.get("is_published"))}""",
        reply_markup=admin_competition_publication_menu()
    )


def get_missing_publication_fields(web_data):
    missing = []

    for key, label in WEB_REQUIRED_FOR_PUBLICATION:
        if not web_data.get(key):
            missing.append(label)

    return missing


def change_admin_publication(chat_id, is_published):
    state = user_data.get(chat_id, {}).get("admin_competition_publication")

    if not state:
        send_admin_competitions_panel(
            chat_id,
            "❌ Сценарий публикации не найден. Начните заново."
        )
        return

    if not admin_web_schema_ready(chat_id):
        return

    competition_number = state["competition_id"]

    try:
        web_data = get_competition_web_data_by_id(competition_number)
    except Exception as e:
        handle_admin_web_error(chat_id, "получение web-данных перед публикацией", e)
        return

    if not web_data:
        clear_admin_web_state(chat_id)
        send_admin_competitions_panel(chat_id, "❌ Конкурс не найден.")
        return

    if is_published:
        missing_fields = get_missing_publication_fields(web_data)

        if missing_fields:
            clear_admin_web_state(chat_id)
            send_admin_competitions_panel(
                chat_id,
                "❌ Нельзя опубликовать конкурс. Заполните обязательные поля:\n"
                + "\n".join(f"• {field}" for field in missing_fields)
            )
            return

    try:
        count = set_competition_publication_by_id(competition_number, is_published)
    except Exception as e:
        handle_admin_web_error(chat_id, "изменение публикации", e)
        return

    clear_admin_web_state(chat_id)

    if not count:
        send_admin_competitions_panel(chat_id, "❌ Конкурс не найден.")
    elif is_published:
        send_admin_competitions_panel(chat_id, "✅ Конкурс опубликован на сайте.")
    else:
        send_admin_competitions_panel(chat_id, "🚫 Конкурс снят с публикации.")


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

    competition_id = add_competition(user_data[message.chat.id]["admin_competition"])
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
    competition = get_competition_by_id(competition_id)

    if not competition:
        bot.send_message(
            message.chat.id,
            "❌ Конкурс не найден"
        )
        return

    user_data.setdefault(message.chat.id, {})
    user_data[message.chat.id]["admin_competition_id"] = competition_id
    user_data[message.chat.id]["admin_competition"] = competition.copy()

    msg = bot.send_message(
        message.chat.id,
        f"Текущее название:\n{escape(competition.get('title') or '')}\n\nВведите новое название или отправьте - чтобы оставить текущее:"
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
    update_competition(competition_id, user_data[message.chat.id]["admin_competition"])

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
    competition = get_competition_by_id(competition_id)

    if not competition:
        bot.send_message(
            message.chat.id,
            "❌ Конкурс не найден"
        )
        return

    delete_competition(competition_id)

    bot.send_message(
        message.chat.id,
        f"🗑 Конкурс {competition_id} удален"
    )

    bot.send_message(
        message.chat.id,
        admin_competitions_text(),
        reply_markup=admin_competitions_menu()
    )


@bot.callback_query_handler(func=lambda callback: (
    callback.data in (
        "competition",
        "back_to_competition",
        "bid",
        "back_to_competition1",
        "apply",
        "rules",
        "admin_competitions",
        "admin_add_competition",
        "admin_change_competition",
        "admin_delete_competition",
        "admin_competition_web_data",
        "admin_competition_publication",
        "admin_web_save",
        "admin_web_cancel",
        "admin_web_publish",
        "admin_web_unpublish",
    )
    or callback.data.startswith("competition_")
))
def competition_callback_message(callback):
    bot.answer_callback_query(callback.id)
    if callback.data.startswith("admin") or callback.data == "back_to_admin_info":
        if not admin_check(callback.message):
            return

    if callback.data == 'competition':

        bot.edit_message_text(
            '🏆 Актуальные конкурсы ArtFlow\n\nВыберите интересующий вас конкурс для просмотра подробной информации и подачи заявки.\n\n👇 Список доступных конкурсов:',
            callback.message.chat.id,
            callback.message.message_id, reply_markup = competition_menu())
    if callback.data.startswith('competition_'):
        competition = get_competition_by_id(callback.data)

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

    elif callback.data == 'admin_competition_web_data':
        if not admin_check(callback.message):
            return

        clear_admin_web_state(callback.message.chat.id)
        msg = bot.send_message(
            callback.message.chat.id,
            f"🌐 Введите числовой ID конкурса для заполнения данных сайта или напишите «{WEB_CANCEL_WORD}»:"
        )
        bot.register_next_step_handler(msg, admin_web_data_id_step)

    elif callback.data == 'admin_competition_publication':
        if not admin_check(callback.message):
            return

        clear_admin_web_state(callback.message.chat.id)
        msg = bot.send_message(
            callback.message.chat.id,
            f"👁 Введите числовой ID конкурса для управления публикацией или напишите «{WEB_CANCEL_WORD}»:"
        )
        bot.register_next_step_handler(msg, admin_publication_id_step)

    elif callback.data == 'admin_web_save':
        if not admin_check(callback.message):
            return

        save_admin_web_data(callback.message.chat.id)

    elif callback.data == 'admin_web_cancel':
        if not admin_check(callback.message):
            return

        cancel_admin_web_action(callback.message.chat.id)

    elif callback.data == 'admin_web_publish':
        if not admin_check(callback.message):
            return

        change_admin_publication(callback.message.chat.id, True)

    elif callback.data == 'admin_web_unpublish':
        if not admin_check(callback.message):
            return

        change_admin_publication(callback.message.chat.id, False)
