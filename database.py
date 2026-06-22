import sqlite3
from config import DATABASE

def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute('''
                CREATE TABLE IF NOT EXISTS ArtFlow_bid
                (
                    id
                    INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER,
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
                    INTEGER
                    PRIMARY
                    KEY
                    AUTOINCREMENT,
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
    conn.close()


def get_user_requests(telegram_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
SELECT
id, city, name_team, status
FROM
ArtFlow_bid
WHERE
telegram_id = ?''',
                (telegram_id,))

    requests = cur.fetchall()
    conn.close()
    return requests