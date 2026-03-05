import sqlite3
import os
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "data/classmate.db")

def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            chat_id TEXT PRIMARY KEY,
            name TEXT,
            joined_at TEXT
        );
        CREATE TABLE IF NOT EXISTS timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT,
            day TEXT,
            subject TEXT,
            time TEXT
        );
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT,
            type TEXT,
            subject TEXT,
            due_date TEXT,
            done INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS overrides (
            chat_id TEXT,
            date TEXT,
            mapped_day TEXT,
            PRIMARY KEY (chat_id, date)
        );
    """)
    conn.commit()
    conn.close()

def is_registered(chat_id) -> bool:
    conn = get_conn()
    row = conn.execute("SELECT 1 FROM users WHERE chat_id=?", (str(chat_id),)).fetchone()
    conn.close()
    return row is not None

def register_user(chat_id, name):
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO users (chat_id, name, joined_at) VALUES (?, ?, ?)",
        (str(chat_id), name, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def get_user_name(chat_id):
    conn = get_conn()
    row = conn.execute("SELECT name FROM users WHERE chat_id=?", (str(chat_id),)).fetchone()
    conn.close()
    return row["name"] if row else "Student"

def get_all_chat_ids():
    conn = get_conn()
    rows = conn.execute("SELECT chat_id FROM users").fetchall()
    conn.close()
    return [r["chat_id"] for r in rows]
