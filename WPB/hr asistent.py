import streamlit as st
import sqlite3
import google.generativeai as genai
from datetime import datetime, date
import pandas as pd
import os

# ----------------- THEME SELECTOR -----------------
theme = st.sidebar.radio("Theme", ["Light", "Dark"])
if theme == "Light":
    bg_color, user_color, bot_color, bot_border = "#FFFFFF", "#DCF8C6", "#FFFFFF", "#DDD"
    title_color, subtitle_color, user_text_color, bot_text_color = "black", "gray", "black", "black"
else:
    bg_color, user_color, bot_color, bot_border = "#181818", "#2a2a2a", "#202020", "#555"
    title_color, subtitle_color, user_text_color, bot_text_color = "white", "white", "white", "white"

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
st.markdown(f"<h1 style='text-align: center; color:{title_color};'>Autopilot HR</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; font-size:18px; color:{subtitle_color};'>Manage employees, leaves, attendance, promotions & reports</p>", unsafe_allow_html=True)

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
    
    c.execute("""CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id INTEGER,
        date TEXT,
        check_in TEXT,
        check_out TEXT,
        FOREIGN KEY(emp_id) REFERENCES employees(id)
    )""")
    
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

# ----------------- FUNCTIONS -----------------
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

def update_leave_status(leave_id, status):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE leaves SET status=? WHERE id=?", (status,leave_id))
    conn.commit()
    conn.close()

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

def add_promotion(emp_id, new_pos, new_sal):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    today = str(date.today())
    c.execute("SELECT position,salary FROM employees WHERE id=?", (emp_id,))
    old_pos, old_sal = c.fetchone()
    c.execute("UPDATE employees SET position=?, salary=? WHERE id=?", (new_pos,new_sal,emp_id))
    c.execute("""INSERT INTO promotions (emp_id,promotion_date,old_position,new_position,old_salary,new_salary)
                 VALUES (?,?,?,?,?,?)""", (emp_id,today,old_pos,new_pos,old_sal,new_sal))
    conn.commit()
    conn.close()

# ----------------- INIT -----------------
init_db()

# ----------------- REPORT MANAGER (Updated) -----------------
st.subheader("Report Manager:")

report_type = st.selectbox("Choose Report", ["Employees","Leaves","Attendance","Promotions"])

uploaded_file = st.file_uploader(f"Upload {report_type} CSV/Excel", type=["csv","xlsx"], key=f"{report_type}_upload")
os.makedirs("uploads", exist_ok=True)

if uploaded_file is not None:
    try:
        save_path = os.path.join("uploads", uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        if uploaded_file.name.lower().endswith(".csv"):
            df = pd.read_csv(save_path)
        else:
            df = pd.read_excel(save_path)

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        df.columns = [col.strip().lower() for col in df.columns]

        if report_type == "Employees":
            for _, row in df.iterrows():
                c.execute("""
                    INSERT INTO employees (first_name,last_name,email,phone,department,position,date_of_hire,salary,address)
                    VALUES (?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(email) DO UPDATE SET
                        first_name=excluded.first_name,
                        last_name=excluded.last_name,
                        phone=excluded.phone,
                        department=excluded.department,
                        position=excluded.position,
                        date_of_hire=excluded.date_of_hire,
                        salary=excluded.salary,
                        address=excluded.address
                """, (
                    row.get("first_name", ""), row.get("last_name", ""), row.get("email", ""),
                    row.get("phone", ""), row.get("department", ""), row.get("position", ""),
                    str(row.get("date_of_hire", "")), float(row.get("salary", 0.0)), row.get("address", "")
                ))
            st.success("Employees imported (upsert by email).")
        else:
            table = report_type.lower()
            df.to_sql(table, conn, if_exists="append", index=False)
            st.success(f"{report_type} data appended.")

        conn.commit()
        conn.close()

    except Exception as e:
        st.error(f"⚠️ Error: {e}")

# download DB button
st.markdown("---")
with open(DB, "rb") as f:
    st.download_button("Download employees.db", data=f, file_name="employees.db", mime="application/x-sqlite3")

















