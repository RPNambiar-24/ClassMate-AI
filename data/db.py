import sqlite3
import json
import os

DB_PATH = "data/classmate.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs("data", exist_ok=True)
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            chat_id     INTEGER PRIMARY KEY,
            name        TEXT,
            timezone    TEXT DEFAULT 'Asia/Kolkata',
            created_at  TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS timetable (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id     INTEGER,
            day         TEXT,
            time        TEXT,
            subject     TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id     INTEGER,
            type        TEXT,
            subject     TEXT,
            due_date    TEXT,
            done        INTEGER DEFAULT 0,
            added_on    TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS overrides (
            chat_id     INTEGER PRIMARY KEY,
            date        TEXT,
            classes     TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS saturday_overrides (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id     INTEGER,
            date        TEXT,
            day_used    TEXT,
            classes     TEXT
        )
    """)

    conn.commit()
    conn.close()


def is_registered(chat_id: int) -> bool:
    conn = get_conn()
    row = conn.execute("SELECT chat_id FROM users WHERE chat_id=?", (chat_id,)).fetchone()
    conn.close()
    return row is not None


def register_user(chat_id: int, name: str):
    from datetime import datetime
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO users (chat_id, name, created_at) VALUES (?, ?, ?)",
        (chat_id, name, datetime.now().strftime("%Y-%m-%d"))
    )
    conn.commit()
    conn.close()


def get_user_name(chat_id: int) -> str:
    conn = get_conn()
    row = conn.execute("SELECT name FROM users WHERE chat_id=?", (chat_id,)).fetchone()
    conn.close()
    return row["name"] if row else "Student"
