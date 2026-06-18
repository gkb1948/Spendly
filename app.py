import os
from datetime import datetime

from flask import Flask, render_template, session, redirect, request, abort, url_for
from database.db import get_db, init_db, seed_db, create_user, get_user_by_email
from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
    get_expense_by_id,
    update_expense,
    add_expense,
    delete_expense as _delete_expense,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev")

# Initialize database on app startup
with app.app_context():
    init_db()
    seed_db()


@app.context_processor
def inject_user():
    return {"user_id": session.get("user_id")}


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def _parse_date_param(value):
    """Validate a YYYY-MM-DD date string. Returns the string or None."""
    if not value:
        return None
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return value
    except ValueError:
        return None


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
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    user = get_user_by_id(user_id)
    if not user:
        session.clear()
        return redirect(url_for("login"))

    start_date = _parse_date_param(request.args.get("start_date"))
    end_date = _parse_date_param(request.args.get("end_date"))

    context = {
        "user": user,
        "stats": get_summary_stats(user_id, start_date=start_date, end_date=end_date),
        "transactions": get_recent_transactions(user_id, start_date=start_date, end_date=end_date),
        "categories": get_category_breakdown(user_id, start_date=start_date, end_date=end_date),
        "filter_start": start_date,
        "filter_end": end_date,
        "active_page": "profile",
    }
    return render_template("profile.html", **context)


@app.route("/analytics")
def analytics():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    return render_template("analytics.html", active_page="analytics")


ALLOWED_CATEGORIES = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]


@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense_route():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    if request.method == "GET":
        return render_template(
            "add_expense.html",
            categories=ALLOWED_CATEGORIES,
            error=None,
            active_page="add_expense",
        )

    amount_str = request.form.get("amount", "").strip()
    category = request.form.get("category", "").strip()
    date_str = request.form.get("date", "").strip()
    description = request.form.get("description", "").strip() or None

    error = None
    try:
        amount = float(amount_str)
        if amount <= 0:
            error = "Amount must be greater than 0."
    except (ValueError, TypeError):
        error = "Amount must be a valid number."

    if not error and category not in ALLOWED_CATEGORIES:
        error = "Please select a valid category."

    if not error:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            error = "Please enter a valid date in YYYY-MM-DD format."

    if error:
        return render_template(
            "add_expense.html",
            categories=ALLOWED_CATEGORIES,
            error=error,
            form_data=request.form,
        )

    add_expense(user_id, amount, category, date_str, description)
    return redirect(url_for("profile"))


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
def edit_expense(id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    expense = get_expense_by_id(id, user_id)
    if not expense:
        abort(404)

    if request.method == "GET":
        return render_template(
            "edit_expense.html",
            expense=expense,
            categories=ALLOWED_CATEGORIES,
            error=None,
        )

    amount_str = request.form.get("amount", "").strip()
    category = request.form.get("category", "").strip()
    date_str = request.form.get("date", "").strip()
    description = request.form.get("description", "").strip() or None

    error = None
    try:
        amount = float(amount_str)
        if amount <= 0:
            error = "Amount must be greater than 0."
    except (ValueError, TypeError):
        error = "Amount must be a valid number."

    if not error and category not in ALLOWED_CATEGORIES:
        error = "Please select a valid category."

    if not error:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            error = "Please enter a valid date in YYYY-MM-DD format."

    if error:
        return render_template(
            "edit_expense.html",
            expense=expense,
            categories=ALLOWED_CATEGORIES,
            error=error,
            form_data=request.form,
        )

    update_expense(id, user_id, amount, category, date_str, description)
    return redirect(url_for("profile"))


@app.route("/expenses/<int:id>/delete", methods=["POST"])
def delete_expense(id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    expense = get_expense_by_id(id, user_id)
    if not expense:
        abort(404)

    _delete_expense(id, user_id)
    return redirect(url_for("profile"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(debug=debug, host="0.0.0.0", port=port)
