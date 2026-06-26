from telebot import types
from loader import  bot
from storage import user_data, FAQ, WhatsApp
from registration import end_registration, performance_time, city
from keyboards import competition_menu, back_to_info_menu, competition_1_menu, back_to_competition_menu, bid_menu, back_to_competition1_menu, apply_menu, request_navigation, contact_menu, faq_menu
from database import get_user_requests, get_participants


@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):

    bot.answer_callback_query(callback.id)

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
    elif callback.data == 'competition_1':

        bot.edit_message_text(
            '''🏆 VIII Международный многожанровый конкурс-фестиваль
«СОДРУЖЕСТВО ТАЛАНТОВ»

📍 Место проведения:
г. Павлодар, ул. Ломова 64
ПГУ им. С. Торайгырова

📅 Дата проведения:
20 июня 2026 года

⏳ Приём заявок:
до 10 июня 2026 года

🎭 Направления конкурса:
• Хореография
• Вокал
• Инструментальное искусство

👥 Возрастные категории:
от 3 до 18 лет

🏅 Каждый участник получает награду.
🎁 Руководителям вручаются благодарственные письма.
💰 Призовой фонд — 300 000 ₸

💳 Стоимость участия:
от 6 000 ₸ до 15 000 ₸ в зависимости от категории участника.

👇 Выберите дальнейшее действие:''',
            callback.message.chat.id,
            callback.message.message_id, reply_markup = competition_1_menu()
        )
    elif callback.data == 'back_to_competition':

        bot.edit_message_text(
            '🏆 Актуальные конкурсы ArtFlow\n\nВыберите интересующий вас конкурс для просмотра подробной информации и подачи заявки.\n\n👇 Список доступных конкурсов:',
            callback.message.chat.id,
            callback.message.message_id, reply_markup = back_to_competition_menu())

    elif callback.data  == 'bid':

        bot.edit_message_text(
            '''📝 Регистрация участника(-ов)

Для подачи заявки на конкурс "СОДРУЖЕСТВО ТАЛАНТОВ" подготовьте следующую информацию:

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

Готовы начать регистрацию?''',
            callback.message.chat.id,
            callback.message.message_id,
        reply_markup= bid_menu()
        )

    elif callback.data == 'back_to_competition1':

        bot.edit_message_text(
            '''🏆 VIII Международный многожанровый конкурс-фестиваль
«СОДРУЖЕСТВО ТАЛАНТОВ»

📍 Место проведения:
г. Павлодар, ул. Ломова 64
ПГУ им. С. Торайгырова

📅 Дата проведения:
20 июня 2026 года

⏳ Приём заявок:
до 10 июня 2026 года

🎭 Направления конкурса:
• Хореография
• Вокал
• Инструментальное искусство

👥 Возрастные категории:
от 3 до 18 лет

🏅 Каждый участник получает награду.
🎁 Руководителям вручаются благодарственные письма.
💰 Призовой фонд — 300 000 ₸

💳 Стоимость участия:
от 6 000 ₸ до 15 000 ₸ в зависимости от категории участника.

👇 Выберите дальнейшее действие:''',
            callback.message.chat.id,
            callback.message.message_id, reply_markup = back_to_competition1_menu())
    elif callback.data == 'apply':

        bot.edit_message_text(
            '📄 Перед подачей заявки на конкурс ArtFlow,\nВыберите интересующий вас конкурс для просмотра подробной информации и подачи заявки.\n\n👇 Список доступных конкурсов:',
            callback.message.chat.id,
            callback.message.message_id, reply_markup = apply_menu())
    elif callback.data == 'rules':
        with open('Artdocuments/ПОЛОЖЕНИЕ СОДРУЖЕСТВО ТАЛАНТОВ.docx', 'rb') as file:
            bot.send_document(
                callback.message.chat.id,
                file,
                caption='📄 Положение конкурса "Содружество талантов"'
            )



    elif callback.data=='registration':
        user_data[callback.message.chat.id] = {
            "participants": [],
            "current_participant": 1
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



    elif callback.data  == 'confirm_reg':
        if callback.message.chat.id not in user_data:
            bot.send_message(
                callback.message.chat.id, "❌ Данные заявки не найдены. Пожалуйста, заполните заявку заново."
            )
            return
        data = user_data[callback.message.chat.id]

        """ conn = sqlite3.connect('ArtFlow.db')
        cur = conn.cursor() """
        from database import get_connection

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            '''
            INSERT INTO ArtFlow_bid (
                telegram_id,
                city,
                name_team,
                number_name,
                number_genre,
                number_of_participants,
                age,
                performance_time,
                SFP_supervisor,
                WhatsApp_number,
                email
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id''',
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
                data['email']
            )
        )

        bid_id = cur.fetchone()[0]



        for participant in data['participants']:

            cur.execute(
                """
                INSERT INTO participants (
                bid_id,
                participant_name
                )
                VALUES (%s, %s)
                """,
                (
                    bid_id,
                    participant
                )
            )
        conn.commit()
        cur.close()
        conn.close()

        end_registration(callback.message)
        del user_data[callback.message.chat.id]

    elif callback.data == "my_requests":

        requests = get_user_requests(
            callback.message.chat.id
        )

        if not requests:
            bot.send_message(
                callback.message.chat.id,
                "📋 У вас пока нет заявок"
            )
            return
        request = requests[0]
        participants = get_participants(request[0])
        participants_text = "\n".join(f"•{participant[0]}"
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
👥 Участников: {request[6]}
🎂 Возрастная категория: {request[7]}        
⏱️ Хронометраж {request[8]}
👨‍🏫 Руководитель: {request[9]}
👥 Участники: {participants_text}
📞 WhatsApp: {request[10]}
📧 E-mail: {request[11]}        
    """, reply_markup = request_navigation(1, len(requests)
        )
        )
    elif callback.data.startswith("request_page_"):

        page = int(callback.data.split("_")[-1])

        requests  = get_user_requests(callback.message.chat.id)

        request = requests[page - 1]
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

👨 Мария
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


    elif callback.data.startswith("faq_"):
        faq = FAQ[callback.data.split()]

        bot.send_message(
            callback.message.chat.id,
            f"❓ {faq['question']}\n\n💬 {faq['answer']}"
        )

    elif callback.data == "wa_1":
        bot.send_message(
            callback.message.chat.id,
            f"📞 Елена Фляум: {WhatsApp["wa_1"]["number"]}"
        )

    elif callback.data == "wa_2":
        bot.send_message(
            callback.message.chat.id,
            f"📞 Марина Михаиловна: {WhatsApp["wa_2"]["number"]}"
        )

    elif callback.data == "em":
        bot.send_message(
            callback.message.chat.id,
            "lemani1974@mail.ru"
        )

