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
                    music_file_name TEXT
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


