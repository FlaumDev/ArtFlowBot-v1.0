from telebot import types
from loader import  bot
from storage import user_data, FAQ, WhatsApp
from database import get_user_requests, get_participants
from admin_keyboards import admin_requests_menu_menu



@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):

    bot.answer_callback_query(callback.id)

    if callback.data == 'admin_requests':
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
        participants_text = "\n".join(
            f"•{participant[2]}"
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

📊 Статус: {request[12]}
    """,
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=admin_requests_menu_menu()
        )