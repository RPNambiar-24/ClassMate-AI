import os
import streamlit as st
import psycopg2
import psycopg2.extras
from datetime import datetime
import pytz

DATABASE_URL = os.getenv("DATABASE_URL")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "classmate123")
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

# ── Auth ──────────────────────────────────────────────
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("🔒 ClassMate AI Dashboard")
        pwd = st.text_input("Enter password", type="password")
        if st.button("Login"):
            if pwd == DASHBOARD_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Wrong password!")
        st.stop()

# ── Data helpers ──────────────────────────────────────
def get_all_users():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT chat_id, name, joined_at FROM users ORDER BY joined_at DESC")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def get_timetable(chat_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, day, time, subject FROM timetable WHERE chat_id=%s ORDER BY day, time", (chat_id,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def get_tasks(chat_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, type, subject, due_date, done FROM tasks WHERE chat_id=%s ORDER BY due_date", (chat_id,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def add_class_db(chat_id, day, time, subject):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO timetable (chat_id, day, time, subject) VALUES (%s,%s,%s,%s)",
                (chat_id, day, time, subject))
    conn.commit(); cur.close(); conn.close()

def delete_class_db(row_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM timetable WHERE id=%s", (row_id,))
    conn.commit(); cur.close(); conn.close()

def delete_task_db(row_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id=%s", (row_id,))
    conn.commit(); cur.close(); conn.close()

def mark_done_db(row_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET done=1 WHERE id=%s", (row_id,))
    conn.commit(); cur.close(); conn.close()

# ── Main App ──────────────────────────────────────────
check_password()

st.set_page_config(page_title="ClassMate AI", page_icon="🎓", layout="wide")
st.title("🎓 ClassMate AI Dashboard")

users = get_all_users()
if not users:
    st.warning("No users registered yet. Send /start to the bot first.")
    st.stop()

# User selector
user_options = {f"{u[1]} ({u[0]})": u[0] for u in users}
selected_label = st.sidebar.selectbox("👤 Select User", list(user_options.keys()))
chat_id = user_options[selected_label]

page = st.sidebar.radio("📂 Page", ["📅 Timetable", "📌 Tasks", "👥 All Users"])

# ── Timetable Page ────────────────────────────────────
if page == "📅 Timetable":
    st.header("📅 Timetable")
    rows = get_timetable(chat_id)

    if rows:
        for day in DAYS:
            day_rows = [r for r in rows if r[1] == day]
            if day_rows:
                st.subheader(f"📆 {day}")
                for r in day_rows:
                    col1, col2, col3, col4 = st.columns([1, 2, 1, 1])
                    col1.write(f"🕐 `{r[2]}`")
                    col2.write(f"**{r[3]}**")
                    if col4.button("🗑️ Delete", key=f"del_tt_{r[0]}"):
                        delete_class_db(r[0])
                        st.success("Deleted!")
                        st.rerun()
    else:
        st.info("No timetable found. Add classes below or import via bot.")

    st.divider()
    st.subheader("➕ Add Class")
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    day_in = col1.selectbox("Day", DAYS, key="add_day")
    time_in = col2.text_input("Time (HH:MM)", placeholder="09:00", key="add_time")
    subj_in = col3.text_input("Subject", placeholder="Mathematics", key="add_subj")
    if col4.button("➕ Add", key="add_btn"):
        if day_in and time_in and subj_in:
            add_class_db(chat_id, day_in, time_in, subj_in)
            st.success(f"Added {subj_in} on {day_in} at {time_in}!")
            st.rerun()
        else:
            st.error("Fill all fields.")

# ── Tasks Page ────────────────────────────────────────
elif page == "📌 Tasks":
    st.header("📌 Tasks")
    rows = get_tasks(chat_id)

    pending = [r for r in rows if not r[4]]
    done = [r for r in rows if r[4]]

    st.subheader("🔴 Pending")
    if pending:
        for r in pending:
            col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 1, 1])
            emoji = "📝" if r[1] == "assignment" else "📋"
            days_left = (datetime.strptime(r[3], "%Y-%m-%d") - datetime.now()).days
            urg = "🔴" if days_left <= 0 else "🟡" if days_left <= 2 else "🟢"
            col1.write(f"{urg} {emoji}")
            col2.write(f"**{r[2]}**")
            col3.write(f"{r[3]} ({days_left}d left)")
            if col4.button("✅", key=f"done_{r[0]}"):
                mark_done_db(r[0])
                st.rerun()
            if col5.button("🗑️", key=f"del_task_{r[0]}"):
                delete_task_db(r[0])
                st.rerun()
    else:
        st.success("All clear! No pending tasks. ✅")

    if done:
        with st.expander(f"✅ Completed ({len(done)})"):
            for r in done:
                col1, col2, col3 = st.columns([1, 3, 1])
                col1.write("✅")
                col2.write(f"~~{r[2]}~~ — {r[3]}")
                if col3.button("🗑️", key=f"del_done_{r[0]}"):
                    delete_task_db(r[0])
                    st.rerun()

# ── Users Page ────────────────────────────────────────
elif page == "👥 All Users":
    st.header("👥 Registered Users")
    st.metric("Total Users", len(users))
    for u in users:
        st.write(f"👤 **{u[1]}** — `{u[0]}` — joined {u[2][:10]}")
