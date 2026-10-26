import os
from dotenv import load_dotenv

load_dotenv()
import mysql.connector

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password=os.getenv("DB_PASSWORD"),
    database="healthcare_db"
)

cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS Patients (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    gender VARCHAR(20),
    phone VARCHAR(15),
    email VARCHAR(100),
    address VARCHAR(255),
    blood_group VARCHAR(5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# 2. Doctors table
cursor.execute("""
CREATE TABLE IF NOT EXISTS Doctors (
    doctor_id INT AUTO_INCREMENT PRIMARY KEY,
    doctor_name VARCHAR(100) NOT NULL,
    specialization VARCHAR(100),
    phone VARCHAR(15),
    email VARCHAR(100)
)
""")

# 3. Appointments table
cursor.execute("""
CREATE TABLE IF NOT EXISTS Appointments (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appointment_date DATETIME NOT NULL,
    reason VARCHAR(255),
    status VARCHAR(30) DEFAULT 'Scheduled',
    FOREIGN KEY (patient_id) REFERENCES Patients(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES Doctors(doctor_id)
)
""")

# 4. Medical Records table
cursor.execute("""
CREATE TABLE IF NOT EXISTS Medical_Records (
    record_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT,
    diagnosis VARCHAR(255) NOT NULL,
    symptoms TEXT,
    treatment TEXT,
    record_date DATE NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES Patients(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES Doctors(doctor_id)
)
""")

# 5. Prescriptions table
cursor.execute("""
CREATE TABLE IF NOT EXISTS Prescriptions (
    prescription_id INT AUTO_INCREMENT PRIMARY KEY,
    record_id INT NOT NULL,
    medicine_name VARCHAR(100) NOT NULL,
    dosage VARCHAR(100),
    frequency VARCHAR(100),
    duration VARCHAR(100),
    FOREIGN KEY (record_id)
        REFERENCES Medical_Records(record_id)
)
""")

print("Doctors table created successfully!")
print("Appointments table created successfully!")
print("Medical Records table created successfully!")
print("Prescriptions table created successfully!")

connection.commit()
print("Patients table created successfully!")

cursor.close()
connection.close()
