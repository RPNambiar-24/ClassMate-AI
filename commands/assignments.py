from data.db import get_conn
from datetime import datetime, timedelta

def add_task(chat_id, task_type, subject, due_date):
    conn = get_conn()
    conn.execute(
        "INSERT INTO tasks (chat_id, type, subject, due_date) VALUES (?, ?, ?, ?)",
        (str(chat_id), task_type, subject, due_date)
    )
    conn.commit()
    conn.close()

def get_all_pending(chat_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, type, subject, due_date FROM tasks WHERE chat_id=? AND done=0 ORDER BY due_date",
        (str(chat_id),)
    ).fetchall()
    conn.close()
    return [{"id": r["id"], "type": r["type"], "subject": r["subject"], "due_date": r["due_date"]} for r in rows]

def get_due_soon(chat_id, days=2):
    conn = get_conn()
    cutoff = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    rows = conn.execute(
        "SELECT id, type, subject, due_date FROM tasks WHERE chat_id=? AND done=0 AND due_date<=? ORDER BY due_date",
        (str(chat_id), cutoff)
    ).fetchall()
    conn.close()
    return [{"id": r["id"], "type": r["type"], "subject": r["subject"], "due_date": r["due_date"]} for r in rows]

def mark_done(chat_id, task_id):
    conn = get_conn()
    conn.execute(
        "UPDATE tasks SET done=1 WHERE chat_id=? AND id=?",
        (str(chat_id), task_id)
    )
    conn.commit()
    conn.close()

def delete_task(chat_id, task_id):
    conn = get_conn()
    conn.execute(
        "DELETE FROM tasks WHERE chat_id=? AND id=?",
        (str(chat_id), task_id)
    )
    conn.commit()
    conn.close()
