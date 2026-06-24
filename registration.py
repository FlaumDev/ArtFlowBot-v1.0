import telebot
from telebot import types
from loader import bot
from storage import user_data
from keyboards import end_registration_menu, exit_registration_menu, age_menu



def city(message):
    user_id = message.chat.id

    user_data[user_id]["city"] = message.text.strip()

    bot.send_message(
        message.chat.id, "🏫 Шаг 2 из 12\nВведите название коллектива:"
    )

    bot.register_next_step_handler(message, name_team)



def name_team(message):

    user_id = message.chat.id

    user_data[user_id]["team"] = message.text.strip()

    bot.send_message(message.chat.id,
                     "🎵 Шаг 3 из 12\nВведите название номера:")
    bot.register_next_step_handler(message, number_name)



def number_name(message):

    user_id = message.chat.id

    user_data[user_id]["name"] = message.text.strip()

    bot.send_message(message.chat.id, "🎭 Шаг 4 из 12\nВведите жанр номера:")
    bot.register_next_step_handler(message, number_genre)



def number_genre(message):

    user_id = message.chat.id

    user_data[user_id]["genre"] = message.text.strip()

    bot.send_message(message.chat.id, "👥 Шаг 5 из 12\nВведите количество участников в номере")
    bot.register_next_step_handler(message, number_of_participants)



def number_of_participants(message):

    user_id = message.chat.id

    try:
        count = int(message.text)

    except ValueError:
        bot.send_message(
            message.chat.id,
            "❌ Введите количество участников числом"
        )
        bot.register_next_step_handler(
            message,
            number_of_participants
        )
        return


    user_data[user_id]["participant_count"] = count

    user_data[user_id]["participants"] = []

    user_data[user_id]["current_participant"] = 1


    bot.send_message(
        message.chat.id,
        f"👥 Шаг 6 из 12\nВведите ФИО 1-го участника:"
    )

    bot.register_next_step_handler(
        message,
        add_participant
    )



def add_participant(message):

    user_id = message.chat.id

    user_data[user_id]["participants"].append(
        message.text.strip()
    )


    current = user_data[user_id]["current_participant"]
    total = user_data[user_id]["participant_count"]


    if current < total:

        user_data[user_id]["current_participant"] += 1


        bot.send_message(
            message.chat.id,
            f"👥 Шаг 6 из 12\nВведите ФИО {current + 1}-го участника:"
        )


        bot.register_next_step_handler(
            message,
            add_participant
        )

    else:

        age(message)



def age(message):

    bot.send_message(
        message.chat.id,
        "🎂 Шаг 7 из 12\nВыберите возрастную категорию:",
        reply_markup = age_menu()
    )

def performance_time(message):

    user_id = message.chat.id

    try:
        user_data[user_id]["performance_time"] = int(message.text.strip())
    except ValueError:
        bot.send_message(message.chat.id, "❌ Ошибка. Введите время числом")

    bot.send_message(message.chat.id, "👤 Шаг 8 из 12\nВведите ФИО руководителя:")
    bot.register_next_step_handler(message, SFP_supervisor)



def SFP_supervisor(message):

    user_id = message.chat.id

    user_data[user_id]["supervisor"] = message.text.strip()

    bot.send_message(message.chat.id, "📞 Шаг 9 из 12\nВведите контактный номер WhatsApp")
    bot.register_next_step_handler(message, WhatsApp_number)



def WhatsApp_number(message):

    user_id = message.chat.id

    user_data[user_id]["WhatsApp"] = message.text.strip()

    bot.send_message(message.chat.id, "📨 Шаг 10 из 12\nВведите ваш e-mail")
    bot.register_next_step_handler(message, email)



def email(message):

    user_id = message.chat.id

    user_data[user_id]["email"] = message.text.strip()

    exit_registration(message)



def exit_registration(message):

    data = user_data[message.chat.id]
    bot.send_message(message.chat.id, f'''📋 Проверьте данные вашей заявки

🏆 Конкурс: СОДРУЖЕСТВО ТАЛАНТОВ

🏙 Город: {data['city']}

🏫 Название коллектива: {data['team']}

🎵 Название номера: {data['name']}

🎭 Жанр номера: {data['genre']}

👥 Количество участников: {len(data['participants'])}

🎂 Возрастная категория: {data['age']}

⏱️ Хронометраж: {data['performance_time']} мин.

👨‍🏫 Руководитель: {data['supervisor']}

📞 Контактный телефон: {data['WhatsApp']}

📧 Электронная почта: {data['email']}

👥 Участники: {chr(10).join(data['participants'])}

🎧 Музыкальный файл: Прикреплён

⚠️ Пожалуйста, внимательно проверьте правильность указанных данных.

После подтверждения заявка будет зарегистрирована в системе ArtFlow и передана организаторам на рассмотрение. В ближайшее время с вами свяжется организатор и отправят счет на оплату''',
                     reply_markup= exit_registration_menu())



def end_registration(message):
    bot.send_message(message.chat.id, '''🎉 Ваша заявка на участие в конкурсе “Содружество Талантов” успешно отправлена!

🙏 Спасибо, что выбрали ArtFlow. В ближайшее время организатор свяжется с вами для подтверждения и отправки счёта на оплату.

📅 Не забудьте, что приём заявок до 10 июня 2026 года. Мы рады видеть вас среди участников и желаем вам удачи!

Если у вас есть вопросы, обращайтесь — мы всегда на связи.''', reply_markup= end_registration_menu())