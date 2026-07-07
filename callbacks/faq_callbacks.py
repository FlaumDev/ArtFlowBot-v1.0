from html import escape
from loader import bot
from storage import user_data
from keyboards.user_keyboards import faq_menu, faq_page_menu
from keyboards.admin_keyboards import admin_faq_menu
from database import get_all_faq, get_faq_by_id, add_faq, update_faq, delete_faq
from callbacks.admin_callbacks import admin_check


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


@bot.callback_query_handler(func=lambda callback: (
    callback.data in (
        "faq",
        "admin_faq",
        "admin_add_faq",
        "admin_change_faq",
        "admin_delete_faq",
    )
    or (callback.data.startswith("faq_") and callback.data.split("_")[-1].isdigit())
    or callback.data.startswith("faqpage_")
))
def faq_callback_message(callback):
    if callback.data.startswith("admin") or callback.data == "back_to_admin_info":
        if not admin_check(callback.message):
            return

    if callback.data == "faq":
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
