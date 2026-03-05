from data.db import get_conn
from datetime import datetime, timedelta

def add_assignment(chat_id, subject, due_date, task_type):
    try:
        datetime.strptime(due_date, "%Y-%m-%d")
    except ValueError:
        return "❌ Invalid date format. Use *YYYY-MM-DD*."
    conn = get_conn()
    conn.execute(
        "INSERT INTO tasks (chat_id, type, subject, due_date) VALUES (?, ?, ?, ?)",
        (str(chat_id), task_type, subject, due_date)
    )
    conn.commit()
    conn.close()
    emoji = "📝" if task_type == "assignment" else "📋"
    return f"{emoji} Added *{subject}* {task_type} due *{due_date}*."

def view_assignments(chat_id, task_type=None):
    conn = get_conn()
    if task_type:
        rows = conn.execute(
            "SELECT id, type, subject, due_date FROM tasks WHERE chat_id=? AND type=? AND done=0 ORDER BY due_date",
            (str(chat_id), task_type)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, type, subject, due_date FROM tasks WHERE chat_id=? AND done=0 ORDER BY due_date",
            (str(chat_id),)
        ).fetchall()
    conn.close()
    if not rows:
        label = task_type.capitalize() + "s" if task_type else "Tasks"
        return f"✅ No pending {label}!"
    label = task_type.capitalize() + "s" if task_type else "All Tasks"
    lines = [f"📌 *{label}*\n"]
    for r in rows:
        emoji = "📝" if r["type"] == "assignment" else "📋"
        days_left = (datetime.strptime(r["due_date"], "%Y-%m-%d") - datetime.now()).days
        urg = "🔴" if days_left <= 0 else "🟡" if days_left <= 2 else "🟢"
        lines.append(f"{urg} {emoji} `#{r['id']}` *{r['subject']}* — {r['due_date']} ({days_left}d left)")
    return "\n".join(lines)

def get_all_pending(chat_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, type, subject, due_date FROM tasks WHERE chat_id=? AND done=0 ORDER BY due_date",
        (str(chat_id),)
    ).fetchall()
    conn.close()
    return [{"id": r["id"], "type": r["type"], "subject": r["subject"], "due_date": r["due_date"]} for r in rows]

def get_due_soon(chat_id, days=2):
    cutoff = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, type, subject, due_date FROM tasks WHERE chat_id=? AND done=0 AND due_date<=? ORDER BY due_date",
        (str(chat_id), cutoff)
    ).fetchall()
    conn.close()
    return [{"id": r["id"], "type": r["type"], "subject": r["subject"], "due_date": r["due_date"]} for r in rows]

def mark_done(chat_id, task_id):
    conn = get_conn()
    updated = conn.execute(
        "UPDATE tasks SET done=1 WHERE chat_id=? AND id=?",
        (str(chat_id), task_id)
    ).rowcount
    conn.commit()
    conn.close()
    return f"✅ Task `#{task_id}` marked as done!" if updated else f"❌ Task `#{task_id}` not found."

def delete_assignment(chat_id, task_id):
    conn = get_conn()
    deleted = conn.execute(
        "DELETE FROM tasks WHERE chat_id=? AND id=?",
        (str(chat_id), task_id)
    ).rowcount
    conn.commit()
    conn.close()
    return f"🗑️ Task `#{task_id}` deleted." if deleted else f"❌ Task `#{task_id}` not found."
