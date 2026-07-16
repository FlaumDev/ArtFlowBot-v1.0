from html import escape


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
