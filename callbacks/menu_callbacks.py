from loader import bot
from storage import WhatsApp
from keyboards.user_keyboards import back_to_info_menu, contact_menu, contact_menu1, contact_menu2


@bot.callback_query_handler(func=lambda callback: callback.data in (
    "back_to_info",
    "contact",
    "wa_1",
    "wa_2",
    "em",
    "contact_1",
    "contact_2",
    "back_to_contact",
))
def menu_callback_message(callback):
    if callback.data == 'back_to_info':
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
