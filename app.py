import os
from dotenv import load_dotenv

load_dotenv()
from flask import Flask, render_template, jsonify, request
import mysql.connector

app = Flask(__name__)


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password=os.getenv("DB_PASSWORD"),
        database="healthcare_db"
    )


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/dashboard")
def dashboard_data():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Total counts
        cursor.execute("SELECT COUNT(*) FROM Patients")
        patients = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Doctors")
        doctors = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Appointments")
        appointments = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Medical_Records")
        records = cursor.fetchone()[0]

        # Appointments grouped by status
        cursor.execute("""
            SELECT status, COUNT(*)
            FROM Appointments
            GROUP BY status
        """)
        appointment_rows = cursor.fetchall()

        appointment_labels = [
            row[0] or "Unspecified" for row in appointment_rows
        ]
        appointment_values = [row[1] for row in appointment_rows]

        # Patients grouped by gender
        cursor.execute("""
            SELECT gender, COUNT(*)
            FROM Patients
            GROUP BY gender
        """)
        gender_rows = cursor.fetchall()

        gender_labels = [
            row[0] or "Unspecified" for row in gender_rows
        ]
        gender_values = [row[1] for row in gender_rows]

        return jsonify({
            "patients": patients,
            "doctors": doctors,
            "appointments": appointments,
            "records": records,
            "appointment_labels": appointment_labels,
            "appointment_values": appointment_values,
            "gender_labels": gender_labels,
            "gender_values": gender_values
        })

    except mysql.connector.Error:
        app.logger.exception("Database query failed")
        return jsonify({"error": "Unable to retrieve dashboard data"}), 500

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@app.route("/api/patients", methods=["POST"])
def add_patient():
    data = request.get_json(silent=True) or {}

    name = data.get("patient_name", "").strip()
    if not name:
        return jsonify({"error": "Patient name is required"}), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO Patients
                (patient_name, date_of_birth, gender, phone,
                 email, address, blood_group)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            name,
            data.get("date_of_birth") or None,
            data.get("gender") or None,
            data.get("phone") or None,
            data.get("email") or None,
            data.get("address") or None,
            data.get("blood_group") or None
        ))

        connection.commit()
        return jsonify({
            "message": "Patient registered successfully!",
            "patient_id": cursor.lastrowid
        }), 201

    except mysql.connector.Error:
        app.logger.exception("Patient registration failed")
        return jsonify({"error": "Could not save patient"}), 500

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()
            
@app.route("/patients")
def patients_page():
    return render_template("patients.html")


@app.route("/api/patients", methods=["GET"])
def list_patients():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT patient_id, patient_name, date_of_birth,
                   gender, phone, email, blood_group
            FROM Patients
            ORDER BY patient_id DESC
        """)

        patients = cursor.fetchall()

        for patient in patients:
            if patient["date_of_birth"]:
                patient["date_of_birth"] = (
                    patient["date_of_birth"].isoformat()
                )

        return jsonify(patients)

    except mysql.connector.Error:
        app.logger.exception("Could not retrieve patients")
        return jsonify({"error": "Could not retrieve patient records"}), 500

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

@app.route("/doctors")
def doctors_page():
    return render_template("doctors.html")


@app.route("/api/doctors", methods=["GET"])
def list_doctors():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT doctor_id, doctor_name, specialization, phone, email
            FROM Doctors
            ORDER BY doctor_id DESC
        """)
        return jsonify(cursor.fetchall())

    except mysql.connector.Error:
        app.logger.exception("Could not retrieve doctors")
        return jsonify({"error": "Could not retrieve doctors"}), 500

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@app.route("/api/doctors", methods=["POST"])
def add_doctor():
    data = request.get_json(silent=True) or {}
    name = data.get("doctor_name", "").strip()

    if not name:
        return jsonify({"error": "Doctor name is required"}), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO Doctors
                (doctor_name, specialization, phone, email)
            VALUES (%s, %s, %s, %s)
        """, (
            name,
            data.get("specialization") or None,
            data.get("phone") or None,
            data.get("email") or None
        ))
        connection.commit()
        return jsonify({
            "message": "Doctor registered successfully!",
            "doctor_id": cursor.lastrowid
        }), 201

    except mysql.connector.Error:
        app.logger.exception("Doctor registration failed")
        return jsonify({"error": "Could not save doctor"}), 500

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

@app.route("/appointments")
def appointments_page():
    return render_template("appointments.html")


@app.route("/api/appointments", methods=["GET"])
def list_appointments():
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT a.appointment_id, p.patient_name, d.doctor_name,
                   a.appointment_date, a.reason, a.status
            FROM Appointments a
            JOIN Patients p ON a.patient_id = p.patient_id
            JOIN Doctors d ON a.doctor_id = d.doctor_id
            ORDER BY a.appointment_date DESC
        """)
        rows = cursor.fetchall()
        for row in rows:
            row["appointment_date"] = row["appointment_date"].isoformat(
                sep=" ", timespec="minutes"
            )
        return jsonify(rows)
    except mysql.connector.Error:
        app.logger.exception("Could not load appointments")
        return jsonify({"error": "Could not load appointments"}), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.route("/api/appointments", methods=["POST"])
def add_appointment():
    data = request.get_json(silent=True) or {}
    try:
        patient_id = int(data.get("patient_id", 0))
        doctor_id = int(data.get("doctor_id", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Select a valid patient and doctor"}), 400

    appointment_date = data.get("appointment_date", "").strip()
    if not appointment_date:
        return jsonify({"error": "Appointment date and time are required"}), 400

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO Appointments
                (patient_id, doctor_id, appointment_date, reason, status)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            patient_id,
            doctor_id,
            appointment_date.replace("T", " "),
            data.get("reason") or None,
            "Scheduled"
        ))
        connection.commit()
        return jsonify({
            "message": "Appointment scheduled successfully!",
            "appointment_id": cursor.lastrowid
        }), 201
    except mysql.connector.Error:
        app.logger.exception("Appointment creation failed")
        return jsonify({
            "error": "Could not schedule appointment. Check patient and doctor IDs."
        }), 400
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.route("/medical-history")
def medical_history_page():
    return render_template("medical_history.html")


@app.route("/api/medical-history", methods=["GET", "POST"])
def medical_history_api():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        data = request.get_json()
        cursor.execute(
            """INSERT INTO Medical_Records
            (patient_id, doctor_id, diagnosis, symptoms, treatment, record_date)
            VALUES (%s, %s, %s, %s, %s, %s)""",
            (
                data["patient_id"],
                data["doctor_id"],
                data["diagnosis"],
                data.get("symptoms", ""),
                data.get("treatment", ""),
                data["record_date"]
            )
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Medical record added successfully!"}), 201

    cursor.execute("""
        SELECT m.record_id, p.patient_name, d.doctor_name,
               m.diagnosis, m.symptoms, m.treatment, m.record_date
        FROM Medical_Records m
        JOIN Patients p ON m.patient_id = p.patient_id
        JOIN Doctors d ON m.doctor_id = d.doctor_id
        ORDER BY m.record_date DESC
    """)
    records = cursor.fetchall()

    for record in records:
        if record["record_date"]:
            record["record_date"] = record["record_date"].isoformat()

    cursor.close()
    conn.close()
    return jsonify(records)


@app.route("/api/prescriptions", methods=["GET", "POST"])
def prescriptions_api():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        data = request.get_json()
        cursor.execute(
            """INSERT INTO Prescriptions
            (record_id, medicine_name, dosage, frequency, duration)
            VALUES (%s, %s, %s, %s, %s)""",
            (
                data["record_id"],
                data["medicine_name"],
                data["dosage"],
                data["frequency"],
                data["duration"]
            )
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Prescription added successfully!"}), 201

    cursor.execute("""
        SELECT pr.prescription_id, pr.record_id, p.patient_name,
               pr.medicine_name, pr.dosage, pr.frequency, pr.duration
        FROM Prescriptions pr
        JOIN Medical_Records mr ON pr.record_id = mr.record_id
        JOIN Patients p ON mr.patient_id = p.patient_id
        ORDER BY pr.prescription_id DESC
    """)
    prescriptions = cursor.fetchall()

    cursor.close()
    conn.close()
    return jsonify(prescriptions)


if __name__ == "__main__":
    app.run(debug=True)
