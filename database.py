import psycopg2
from dotenv import load_dotenv
import os
import re
load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )


def competition_row_to_dict(competition):
    return {
        "title": competition[1],
        "name": competition[1],
        "description": competition[2],
        "rules_file": competition[3],
        "date": competition[4],
        "place": competition[5],
        "price": competition[6]
    }


WEB_COMPETITION_COLUMNS = (
    "event_date",
    "application_deadline",
    "city",
    "short_description",
    "directions",
    "poster_url",
    "rules_url",
    "is_published",
    "updated_at"
)


def get_all_competitions():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute('''
    SELECT id, name, description, document, date, place, price
    FROM competitions
    ORDER BY id ASC
    ''')

    competitions = cur.fetchall()

    cur.close()
    conn.close()

    return {
        f"competition_{competition[0]}": competition_row_to_dict(competition)
        for competition in competitions
    }


def get_competition_by_id(competition_id):
    if not competition_id.startswith("competition_"):
        return None

    competition_number = competition_id.split("_")[-1]

    if not competition_number.isdigit():
        return None

    conn = get_connection()
    cur = conn.cursor()

    cur.execute('''
    SELECT id, name, description, document, date, place, price
    FROM competitions
    WHERE id = %s
    ''', (int(competition_number),))

    competition = cur.fetchone()

    cur.close()
    conn.close()

    if not competition:
        return None

    return competition_row_to_dict(competition)


def add_competition(competition):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute('''
    INSERT INTO competitions (name, description, document, date, place, price)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING id
    ''', (
        competition.get("title") or competition.get("name"),
        competition.get("description"),
        competition.get("rules_file"),
        competition.get("date"),
        competition.get("place"),
        competition.get("price")
    ))

    competition_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return f"competition_{competition_id}"


def update_competition(competition_id, competition):
    if not competition_id.startswith("competition_"):
        return 0

    competition_number = competition_id.split("_")[-1]

    if not competition_number.isdigit():
        return 0

    conn = get_connection()
    cur = conn.cursor()

    cur.execute('''
    UPDATE competitions
    SET name = %s,
        description = %s,
        document = %s,
        date = %s,
        place = %s,
        price = %s
    WHERE id = %s
    ''', (
        competition.get("title") or competition.get("name"),
        competition.get("description"),
        competition.get("rules_file"),
        competition.get("date"),
        competition.get("place"),
        competition.get("price"),
        int(competition_number)
    ))

    count = cur.rowcount

    conn.commit()
    cur.close()
    conn.close()

    return count


def competitions_web_columns_ready():
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute('''
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = current_schema()
            AND table_name = %s
            AND column_name = ANY(%s)
        ''', ("competitions", list(WEB_COMPETITION_COLUMNS)))

        existing_columns = {row[0] for row in cur.fetchall()}

        return set(WEB_COMPETITION_COLUMNS).issubset(existing_columns)
    finally:
        cur.close()
        conn.close()


def get_competition_web_data_by_id(competition_id):
    if not isinstance(competition_id, int) or isinstance(competition_id, bool) or competition_id <= 0:
        return None

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute('''
        SELECT id, name, event_date, application_deadline, city,
               short_description, directions, poster_url, rules_url,
               is_published, updated_at
        FROM competitions
        WHERE id = %s
        ''', (competition_id,))

        competition = cur.fetchone()

        if not competition:
            return None

        return {
            "id": competition[0],
            "name": competition[1],
            "event_date": competition[2],
            "application_deadline": competition[3],
            "city": competition[4],
            "short_description": competition[5],
            "directions": competition[6],
            "poster_url": competition[7],
            "rules_url": competition[8],
            "is_published": competition[9],
            "updated_at": competition[10]
        }
    finally:
        cur.close()
        conn.close()


def update_competition_web_data_by_id(
        competition_id,
        event_date,
        application_deadline,
        city,
        short_description,
        directions,
        poster_url,
        rules_url
):
    if not isinstance(competition_id, int) or isinstance(competition_id, bool) or competition_id <= 0:
        return 0

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute('''
        UPDATE competitions
        SET event_date = %s,
            application_deadline = %s,
            city = %s,
            short_description = %s,
            directions = %s,
            poster_url = %s,
            rules_url = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        ''', (
            event_date,
            application_deadline,
            city,
            short_description,
            directions,
            poster_url,
            rules_url,
            competition_id
        ))

        count = cur.rowcount
        conn.commit()

        return count
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def set_competition_publication_by_id(competition_id, is_published):
    if not isinstance(competition_id, int) or isinstance(competition_id, bool) or competition_id <= 0:
        return 0

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute('''
        UPDATE competitions
        SET is_published = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        ''', (
            is_published,
            competition_id
        ))

        count = cur.rowcount
        conn.commit()

        return count
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def delete_competition(competition_id):
    if not competition_id.startswith("competition_"):
        return 0

    competition_number = competition_id.split("_")[-1]

    if not competition_number.isdigit():
        return 0

    conn = get_connection()
    cur = conn.cursor()

    cur.execute('''
    DELETE FROM competitions
    WHERE id = %s
    ''', (int(competition_number),))

    count = cur.rowcount

    conn.commit()
    cur.close()
    conn.close()

    return count



def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute('''
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = current_schema()
        AND table_name = 'faq'
    )
    ''')
    faq_table_exists = cur.fetchone()[0]

    cur.execute('''
                CREATE TABLE IF NOT EXISTS ArtFlow_bid
                (
                    id
                    SERIAL PRIMARY KEY,
                    telegram_id BIGINT,
                    city TEXT,
                    name_team TEXT,
                    number_name TEXT,
                    number_genre TEXT,
                    number_of_participants INTEGER,
                    age TEXT,
                    performance_time INTEGER,
                    SFP_supervisor TEXT,
                    WhatsApp_number TEXT,
                    email TEXT,
                    status TEXT DEFAULT 'На рассмотрении',
                    create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    music_file_id TEXT,
                    music_file_name TEXT,
                    competition_id INTEGER,
                    competition_name TEXT
                )
                ''')

    cur.execute('''
                CREATE TABLE IF NOT EXISTS participants
                (
                    id
                    SERIAL PRIMARY KEY,
                    bid_id
                    INTEGER,
                    participant_name
                    TEXT,
                    FOREIGN KEY (bid_id)
                    REFERENCES ArtFlow_bid
                    (id)
                    ON
                    DELETE
                    CASCADE
                )    
                ''')

    cur.execute('''
                CREATE TABLE IF NOT EXISTS faq
                (
                    id
                    SERIAL PRIMARY KEY,
                    question TEXT,
                    answer TEXT,
                    create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')

    cur.execute('''
                CREATE TABLE IF NOT EXISTS admins
                (
                    id
                    SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE,
                    create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    name TEXT
                )
                ''')

    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT UNIQUE NOT NULL,
        username TEXT,
        first_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP )
        '''
    )

    cur.execute("""
        CREATE TABLE IF NOT EXISTS competitions (
        id SERIAL PRIMARY KEY,
        name TEXT,
        description TEXT,
        document TEXT,
        date TEXT,
        place TEXT,
        price TEXT,
        create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        event_date DATE,
        application_deadline DATE,
        city TEXT,
        short_description TEXT,
        directions TEXT,
        poster_url TEXT,
        rules_url TEXT,
        is_published BOOLEAN NOT NULL DEFAULT FALSE,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    

    from commands import ADMIN_IDS

    for admin_id in ADMIN_IDS:
        cur.execute('''
        INSERT INTO admins (telegram_id)
        VALUES (%s)
        ON CONFLICT (telegram_id) DO NOTHING
        ''', (admin_id,))

    if not faq_table_exists:
        from storage import FAQ

        for faq in FAQ.values():
            cur.execute('''
            INSERT INTO faq (question, answer)
            VALUES (%s, %s)
            ''', (faq["question"], faq["answer"]))

    conn.commit()
    cur.close()
    conn.close()


def get_user_requests(telegram_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
SELECT
*
FROM
ArtFlow_bid
WHERE
telegram_id = %s
                ORDER BY id ASC''',
                (telegram_id,))

    requests = cur.fetchall()
    cur.close()
    conn.close()
    return requests

def get_all_users_requests():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
    SELECT * FROM ArtFlow_bid
        ORDER BY id ASC
    ''')

    requests = cur.fetchall()
    cur.close()
    conn.close()
    return requests

def get_participants(bid_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute('''
    SELECT participant_name FROM participants
        WHERE bid_id = %s
    ''', (bid_id,))

    participants = cur.fetchall()

    cur.close()
    conn.close()
    return participants


def get_all_requests():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
    SELECT * FROM ArtFlow_bid
    ORDER BY id ASC
                ''')

    requests = cur.fetchall()

    cur.close()
    conn.close()

    return requests

def get_all_telegram_ids():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute('''
    SELECT telegram_id FROM users
    WHERE telegram_id IS NOT NULL
    ORDER BY telegram_id ASC
    ''')

    users = cur.fetchall()

    cur.close()
    conn.close()

    return users

def get_all_admins():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute('''
    SELECT * FROM admins
    ORDER BY id ASC
    ''')

    admins = cur.fetchall()

    cur.close()
    conn.close()

    return admins

def is_admin(telegram_id):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute('''
        SELECT 1 FROM admins
        WHERE telegram_id = %s
        ''', (telegram_id,))

        admin = cur.fetchone()

        cur.close()
        conn.close()

        return bool(admin)
    except Exception:
        from commands import ADMIN_IDS
        return telegram_id in ADMIN_IDS

def add_admin(telegram_id, name = None):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute('''
    INSERT INTO admins (telegram_id, name)
    VALUES (%s, %s)
    ON CONFLICT (telegram_id) DO NOTHING
    RETURNING id
    ''', (telegram_id,name))

    admin = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    return admin

def delete_admin(telegram_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute('''
    DELETE FROM admins
    WHERE telegram_id = %s
    ''', (telegram_id,))

    count = cur.rowcount

    conn.commit()
    cur.close()
    conn.close()

    return count

def get_all_faq():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute('''
    SELECT id, question, answer FROM faq
    ORDER BY id ASC
    ''')

    faq = cur.fetchall()

    cur.close()
    conn.close()

    return faq

def get_faq_by_id(faq_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute('''
    SELECT id, question, answer FROM faq
    WHERE id = %s
    ''', (faq_id,))

    faq = cur.fetchone()

    cur.close()
    conn.close()

    return faq

def add_faq(question, answer):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute('''
    INSERT INTO faq (question, answer)
    VALUES (%s, %s)
    RETURNING id
    ''', (question, answer))

    faq_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return faq_id

def update_faq(faq_id, question, answer):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute('''
    UPDATE faq
    SET question = %s,
        answer = %s
    WHERE id = %s
    ''', (question, answer, faq_id))

    count = cur.rowcount

    conn.commit()
    cur.close()
    conn.close()

    return count

def delete_faq(faq_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute('''
    DELETE FROM faq
    WHERE id = %s
    ''', (faq_id,))

    count = cur.rowcount

    conn.commit()
    cur.close()
    conn.close()

    return count

def get_request_by_id(bid_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute('''
    SELECT * FROM ArtFlow_bid
    WHERE id = %s
    ''', (bid_id,))

    request = cur.fetchone()

    cur.close()
    conn.close()

    return request

def search_requests(search_text):
    conn = get_connection()
    cur = conn.cursor()

    request_id = int(search_text) if search_text.isdigit() and len(search_text) <= 9 else None
    search_like = f"%{search_text}%"
    phone_text = ''.join(symbol for symbol in search_text if symbol.isdigit())
    phone_like = f"%{phone_text}%" if phone_text else search_like

    cur.execute('''
    SELECT * FROM ArtFlow_bid
    WHERE id = %s
        OR email ILIKE %s
        OR WhatsApp_number ILIKE %s
        OR regexp_replace(WhatsApp_number, '[^0-9]', '', 'g') ILIKE %s
    ORDER BY id ASC
    ''', (request_id, search_like, search_like, phone_like))

    requests = cur.fetchall()

    cur.close()
    conn.close()

    return requests


def delete_request(bid_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute('''
    DELETE FROM ArtFlow_bid
    WHERE id = %s
    ''', (bid_id,))

    conn.commit()
    cur.close()
    conn.close()

def update_request_status(bid_id, status):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute('''
    UPDATE ArtFlow_bid
    SET status = %s
    WHERE id = %s
    ''', (status, bid_id))

    conn.commit()
    cur.close()
    conn.close()

def all_count():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute('''
    SELECT COUNT(*) FROM ArtFlow_bid
    ''')
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count

def all_participants():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute('''
    SELECT COUNT(*) FROM participants
    ''')
    part_count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return part_count

def requests_status():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute('''
    SELECT * FROM ArtFlow_bid
    ''')

    status = cur.fetchall()

    cur.close()
    conn.close()

    return status

def request_time(days):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute('''
    SELECT COUNT(*) FROM ArtFlow_bid
    WHERE create_at >= NOW() - (%s * INTERVAL '1 days')
    ''', (days,))

    count = cur.fetchone()[0]

    cur.close()
    conn.close()

    return count

def save_user(message):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute('''
    INSERT INTO users (telegram_id, username, first_name)
    VALUES (%s, %s, %s)
    ON CONFLICT (telegram_id) DO NOTHING
    ''', (
        message.chat.id,
        message.from_user.username,
        message.from_user.first_name
    ))

    conn.commit()
    cur.close()
    conn.close()



def normalized_phone(phone):
    digits = re.sub(r"\D", "", phone)

    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]

    if digits.startswith("7") and len(digits) == 11:
        return digits

    return digits


def search_request_by_id(request_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT * FROM ArtFlow_bid
        WHERE id = %s
    
    """, (request_id,))

    requests = cur.fetchall()

    cur.close()
    conn.close()

    return requests



def search_request_by_email(email):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT * FROM ArtFlow_bid
    WHERE email ILIKE %s
    ORDER BY id ASC
    """, (f"%{email}%",))

    requests = cur.fetchall()

    cur.close()
    conn.close()

    return requests



def search_request_by_whatsapp(phone):
    conn = get_connection()
    cur = conn.cursor()

    phone = normalized_phone(phone)

    cur.execute("""
    SELECT * FROM ArtFlow_bid
        WHERE regexp_replace(WhatsApp_number, '[^0-9]', '', 'g') ILIKE %s
        ORDER BY id ASC
    """, (f"%{phone}%",))

    requests = cur.fetchall()

    cur.close()
    conn.close()

    return requests

def search_request_by_participant(participant_name):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT DISTINCT a.* FROM ArtFlow_bid a
    JOIN participants p ON a.id = p.bid_id
    WHERE p.participant_name ILIKE %s
    ORDER BY a.id ASC
    """, (f"%{participant_name}%",))

    requests = cur.fetchall()

    cur.close()
    conn.close()

    return requests

def get_admin_name(telegram_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
                SELECT name FROM admins
                WHERE telegram_id = %s
                """, (telegram_id,))

    row = cur.fetchone()

    cur.close()
    conn.close()

    if row:
        return row[0]

    return None
