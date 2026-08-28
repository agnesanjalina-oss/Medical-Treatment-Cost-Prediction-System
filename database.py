import sqlite3

DATABASE = "database.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_database():

    conn = get_db_connection()

    # =========================
    # USERS TABLE
    # =========================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            user_type TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # =========================
    # PATIENTS TABLE
    # =========================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            disease TEXT NOT NULL,
            treatment TEXT NOT NULL,
            hospital TEXT NOT NULL
        )
    """)

    # =========================
    # PREDICTIONS TABLE
    # =========================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            predicted_cost REAL NOT NULL,
            prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id)
            REFERENCES patients(id)
        )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_database()
    print("Database created successfully!")