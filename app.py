from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

# =====================================================
# APPLICATION SETTINGS
# =====================================================

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "medical_cost_secret"
)

# Use one database file consistently
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "medical_cost.db")


# =====================================================
# DATABASE CONNECTION
# =====================================================

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# =====================================================
# INITIALIZE DATABASE
# =====================================================

def init_db():

    conn = get_db_connection()

    # -------------------------------------------------
    # USERS TABLE
    # -------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            user_type TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # -------------------------------------------------
    # PATIENTS TABLE
    # -------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            blood_group TEXT,
            disease TEXT NOT NULL,
            admission_date TEXT
        )
    """)

    # -------------------------------------------------
    # PREDICTIONS TABLE
    # -------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            patient_name TEXT NOT NULL,
            disease TEXT NOT NULL,
            treatment_type TEXT NOT NULL,
            hospital_days INTEGER NOT NULL,
            icu INTEGER NOT NULL,
            predicted_cost REAL NOT NULL,
            prediction_date TEXT NOT NULL,

            FOREIGN KEY (patient_id)
            REFERENCES patients(id)
        )
    """)

    # -------------------------------------------------
    # CREATE DEMO ADMIN ACCOUNT
    # -------------------------------------------------

    admin = conn.execute(
        """
        SELECT *
        FROM users
        WHERE email = ?
        """,
        ("admin@gmail.com",)
    ).fetchone()

    if admin is None:

        conn.execute("""
            INSERT INTO users
            (
                name,
                email,
                phone,
                user_type,
                password
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            "Administrator",
            "admin@gmail.com",
            "",
            "Hospital Staff",
            "123456"
        ))

    conn.commit()
    conn.close()


# =====================================================
# IMPORTANT:
# INITIALIZE DATABASE WHEN FLASK/GUNICORN STARTS
# =====================================================

init_db()


# =====================================================
# LOGIN PAGE
# =====================================================

@app.route("/")
def login_page():

    return render_template("login.html")


# =====================================================
# LOGIN
# =====================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()

        # Check empty fields
        if not email or not password:

            return """
            <h3>Please enter email and password.</h3>
            <a href="/">Back to Login</a>
            """

        conn = get_db_connection()

        user = conn.execute("""
            SELECT *
            FROM users
            WHERE email = ? AND password = ?
        """, (
            email,
            password
        )).fetchone()

        conn.close()

        # Successful login
        if user:

            session["user"] = user["email"]
            session["user_name"] = user["name"]
            session["user_type"] = user["user_type"]

            return redirect(
                url_for("dashboard")
            )

        # Invalid login
        return """
        <h3>Invalid Email or Password</h3>

        <p>Please check your email and password.</p>

        <a href="/">Back to Login</a>
        """

    return redirect(
        url_for("login_page")
    )


# =====================================================
# REGISTER PAGE + REGISTRATION
# =====================================================

@app.route("/register", methods=["GET", "POST"])
def register_page():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        user_type = request.form.get(
            "user_type",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()

        confirm_password = request.form.get(
            "confirm_password",
            ""
        ).strip()

        # -------------------------------------------------
        # VALIDATE REQUIRED FIELDS
        # -------------------------------------------------

        if not name or not email or not password:

            return """
            <h3>Please fill in all required fields.</h3>

            <a href="/register">
                Back to Register
            </a>
            """

        # -------------------------------------------------
        # CHECK PASSWORD
        # -------------------------------------------------

        if password != confirm_password:

            return """
            <h3>Passwords do not match!</h3>

            <a href="/register">
                Back to Register
            </a>
            """

        # -------------------------------------------------
        # DEFAULT USER TYPE
        # -------------------------------------------------

        if not user_type:

            user_type = "Hospital Staff"

        # -------------------------------------------------
        # SAVE USER
        # -------------------------------------------------

        conn = get_db_connection()

        try:

            conn.execute("""
                INSERT INTO users
                (
                    name,
                    email,
                    phone,
                    user_type,
                    password
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                name,
                email,
                phone,
                user_type,
                password
            ))

            conn.commit()

        except sqlite3.IntegrityError:

            conn.close()

            return """
            <h3>Email already exists!</h3>

            <p>
                Please use a different email address.
            </p>

            <a href="/register">
                Back to Register
            </a>
            """

        conn.close()

        return """
        <h3>Registration Successful!</h3>

        <p>
            Your account has been created successfully.
        </p>

        <a href="/">
            Go to Login
        </a>
        """

    return render_template(
        "register.html"
    )


# =====================================================
# DASHBOARD
# =====================================================

@app.route("/dashboard")
def dashboard():

    # Check login
    if "user" not in session:

        return redirect(
            url_for("login_page")
        )

    return render_template(
        "dashboard.html",
        user=session.get("user"),
        user_name=session.get("user_name"),
        user_type=session.get("user_type")
    )


# =====================================================
# PATIENT INFORMATION
# =====================================================

@app.route("/patient", methods=["GET", "POST"])
def patient():

    # Check login
    if "user" not in session:

        return redirect(
            url_for("login_page")
        )

    # -------------------------------------------------
    # SAVE PATIENT
    # -------------------------------------------------

    if request.method == "POST":

        patient_name = request.form.get(
            "patient_name",
            ""
        ).strip()

        age = request.form.get(
            "age",
            ""
        ).strip()

        gender = request.form.get(
            "gender",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        address = request.form.get(
            "address",
            ""
        ).strip()

        blood_group = request.form.get(
            "blood_group",
            ""
        ).strip()

        disease = request.form.get(
            "disease",
            ""
        ).strip()

        admission_date = request.form.get(
            "admission_date",
            ""
        ).strip()

        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if (
            not patient_name
            or not age
            or not gender
            or not disease
        ):

            return """
            <h3>
                Please fill in all required
                patient information.
            </h3>

            <a href="/patient">
                Back to Patient Information
            </a>
            """

        # Check age
        try:

            age = int(age)

        except ValueError:

            return """
            <h3>Age must be a number.</h3>

            <a href="/patient">
                Back to Patient Information
            </a>
            """

        if age <= 0:

            return """
            <h3>Age must be greater than 0.</h3>

            <a href="/patient">
                Back to Patient Information
            </a>
            """

        # -------------------------------------------------
        # INSERT PATIENT
        # -------------------------------------------------

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO patients
            (
                patient_name,
                age,
                gender,
                phone,
                address,
                blood_group,
                disease,
                admission_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            patient_name,
            age,
            gender,
            phone,
            address,
            blood_group,
            disease,
            admission_date
        ))

        conn.commit()
        conn.close()

        return redirect(
            url_for("patient")
        )

    # -------------------------------------------------
    # GET PATIENTS
    # -------------------------------------------------

    conn = get_db_connection()

    patients = conn.execute("""
        SELECT *
        FROM patients
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "patient.html",
        patients=patients
    )


# =====================================================
# TREATMENT COST PREDICTION
# =====================================================

@app.route("/prediction", methods=["GET", "POST"])
def prediction():

    # Check login
    if "user" not in session:

        return redirect(
            url_for("login_page")
        )

    predicted_cost = None

    # -------------------------------------------------
    # MAKE PREDICTION
    # -------------------------------------------------

    if request.method == "POST":

        patient_id = request.form.get(
            "patient_id",
            ""
        ).strip()

        patient_name = request.form.get(
            "patient_name",
            ""
        ).strip()

        disease = request.form.get(
            "disease",
            ""
        ).strip()

        treatment_type = request.form.get(
            "treatment_type",
            ""
        ).strip()

        hospital_days_text = request.form.get(
            "hospital_days",
            "0"
        ).strip()

        icu_text = request.form.get(
            "icu",
            "0"
        ).strip()

        # -------------------------------------------------
        # VALIDATE REQUIRED FIELDS
        # -------------------------------------------------

        if not patient_name:

            return """
            <h3>Please enter patient name.</h3>

            <a href="/prediction">
                Back to Prediction
            </a>
            """

        if not disease:

            return """
            <h3>Please enter disease.</h3>

            <a href="/prediction">
                Back to Prediction
            </a>
            """

        if not treatment_type:

            treatment_type = "General Treatment"

        # -------------------------------------------------
        # VALIDATE NUMBERS
        # -------------------------------------------------

        try:

            hospital_days = int(
                hospital_days_text
            )

            icu = int(
                icu_text
            )

        except ValueError:

            return """
            <h3>
                Hospital days and ICU must be numbers.
            </h3>

            <a href="/prediction">
                Back to Prediction
            </a>
            """

        if hospital_days < 0:

            hospital_days = 0

        if icu not in [0, 1]:

            icu = 0

        # -------------------------------------------------
        # DEMO COST CALCULATION
        # -------------------------------------------------

        base_cost = 5000

        daily_cost = hospital_days * 3000

        icu_cost = icu * 10000

        predicted_cost = (
            base_cost
            + daily_cost
            + icu_cost
        )

        # -------------------------------------------------
        # SAVE PREDICTION
        # -------------------------------------------------

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO predictions
            (
                patient_id,
                patient_name,
                disease,
                treatment_type,
                hospital_days,
                icu,
                predicted_cost,
                prediction_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            patient_id if patient_id else None,
            patient_name,
            disease,
            treatment_type,
            hospital_days,
            icu,
            predicted_cost,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        ))

        conn.commit()
        conn.close()

    # -------------------------------------------------
    # SHOW PATIENTS FOR PREDICTION
    # -------------------------------------------------

    conn = get_db_connection()

    patients = conn.execute("""
        SELECT *
        FROM patients
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "prediction.html",
        predicted_cost=predicted_cost,
        patients=patients
    )


# =====================================================
# PREDICTION HISTORY
# =====================================================

@app.route("/history")
def history():

    # Check login
    if "user" not in session:

        return redirect(
            url_for("login_page")
        )

    conn = get_db_connection()

    predictions = conn.execute("""
        SELECT *
        FROM predictions
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "history.html",
        predictions=predictions
    )


# =====================================================
# LOGOUT
# =====================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login_page")
    )


# =====================================================
# RUN APPLICATION LOCALLY
# =====================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),
        debug=True
    )