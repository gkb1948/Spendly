from flask import Flask, render_template, session, redirect, request, abort, url_for
from database.db import get_db, init_db, seed_db, create_user, get_user_by_email

app = Flask(__name__)
app.secret_key = "dev"

# Initialize database on app startup
with app.app_context():
    init_db()
    seed_db()


@app.context_processor
def inject_user():
    return {"user_id": session.get("user_id")}


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/register", methods=["POST"])
def register_post():
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")

    error = None
    try:
        create_user(name, email, password)
    except ValueError as e:
        error = str(e)

    if error:
        return render_template("register.html", error=error)

    return redirect(url_for("login"))


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login_post():
    from werkzeug.security import check_password_hash

    email = request.form.get("email")
    password = request.form.get("password")

    error = None
    user = get_user_by_email(email) if email else None

    if not user:
        error = "Invalid email or password"
    elif not check_password_hash(user["password_hash"], password):
        error = "Invalid email or password"

    if error:
        return render_template("login.html", error=error)

    session["user_id"] = user["id"]
    return redirect(url_for("landing"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    # Authentication guard
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))
    
    # Build hardcoded context with all four sections
    context = {
        "user": {
            "name": "Demo User",
            "email": "demo@spendly.com",
            "joined": "May 22, 2026",
            "initials": "DU"
        },
        "stats": {
            "total_spent": "₹393.24",
            "transaction_count": 8,
            "top_category": "Bills"
        },
        "transactions": [
            {
                "date": "May 20",
                "description": "Misc",
                "category": "Other",
                "amount": "₹15.00"
            },
            {
                "date": "May 15",
                "description": "Clothes",
                "category": "Shopping",
                "amount": "₹89.99"
            },
            {
                "date": "May 12",
                "description": "Movie",
                "category": "Entertainment",
                "amount": "₹20.00"
            },
            {
                "date": "May 09",
                "description": "Pharmacy",
                "category": "Health",
                "amount": "₹35.75"
            },
            {
                "date": "May 07",
                "description": "Electricity",
                "category": "Bills",
                "amount": "₹150.00"
            },
            {
                "date": "May 05",
                "description": "Gas",
                "category": "Transport",
                "amount": "₹25.00"
            },
            {
                "date": "May 03",
                "description": "Lunch",
                "category": "Food",
                "amount": "₹12.99"
            },
            {
                "date": "May 01",
                "description": "Groceries",
                "category": "Food",
                "amount": "₹45.50"
            }
        ],
        "categories": [
            {
                "name": "Bills",
                "total": "₹150.00",
                "count": 1,
                "percentage": 38.1
            },
            {
                "name": "Shopping",
                "total": "₹89.99",
                "count": 1,
                "percentage": 22.9
            },
            {
                "name": "Food",
                "total": "₹58.49",
                "count": 2,
                "percentage": 14.9
            },
            {
                "name": "Health",
                "total": "₹35.75",
                "count": 1,
                "percentage": 9.1
            },
            {
                "name": "Entertainment",
                "total": "₹20.00",
                "count": 1,
                "percentage": 5.1
            },
            {
                "name": "Transport",
                "total": "₹25.00",
                "count": 1,
                "percentage": 6.4
            },
            {
                "name": "Other",
                "total": "₹15.00",
                "count": 1,
                "percentage": 3.8
            }
        ]
    }
    
    return render_template("profile.html", **context)


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
