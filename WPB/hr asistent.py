import streamlit as st
import sqlite3
import google.generativeai as genai

# ----------------- THEME SELECTOR -----------------
theme = st.sidebar.radio("🌈 Choose Theme", ["Light", "Dark", "Custom"])
if theme == "Light":
    bg_color, user_color, bot_color, bot_border = "#FFFFFF", "#DCF8C6", "#FFFFFF", "#DDD"
elif theme == "Dark":
    bg_color, user_color, bot_color, bot_border = "#1E1E1E", "#056162", "#2A2A2A", "#444"
else:
    bg_color, user_color, bot_color, bot_border = "#87F1DC", "#B6F7C1", "#FFFFFF", "#DDD"

if theme == "Dark":
    title_color, subtitle_color, user_text_color, bot_text_color = "white", "lightgray", "white", "white"
else:
    title_color, subtitle_color, user_text_color, bot_text_color = "black", "gray", "black", "black"

st.markdown(f"""
    <style>
    .stApp {{background-color: {bg_color};}}
    .chat-container {{max-width: 600px; margin: auto; padding-bottom: 100px;}}
    .message {{
        padding: 10px 15px; border-radius: 20px; margin: 10px;
        display: inline-block; max-width: 80%; word-wrap: break-word; font-size: 15px;
    }}
    .user {{
        background-color: {user_color};
        margin-left: auto; display: block; text-align: right;
        color: {user_text_color};
    }}
    .bot {{
        background-color: {bot_color};
        border: 1px solid {bot_border};
        margin-right: auto; display: block; text-align: left;
        color: {bot_text_color};
    }}
    .sticky-bar {{
        position: fixed; bottom: 0; left: 0; right: 0;
        background: white; padding: 10px;
        border-top: 1px solid #ddd;
        display: flex; gap: 10px; z-index: 1000; align-items: center;
    }}
    </style>
""", unsafe_allow_html=True)

# ----------------- TITLE -----------------
st.markdown(f"<h1 style='text-align: center; color:{title_color};'>HR Assistant</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; font-size:18px; color:{subtitle_color};'>Manage employees, leaves & chatbot</p>", unsafe_allow_html=True)

# ----------------- GEMINI SETUP -----------------
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-2.0-flash")

# ----------------- DATABASE -----------------
DB = "employees.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT, last_name TEXT,
        email TEXT UNIQUE, phone TEXT,
        department TEXT, position TEXT,
        date_of_hire TEXT, salary REAL,
        address TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS leaves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id INTEGER,
        start_date TEXT,
        end_date TEXT,
        reason TEXT,
        status TEXT DEFAULT 'Pending',
        FOREIGN KEY(emp_id) REFERENCES employees(id)
    )""")
    conn.commit()
    conn.close()

def add_employee(data):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""INSERT INTO employees
        (first_name,last_name,email,phone,department,position,date_of_hire,salary,address)
        VALUES (?,?,?,?,?,?,?,?,?)""", data)
    conn.commit()
    conn.close()

def get_employees():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM employees")
    rows = c.fetchall()
    conn.close()
    return rows

def apply_leave(emp_id, start, end, reason):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO leaves (emp_id,start_date,end_date,reason) VALUES (?,?,?,?)",
              (emp_id,start,end,reason))
    conn.commit()
    conn.close()

def get_leaves():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""SELECT leaves.id, employees.first_name||' '||employees.last_name, 
                        leaves.start_date, leaves.end_date, leaves.reason, leaves.status, leaves.emp_id
                 FROM leaves JOIN employees ON leaves.emp_id = employees.id""")
    rows = c.fetchall()
    conn.close()
    return rows

def get_leaves_by_employee(emp_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT start_date,end_date,reason,status FROM leaves WHERE emp_id=?", (emp_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def update_leave_status(leave_id, status):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE leaves SET status=? WHERE id=?", (status,leave_id))
    conn.commit()
    conn.close()

init_db()

# ----------------- SIDEBAR: EMPLOYEE + LEAVE -----------------
st.sidebar.subheader("➕ Add New Employee")
with st.sidebar.form("emp_form"):
    fname = st.text_input("First Name")
    lname = st.text_input("Last Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone")
    dept = st.text_input("Department")
    pos = st.text_input("Position")
    doh = st.date_input("Date of Hire")
    salary = st.number_input("Salary", min_value=0.0, step=1000.0)
    addr = st.text_area("Address")
    submit = st.form_submit_button("Save Employee")
    if submit:
        try:
            add_employee((fname,lname,email,phone,dept,pos,str(doh),salary,addr))
            st.sidebar.success("✅ Employee Added!")
        except Exception as e:
            st.sidebar.error(f"⚠️ Error: {e}")

st.sidebar.subheader("📝 Apply for Leave")
with st.sidebar.form("leave_form"):
    employees = get_employees()
    emp_map = {f"{e[1]} {e[2]}": e[0] for e in employees}
    emp_name = st.selectbox("Select Employee", list(emp_map.keys()) if emp_map else ["No employees"])
    start = st.date_input("Start Date")
    end = st.date_input("End Date")
    reason = st.text_area("Reason")
    leave_submit = st.form_submit_button("Apply Leave")
    if leave_submit and employees:
        apply_leave(emp_map[emp_name], str(start), str(end), reason)
        st.sidebar.success("✅ Leave Applied!")

# ----------------- EMPLOYEE LIST + LEAVE HISTORY -----------------
st.subheader("👥 Employee Records with Leave History")
rows = get_employees()
if rows:
    for r in rows:
        st.markdown(f"### {r[1]} {r[2]}  ({r[5]} - {r[6]})")
        st.write(f"📧 {r[3]} | 📱 {r[4]} | 💰 {r[7]} | 🏠 {r[8]} | Hired: {r[6]}")
        
        # show leave history
        leaves = get_leaves_by_employee(r[0])
        if leaves:
            st.write("**Leave History:**")
            for l in leaves:
                st.write(f"📅 {l[0]} → {l[1]} | {l[2]} | Status: {l[3]}")
        else:
            st.write("_No leaves applied yet_")
        st.divider()
else:
    st.info("No employees yet. Add from sidebar.")

# ----------------- LEAVE LIST (Approve/Reject) -----------------
st.subheader("📌 Pending Leave Requests")
leaves = [l for l in get_leaves() if l[5] == "Pending"]
if leaves:
    for l in leaves:
        col1, col2, col3 = st.columns([3,2,2])
        with col1:
            st.write(f"**{l[1]}** ({l[2]} → {l[3]}) \nReason: {l[4]} \nStatus: {l[5]}")
        with col2:
            if st.button("✅ Approve", key=f"approve_{l[0]}"):
                update_leave_status(l[0], "Approved")
                st.rerun()
        with col3:
            if st.button("❌ Reject", key=f"reject_{l[0]}"):
                update_leave_status(l[0], "Rejected")
                st.rerun()
else:
    st.info("No pending leave requests.")

# ----------------- CHAT HISTORY -----------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_input" not in st.session_state:
    st.session_state.chat_input = ""

st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
for msg in st.session_state.messages:
    role = "user" if msg["role"] == "user" else "bot"
    st.markdown(f"<div class='message {role}'>{msg['content']}</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ----------------- CHAT FUNCTION -----------------
def send_message():
    user_msg = st.session_state.chat_input.strip()
    if user_msg == "":
        return
    st.session_state.messages.append({"role": "user", "content": user_msg})

    try:
        employees = get_employees()
        leaves = get_leaves()
        context = f"Employees: {employees}\nLeaves: {leaves}\n\nUser query: {user_msg}"
        response = model.generate_content(context)
        reply = response.text
    except Exception as e:
        reply = f"⚠️ Error: {e}"

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.session_state.chat_input = ""
    st.rerun()

# ----------------- INPUT BAR -----------------
st.markdown('<div class="sticky-bar">', unsafe_allow_html=True)
col1, col2 = st.columns([10, 1])
with col1:
    st.text_input("Type a message...", key="chat_input", label_visibility="collapsed", on_change=send_message)
with col2:
    if st.button("➤"):
        send_message()
st.markdown('</div>', unsafe_allow_html=True)
