# Healthcare Scheduling System

## 1. Project Overview

The Healthcare Scheduling System is a web-based application developed using Python Flask and MySQL. It helps manage hospital activities such as patient details, doctor information, appointments, prescriptions, medical records and billing.

The main objective of this project is to simplify healthcare administration through a centralized system.

## 2. Project Objectives

- To maintain patient and doctor information.
- To schedule and manage appointments.
- To maintain prescriptions and medical records.
- To manage billing and payment status.
- To generate basic reports and summaries.
- To manage user login and roles.

## 3. Features

1. **Dashboard:** Displays total patients, doctors, appointments and revenue.
2. **Patient Management:** Add, view, edit and delete patient details.
3. **Doctor Management:** Manage doctor profiles and availability.
4. **Appointment Scheduling:** Schedule appointments and update appointment status.
5. **Prescription Management:** Create prescriptions and add prescribed medicines.
6. **Medical Records:** Store symptoms, diagnosis and treatment details.
7. **Billing Management:** Create bills and update payment status.
8. **Reports and Analytics:** Display patient, doctor, appointment and payment summaries.
9. **User and Role Management:** View registered users and their roles.

## 4. Technologies Used

- Frontend: HTML, CSS
- Backend: Python, Flask
- Database: MySQL
- Development Tool: Visual Studio Code

## 5. Project Folder Structure

```text
Healthcare_Scheduling_System/
│
├── app.py
├── db.py
├── requirements.txt
├── README.md
├── create_admin.py
├── test_db.py
│
├── templates/
│
└── static/
    └── css/
        └── style.css
```

## 6. Installation Requirements

- Python 3
- MySQL Server
- Visual Studio Code
- Required Python packages

## 7. Installation and Execution

### Step 1: Download the Project

Download or clone the project from GitHub and open the project folder in VS Code.

### Step 2: Create Virtual Environment

```bash
python -m venv venv
```

### Step 3: Activate Virtual Environment

For Windows:

```bash
venv\Scripts\activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Configure MySQL

Create the database named `healthcare_db` in MySQL.

Configure the database username, password and connection details in `db.py`.

Create the required database tables before running the application.

### Step 6: Run the Application

```bash
python app.py
```

### Step 7: Open in Browser

```text
http://127.0.0.1:5000/
```

## 8. Database

Database Name: `healthcare_db`

MySQL is used to store user, patient, doctor, appointment, prescription, medical record and billing information.

## 9. Expected Outcome

The system provides a simple interface to manage healthcare scheduling activities. It helps organize hospital information and makes basic administrative operations easier.

## 10. Future Enhancements

- Patient and doctor self-service login.
- User creation and profile management.
- Online appointment booking.
- Advanced reports and analytics.
- Cloud deployment.

## 11. Author

Healthcare Scheduling System – Academic Project