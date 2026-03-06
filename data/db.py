import os
import psycopg2
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")


def get_conn():
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    conn.autocommit = False
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            chat_id TEXT PRIMARY KEY,
            name TEXT,
            joined_at TEXT,
            dashboard_password TEXT
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS timetable (
            id SERIAL PRIMARY KEY,
            chat_id TEXT,
            day TEXT,
            subject TEXT,
            time TEXT
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            chat_id TEXT,
            type TEXT,
            subject TEXT,
            due_date TEXT,
            done INTEGER DEFAULT 0
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS overrides (
            chat_id TEXT,
            date TEXT,
            mapped_day TEXT,
            PRIMARY KEY (chat_id, date)
        );
    """)
    cur.execute("""
        ALTER TABLE users ADD COLUMN IF NOT EXISTS dashboard_password TEXT;
    """)
    conn.commit()
    cur.close()
    conn.close()


def is_registered(chat_id) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE chat_id=%s", (str(chat_id),))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row is not None


def register_user(chat_id, name):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (chat_id, name, joined_at) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
        (str(chat_id), name, datetime.now().isoformat())
    )
    conn.commit()
    cur.close()
    conn.close()


def get_user_name(chat_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT name FROM users WHERE chat_id=%s", (str(chat_id),))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else "Student"


def get_all_chat_ids():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT chat_id FROM users")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [r[0] for r in rows]


def set_dashboard_password(chat_id, password):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET dashboard_password=%s WHERE chat_id=%s",
        (password, str(chat_id))
    )
    conn.commit()
    cur.close()
    conn.close()


def verify_dashboard_password(password):
    """Returns chat_id if password matches any user, else None."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT chat_id FROM users WHERE dashboard_password=%s", (password,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None
