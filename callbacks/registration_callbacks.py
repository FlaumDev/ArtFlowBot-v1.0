from loader import bot
from storage import user_data
from registration import end_registration, performance_time, city, number_of_participants, exit_registration, music_file
from callbacks.competition_callbacks import get_current_competition


@bot.callback_query_handler(func=lambda callback: (
    callback.data == "registration"
    or callback.data.startswith("age_")
    or callback.data.startswith("genre_")
    or callback.data == "confirm_reg"
    or callback.data.startswith("mus_")
))
def registration_callback_message(callback):
    bot.answer_callback_query(callback.id)
    if callback.data=='registration':
        competition_id, competition = get_current_competition(callback.message.chat.id)

        if not competition:
            bot.send_message(
                callback.message.chat.id,
                "❌ Конкурс не найден"
            )
            return

        user_data[callback.message.chat.id] = {
            "participants": [],
            "current_participant": 1,
            "music_file_id": None,
            "music_file_name": "Не используется",
            "selected_competition": competition_id,
            "competition_name": competition.get("title"),
            "competition_date": competition.get("date")
        }



        msg = bot.send_message(callback.message.chat.id, "🏙 Шаг 1 из 12\nВведите город:")
        bot.register_next_step_handler(msg, city)



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

        msg = bot.send_message(user_id, "⏱️ Шаг 7 из 12\nВведите хронометраж выступления (в минутах):")
        bot.register_next_step_handler(msg, performance_time)


    elif callback.data.startswith("genre_"):

        user_id = callback.message.chat.id

        genres = {
            "genre_1": "Хореография",
            "genre_2": "Вокал",
            "genre_3": "Инструментальный",
        }

        user_data[user_id]["genre"] = genres[callback.data]

        msg = bot.send_message(
            user_id,
            "👥 Шаг 5 из 12\nВведите количество участников в номере"
        )

        bot.register_next_step_handler(msg, number_of_participants)



    elif callback.data  == 'confirm_reg':
        if callback.message.chat.id not in user_data:
            bot.send_message(callback.message.chat.id, "❌ Данные заявки не найдены. Пожалуйста, заполните заявку заново.")
            return

        data = user_data[callback.message.chat.id]

        from database import get_connection

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            '''
            INSERT INTO ArtFlow_bid (telegram_id,
                                     city,
                                     name_team,
                                     number_name,
                                     number_genre,
                                     number_of_participants,
                                     age,
                                     performance_time,
                                     SFP_supervisor,
                                     WhatsApp_number,
                                     email,
                                     music_file_id,
                                     music_file_name,
                                     competition_id,
                                     competition_name
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            ''',
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
                data['email'],
                data['music_file_id'],
                data['music_file_name'],
                int(data['selected_competition'].split("_")[-1]),
                data['competition_name']
            )
        )

        bid_id = cur.fetchone()[0]


        for participant in data['participants']:
            cur.execute("""
                        INSERT INTO participants (bid_id, participant_name)
                        VALUES (%s, %s)
                        """, (bid_id, participant))

        conn.commit()
        cur.close()
        conn.close()
        end_registration(callback.message)

        user_data.pop(callback.message.chat.id, None)

    elif callback.data.startswith("mus_"):

        user_id = callback.message.chat.id

        if callback.data.endswith("yes"):
            msg = bot.send_message(user_id, "🎵 Прикрепите музыкальный файл")
            bot.register_next_step_handler(msg, music_file)
        elif callback.data.endswith("no"):
            user_data[user_id]["music_file_id"] = None
            user_data[user_id]["music_file_name"] = "Не используется"
            exit_registration(callback.message)
