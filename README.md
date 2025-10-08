# Emeet-app
eMeet: Secure Faculty-Student Appointment Scheduler built with Python Flask, PyMySQL, and bcrypt for robust user authentication.

eMeet is a modern, web-based platform designed to simplify and manage appointments between university faculty and students. It replaces traditional email and manual scheduling methods with a centralized, secure system.

🌟 Project Status:
This repository currently hosts the complete foundational architecture and the fully functional user authentication system.

💻 Tech Stack
Category	Technology	Purpose
Backend	Python 3 / Flask	Lightweight web application framework for routing and logic.
Database	MySQL	Relational database to store user and appointment data.
DB Connector	PyMySQL	Pure Python driver for seamless MySQL connectivity.
Security	bcrypt	Used for secure, one-way hashing of all user passwords.
Frontend	HTML5 / Bootstrap 5	Responsive user interface design.

Export to Sheets
🎯 Key Features (Phase 1 Deliverables)
Role-Based Registration: Students and Teachers can create separate, secure accounts.

Secure Authentication: Users are validated against the hashed passwords stored in the database.

Session Management: Users maintain a secure, logged-in state to access their respective dashboards.

Logout Functionality: Securely clears session data.

🛠️ Installation and Setup (Local Development)
Follow these steps to get the project running on your local machine:

1. Database Setup
Open MySQL Workbench or your preferred MySQL client.

Create the necessary database and tables by running the SQL script provided in the previous steps. The database name must be emeet_db.

2. Environment Setup
Clone this repository or download the project files.

Open the project folder (eMeetProject) in your terminal or VS Code.

Install the required Python packages:
pip install Flask pymysql bcrypt

3. Configuration
Open app.py.

Update the database connection details in the script with your own MySQL credentials:

Python

DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'your_mysql_password' # <-- Change this
DB_NAME = 'emeet_db'
4. Run the Application
Execute the main application file from your project directory:
python app.py

The application will start running on your local server: http://127.0.0.1:5000/

🛣️ Future Plans (Phase 3)
The following core features are planned for the next phases:

Appointment Request: Students will be able to view a list of teachers and submit a request with a preferred time/reason.

Appointment Management: Teachers will have a dedicated view to accept, reject, or comment on pending appointments.

Status Tracking: Both users will be able to track the real-time status (Pending, Approved, Rejected) of their appointments.

Notifications: Implement basic email or in-app notifications for status updates.
