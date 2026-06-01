import sys
import random
from datetime import datetime
from werkzeug.security import generate_password_hash
from database.db import get_db

# Indian names across regions
first_names = [
    "Vikram", "Priya", "Aditya", "Ravi", "Neha", "Arjun", "Divya", "Rohan",
    "Ananya", "Sanjay", "Pooja", "Rahul", "Shreya", "Karan", "Isha", "Nikhil",
    "Anjali", "Varun", "Meera", "Abhishek", "Tanya", "Harshit", "Simran", "Aryan"
]

last_names = [
    "Patel", "Sharma", "Gupta", "Kumar", "Rao", "Singh", "Khan", "Iyer",
    "Nair", "Reddy", "Malhotra", "Verma", "Sinha", "Saxena", "Desai", "Menon",
    "Kapoor", "Khanna", "Bhat", "Joshi"
]

def generate_user_data():
    """Generate a random Indian user with name and email."""
    first = random.choice(first_names)
    last = random.choice(last_names)
    name = f"{first} {last}"
    email = f"{first.lower()}.{last.lower()}{random.randint(10, 999)}@gmail.com"
    return name, email

def email_exists(conn, email):
    """Check if email already exists in users table."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE email = ?", (email,))
    count = cursor.fetchone()[0]
    return count > 0

def seed_user():
    """Create and insert a single dummy Indian user."""
    conn = get_db()
    cursor = conn.cursor()

    # Generate unique user
    max_attempts = 10
    for attempt in range(max_attempts):
        name, email = generate_user_data()
        if not email_exists(conn, email):
            break
        if attempt == max_attempts - 1:
            print("Error: Could not generate unique email after max attempts")
            conn.close()
            sys.exit(1)

    # Hash password
    password_hash = generate_password_hash("password123")

    # Insert user
    cursor.execute(
        "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
        (name, email, password_hash, datetime.now().isoformat())
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Print confirmation
    print(f"id: {user_id}")
    print(f"name: {name}")
    print(f"email: {email}")

if __name__ == "__main__":
    seed_user()
