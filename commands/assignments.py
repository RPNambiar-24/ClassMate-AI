from data.db import get_conn
from datetime import datetime, timedelta


def add_assignment(chat_id, subject, due_date, task_type):
    try:
        datetime.strptime(due_date, "%Y-%m-%d")
    except ValueError:
        return "❌ Invalid date format. Use *YYYY-MM-DD*."
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (chat_id, type, subject, due_date) VALUES (%s, %s, %s, %s)",
        (str(chat_id), task_type, subject, due_date)
    )
    conn.commit()
    cur.close()
    conn.close()
    emoji = "📝" if task_type == "assignment" else "📋"
    return f"{emoji} Added *{subject}* {task_type} due *{due_date}*."


def view_assignments(chat_id, task_type=None):
    conn = get_conn()
    cur = conn.cursor()
    if task_type:
        cur.execute(
            "SELECT id, type, subject, due_date FROM tasks WHERE chat_id=%s AND type=%s AND done=0 ORDER BY due_date",
            (str(chat_id), task_type)
        )
    else:
        cur.execute(
            "SELECT id, type, subject, due_date FROM tasks WHERE chat_id=%s AND done=0 ORDER BY due_date",
            (str(chat_id),)
        )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    if not rows:
        label = task_type.capitalize() + "s" if task_type else "Tasks"
        return f"✅ No pending {label}!"
    label = task_type.capitalize() + "s" if task_type else "All Tasks"
    lines = [f"📌 *{label}*\n"]
    for r in rows:
        emoji = "📝" if r[1] == "assignment" else "📋"
        days_left = (datetime.strptime(r[3], "%Y-%m-%d") - datetime.now()).days
        urg = "🔴" if days_left <= 0 else "🟡" if days_left <= 2 else "🟢"
        lines.append(f"{urg} {emoji} `#{r[0]}` *{r[2]}* — {r[3]} ({days_left}d left)")
    return "\n".join(lines)


def get_all_pending(chat_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, type, subject, due_date FROM tasks WHERE chat_id=%s AND done=0 ORDER BY due_date",
        (str(chat_id),)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "type": r[1], "subject": r[2], "due_date": r[3]} for r in rows]


def get_due_soon(chat_id, days=2):
    cutoff = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, type, subject, due_date FROM tasks WHERE chat_id=%s AND done=0 AND due_date<=%s ORDER BY due_date",
        (str(chat_id), cutoff)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "type": r[1], "subject": r[2], "due_date": r[3]} for r in rows]


def mark_done(chat_id, task_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE tasks SET done=1 WHERE chat_id=%s AND id=%s",
        (str(chat_id), task_id)
    )
    updated = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return f"✅ Task `#{task_id}` marked as done!" if updated else f"❌ Task `#{task_id}` not found."


def delete_assignment(chat_id, task_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM tasks WHERE chat_id=%s AND id=%s",
        (str(chat_id), task_id)
    )
    deleted = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return f"🗑️ Task `#{task_id}` deleted." if deleted else f"❌ Task `#{task_id}` not found."
