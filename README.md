@"
DROP DATABASE IF EXISTS votehub_db;
CREATE DATABASE votehub_db;
USE votehub_db;

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    phone VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin','voter') DEFAULT 'voter',
    status ENUM('active','pending','blocked') DEFAULT 'pending',
    email_verified TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE voters (
    voter_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    voter_uid VARCHAR(50) UNIQUE,
    date_of_birth DATE,
    gender ENUM('Male','Female','Other'),
    address TEXT,
    id_type VARCHAR(50),
    id_number VARCHAR(100),
    id_document VARCHAR(255),
    profile_photo VARCHAR(255),
    verification_status ENUM('pending','approved','rejected') DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE elections (
    election_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    start_datetime DATETIME NOT NULL,
    end_datetime DATETIME NOT NULL,
    status ENUM('draft','active','completed','cancelled') DEFAULT 'draft',
    result_published TINYINT(1) DEFAULT 0,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

CREATE TABLE candidates (
    candidate_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    party_name VARCHAR(100),
    symbol VARCHAR(255),
    photo VARCHAR(255),
    manifesto_file VARCHAR(255),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE election_candidates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    election_id INT NOT NULL,
    candidate_id INT NOT NULL,
    FOREIGN KEY (election_id) REFERENCES elections(election_id) ON DELETE CASCADE,
    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id) ON DELETE CASCADE
);

CREATE TABLE votes (
    vote_id INT AUTO_INCREMENT PRIMARY KEY,
    election_id INT NOT NULL,
    voter_id INT NOT NULL,
    candidate_id INT NOT NULL,
    vote_hash VARCHAR(255),
    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_vote (election_id, voter_id),
    FOREIGN KEY (election_id) REFERENCES elections(election_id),
    FOREIGN KEY (voter_id) REFERENCES voters(voter_id),
    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id)
);

CREATE TABLE vote_receipts (
    receipt_id INT AUTO_INCREMENT PRIMARY KEY,
    vote_id INT NOT NULL,
    receipt_code VARCHAR(100) UNIQUE,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vote_id) REFERENCES votes(vote_id)
);

CREATE TABLE otp_verifications (
    otp_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(120) NOT NULL,
    otp_code VARCHAR(10) NOT NULL,
    purpose ENUM('register','forgot_password') DEFAULT 'register',
    is_used TINYINT(1) DEFAULT 0,
    expires_at DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE password_resets (
    reset_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    reset_token VARCHAR(255) NOT NULL,
    expires_at DATETIME NOT NULL,
    is_used TINYINT(1) DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    title VARCHAR(150),
    message TEXT,
    is_read TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE audit_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(150),
    description TEXT,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

CREATE TABLE login_attempts (
    attempt_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(120),
    ip_address VARCHAR(50),
    status ENUM('success','failed') DEFAULT 'failed',
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE results (
    result_id INT AUTO_INCREMENT PRIMARY KEY,
    election_id INT NOT NULL,
    candidate_id INT NOT NULL,
    total_votes INT DEFAULT 0,
    result_status ENUM('pending','published') DEFAULT 'pending',
    FOREIGN KEY (election_id) REFERENCES elections(election_id) ON DELETE CASCADE,
    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id) ON DELETE CASCADE
);

CREATE TABLE settings (
    setting_id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE,
    setting_value TEXT
);
"@ | Set-Content database\schema.sql

@"
USE votehub_db;

INSERT INTO users 
(full_name, email, phone, password_hash, role, status, email_verified)
VALUES
('System Admin', 'admin@votehub.com', '9999999999', '\$2b\$12\$demo_admin_password_hash', 'admin', 'active', 1),
('Demo Voter', 'voter@votehub.com', '8888888888', '\$2b\$12\$demo_voter_password_hash', 'voter', 'active', 1);

INSERT INTO voters
(user_id, voter_uid, date_of_birth, gender, address, id_type, id_number, verification_status)
VALUES
(2, 'VH-VOTER-1001', '2002-05-15', 'Male', 'Demo Address', 'College ID', 'COLL1001', 'approved');

INSERT INTO candidates
(full_name, party_name, symbol, description)
VALUES
('Rahul Sharma', 'Student Unity Party', 'symbol_1.png', 'Focused on student welfare and campus development.'),
('Aisha Khan', 'Youth Progress Party', 'symbol_2.png', 'Focused on academic support and student activities.'),
('Neha Verma', 'Future Leaders Party', 'symbol_3.png', 'Focused on innovation and digital campus initiatives.');

INSERT INTO elections
(title, description, start_datetime, end_datetime, status, result_published, created_by)
VALUES
('Student Council Election 2026', 'Election for selecting student council representatives.', '2026-07-01 09:00:00', '2026-07-01 17:00:00', 'draft', 0, 1);

INSERT INTO election_candidates
(election_id, candidate_id)
VALUES
(1,1),
(1,2),
(1,3);

INSERT INTO settings
(setting_key, setting_value)
VALUES
('app_name', 'VoteHub'),
('college_project_title', 'A Secure Online Voting & Election Management System'),
('result_visibility', 'admin_only');
"@ | Set-Content database\seed.sql

@"
SOURCE schema.sql;
SOURCE seed.sql;
"@ | Set-Content database\voting_system.sql

Write-Host "Major-level database files added successfully!" -ForegroundColor Green





# 🗳️ VoteHub - Secure Online Voting System

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.x-black?logo=flask)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange?logo=mysql)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-purple?logo=bootstrap)
![License](https://img.shields.io/badge/License-Educational-green)

---

# 📌 Project Overview

**VoteHub** is a modern, secure, and scalable Online Voting System developed using **Python Flask** and **MySQL**. The system allows administrators to manage elections, candidates, and voters while enabling registered voters to securely cast their votes through an intuitive web interface.

The application is designed with a strong focus on:

- Security
- Transparency
- User Experience
- Authentication
- Data Integrity
- Modern UI Design

This project can be used by:

- Colleges
- Universities
- Schools
- Organizations
- Companies
- Clubs
- Student Councils
- Society Elections

---

# 🎯 Project Objectives

The main objectives of VoteHub are:

- Develop a secure online voting platform.
- Eliminate manual voting errors.
- Prevent duplicate voting.
- Maintain vote confidentiality.
- Provide a transparent election process.
- Generate real-time election reports.
- Improve election management efficiency.
- Build a scalable voting platform.

---

# 🚀 Key Features

## 👤 User Module

- User Registration
- Gmail OTP Verification
- Secure Login
- Password Encryption
- User Dashboard
- Profile Management
- Voting History
- Vote Receipt
- Logout

---

## 🗳️ Voting Module

- Live Elections
- One Person One Vote
- Vote Confirmation
- Vote Locking
- Duplicate Vote Prevention
- Vote Receipt Generation
- Secure Vote Storage

---

## 👨‍💼 Admin Module

- Admin Login
- Dashboard
- Manage Elections
- Manage Candidates
- Manage Voters
- Approve / Reject Voters
- View Reports
- Publish Results
- Activity Logs

---

## 🏆 Candidate Module

- Add Candidate
- Edit Candidate
- Delete Candidate
- Upload Candidate Photo
- Upload Party Symbol
- Upload Manifesto PDF
- Candidate Profile Page

---

## 📊 Election Module

- Create Election
- Start Election
- End Election
- Schedule Elections
- Multiple Elections
- Election Status
- Election Countdown Timer

---

## 📈 Reports Module

- Total Registered Voters
- Total Candidates
- Total Votes
- Turnout Percentage
- Candidate-wise Results
- PDF Reports
- Excel Reports

---

# 🔐 Security Features

VoteHub implements several security measures to ensure election integrity.

### Authentication

- Secure Password Hashing
- Gmail OTP Verification
- Session Management
- Role-Based Authentication

### Voting Security

- One Vote Per Voter
- Duplicate Vote Prevention
- Vote Validation
- Audit Logs

### System Security

- Input Validation
- SQL Injection Prevention
- XSS Protection
- Secure Sessions
- Login Attempt Tracking

---

# 🛠️ Technology Stack

## Frontend

- HTML5
- CSS3
- JavaScript
- Bootstrap 5
- Bootstrap Icons

---

## Backend

- Python
- Flask Framework

---

## Database

- MySQL
- phpMyAdmin

---

## Email Service

- Gmail SMTP
- Google App Password

---

## Reporting

- ReportLab
- OpenPyXL

---

## QR Features

- QRCode Library

---

## Image Processing

- Pillow

---

## Development Tools

- Visual Studio Code
- XAMPP
- Git
- GitHub
- PowerShell

---

# 📂 Project Folder Structure

```text
secure-online-voting-system
│
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── .env
│
├── app
│   ├── models
│   ├── routes
│   ├── services
│   ├── static
│   │   ├── css
│   │   ├── js
│   │   ├── images
│   │   └── uploads
│   ├── templates
│   ├── utils
│   ├── extensions.py
│   └── __init__.py
│
├── database
│   ├── schema.sql
│   ├── seed.sql
│   └── voting_system.sql
│
├── docs
├── migrations
└── tests
```

---

# 💻 System Requirements

Before running the project, install the following software.

| Software | Version |
|----------|----------|
| Python | 3.11 or Above |
| MySQL | 8.0+ |
| XAMPP | Latest |
| VS Code | Latest |
| Git | Latest |

---

# 📦 Python Libraries Used

Install all dependencies using:

```powershell
pip install -r requirements.txt
```

If the requirements file is not available, install them manually.

```powershell
pip install flask
pip install flask-mysqldb
pip install bcrypt
pip install python-dotenv
pip install reportlab
pip install openpyxl
pip install qrcode
pip install pillow
pip install flask-mail
pip install flask-session
```

---

# ⚙️ Project Installation

## Step 1

Clone the repository.

```powershell
git clone https://github.com/yourusername/votehub.git
```

OR

Download ZIP from GitHub and extract it.

---

## Step 2

Move project folder.

```text
C:\xampp\htdocs\
```

Final path should look like

```text
C:\xampp\htdocs\secure-online-voting-system
```

---

## Step 3

Open VS Code.

```powershell
code .
```

or

```powershell
cd C:\xampp\htdocs\secure-online-voting-system
code .
```

---

## Step 4

Create Virtual Environment.

```powershell
python -m venv venv
```

Activate it.

```powershell
venv\Scripts\activate
```

---

## Step 5

Install Project Dependencies.

```powershell
pip install -r requirements.txt
```

---

# 🗄️ Database Setup

Start XAMPP.

Run

- Apache
- MySQL

Now open

```text
http://localhost/phpmyadmin
```

Click

```
New
```

Create database.

```
votehub_db
```

Open SQL tab.

Paste the complete SQL query provided in this project.

Click

```
Go
```

All required tables will be created automatically.

---

# 🔑 Environment Configuration

Create a file named

```
.env
```

inside project root.

Add the following configuration.

```env
SECRET_KEY=votehub_secret_key_123

MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DB=votehub_db

MAIL_USERNAME=votehub.project@gmail.com
MAIL_APP_PASSWORD=YOUR_GOOGLE_APP_PASSWORD
```

Replace

```
YOUR_GOOGLE_APP_PASSWORD
```

with your Gmail App Password.

> Never use your normal Gmail password.

---

# 👨‍💻 Running the Project

Open terminal.

Activate virtual environment.

```powershell
venv\Scripts\activate
```

Run the Flask application.

```powershell
python app.py
```

Project will start at

```text
http://127.0.0.1:5000
```

Open it in your browser.

---

# 🔐 Default Admin Login

Create an admin account in the database.

Default credentials.

```
Email

admin@votehub.com

Password

admin123
```

> The password stored in the database must be the generated bcrypt hash and not plain text.

---

# 📧 Gmail OTP Configuration

VoteHub uses Gmail SMTP for sending One-Time Password (OTP) during registration and account verification.

## Step 1: Create a Gmail Account

Example:

```
votehub.project@gmail.com
```

---

## Step 2: Enable 2-Step Verification

Open

```
https://myaccount.google.com/security
```

Enable

```
2-Step Verification
```

---

## Step 3: Generate Google App Password

Go to

```
https://myaccount.google.com/apppasswords
```

Create App Password

```
VoteHub
```

Google will generate a 16-character password.

Example

```
abcd efgh ijkl mnop
```

Use this password inside the `.env` file.

---

# 🏗️ Complete Project Workflow

The following diagram explains the overall workflow of the application.

```
User Registration
        │
        ▼
Email OTP Generated
        │
        ▼
OTP Saved in Database
        │
        ▼
OTP Sent to Gmail
        │
        ▼
User Verification
        │
        ▼
Account Activated
        │
        ▼
Login
        │
        ▼
Voter Dashboard
        │
        ▼
Available Elections
        │
        ▼
Vote Casting
        │
        ▼
Vote Locked
        │
        ▼
Result Generation
        │
        ▼
Reports & Analytics
```

---

# 🗄️ Database Tables

The project uses multiple normalized tables.

| Table | Purpose |
|---------|-----------------------------|
| users | User Authentication |
| voters | Voter Details |
| candidates | Candidate Information |
| elections | Election Information |
| election_candidates | Candidate Mapping |
| votes | Vote Records |
| vote_receipts | Vote Receipt |
| otp_verifications | OTP Verification |
| password_resets | Password Reset |
| notifications | User Notifications |
| audit_logs | Activity Logs |
| login_attempts | Login Security |
| results | Election Results |
| settings | Application Settings |

---

# 🔐 Security Architecture

VoteHub follows multiple layers of security.

## Authentication

- Gmail OTP Verification
- Secure Login
- Password Hashing using bcrypt
- Session Management
- Role Based Access

---

## Data Security

- MySQL Prepared Statements
- SQL Injection Protection
- Password Encryption
- Secure Cookies

---

## Voting Security

- One Person One Vote
- Vote Locking
- Vote Validation
- Duplicate Vote Prevention
- Secure Vote Storage

---

## Application Security

- Input Validation
- XSS Protection
- Session Timeout
- Login Attempt Logging
- Audit Trail

---

# 📊 Admin Dashboard

Administrator can perform the following operations.

- View Dashboard
- Manage Voters
- Approve Voters
- Reject Voters
- Block Users
- Manage Candidates
- Upload Candidate Photos
- Upload Party Symbols
- Upload Manifesto
- Create Elections
- Start Election
- End Election
- Publish Results
- Generate Reports
- Export PDF
- Export Excel

---

# 👤 Voter Dashboard

Each voter has access to:

- Personal Dashboard
- Profile
- Elections
- Candidate Details
- Vote Casting
- Vote History
- Vote Receipt
- Notifications

---

# 📈 Reports & Analytics

VoteHub generates multiple reports.

- Registered Users
- Total Voters
- Candidate Count
- Election Count
- Votes Cast
- Voter Turnout
- Candidate Wise Result
- PDF Report
- Excel Report
- CSV Export

---

# 📱 Responsive Design

The project is fully responsive.

Supports

- Desktop
- Laptop
- Tablet
- Mobile Devices

Built using Bootstrap 5.

---

# 📸 Screenshots

You can add screenshots here.

Example

```
screenshots/

login.png

register.png

admin_dashboard.png

voter_dashboard.png

candidate_management.png

election_management.png

voting_page.png

results.png
```

These screenshots make the GitHub repository more professional.

---

# 🚀 Future Enhancements

The current version of VoteHub includes all major election management functionalities. Future versions can include the following advanced features.

## AI Features

- AI-based Voter Verification
- AI Fraud Detection
- AI Election Analytics
- AI Result Prediction
- AI Activity Monitoring

---

## Blockchain Integration

- Blockchain Vote Storage
- Immutable Vote Records
- Transparent Verification
- Distributed Ledger Technology

---

## Face Recognition

- OpenCV Face Verification
- Face Matching Before Voting
- Duplicate Face Detection

---

## QR Code Features

- Digital Voter Card
- QR Based Verification
- QR Vote Receipt

---

## Mobile Application

- Android Application
- iOS Application
- Push Notifications

---

## Cloud Deployment

- AWS
- Microsoft Azure
- Google Cloud Platform
- Docker
- Kubernetes

---

# 🐞 Common Errors & Solutions

## Database Connection Error

**Reason**

- MySQL Server Not Running

**Solution**

Start MySQL from XAMPP Control Panel.

---

## Module Not Found

**Reason**

Python library missing.

**Solution**

```powershell
pip install -r requirements.txt
```

---

## Gmail OTP Not Working

Check

- Gmail App Password
- 2-Step Verification
- Internet Connection

Test email service

```powershell
python -c "from app.services.email_service import send_otp_email; print(send_otp_email('your_email@gmail.com','123456'))"
```

Expected Output

```
(True, 'OTP sent successfully')
```

---

## MySQL Table Not Found

Run the SQL setup query again inside phpMyAdmin.

---

## Flask Application Not Starting

Run

```powershell
python app.py
```

Check for missing dependencies.

---

## Port Already In Use

Stop the existing Flask server.

Press

```
CTRL + C
```

Run again

```powershell
python app.py
```

---

# 📂 Git Commands

Clone Repository

```powershell
git clone https://github.com/yourusername/votehub.git
```

Check Status

```powershell
git status
```

Add Files

```powershell
git add .
```

Commit

```powershell
git commit -m "Project Updated"
```

Push

```powershell
git push origin main
```

Pull Latest Changes

```powershell
git pull origin main
```

---

# 📦 Sharing the Project

To share the project with another user.

## Step 1

Zip the project folder.

```
secure-online-voting-system.zip
```

---

## Step 2

Share the ZIP file.

---

## Step 3

Receiver should

- Extract ZIP
- Install Python
- Install XAMPP
- Install Libraries
- Create Database
- Import SQL
- Configure `.env`
- Run

```powershell
python app.py
```

Project will work successfully.

---

# ⭐ Project Highlights

✔ Secure Authentication

✔ Gmail OTP Verification

✔ Professional Dashboard

✔ Candidate Management

✔ Election Management

✔ Secure Voting

✔ Vote Receipt

✔ Duplicate Vote Prevention

✔ Admin Analytics

✔ PDF Reports

✔ Excel Reports

✔ Glassmorphism UI

✔ Responsive Design

✔ Secure Password Hashing

✔ Activity Logs

✔ Professional Folder Structure

✔ Easy Deployment

✔ Industry Standard Coding Practices

---

# 📖 Learning Outcomes

During the development of VoteHub, the following concepts were implemented.

- Python Flask Framework
- REST Based Routing
- Authentication
- Session Management
- Password Encryption
- OTP Verification
- CRUD Operations
- MySQL Database Design
- Bootstrap UI
- JavaScript Validation
- Responsive Design
- File Uploads
- Report Generation
- Security Best Practices
- Git Version Control

---

# 👨‍💻 Developed By

**Project Name**

VoteHub – Secure Online Voting System

**Technology**

Python Flask | MySQL | Bootstrap | JavaScript | HTML | CSS

**Project Type**

Major Academic Project

**Project Category**

Web Application

**Version**

Version 1.0

---

# 📜 License

This project is developed for educational and academic purposes.

You are free to modify and extend the project for learning and research purposes.

Commercial use requires appropriate permission from the project owner.

---

# 🙏 Acknowledgement

The development of VoteHub was completed using modern web development technologies including Python Flask, MySQL, Bootstrap, JavaScript, and HTML/CSS.

Special thanks to the open-source community and official documentation of Python, Flask, MySQL, Bootstrap, and other libraries that helped in building this project.

---

# ⭐ Support

If you found this project useful, consider giving it a ⭐ on GitHub.

Happy Coding! 🚀

---

# 📧 Contact

For project-related queries:

**Project:** VoteHub – Secure Online Voting System

GitHub Repository:

```
https://github.com/yourusername/votehub
```

Email:

```
your-email@example.com
```


DROP DATABASE IF EXISTS votehub_db;
CREATE DATABASE votehub_db CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE votehub_db;

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    phone VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin','voter') DEFAULT 'voter',
    status ENUM('active','pending','blocked') DEFAULT 'pending',
    email_verified TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE voters (
    voter_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    voter_uid VARCHAR(50) UNIQUE,
    date_of_birth DATE,
    gender ENUM('Male','Female','Other'),
    address TEXT,
    id_type VARCHAR(50),
    id_number VARCHAR(100),
    id_document VARCHAR(255),
    profile_photo VARCHAR(255),
    verification_status ENUM('pending','approved','rejected') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE candidates (
    candidate_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    party_name VARCHAR(100),
    symbol VARCHAR(255),
    photo VARCHAR(255),
    manifesto_file VARCHAR(255),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE elections (
    election_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    start_datetime DATETIME NOT NULL,
    end_datetime DATETIME NOT NULL,
    status ENUM('draft','active','completed','cancelled') DEFAULT 'draft',
    result_published TINYINT(1) DEFAULT 0,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE SET NULL
);

CREATE TABLE election_candidates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    election_id INT NOT NULL,
    candidate_id INT NOT NULL,
    UNIQUE KEY unique_election_candidate (election_id, candidate_id),
    FOREIGN KEY (election_id) REFERENCES elections(election_id) ON DELETE CASCADE,
    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id) ON DELETE CASCADE
);

CREATE TABLE votes (
    vote_id INT AUTO_INCREMENT PRIMARY KEY,
    election_id INT NOT NULL,
    voter_id INT NOT NULL,
    candidate_id INT NOT NULL,
    vote_hash VARCHAR(255),
    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_vote (election_id, voter_id),
    FOREIGN KEY (election_id) REFERENCES elections(election_id) ON DELETE CASCADE,
    FOREIGN KEY (voter_id) REFERENCES voters(voter_id) ON DELETE CASCADE,
    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id) ON DELETE CASCADE
);

CREATE TABLE vote_receipts (
    receipt_id INT AUTO_INCREMENT PRIMARY KEY,
    vote_id INT NOT NULL,
    receipt_code VARCHAR(100) UNIQUE,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vote_id) REFERENCES votes(vote_id) ON DELETE CASCADE
);

CREATE TABLE otp_verifications (
    otp_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(120) NOT NULL,
    otp_code VARCHAR(10) NOT NULL,
    purpose ENUM('register','forgot_password') DEFAULT 'register',
    is_used TINYINT(1) DEFAULT 0,
    expires_at DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE password_resets (
    reset_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    reset_token VARCHAR(255) NOT NULL,
    expires_at DATETIME NOT NULL,
    is_used TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    title VARCHAR(150),
    message TEXT,
    is_read TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE audit_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(150),
    description TEXT,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

CREATE TABLE login_attempts (
    attempt_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(120),
    ip_address VARCHAR(50),
    status ENUM('success','failed') DEFAULT 'failed',
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE results (
    result_id INT AUTO_INCREMENT PRIMARY KEY,
    election_id INT NOT NULL,
    candidate_id INT NOT NULL,
    total_votes INT DEFAULT 0,
    result_status ENUM('pending','published') DEFAULT 'pending',
    FOREIGN KEY (election_id) REFERENCES elections(election_id) ON DELETE CASCADE,
    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id) ON DELETE CASCADE
);

CREATE TABLE settings (
    setting_id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE,
    setting_value TEXT
);