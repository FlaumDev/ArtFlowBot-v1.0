import psycopg2
from dotenv import load_dotenv
import os
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

def search_requests_by_participant(participant_name):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute('''
    SELECT DISTINCT ArtFlow_bid.* FROM ArtFlow_bid
    JOIN participants ON participants.bid_id = ArtFlow_bid.id
    WHERE participants.participant_name ILIKE %s
    ORDER BY ArtFlow_bid.id ASC
    ''', (f"%{participant_name}%",))

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
