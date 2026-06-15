from datetime import datetime

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

    from database.queries import get_user_by_id, get_summary_stats, get_recent_transactions, get_category_breakdown

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
