import json
from datetime import datetime
from data.db import get_conn
from utils.google_calendar import create_event, delete_event_by_title


def add_assignment(chat_id: int, subject: str, due_date: str, type_: str = "assignment") -> str:
    try:
        datetime.strptime(due_date, "%Y-%m-%d")
    except ValueError:
        return "❌ Invalid date. Use *YYYY-MM-DD* (e.g. 2026-03-01)."

    conn = get_conn()
    conn.execute(
        "INSERT INTO assignments (chat_id, type, subject, due_date, done, added_on) VALUES (?,?,?,?,0,?)",
        (chat_id, type_, subject, due_date, datetime.now().strftime("%Y-%m-%d"))
    )
    conn.commit()
    row = conn.execute(
        "SELECT id FROM assignments WHERE chat_id=? ORDER BY id DESC LIMIT 1", (chat_id,)
    ).fetchone()
    conn.close()

    emoji = "📝" if type_ == "assignment" else "📋"
    type_label = "Assignment" if type_ == "assignment" else "Test"
    days_left = (datetime.strptime(due_date, "%Y-%m-%d") - datetime.now()).days
    calendar_msg = create_event(subject, due_date, type_)

    return (
        f"{emoji} *{type_label} Added!*\n"
        f"📚 Subject: *{subject}*\n"
        f"📅 Due: *{due_date}* ({days_left}d left)\n"
        f"🆔 ID: #{row['id']}\n"
        f"{calendar_msg}"
    )


def view_assignments(chat_id: int, filter_type: str = None) -> str:
    conn = get_conn()
    today = datetime.now().strftime("%Y-%m-%d")
    query = "SELECT * FROM assignments WHERE chat_id=? AND done=0 AND due_date>=? ORDER BY due_date"
    rows = conn.execute(query, (chat_id, today)).fetchall()
    conn.close()

    pending = [dict(r) for r in rows]
    if filter_type:
        pending = [r for r in pending if r["type"] == filter_type]

    if not pending:
        return "🎉 No pending items!"

    header = {
        "assignment": "📝 *Upcoming Assignments*\n",
        "test": "📋 *Upcoming Tests*\n",
        None: "📌 *All Upcoming Tasks*\n"
    }[filter_type]

    lines = [header]
    for item in pending:
        emoji = "📝" if item["type"] == "assignment" else "📋"
        days_left = (datetime.strptime(item["due_date"], "%Y-%m-%d") - datetime.now()).days
        urgency = "🔴" if days_left <= 1 else "🟡" if days_left <= 3 else "🟢"
        lines.append(
            f"{urgency} {emoji} [#{item['id']}] *{item['subject']}*\n"
            f"   📅 {item['due_date']} — {days_left}d left"
        )
    return "\n".join(lines)


def mark_done(chat_id: int, item_id: int) -> str:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM assignments WHERE id=? AND chat_id=?", (item_id, chat_id)
    ).fetchone()
    if not row:
        conn.close()
        return f"❌ No item with ID #{item_id}."
    conn.execute("UPDATE assignments SET done=1 WHERE id=?", (item_id,))
    conn.commit()
    conn.close()
    delete_event_by_title(row["subject"], row["due_date"])
    emoji = "📝" if row["type"] == "assignment" else "📋"
    return f"✅ {emoji} *{row['subject']}* marked as done!"


def delete_assignment(chat_id: int, item_id: int) -> str:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM assignments WHERE id=? AND chat_id=?", (item_id, chat_id)
    ).fetchone()
    if not row:
        conn.close()
        return f"❌ No item with ID #{item_id}."
    conn.execute("DELETE FROM assignments WHERE id=?", (item_id,))
    conn.commit()
    conn.close()
    delete_event_by_title(row["subject"], row["due_date"])
    return f"🗑️ Deleted *{row['subject']}* (#{item_id})."


def get_due_soon(chat_id: int, days: int = 1) -> list:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM assignments WHERE chat_id=? AND done=0", (chat_id,)
    ).fetchall()
    conn.close()
    result = []
    for row in rows:
        try:
            due = datetime.strptime(row["due_date"], "%Y-%m-%d")
            diff = (due - datetime.now()).days
            if 0 <= diff <= days:
                result.append(dict(row))
        except Exception:
            pass
    return result


def get_all_pending(chat_id: int) -> list:
    conn = get_conn()
    today = datetime.now().strftime("%Y-%m-%d")
    rows = conn.execute(
        "SELECT * FROM assignments WHERE chat_id=? AND done=0 AND due_date>=?",
        (chat_id, today)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
