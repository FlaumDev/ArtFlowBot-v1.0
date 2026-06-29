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
                    status TEXT DEFAULT 'На рассмотрении'
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
        WHERE ORDER BY id ASC
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