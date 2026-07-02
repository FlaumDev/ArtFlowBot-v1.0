import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup

from loader import bot
from storage import user_data
from keyboards import end_registration_menu, exit_registration_menu, age_menu, genre_menu
import re


def city(message):
    user_id = message.chat.id

    if message.content_type != "text":
        bot.send_message(
            message.chat.id, "❌ Введите текстом"
        )

        bot.register_next_step_handler(message, city)
        return

    user_data[user_id]["city"] = message.text.strip()

    bot.send_message(
        message.chat.id, "🏫 Шаг 2 из 11\nВведите название коллектива:"
    )

    bot.register_next_step_handler(message, name_team)



def name_team(message):

    user_id = message.chat.id

    if message.content_type != "text":
        bot.send_message(
            message.chat.id, "❌ Введите текстом"
        )

        bot.register_next_step_handler(message, name_team)
        return

    user_data[user_id]["team"] = message.text.strip()

    bot.send_message(message.chat.id,
                     "🎵 Шаг 3 из 11\nВведите название номера:")
    bot.register_next_step_handler(message, number_name)



def number_name(message):

    user_id = message.chat.id

    if message.content_type != "text":
        bot.send_message(
            message.chat.id, "❌ Введите текстом"
        )

        bot.register_next_step_handler(message, number_name)
        return

    user_data[user_id]["name"] = message.text.strip()

    bot.send_message(message.chat.id, "🎭 Шаг 4 из 11\nВведите жанр номера:", reply_markup = genre_menu())






def number_of_participants(message):

    user_id = message.chat.id

    try:
        count = int(message.text)
        if count <= 0:
            raise ValueError

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
        f"👥 Шаг 6 из 11\nВведите ФИО 1-го участника:"
    )

    bot.register_next_step_handler(
        message,
        add_participant
    )



def add_participant(message):

    user_id = message.chat.id

    if not message.text:
        bot.send_message(
            message.chat.id, "❌ Введите текстом"
        )

        bot.register_next_step_handler(message, add_participant)
        return

    user_data[user_id]["participants"].append(
        message.text.strip()
    )


    current = user_data[user_id]["current_participant"]
    total = user_data[user_id]["participant_count"]


    if current < total:

        user_data[user_id]["current_participant"] += 1


        bot.send_message(
            message.chat.id,
            f"👥 Шаг 6 из 11\nВведите ФИО {current + 1}-го участника:"
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
        time = int(message.text)
        if time <= 0:
            raise ValueError

    except ValueError:
        bot.send_message(message.chat.id, "❌ Ошибка. Время выступления числом больше 0")
        bot.register_next_step_handler(message, performance_time)
        return
    user_data[user_id]["performance_time"] = time

    bot.send_message(message.chat.id, "👤 Шаг 8 из 11\nВведите ФИО руководителя:")
    bot.register_next_step_handler(message, SFP_supervisor)



def SFP_supervisor(message):

    user_id = message.chat.id

    if message.content_type != "text":
        bot.send_message(
            message.chat.id, "❌ Введите текстом"
        )

        bot.register_next_step_handler(message, SFP_supervisor)
        return

    user_data[user_id]["supervisor"] = message.text.strip()

    bot.send_message(message.chat.id, "📞 Шаг 9 из 11\nВведите контактный номер WhatsApp")
    bot.register_next_step_handler(message, WhatsApp_number)



def WhatsApp_number(message):

    user_id = message.chat.id

    if message.content_type != "text":
        bot.send_message(
            message.chat.id, "❌ Пожалуйста, введите номер телефона сообщением"
        )
        bot.register_next_step_handler(message, WhatsApp_number)
        return

    clean_phone = re.sub(r"[^\d+]", "", message.text)

    pattern = r"^\+?[0-9]{10,15}$"

    if not re.match(pattern, clean_phone):
        bot.send_message(
            message.chat.id, "❌ Неверный формат номера\nПримеры: +77052510210\n87052510210"
        )
        bot.register_next_step_handler(message, WhatsApp_number)
        return

    user_data[user_id]["WhatsApp"] = clean_phone

    bot.send_message(message.chat.id, "📨 Шаг 10 из 11\nВведите ваш e-mail")
    bot.register_next_step_handler(message, email)



def email(message):



    user_id = message.chat.id

    if message.content_type != "text":
        bot.send_message(
            message.chat.id, "❌ Введите e-mail текстом"
        )
        bot.register_next_step_handler(message, email)
        return
    email_text = message.text.strip()

    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"

    if not re.match(pattern, email_text):
        bot.send_message(
            message.chat.id, "❌ Некорректный e-mail.\nПример: example@gmail.com"
        )
        bot.register_next_step_handler(message, email)
        return

    user_data[user_id]["email"] = email_text

    markup = InlineKeyboardMarkup()

    markup.row(types.InlineKeyboardButton('✅ Да', callback_data = 'mus_yes'),
               types.InlineKeyboardButton('❌ Нет', callback_data = 'mus_no'))

    bot.send_message(message.chat.id, '🎵 Используется ли музыкальное сопровождение?', reply_markup=markup)


def music_file(message):
    user_id = message.chat.id

    if message.audio:
        user_data[user_id]["music_file_id"] = message.audio.file_id
        user_data[user_id]["music_file_name"] = message.audio.file_name or "audio"

    elif message.document:
        user_data[user_id]["music_file_id"] = message.document.file_id
        user_data[user_id]["music_file_name"] = message.document.file_name or "document"
    else:
        msg = bot.send_message(
            message.chat.id,
            "❌ Прикрепите музыкальный файл"
        )
        bot.register_next_step_handler(msg, music_file)
        return

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

🎧 Музыкальный файл: {data.get('music_file_name', 'Не используется')}

⚠️ Пожалуйста, внимательно проверьте правильность указанных данных.

После подтверждения заявка будет зарегистрирована в системе ArtFlow и передана организаторам на рассмотрение. В ближайшее время с вами свяжется организатор и отправят счет на оплату''',
                     reply_markup= exit_registration_menu())



def end_registration(message):
    bot.send_message(message.chat.id, '''🎉 Ваша заявка на участие в конкурсе “Содружество Талантов” успешно отправлена!

🙏 Спасибо, что выбрали ArtFlow. В ближайшее время организатор свяжется с вами для подтверждения и отправки счёта на оплату.

📅 Не забудьте, что приём заявок до 10 июня 2026 года. Мы рады видеть вас среди участников и желаем вам удачи!

Если у вас есть вопросы, обращайтесь — мы всегда на связи.''', reply_markup= end_registration_menu())