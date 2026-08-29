import os
import sqlite3
import joblib
import pandas as pd

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "medical_cost_prediction_secret_key"
)


# ============================================================
# FILE PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "model",
    "medical_cost_model.pkl"
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "database.db"
)


# ============================================================
# LOAD ML MODEL
# ============================================================

try:

    model = joblib.load(MODEL_PATH)

    print("========================================")
    print("ML MODEL LOADED SUCCESSFULLY")
    print("========================================")
    print("Model:", MODEL_PATH)

    if hasattr(model, "feature_names_in_"):

        print("Model features:")
        print(list(model.feature_names_in_))

except Exception as e:

    model = None

    print("========================================")
    print("ERROR: ML MODEL COULD NOT BE LOADED")
    print("========================================")
    print(e)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db_connection():

    conn = sqlite3.connect(
        DATABASE_PATH
    )

    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_database():

    conn = get_db_connection()

    cursor = conn.cursor()

    # USERS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT UNIQUE NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL

        )
    """)

    # PATIENTS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            patient_name TEXT NOT NULL,

            age INTEGER NOT NULL,

            gender TEXT NOT NULL,

            disease TEXT NOT NULL,

            department TEXT NOT NULL

        )
    """)

    # PREDICTION HISTORY TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prediction_history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            patient_id INTEGER,

            patient_name TEXT,

            age INTEGER,

            gender TEXT,

            department TEXT,

            disease TEXT,

            treatment_type TEXT,

            hospital_days INTEGER,

            icu TEXT,

            hospital_type TEXT,

            hospital_location TEXT,

            predicted_cost REAL,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP

        )
    """)

    conn.commit()

    conn.close()

    print("Database initialized successfully.")


init_database()


# ============================================================
# LOGIN PAGE
# ============================================================

@app.route("/")
def index():

    if "user_id" in session:

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "login.html"
    )


# ============================================================
# REGISTER
# ============================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "GET":

        return render_template(
            "register.html"
        )

    name = request.form.get(
        "name",
        ""
    ).strip()

    username = request.form.get(
        "username",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    password = request.form.get(
        "password",
        ""
    ).strip()

    confirm_password = request.form.get(
        "confirm_password",
        ""
    ).strip()

    # DEFAULT USERNAME
    if not username:

        if email:

            username = email.split("@")[0]

        else:

            username = name

    if not name:

        name = username

    # VALIDATION
    if not email:

        flash(
            "Email is required."
        )

        return redirect(
            url_for("register")
        )

    if not password:

        flash(
            "Password is required."
        )

        return redirect(
            url_for("register")
        )

    if password != confirm_password:

        flash(
            "Passwords do not match."
        )

        return redirect(
            url_for("register")
        )

    if len(password) < 6:

        flash(
            "Password must contain at least 6 characters."
        )

        return redirect(
            url_for("register")
        )

    conn = get_db_connection()

    try:

        # CHECK EMAIL
        existing_email = conn.execute(
            """
            SELECT id
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        if existing_email:

            flash(
                "Email already exists. Please login."
            )

            return redirect(
                url_for("index")
            )

        # CHECK USERNAME
        existing_username = conn.execute(
            """
            SELECT id
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

        if existing_username:

            base_username = username

            counter = 1

            while True:

                new_username = (
                    base_username
                    + "_"
                    + str(counter)
                )

                check_username = conn.execute(
                    """
                    SELECT id
                    FROM users
                    WHERE username = ?
                    """,
                    (new_username,)
                ).fetchone()

                if not check_username:

                    username = new_username

                    break

                counter += 1

        # INSERT USER
        conn.execute(
            """
            INSERT INTO users
            (
                username,
                email,
                password
            )
            VALUES (?, ?, ?)
            """,
            (
                username,
                email,
                password
            )
        )

        conn.commit()

        flash(
            "Registration successful. Please login."
        )

        return redirect(
            url_for("index")
        )

    except sqlite3.Error as e:

        conn.rollback()

        flash(
            "Registration error: "
            + str(e)
        )

        return redirect(
            url_for("register")
        )

    finally:

        conn.close()


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "GET":

        return redirect(
            url_for("index")
        )

    login_value = request.form.get(
        "username",
        ""
    ).strip().lower()

    if not login_value:

        login_value = request.form.get(
            "email",
            ""
        ).strip().lower()

    password = request.form.get(
        "password",
        ""
    ).strip()

    if not login_value or not password:

        flash(
            "Please enter username/email and password."
        )

        return redirect(
            url_for("index")
        )

    conn = get_db_connection()

    try:

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE LOWER(email) = ?
               OR LOWER(username) = ?
            """,
            (
                login_value,
                login_value
            )
        ).fetchone()

    except sqlite3.Error as e:

        conn.close()

        flash(
            "Database error: "
            + str(e)
        )

        return redirect(
            url_for("index")
        )

    conn.close()

    if user and user["password"] == password:

        session.clear()

        session["user_id"] = user["id"]

        session["username"] = user["username"]

        session["email"] = user["email"]

        return redirect(
            url_for("dashboard")
        )

    flash(
        "Invalid username/email or password."
    )

    return redirect(
        url_for("index")
    )


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("index")
        )

    conn = get_db_connection()

    try:

        patients = conn.execute(
            """
            SELECT *
            FROM patients
            ORDER BY id DESC
            """
        ).fetchall()

        total_patients = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM patients
            """
        ).fetchone()["total"]

        total_predictions = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM prediction_history
            """
        ).fetchone()["total"]

    finally:

        conn.close()

    return render_template(
        "dashboard.html",
        patients=patients,
        total_patients=total_patients,
        total_predictions=total_predictions
    )


# ============================================================
# ADD PATIENT
# ============================================================

@app.route(
    "/patient",
    methods=["GET", "POST"]
)
def patient():

    if "user_id" not in session:

        return redirect(
            url_for("index")
        )

    if request.method == "GET":

        return render_template(
            "patient.html"
        )

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

    disease = request.form.get(
        "disease",
        ""
    ).strip()

    department = request.form.get(
        "department",
        ""
    ).strip()

    # VALIDATION
    if not patient_name:

        flash(
            "Patient name is required."
        )

        return redirect(
            url_for("patient")
        )

    if not age:

        flash(
            "Age is required."
        )

        return redirect(
            url_for("patient")
        )

    if not gender:

        flash(
            "Gender is required."
        )

        return redirect(
            url_for("patient")
        )

    if not disease:

        flash(
            "Disease is required."
        )

        return redirect(
            url_for("patient")
        )

    if not department:

        flash(
            "Department is required."
        )

        return redirect(
            url_for("patient")
        )

    try:

        age = int(age)

        if age < 0 or age > 120:

            raise ValueError

    except ValueError:

        flash(
            "Please enter a valid age between 0 and 120."
        )

        return redirect(
            url_for("patient")
        )

    conn = get_db_connection()

    try:

        cursor = conn.execute(
            """
            INSERT INTO patients
            (
                patient_name,
                age,
                gender,
                disease,
                department
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                patient_name,
                age,
                gender,
                disease,
                department
            )
        )

        conn.commit()

        patient_id = cursor.lastrowid

        print(
            "Patient saved successfully:",
            patient_id,
            patient_name
        )

        flash(
            "Patient added successfully."
        )

        return redirect(
            url_for("patients")
        )

    except sqlite3.Error as e:

        conn.rollback()

        flash(
            "Could not save patient: "
            + str(e)
        )

        return redirect(
            url_for("patient")
        )

    finally:

        conn.close()


# ============================================================
# PATIENT LIST
# ============================================================

@app.route("/patients")
def patients():

    if "user_id" not in session:

        return redirect(
            url_for("index")
        )

    conn = get_db_connection()

    try:

        patient_records = conn.execute(
            """
            SELECT
                id,
                patient_name,
                age,
                gender,
                disease,
                department
            FROM patients
            ORDER BY id DESC
            """
        ).fetchall()

    except sqlite3.Error as e:

        conn.close()

        flash(
            "Could not load patients: "
            + str(e)
        )

        return redirect(
            url_for("dashboard")
        )

    conn.close()

    return render_template(
        "patients.html",
        patients=patient_records
    )


# ============================================================
# DELETE PATIENT
# ============================================================

@app.route(
    "/delete_patient/<int:patient_id>",
    methods=["POST"]
)
def delete_patient(patient_id):

    if "user_id" not in session:

        return redirect(
            url_for("index")
        )

    conn = get_db_connection()

    try:

        patient_record = conn.execute(
            """
            SELECT id
            FROM patients
            WHERE id = ?
            """,
            (patient_id,)
        ).fetchone()

        if not patient_record:

            flash(
                "Patient not found."
            )

            return redirect(
                url_for("patients")
            )

        conn.execute(
            """
            DELETE FROM patients
            WHERE id = ?
            """,
            (patient_id,)
        )

        conn.commit()

        flash(
            "Patient deleted successfully."
        )

    except sqlite3.Error as e:

        conn.rollback()

        flash(
            "Could not delete patient: "
            + str(e)
        )

    finally:

        conn.close()

    return redirect(
        url_for("patients")
    )


# ============================================================
# PREDICTION
# ============================================================

@app.route(
    "/prediction",
    methods=["GET", "POST"]
)
def prediction():

    if "user_id" not in session:

        return redirect(
            url_for("index")
        )

    predicted_cost = None

    selected_patient = None

    # GET PATIENT ID
    patient_id = request.args.get(
        "patient_id",
        ""
    ).strip()

    if patient_id:

        conn = get_db_connection()

        try:

            selected_patient = conn.execute(
                """
                SELECT *
                FROM patients
                WHERE id = ?
                """,
                (patient_id,)
            ).fetchone()

        finally:

            conn.close()

    # POST PREDICTION
    if request.method == "POST":

        if model is None:

            flash(
                "ML model could not be loaded."
            )

            return redirect(
                url_for("prediction")
            )

        try:

            # GET INPUTS
            age_text = request.form.get(
                "age",
                ""
            ).strip()

            gender = request.form.get(
                "gender",
                ""
            ).strip()

            department = request.form.get(
                "department",
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
                ""
            ).strip()

            # ICU
            icu_value = request.form.get(
                "icu",
                "No"
            ).strip()

            if icu_value.lower() == "yes":

                icu = 1
                icu_display = "Yes"

            else:

                icu = 0
                icu_display = "No"

            # OTHER INPUTS
            hospital_type = request.form.get(
                "hospital_type",
                ""
            ).strip()

            hospital_location = request.form.get(
                "hospital_location",
                ""
            ).strip()

            patient_name = request.form.get(
                "patient_name",
                ""
            ).strip()

            posted_patient_id = request.form.get(
                "patient_id",
                ""
            ).strip()

            # VALIDATE AGE
            if not age_text:

                raise ValueError(
                    "Age is required."
                )

            age = int(age_text)

            if age < 0 or age > 120:

                raise ValueError(
                    "Age must be between 0 and 120."
                )

            # VALIDATE HOSPITAL DAYS
            if not hospital_days_text:

                raise ValueError(
                    "Hospital days is required."
                )

            hospital_days = int(
                hospital_days_text
            )

            if (
                hospital_days < 1
                or hospital_days > 365
            ):

                raise ValueError(
                    "Hospital days must be between 1 and 365."
                )

            # VALIDATE CATEGORICAL INPUTS
            required_values = [

                gender,

                department,

                disease,

                treatment_type,

                hospital_type,

                hospital_location

            ]

            if any(
                not value
                for value in required_values
            ):

                raise ValueError(
                    "Please fill in all prediction fields."
                )

            # CREATE DATAFRAME
            input_data = pd.DataFrame(
                [
                    {
                        "age": age,

                        "gender": gender,

                        "department": department,

                        "disease": disease,

                        "treatment_type": treatment_type,

                        "hospital_days": hospital_days,

                        "icu": icu,

                        "hospital_type": hospital_type,

                        "hospital_location": hospital_location
                    }
                ]
            )

            # MATCH MODEL FEATURES
            if hasattr(
                model,
                "feature_names_in_"
            ):

                model_features = list(
                    model.feature_names_in_
                )

                input_data = input_data[
                    model_features
                ]

            print()
            print(
                "========================================"
            )
            print(
                "PREDICTION INPUT"
            )
            print(
                "========================================"
            )

            print(input_data)

            print(
                "ICU form value:",
                icu_value
            )

            print(
                "ICU model value:",
                icu
            )

            print(
                "========================================"
            )

            # MAKE PREDICTION
            prediction_result = model.predict(
                input_data
            )

            predicted_cost = float(
                prediction_result[0]
            )

            predicted_cost = max(
                0,
                predicted_cost
            )

            predicted_cost = round(
                predicted_cost,
                2
            )

            # SAVE PREDICTION HISTORY
            conn = get_db_connection()

            try:

                patient_id_value = None

                if posted_patient_id:

                    try:

                        patient_id_value = int(
                            posted_patient_id
                        )

                    except ValueError:

                        patient_id_value = None

                conn.execute(
                    """
                    INSERT INTO prediction_history
                    (
                        patient_id,
                        patient_name,
                        age,
                        gender,
                        department,
                        disease,
                        treatment_type,
                        hospital_days,
                        icu,
                        hospital_type,
                        hospital_location,
                        predicted_cost
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        patient_id_value,
                        patient_name,
                        age,
                        gender,
                        department,
                        disease,
                        treatment_type,
                        hospital_days,
                        icu_display,
                        hospital_type,
                        hospital_location,
                        predicted_cost
                    )
                )

                conn.commit()

            except sqlite3.Error as e:

                conn.rollback()

                raise Exception(
                    "Could not save prediction: "
                    + str(e)
                )

            finally:

                conn.close()

            flash(
                "Treatment cost predicted successfully."
            )

        except ValueError as e:

            flash(
                "Invalid input: "
                + str(e)
            )

        except Exception as e:

            flash(
                "Prediction error: "
                + str(e)
            )

    # RENDER PREDICTION PAGE
    return render_template(
        "prediction.html",
        predicted_cost=predicted_cost,
        selected_patient=selected_patient
    )


# ============================================================
# HISTORY
# ============================================================

@app.route("/history")
def history():

    if "user_id" not in session:

        return redirect(
            url_for("index")
        )

    conn = get_db_connection()

    try:

        history_records = conn.execute(
            """
            SELECT *
            FROM prediction_history
            ORDER BY id DESC
            """
        ).fetchall()

    except sqlite3.Error as e:

        conn.close()

        flash(
            "Could not load prediction history: "
            + str(e)
        )

        return redirect(
            url_for("dashboard")
        )

    conn.close()

    return render_template(
        "history.html",
        history=history_records
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("index")
    )


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    print()
    print("========================================")
    print("BANGLADESH MEDICAL COST PREDICTION")
    print("========================================")

    print(
        "ML model loaded:",
        model is not None
    )

    print(
        "Database:",
        DATABASE_PATH
    )

    print(
        "Starting Flask server..."
    )

    print(
        "========================================"
    )

    print()

    # Port 5000 is already being used by macOS.
    # Use port 5001 for local development.
    # If a hosting service provides PORT,
    # that PORT will be used automatically.

    port = int(
        os.environ.get(
            "PORT",
            5001
        )
    )

    print(
        f"Server running at: http://127.0.0.1:{port}"
    )

    print()

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )

