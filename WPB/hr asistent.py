import streamlit as st
import sqlite3
import google.generativeai as genai
from datetime import datetime, date
import pandas as pd

# ----------------- THEME SELECTOR -----------------
theme = st.sidebar.radio("🌈 Choose Theme", ["Light", "Dark", "Custom"])
if theme == "Light":
    bg_color, user_color, bot_color, bot_border = "#FFFFFF", "#DCF8C6", "#FFFFFF", "#DDD"
elif theme == "Dark":
    bg_color, user_color, bot_color, bot_border = "#1E1E1E", "#FFFFFF", "#2A2A2A", "#444"
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
st.markdown(f"<p style='text-align: center; font-size:18px; color:{subtitle_color};'>Manage employees, leaves, attendance, promotions & reports</p>", unsafe_allow_html=True)

# ----------------- GEMINI SETUP -----------------
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-2.0-flash")

# ----------------- DATABASE -----------------
DB = "employees.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    # Employees
    c.execute("""CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT, last_name TEXT,
        email TEXT UNIQUE, phone TEXT,
        department TEXT, position TEXT,
        date_of_hire TEXT, salary REAL,
        address TEXT
    )""")
    
    # Leaves
    c.execute("""CREATE TABLE IF NOT EXISTS leaves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id INTEGER,
        start_date TEXT,
        end_date TEXT,
        reason TEXT,
        status TEXT DEFAULT 'Pending',
        FOREIGN KEY(emp_id) REFERENCES employees(id)
    )""")
    
    # Attendance
    c.execute("""CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id INTEGER,
        date TEXT,
        check_in TEXT,
        check_out TEXT,
        FOREIGN KEY(emp_id) REFERENCES employees(id)
    )""")
    
    # Promotions
    c.execute("""CREATE TABLE IF NOT EXISTS promotions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id INTEGER,
        promotion_date TEXT,
        old_position TEXT,
        new_position TEXT,
        old_salary REAL,
        new_salary REAL,
        FOREIGN KEY(emp_id) REFERENCES employees(id)
    )""")
    
    conn.commit()
    conn.close()

# ----------------- EMPLOYEE FUNCTIONS -----------------
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

# ----------------- LEAVE FUNCTIONS -----------------
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

# ----------------- ATTENDANCE FUNCTIONS -----------------
def mark_check_in(emp_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    today = str(date.today())
    now = datetime.now().strftime("%H:%M:%S")
    c.execute("INSERT INTO attendance (emp_id,date,check_in) VALUES (?,?,?)", (emp_id,today,now))
    conn.commit()
    conn.close()

def mark_check_out(emp_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    today = str(date.today())
    now = datetime.now().strftime("%H:%M:%S")
    c.execute("UPDATE attendance SET check_out=? WHERE emp_id=? AND date=? AND check_out IS NULL", (now,emp_id,today))
    conn.commit()
    conn.close()

def get_attendance_by_employee(emp_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT date,check_in,check_out FROM attendance WHERE emp_id=?", (emp_id,))
    rows = c.fetchall()
    conn.close()
    return rows

# ----------------- PROMOTION FUNCTIONS -----------------
def add_promotion(emp_id, new_pos, new_sal):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    today = str(date.today())
    # get old data
    c.execute("SELECT position,salary FROM employees WHERE id=?", (emp_id,))
    old_pos, old_sal = c.fetchone()
    # update employee record
    c.execute("UPDATE employees SET position=?, salary=? WHERE id=?", (new_pos,new_sal,emp_id))
    # insert promotion record
    c.execute("""INSERT INTO promotions (emp_id,promotion_date,old_position,new_position,old_salary,new_salary)
                 VALUES (?,?,?,?,?,?)""", (emp_id,today,old_pos,new_pos,old_sal,new_sal))
    conn.commit()
    conn.close()

def get_promotions(emp_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT promotion_date,old_position,new_position,old_salary,new_salary FROM promotions WHERE emp_id=?", (emp_id,))
    rows = c.fetchall()
    conn.close()
    return rows

# ----------------- INIT -----------------
init_db()

# ----------------- SIDEBAR: EMPLOYEE + LEAVE + ATTENDANCE + PROMOTION -----------------
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

st.sidebar.subheader("⏱ Attendance")
with st.sidebar.form("attendance_form"):
    employees = get_employees()
    emp_map = {f"{e[1]} {e[2]}": e[0] for e in employees}
    emp_name = st.selectbox("Select Employee", list(emp_map.keys()) if emp_map else ["No employees"], key="att_emp")
    action = st.radio("Action", ["Check-in","Check-out"])
    att_submit = st.form_submit_button("Mark Attendance")
    if att_submit and employees:
        if action=="Check-in":
            mark_check_in(emp_map[emp_name])
            st.sidebar.success("✅ Check-in marked!")
        else:
            mark_check_out(emp_map[emp_name])
            st.sidebar.success("✅ Check-out marked!")

st.sidebar.subheader("🎖 Promotion")
with st.sidebar.form("promotion_form"):
    employees = get_employees()
    emp_map = {f"{e[1]} {e[2]}": e[0] for e in employees}
    emp_name = st.selectbox("Select Employee", list(emp_map.keys()) if emp_map else ["No employees"], key="prom_emp")
    new_pos = st.text_input("New Position")
    new_sal = st.number_input("New Salary", min_value=0.0, step=1000.0)
    prom_submit = st.form_submit_button("Promote Employee")
    if prom_submit and employees:
        add_promotion(emp_map[emp_name], new_pos, new_sal)
        st.sidebar.success("✅ Promotion Added!")

# ----------------- EMPLOYEE LIST -----------------
st.subheader("👥 Employee Records")
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
        
        # show attendance history
        att = get_attendance_by_employee(r[0])
        if att:
            st.write("**Attendance History:**")
            for a in att[-5:]:  # last 5 records
                st.write(f"📅 {a[0]} | In: {a[1]} | Out: {a[2]}")
        
        # show promotion history
        prom = get_promotions(r[0])
        if prom:
            st.write("**Promotion History:**")
            for p in prom:
                st.write(f"📅 {p[0]} | {p[1]} → {p[2]} | 💰 {p[3]} → {p[4]}")
        
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

# ----------------- REPORT MANAGER -----------------
st.subheader("📊 Report Manager")

report_type = st.selectbox("Choose Report", ["Employees","Leaves","Attendance","Promotions"])

uploaded_file = st.file_uploader(f"Upload {report_type} CSV/Excel", type=["csv","xlsx"], key=f"{report_type}_upload")

if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        conn = sqlite3.connect(DB)
        df.to_sql(report_type.lower(), conn, if_exists="append", index=False)
        conn.close()
        st.success(f"✅ {report_type} file imported successfully!")
    except Exception as e:
        st.error(f"⚠️ Error: {e}")

if st.button(f"⬇️ Download {report_type} Report (CSV)"):
    conn = sqlite3.connect(DB)
    df = pd.read_sql(f"SELECT * FROM {report_type.lower()}", conn)
    conn.close()
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=f"Download {report_type} CSV",
        data=csv,
        file_name=f"{report_type.lower()}_report.csv",
        mime="text/csv",
    )

if st.button(f"⬇️ Download {report_type} Report (Excel)"):
    conn = sqlite3.connect(DB)
    df = pd.read_sql(f"SELECT * FROM {report_type.lower()}", conn)
    conn.close()
    excel_file = f"{report_type.lower()}_report.xlsx"
    df.to_excel(excel_file, index=False)
    with open(excel_file, "rb") as f:
        st.download_button(
            label=f"Download {report_type} Excel",
            data=f,
            file_name=excel_file,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

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


