
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from db import get_db_connection

app = Flask(__name__)
app.secret_key = "healthcare_project_secret_key_change_later"


# ==================================
# HOME PAGE
# ==================================

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# ==================================
# LOGIN
# ==================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute("""
                SELECT * FROM users
                WHERE email = %s AND role = %s
            """, (email, role))

            user = cursor.fetchone()

            if user and check_password_hash(
                user["password_hash"], password
            ):

                session["user_id"] = user["user_id"]
                session["name"] = user["full_name"]
                session["role"] = user["role"]

                return redirect(url_for("dashboard"))

            else:
                flash("Invalid email, password or role!")

        except Exception as e:
            flash("Database error: " + str(e))

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()

    return render_template("login.html")


# ==================================
# DASHBOARD
# ==================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) AS total FROM patients")
        total_patients = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM doctors")
        total_doctors = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM appointments")
        total_appointments = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM appointments
            WHERE status = 'Booked'
        """)
        pending_appointments = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0) AS revenue
            FROM bills
            WHERE payment_status = 'Paid'
        """)
        total_revenue = cursor.fetchone()["revenue"]

        cursor.execute("""
            SELECT
                a.appointment_date,
                a.appointment_time,
                a.status,
                p.full_name AS patient_name,
                d.full_name AS doctor_name
            FROM appointments a
            JOIN patients p ON a.patient_id = p.patient_id
            JOIN doctors d ON a.doctor_id = d.doctor_id
            ORDER BY a.appointment_id DESC
            LIMIT 5
        """)
        recent_appointments = cursor.fetchall()

        cursor.execute("""
            SELECT
                p.prescription_id,
                p.prescription_date,
                p.diagnosis,
                pt.full_name AS patient_name,
                d.full_name AS doctor_name
            FROM prescriptions p
            JOIN patients pt ON p.patient_id = pt.patient_id
            JOIN doctors d ON p.doctor_id = d.doctor_id
            ORDER BY p.prescription_id DESC
            LIMIT 5
        """)
        recent_prescriptions = cursor.fetchall()

        return render_template(
            "dashboard.html",
            total_patients=total_patients,
            total_doctors=total_doctors,
            total_appointments=total_appointments,
            pending_appointments=pending_appointments,
            total_revenue=total_revenue,
            recent_appointments=recent_appointments,
            recent_prescriptions=recent_prescriptions
        )

    except Exception as e:
        return "Dashboard Error: " + str(e)

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# ==================================
# LOGOUT
# ==================================

@app.route("/logout")
def logout():

    session.clear()
    return redirect(url_for("login"))


# ==================================
# PATIENT MANAGEMENT
# ==================================

@app.route("/patients")
def patients():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        return "Access Denied", 403

    search = request.args.get("search", "").strip()

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT * FROM patients
            WHERE full_name LIKE %s
            OR phone LIKE %s
            ORDER BY patient_id DESC
        """

        search_value = "%" + search + "%"

        cursor.execute(query, (search_value, search_value))
        patient_list = cursor.fetchall()

        return render_template(
            "patients.html",
            patients=patient_list,
            search=search
        )

    except Exception as e:
        return "Patient Error: " + str(e)

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# Add Patient

@app.route("/patients/add", methods=["POST"])
def add_patient():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        return "Access Denied", 403

    name = request.form["full_name"]
    dob = request.form.get("date_of_birth") or None
    gender = request.form.get("gender")
    blood_group = request.form.get("blood_group")
    phone = request.form.get("phone")
    email = request.form.get("email")
    address = request.form.get("address")
    emergency = request.form.get("emergency_contact")
    conditions = request.form.get("medical_conditions")

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
            INSERT INTO patients
            (full_name, date_of_birth, gender, blood_group,
             phone, email, address, emergency_contact,
             medical_conditions)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            name, dob, gender, blood_group,
            phone, email, address, emergency, conditions
        )

        cursor.execute(query, values)
        connection.commit()

        flash("Patient Added Successfully!")

    except Exception as e:
        flash("Error: " + str(e))

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

    return redirect(url_for("patients"))


# Edit Patient

@app.route("/patients/edit/<int:patient_id>", methods=["GET", "POST"])
def edit_patient(patient_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        return "Access Denied", 403

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        if request.method == "POST":

            query = """
                UPDATE patients
                SET full_name=%s,
                    date_of_birth=%s,
                    gender=%s,
                    blood_group=%s,
                    phone=%s,
                    email=%s,
                    address=%s,
                    emergency_contact=%s,
                    medical_conditions=%s
                WHERE patient_id=%s
            """

            values = (
                request.form["full_name"],
                request.form.get("date_of_birth") or None,
                request.form.get("gender"),
                request.form.get("blood_group"),
                request.form.get("phone"),
                request.form.get("email"),
                request.form.get("address"),
                request.form.get("emergency_contact"),
                request.form.get("medical_conditions"),
                patient_id
            )

            cursor.execute(query, values)
            connection.commit()

            flash("Patient Updated Successfully!")
            return redirect(url_for("patients"))

        cursor.execute(
            "SELECT * FROM patients WHERE patient_id=%s",
            (patient_id,)
        )

        patient = cursor.fetchone()

        if not patient:
            return "Patient Not Found", 404

        return render_template("edit_patient.html", patient=patient)

    except Exception as e:
        return "Error: " + str(e)

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# Delete Patient

@app.route("/patients/delete/<int:patient_id>", methods=["POST"])
def delete_patient(patient_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        return "Access Denied", 403

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM patients WHERE patient_id=%s",
            (patient_id,)
        )

        connection.commit()
        flash("Patient Deleted Successfully!")

    except Exception as e:
        flash("Cannot delete patient. Related records may exist. " + str(e))

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

    return redirect(url_for("patients"))


# ==================================
# DOCTOR MANAGEMENT
# ==================================

@app.route("/doctors")
def doctors():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        return "Access Denied", 403

    search = request.args.get("search", "").strip()

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT * FROM doctors
            WHERE full_name LIKE %s
            OR specialization LIKE %s
            OR phone LIKE %s
            ORDER BY doctor_id DESC
        """

        search_value = "%" + search + "%"

        cursor.execute(
            query,
            (search_value, search_value, search_value)
        )

        doctor_list = cursor.fetchall()

        return render_template(
            "doctors.html",
            doctors=doctor_list,
            search=search
        )

    except Exception as e:
        return "Doctor Error: " + str(e)

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# Add Doctor

@app.route("/doctors/add", methods=["POST"])
def add_doctor():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        return "Access Denied", 403

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
            INSERT INTO doctors
            (full_name, specialization, qualification,
             experience, phone, email, consultation_fee,
             availability)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            request.form["full_name"],
            request.form.get("specialization"),
            request.form.get("qualification"),
            request.form.get("experience") or None,
            request.form.get("phone"),
            request.form.get("email"),
            request.form.get("consultation_fee") or None,
            request.form.get("availability")
        )

        cursor.execute(query, values)
        connection.commit()

        flash("Doctor Added Successfully!")

    except Exception as e:
        flash("Error: " + str(e))

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

    return redirect(url_for("doctors"))


# Edit Doctor

@app.route("/doctors/edit/<int:doctor_id>", methods=["GET", "POST"])
def edit_doctor(doctor_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        return "Access Denied", 403

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        if request.method == "POST":

            query = """
                UPDATE doctors
                SET full_name=%s,
                    specialization=%s,
                    qualification=%s,
                    experience=%s,
                    phone=%s,
                    email=%s,
                    consultation_fee=%s,
                    availability=%s
                WHERE doctor_id=%s
            """

            values = (
                request.form["full_name"],
                request.form.get("specialization"),
                request.form.get("qualification"),
                request.form.get("experience") or None,
                request.form.get("phone"),
                request.form.get("email"),
                request.form.get("consultation_fee") or None,
                request.form.get("availability"),
                doctor_id
            )

            cursor.execute(query, values)
            connection.commit()

            flash("Doctor Updated Successfully!")
            return redirect(url_for("doctors"))

        cursor.execute(
            "SELECT * FROM doctors WHERE doctor_id=%s",
            (doctor_id,)
        )

        doctor = cursor.fetchone()

        if not doctor:
            return "Doctor Not Found", 404

        return render_template("edit_doctor.html", doctor=doctor)

    except Exception as e:
        return "Error: " + str(e)

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# Delete Doctor

@app.route("/doctors/delete/<int:doctor_id>", methods=["POST"])
def delete_doctor(doctor_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        return "Access Denied", 403

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM doctors WHERE doctor_id=%s",
            (doctor_id,)
        )

        connection.commit()
        flash("Doctor Deleted Successfully!")

    except Exception as e:
        flash("Cannot delete doctor. Related records may exist. " + str(e))

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

    return redirect(url_for("doctors"))


# ==================================
# APPOINTMENT MANAGEMENT
# ==================================

@app.route("/appointments")
def appointments():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        flash("Access denied!")
        return redirect(url_for("dashboard"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            a.appointment_id,
            p.full_name AS patient_name,
            d.full_name AS doctor_name,
            a.appointment_date,
            a.appointment_time,
            a.reason,
            a.status
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        JOIN doctors d ON a.doctor_id = d.doctor_id
        ORDER BY a.appointment_date DESC
    """)

    appointment_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "appointments.html",
        appointments=appointment_list
    )


# Add Appointment

@app.route("/appointments/add", methods=["GET", "POST"])
def add_appointment():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        flash("Access denied!")
        return redirect(url_for("dashboard"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":

        patient_id = request.form["patient_id"]
        doctor_id = request.form["doctor_id"]
        appointment_date = request.form["appointment_date"]
        appointment_time = request.form["appointment_time"]
        reason = request.form["reason"]

        cursor.execute("""
            INSERT INTO appointments
            (patient_id, doctor_id, appointment_date,
             appointment_time, reason, status)
            VALUES (%s, %s, %s, %s, %s, 'Booked')
        """, (
            patient_id,
            doctor_id,
            appointment_date,
            appointment_time,
            reason
        ))

        conn.commit()

        cursor.close()
        conn.close()

        flash("Appointment booked successfully!")
        return redirect(url_for("appointments"))

    cursor.execute("SELECT patient_id, full_name FROM patients")
    patients = cursor.fetchall()

    cursor.execute("SELECT doctor_id, full_name FROM doctors")
    doctors = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "add_appointment.html",
        patients=patients,
        doctors=doctors
    )


# Update Appointment Status

@app.route("/appointments/status/<int:appointment_id>", methods=["POST"])
def update_appointment_status(appointment_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        return "Access Denied", 403

    status = request.form.get("status")

    allowed_status = [
        "Booked",
        "Completed",
        "Cancelled",
        "Rescheduled"
    ]

    if status not in allowed_status:
        return "Invalid Status", 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE appointments
        SET status = %s
        WHERE appointment_id = %s
    """, (status, appointment_id))

    conn.commit()

    cursor.close()
    conn.close()

    flash("Appointment status updated successfully!")

    return redirect(url_for("appointments"))


# ==================================
# PRESCRIPTION MANAGEMENT
# ==================================

# View Prescriptions

@app.route("/prescriptions")
def prescriptions():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            p.prescription_id,
            p.prescription_date,
            p.diagnosis,
            p.instructions,
            pt.full_name AS patient_name,
            d.full_name AS doctor_name
        FROM prescriptions p
        JOIN patients pt ON p.patient_id = pt.patient_id
        JOIN doctors d ON p.doctor_id = d.doctor_id
        ORDER BY p.prescription_id DESC
    """)

    prescription_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "prescriptions.html",
        prescriptions=prescription_list
    )


# Add Prescription with Multiple Medicines

@app.route("/prescriptions/add", methods=["GET", "POST"])
def add_prescription():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        return "Access Denied", 403

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":

        try:
            prescription_date = request.form["prescription_date"]
            patient_id = request.form["patient_id"]
            doctor_id = request.form["doctor_id"]
            diagnosis = request.form["diagnosis"]
            instructions = request.form["instructions"]

            cursor.execute("""
                INSERT INTO prescriptions
                (prescription_date, patient_id, doctor_id,
                 diagnosis, instructions)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                prescription_date,
                patient_id,
                doctor_id,
                diagnosis,
                instructions
            ))

            prescription_id = cursor.lastrowid

            medicine_names = request.form.getlist("medicine_name[]")
            dosages = request.form.getlist("dosage[]")
            frequencies = request.form.getlist("frequency[]")
            durations = request.form.getlist("duration[]")
            quantities = request.form.getlist("quantity[]")

            for i in range(len(medicine_names)):

                medicine_name = medicine_names[i].strip()

                if medicine_name:

                    dosage = dosages[i] if i < len(dosages) else ""
                    frequency = frequencies[i] if i < len(frequencies) else ""
                    duration = durations[i] if i < len(durations) else ""
                    quantity = quantities[i] if i < len(quantities) else ""

                    cursor.execute("""
                        INSERT INTO prescription_medicines
                        (prescription_id, medicine_name, dosage,
                         frequency, duration, quantity)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        prescription_id,
                        medicine_name,
                        dosage,
                        frequency,
                        duration,
                        int(quantity) if quantity.strip() else None
                    ))

            conn.commit()

            flash("Prescription and medicines added successfully!")
            return redirect(url_for("prescriptions"))

        except Exception as e:
            conn.rollback()
            flash("Error adding prescription: " + str(e))
            return redirect(url_for("add_prescription"))

        finally:
            cursor.close()
            conn.close()

    cursor.execute("""
        SELECT patient_id, full_name
        FROM patients
        ORDER BY full_name
    """)
    patients = cursor.fetchall()

    cursor.execute("""
        SELECT doctor_id, full_name
        FROM doctors
        ORDER BY full_name
    """)
    doctors = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "add_prescription.html",
        patients=patients,
        doctors=doctors
    )


# View Prescription Medicine Details

@app.route("/prescriptions/medicines/<int:prescription_id>")
def prescription_medicines(prescription_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM prescription_medicines
        WHERE prescription_id = %s
    """, (prescription_id,))

    medicines = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "prescription_medicines.html",
        medicines=medicines,
        prescription_id=prescription_id
    )

# ==================================
# MEDICAL RECORDS
# ==================================

@app.route("/medical_records")
def medical_records():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            mr.record_id,
            pt.full_name AS patient_name,
            d.full_name AS doctor_name,
            mr.record_date,
            mr.symptoms,
            mr.diagnosis,
            mr.treatment,
            mr.notes
        FROM medical_records AS mr
        JOIN patients AS pt
            ON mr.patient_id = pt.patient_id
        JOIN doctors AS d
            ON mr.doctor_id = d.doctor_id
        ORDER BY mr.record_date DESC
    """)

    records = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "medical_records.html",
        records=records
    )



# Add Medical Record

@app.route("/medical_records/add", methods=["GET", "POST"])
def add_medical_record():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        if request.method == "POST":

            patient_id = request.form.get("patient_id")
            doctor_id = request.form.get("doctor_id")
            record_date = request.form.get("record_date")
            symptoms = request.form.get("symptoms", "")
            diagnosis = request.form.get("diagnosis", "")
            treatment = request.form.get("treatment", "")
            notes = request.form.get("notes", "")

            if not patient_id or not doctor_id or not record_date:
                flash("Please select patient, doctor and date.")
                return redirect(url_for("add_medical_record"))

            cursor.execute("""
                INSERT INTO medical_records
                (
                    patient_id,
                    doctor_id,
                    record_date,
                    symptoms,
                    diagnosis,
                    treatment,
                    notes
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                patient_id,
                doctor_id,
                record_date,
                symptoms,
                diagnosis,
                treatment,
                notes
            ))

            connection.commit()

            flash("Medical record added successfully!")
            return redirect(url_for("medical_records"))

        # Fetch Patient Names
        cursor.execute("""
            SELECT patient_id, full_name
            FROM patients
            ORDER BY full_name ASC
        """)
        patients = cursor.fetchall()

        # Fetch Doctor Names
        cursor.execute("""
            SELECT doctor_id, full_name
            FROM doctors
            ORDER BY full_name ASC
        """)
        doctors = cursor.fetchall()

        return render_template(
            "add_medical_record.html",
            patients=patients,
            doctors=doctors
        )

    except Exception as e:
        if connection:
            connection.rollback()
        return "Medical Record Error: " + str(e)

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# ==================================
# BILLING MANAGEMENT
# ==================================

# View Bills

@app.route("/billing")
def billing():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            b.bill_id,
            b.patient_id,
            pt.full_name AS patient_name,
            b.appointment_id,
            b.bill_date,
            b.consultation_fee,
            b.medicine_charge,
            b.lab_charge,
            b.total_amount,
            b.payment_status
        FROM bills AS b
        JOIN patients AS pt
            ON b.patient_id = pt.patient_id
        ORDER BY b.bill_id DESC
    """)

    bills = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "billing.html",
        bills=bills
    )


# Add New Bill

@app.route("/billing/add", methods=["GET", "POST"])
def add_bill():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        flash("Only Admin can create bills.")
        return redirect(url_for("billing"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":

        patient_id = request.form["patient_id"]
        bill_date = request.form["bill_date"]

        consultation_fee = float(
            request.form.get("consultation_fee") or 0
        )

        medicine_charge = float(
            request.form.get("medicine_charge") or 0
        )

        lab_charge = float(
            request.form.get("lab_charge") or 0
        )

        total_amount = (
            consultation_fee
            + medicine_charge
            + lab_charge
        )

        cursor.execute("""
            INSERT INTO bills
            (
                patient_id,
                bill_date,
                consultation_fee,
                medicine_charge,
                lab_charge,
                total_amount,
                payment_status
            )
            VALUES (%s, %s, %s, %s, %s, %s, 'Pending')
        """, (
            patient_id,
            bill_date,
            consultation_fee,
            medicine_charge,
            lab_charge,
            total_amount
        ))

        conn.commit()

        cursor.close()
        conn.close()

        flash("Bill generated successfully!")
        return redirect(url_for("billing"))

    cursor.execute("""
        SELECT patient_id, full_name
        FROM patients
        ORDER BY full_name
    """)

    patients = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "add_bill.html",
        patients=patients
    )


# Update Payment Status

@app.route("/billing/status/<int:bill_id>", methods=["POST"])
def update_bill_status(bill_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        flash("Only Admin can update payment status.")
        return redirect(url_for("billing"))

    payment_status = request.form.get("payment_status")

    allowed_status = [
        "Pending",
        "Paid",
        "Partially Paid"
    ]

    if payment_status not in allowed_status:
        flash("Invalid payment status.")
        return redirect(url_for("billing"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE bills
        SET payment_status = %s
        WHERE bill_id = %s
    """, (payment_status, bill_id))

    conn.commit()

    cursor.close()
    conn.close()

    flash("Payment status updated successfully!")

    return redirect(url_for("billing"))


# ==================================
# REPORTS AND ANALYTICS
# ==================================

@app.route("/reports")
def reports():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT COUNT(*) AS total_patients
        FROM patients
    """)
    total_patients = cursor.fetchone()["total_patients"]

    cursor.execute("""
        SELECT COUNT(*) AS total_doctors
        FROM doctors
    """)
    total_doctors = cursor.fetchone()["total_doctors"]

    cursor.execute("""
        SELECT COUNT(*) AS total_appointments
        FROM appointments
    """)
    total_appointments = cursor.fetchone()["total_appointments"]

    cursor.execute("""
        SELECT
            payment_status,
            COALESCE(SUM(total_amount), 0) AS amount
        FROM bills
        GROUP BY payment_status
    """)
    payment_summary = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "reports.html",
        total_patients=total_patients,
        total_doctors=total_doctors,
        total_appointments=total_appointments,
        payment_summary=payment_summary
    )


# ==================================
# USER AND ROLE MANAGEMENT
# ==================================

@app.route("/users")
def users():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Admin":
        flash("Access denied. Admin only.")
        return redirect(url_for("dashboard"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            user_id,
            full_name,
            email,
            role
        FROM users
        ORDER BY user_id DESC
    """)

    user_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "users.html",
        users=user_list
    )


# ==================================
# RUN FLASK APPLICATION
# ==================================

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)