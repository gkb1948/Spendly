import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash


def get_db():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "spendly.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


def seed_db():
    conn = get_db()
    cursor = conn.cursor()

    # Check if already seeded
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    if count > 0:
        conn.close()
        return

    # Insert demo user
    hashed_password = generate_password_hash("demo123")
    cursor.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", hashed_password)
    )
    user_id = cursor.lastrowid

    # Insert sample expenses
    expenses_data = [
        (user_id, 45.50, "Food", "2026-05-01", "Groceries"),
        (user_id, 12.99, "Food", "2026-05-03", "Lunch"),
        (user_id, 25.00, "Transport", "2026-05-05", "Gas"),
        (user_id, 150.00, "Bills", "2026-05-07", "Electricity"),
        (user_id, 35.75, "Health", "2026-05-09", "Pharmacy"),
        (user_id, 20.00, "Entertainment", "2026-05-12", "Movie"),
        (user_id, 89.99, "Shopping", "2026-05-15", "Clothes"),
        (user_id, 15.00, "Other", "2026-05-20", "Misc"),
    ]

    cursor.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        expenses_data
    )

    conn.commit()
    conn.close()


def get_user_by_email(email):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None


def create_user(name, email, password):
    if not name or not name.strip():
        raise ValueError("Name is required")
    if not email or "@" not in email:
        raise ValueError("Valid email is required")
    if not password or len(password) < 6:
        raise ValueError("Password must be at least 6 characters")

    conn = get_db()
    cursor = conn.cursor()

    try:
        hashed_password = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name.strip(), email, hashed_password)
        )
        conn.commit()
        user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError("Email already registered")
    finally:
        conn.close()

    return user_id
