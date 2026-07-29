from loader import bot
from database import all_count, all_participants, requests_status, request_time, get_all_telegram_ids, get_all_admins, is_admin, add_admin, delete_admin
from keyboards.admin_keyboards import admin_requests_menu, admin_stats_menu, admins_func_menu


def admin_list_text():
    admins = get_all_admins()

    if not admins:
        return "📋 Администраторов пока нет"

    text = "📋 Администраторы\n\n"

    for admin in admins:
        text += f"ID: {admin[1]} ! Имя: {admin[3] or '-'}\n"

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
        except Exception as e:
            print(f"Ошибка рассылки пользователю {telegram_id}: {e}")
            errors += 1

    bot.send_message(
        message.chat.id,
        f"""📤 Рассылка завершена

✅ Успешно: {success}
❌ Ошибок: {errors}"""
    )


def admin_check(message):
    if not is_admin(message.chat.id):
        bot.send_message(
            message.chat.id,
            "❌ У вас нет доступа к панели администратора."
        )
        return False

    return True


@bot.callback_query_handler(func=lambda callback: callback.data in (
    "admin_spam",
    "admin_add_admin",
    "admin_delete_admin",
    "admin_list_admins",
    "admin_stats",
    "back_to_admin_info",
    "admins_func",
))
def admin_callback_message(callback):
    bot.answer_callback_query(callback.id)
    if callback.data.startswith("admin") or callback.data == "back_to_admin_info":
        if not admin_check(callback.message):
            return

    if callback.data == 'admin_spam':
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

    elif callback.data == "admin_stats":
        stat1 = 0
        stat2 = 0
        stat3 = 0
        stat4 = 0
        genre1 = 0
        genre2 = 0
        genre3 = 0
        genre4 = 0

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
            elif genre.lower() == "изо":
                genre4 += 1
            else:
                print("Неизвестный жанр:", genre)





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
• ИЗО — {genre4}

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


    elif callback.data == "admins_func":
        bot.edit_message_text("Выберите действие",
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=admins_func_menu()
        )
