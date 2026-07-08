from html import escape
from loader import bot
from storage import user_data
from keyboards.user_keyboards import competition_menu, competition_1_menu, back_to_competition_menu, bid_menu, back_to_competition1_menu, apply_menu
from keyboards.admin_keyboards import admin_competitions_menu
from callbacks.admin_callbacks import admin_check
from database import get_all_competitions, get_competition_by_id, add_competition, update_competition, delete_competition


def get_current_competition(user_id):
    competition_id = "competition_1"

    if user_id in user_data:
        competition_id = user_data[user_id].get("selected_competition", competition_id)

    competitions = get_all_competitions()

    if competition_id not in competitions and competitions:
        competition_id = next(iter(competitions))

    return competition_id, competitions.get(competition_id)


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
