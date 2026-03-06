import os
import psycopg2
import streamlit as st
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode="require")


# ── Auth ──────────────────────────────────────────────
def verify_password(password):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT chat_id FROM users WHERE dashboard_password=%s", (password,))
        row = cur.fetchone()
        cur.close(); conn.close()
        return row[0] if row else None
    except:
        return None


def get_user_name(chat_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT name FROM users WHERE chat_id=%s", (str(chat_id),))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row[0] if row else "Student"


def login_page():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background: #0f0f1a; }
        .login-wrap {
            max-width: 420px;
            margin: 6rem auto;
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            padding: 3rem 2.5rem;
            border-radius: 20px;
            box-shadow: 0 8px 40px rgba(0,212,255,0.15);
            text-align: center;
        }
        .brand { font-size: 2.8rem; font-weight: 800; color: #00d4ff; letter-spacing: -1px; }
        .tagline { color: #888; margin-top: 0.3rem; margin-bottom: 2rem; font-size: 0.95rem; }
        </style>
        <div class="login-wrap">
            <div class="brand">🎓 ClassMate AI</div>
            <div class="tagline">Your personal academic assistant</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col = st.columns([1, 2, 1])[1]
    with col:
        st.subheader("🔐 Login")
        password = st.text_input("Password", type="password", placeholder="Set via /setpassword in bot")
        if st.button("🚀 Login", use_container_width=True):
            if not password:
                st.error("Enter your password.")
            else:
                chat_id = verify_password(password)
                if chat_id:
                    st.session_state.authenticated = True
                    st.session_state.chat_id = chat_id
                    st.session_state.name = get_user_name(chat_id)
                    st.rerun()
                else:
                    st.error("❌ Invalid password.")
        st.info("💡 Set your password in the bot: `/setpassword yourpassword`")


# ── DB Helpers ────────────────────────────────────────
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


def get_overrides(chat_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT date, mapped_day FROM overrides WHERE chat_id=%s ORDER BY date", (chat_id,))
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


def add_task_db(chat_id, task_type, subject, due_date):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (chat_id, type, subject, due_date) VALUES (%s,%s,%s,%s)",
                (chat_id, task_type, subject, due_date))
    conn.commit(); cur.close(); conn.close()


def mark_done_db(row_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET done=1 WHERE id=%s", (row_id,))
    conn.commit(); cur.close(); conn.close()


def delete_task_db(row_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id=%s", (row_id,))
    conn.commit(); cur.close(); conn.close()


def set_saturday_db(chat_id, date, mapped_day):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO overrides (chat_id, date, mapped_day) VALUES (%s,%s,%s)
        ON CONFLICT (chat_id, date) DO UPDATE SET mapped_day=%s
    """, (chat_id, date, mapped_day, mapped_day))
    conn.commit(); cur.close(); conn.close()


def delete_override_db(chat_id, date):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM overrides WHERE chat_id=%s AND date=%s", (chat_id, date))
    conn.commit(); cur.close(); conn.close()


def update_password_db(chat_id, password):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET dashboard_password=%s WHERE chat_id=%s", (password, chat_id))
    conn.commit(); cur.close(); conn.close()


# ── Styles ────────────────────────────────────────────
def apply_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

        .main-header {
            background: linear-gradient(135deg, #00d4ff, #0077ff);
            padding: 1.5rem 2rem;
            border-radius: 16px;
            margin-bottom: 1.5rem;
            color: white;
        }
        .main-header h1 { margin: 0; font-size: 1.8rem; font-weight: 800; }
        .main-header p  { margin: 0.3rem 0 0 0; opacity: 0.85; font-size: 0.9rem; }

        .stat-card {
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            border: 1px solid #00d4ff33;
            border-radius: 12px;
            padding: 1.2rem;
            text-align: center;
            color: white;
        }
        .stat-number { font-size: 2rem; font-weight: 800; color: #00d4ff; }
        .stat-label  { color: #aaa; font-size: 0.8rem; margin-top: 0.2rem; }

        .class-row {
            background: #1a1a2e;
            border-left: 4px solid #00d4ff;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            margin: 0.25rem 0;
            color: white;
            font-size: 0.9rem;
        }
        .task-urgent { border-left-color: #ff4444 !important; }
        .task-soon   { border-left-color: #ffaa00 !important; }
        .task-ok     { border-left-color: #00cc66 !important; }
        </style>
    """, unsafe_allow_html=True)


# ── App Entry ─────────────────────────────────────────
st.set_page_config(
    page_title="ClassMate AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)
apply_styles()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    login_page()
    st.stop()

chat_id = st.session_state.chat_id
name = st.session_state.name

# ── Sidebar ───────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
        <div style='text-align:center; padding:1rem 0;'>
            <div style='font-size:2.5rem;'>🎓</div>
            <div style='font-size:1.1rem; font-weight:800; color:#00d4ff;'>ClassMate AI</div>
            <div style='color:#aaa; font-size:0.82rem; margin-top:0.3rem;'>Welcome, {name}!</div>
        </div>
    """, unsafe_allow_html=True)
    st.divider()
    page = st.radio("Navigate", [
        "🏠 Overview",
        "📅 Timetable",
        "📅 Saturday Setup",
        "📌 Tasks",
        "⚙️ Settings"
    ])
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# ── Header ────────────────────────────────────────────
st.markdown(f"""
    <div class="main-header">
        <h1>🎓 ClassMate AI Dashboard</h1>
        <p>Hello, {name}! Manage your timetable, tasks and schedule — all in one place.</p>
    </div>
""", unsafe_allow_html=True)

# ── Overview ──────────────────────────────────────────
if page == "🏠 Overview":
    tt_rows   = get_timetable(chat_id)
    task_rows = get_tasks(chat_id)
    pending   = [r for r in task_rows if not r[4]]
    overdue   = [r for r in pending if (datetime.strptime(r[3], "%Y-%m-%d") - datetime.now()).days < 0]
    today     = datetime.now().strftime("%A")
    today_cls = [r for r in tt_rows if r[1] == today]

    c1, c2, c3, c4 = st.columns(4)
    for col, num, label in [
        (c1, len(tt_rows),     "Classes / Week"),
        (c2, len(today_cls),   "Classes Today"),
        (c3, len(pending),     "Pending Tasks"),
        (c4, len(overdue),     "Overdue"),
    ]:
        col.markdown(
            f'<div class="stat-card"><div class="stat-number">{num}</div>'
            f'<div class="stat-label">{label}</div></div>',
            unsafe_allow_html=True
        )

    st.markdown("---")
    left, right = st.columns(2)

    with left:
        st.subheader(f"📅 Today — {today}")
        if today_cls:
            for r in today_cls:
                st.markdown(f'<div class="class-row">🕐 <b>{r[2]}</b> — {r[3]}</div>', unsafe_allow_html=True)
        else:
            st.info("No classes today! 🎉")

    with right:
        st.subheader("⚠️ Upcoming Deadlines")
        upcoming = sorted(pending, key=lambda r: r[3])[:5]
        if upcoming:
            for r in upcoming:
                days_left = (datetime.strptime(r[3], "%Y-%m-%d") - datetime.now()).days
                cls = "task-urgent" if days_left <= 0 else "task-soon" if days_left <= 2 else "task-ok"
                emoji = "📝" if r[1] == "assignment" else "📋"
                st.markdown(
                    f'<div class="class-row {cls}">{emoji} <b>{r[2]}</b> — {r[3]} ({days_left}d left)</div>',
                    unsafe_allow_html=True
                )
        else:
            st.success("All clear! No upcoming deadlines. ✅")

# ── Timetable ─────────────────────────────────────────
elif page == "📅 Timetable":
    st.header("📅 Weekly Timetable")
    rows = get_timetable(chat_id)

    if rows:
        for day in DAYS:
            day_rows = [r for r in rows if r[1] == day]
            if day_rows:
                st.subheader(f"📆 {day}")
                for r in day_rows:
                    col1, col2, col3 = st.columns([2, 5, 1])
                    col1.markdown(f'<div class="class-row">🕐 {r[2]}</div>', unsafe_allow_html=True)
                    col2.write(f"**{r[3]}**")
                    if col3.button("🗑️", key=f"del_tt_{r[0]}"):
                        delete_class_db(r[0])
                        st.success("Deleted!")
                        st.rerun()
    else:
        st.info("No timetable yet. Add classes below or import a JSON via the bot.")

    st.divider()
    st.subheader("➕ Add Class")
    col1, col2, col3, col4 = st.columns([2, 2, 3, 1])
    day_in  = col1.selectbox("Day", DAYS, key="add_day")
    time_in = col2.text_input("Time (HH:MM)", placeholder="09:00")
    subj_in = col3.text_input("Subject", placeholder="e.g. Data Structures")
    if col4.button("➕ Add"):
        if day_in and time_in and subj_in:
            add_class_db(chat_id, day_in, time_in, subj_in)
            st.success(f"✅ Added {subj_in} on {day_in} at {time_in}!")
            st.rerun()
        else:
            st.error("Fill all fields.")

# ── Saturday Setup ────────────────────────────────────
elif page == "📅 Saturday Setup":
    st.header("📅 Saturday Timetable Setup")
    st.info("Set what timetable each Saturday should follow — any weekday, holiday, or normal.")

    overrides = get_overrides(chat_id)
    sat_overrides = []
    for o in overrides:
        try:
            if datetime.strptime(o[0], "%Y-%m-%d").weekday() == 5:
                sat_overrides.append(o)
        except:
            pass

    if sat_overrides:
        st.subheader("📋 Upcoming Saturday Overrides")
        for o in sat_overrides:
            col1, col2, col3 = st.columns([2, 3, 1])
            col1.write(f"📅 **{o[0]}**")
            col2.write(f"→ *{o[1]}*")
            if col3.button("🗑️", key=f"del_sat_{o[0]}"):
                delete_override_db(chat_id, o[0])
                st.rerun()
    else:
        st.info("No Saturday overrides set yet.")

    st.divider()
    st.subheader("➕ Set Saturday Override")
    col1, col2, col3 = st.columns([2, 3, 1])
    sat_date = col1.date_input("Saturday Date")
    mapped   = col2.selectbox("Follows Timetable Of", DAYS + ["holiday"])
    if col3.button("✅ Set"):
        set_saturday_db(chat_id, str(sat_date), mapped)
        st.success(f"✅ Saturday {sat_date} → *{mapped}*!")
        st.rerun()

# ── Tasks ─────────────────────────────────────────────
elif page == "📌 Tasks":
    st.header("📌 Assignments & Tests")
    rows    = get_tasks(chat_id)
    pending = [r for r in rows if not r[4]]
    done    = [r for r in rows if r[4]]

    tab1, tab2 = st.tabs(["⏳ Pending", "✅ Completed"])

    with tab1:
        if pending:
            for r in pending:
                emoji     = "📝" if r[1] == "assignment" else "📋"
                days_left = (datetime.strptime(r[3], "%Y-%m-%d") - datetime.now()).days
                cls       = "task-urgent" if days_left <= 0 else "task-soon" if days_left <= 2 else "task-ok"
                c1, c2, c3, c4, c5 = st.columns([1, 3, 2, 1, 1])
                c1.write(emoji)
                c2.markdown(f'<div class="class-row {cls}"><b>{r[2]}</b></div>', unsafe_allow_html=True)
                c3.write(f"{r[3]} ({days_left}d left)")
                if c4.button("✅", key=f"done_{r[0]}"):
                    mark_done_db(r[0]); st.rerun()
                if c5.button("🗑️", key=f"del_t_{r[0]}"):
                    delete_task_db(r[0]); st.rerun()
        else:
            st.success("All clear! No pending tasks. ✅")

        st.divider()
        st.subheader("➕ Add Task")
        c1, c2, c3, c4 = st.columns([2, 3, 2, 1])
        type_in = c1.selectbox("Type", ["assignment", "test"])
        subj_in = c2.text_input("Subject", placeholder="e.g. Physics")
        date_in = c3.date_input("Due Date")
        if c4.button("➕ Add", key="add_task"):
            if subj_in:
                add_task_db(chat_id, type_in, subj_in, str(date_in))
                st.success("✅ Added!"); st.rerun()
            else:
                st.error("Enter a subject.")

    with tab2:
        if done:
            for r in done:
                c1, c2, c3 = st.columns([1, 5, 1])
                c1.write("✅")
                c2.write(f"~~{r[2]}~~ — {r[3]}")
                if c3.button("🗑️", key=f"del_done_{r[0]}"):
                    delete_task_db(r[0]); st.rerun()
        else:
            st.info("No completed tasks yet.")

# ── Settings ──────────────────────────────────────────
elif page == "⚙️ Settings":
    st.header("⚙️ Settings")

    st.subheader("👤 Your Info")
    st.write(f"**Name:** {name}")
    st.write(f"**Chat ID:** `{chat_id}`")

    st.divider()
    st.subheader("🔒 Change Password")
    st.info("You can also change it via the bot: `/setpassword newpassword`")
    new_pwd     = st.text_input("New Password", type="password")
    confirm_pwd = st.text_input("Confirm Password", type="password")
    if st.button("💾 Save Password"):
        if not new_pwd:
            st.error("Enter a password.")
        elif new_pwd != confirm_pwd:
            st.error("Passwords don't match.")
        elif len(new_pwd) < 4:
            st.error("Must be at least 4 characters.")
        else:
            update_password_db(chat_id, new_pwd)
            st.success("✅ Password updated! Use it next time you login.")
