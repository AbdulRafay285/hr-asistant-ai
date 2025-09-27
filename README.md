
 📌 Autopilot HR – Streamlit HR Assistant

Autopilot HR is a **Streamlit-based HR management system** powered by **SQLite** and **Google Gemini AI**.
It allows HR teams to manage employees, leaves, attendance, promotions, and generate reports with a simple web interface.

Features:

**Theme Selector** (Light, Dark, Custom)
**Employee Management** – Add, view, update employee records
**Leave Management** – Apply, approve, reject leave requests
**Attendance Tracking** – Check-in, Check-out system
**Promotions** – Manage employee promotions & salary updates
**Report Manager** – Import/Export data in CSV/Excel format
**Chat Assistant (Gemini AI)** – Ask HR-related questions & get answers
**SQLite Database** – Local lightweight storage

Project Structure:

📦 autopilot-hr
├── 📄 hr_assistant.py      # Main Streamlit app
├── 📄 employees.db         # SQLite Database (auto-created)
├── 📄 requirements.txt     # Python dependencies
├── 📄 README.md            # Project documentation
└── 📂 .streamlit
    └── 📄 secrets.toml     # API keys

Database Schema:

* **Employees** → Personal & job details
* **Leaves** → Leave requests (Pending/Approved/Rejected)
* **Attendance** → Daily check-in/check-out logs
* **Promotions** → Record of promotions & salary changes

## 📷 Screenshots

### Dashboard

![Dashboard Screenshot](https://via.placeholder.com/800x400.png?text=Dashboard+Preview)

### Employee Records

![Employees Screenshot](https://via.placeholder.com/800x400.png?text=Employee+Records)


* ✅ Role-based access (Admin / Employee)
* ✅ Email notifications for approvals/rejections
* ✅ More AI-powered insights (leave trends, attrition predictions)
* ✅ Deploy to Streamlit Cloud

Contributing:

Pull requests are welcome! For major changes, please open an issue first to discuss.

License:

MIT License © 2025 AbdulRafay.
