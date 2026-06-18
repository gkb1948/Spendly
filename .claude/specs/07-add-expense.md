Spec: Add Expense
Overview

Step 7 lets a logged-in user add a new expense via a form at /expenses/add. The GET handler renders a blank form; the POST handler validates the submission and inserts a new row into the expenses table. After a successful add, the user is redirected to their profile page where the new expense appears in the transaction list. This step establishes the form pattern that Step 8 (Edit Expense) follows.
Depends on

    Step 1: Database setup (expenses table exists with all required columns)
    Step 3: Login / Logout (session["user_id"] is set and enforced)
    Step 4: Profile page renders the transaction list (the destination after a successful add)

Routes

    GET /expenses/add — render blank add-expense form — logged-in only
    POST /expenses/add — validate and insert new expense — logged-in only

Database changes

No new tables or columns. The existing expenses table has all required columns: id, user_id, amount, category, date, description, created_at.

A new query helper add_expense(user_id, amount, category, date, description) is added to database/queries.py.
Templates

    Create: templates/add_expense.html
        Extends base.html
        Form with method="POST" and action="/expenses/add"
        Fields (mirrors edit_expense.html layout):
            amount — number input, step="0.01", min="0.01", required
            category — <select> with 7 fixed options and a blank default, required
            date — <input type="date">, required
            description — text input, optional, max 200 chars
        Submit button ("Add Expense") and a cancel link back to /profile
        Display error message when validation fails, re-populating submitted values

    Modify: templates/profile.html
        No structural changes needed — the new expense will appear in the transaction list automatically after redirect

Files to change

    database/queries.py
        Add add_expense(user_id, amount, category, date, description) — issues a parameterised INSERT and commits; returns the new row id

    app.py
        Import add_expense from database.queries
        Replace the GET-only stub at /expenses/add with a full GET + POST handler:
            GET: render add_expense.html with categories list and no form_data
            POST: read form fields, validate, call add_expense, redirect to /profile on success; re-render form with errors otherwise
        Change the route decorator to accept both methods: @app.route("/expenses/add", methods=["GET", "POST"])

Files to create

    templates/add_expense.html — the add-expense form template extending base.html

New dependencies

No new dependencies.
Rules for implementation

    No SQLAlchemy or ORMs — raw sqlite3 only via get_db()
    Parameterised queries only — never string-format values into SQL
    Foreign keys PRAGMA must be enabled on every connection (already done in get_db())
    Unauthenticated access to both GET and POST must redirect to /login
    Validation rules for POST:
        amount: required, must be a positive number > 0 (parse with float(); catch ValueError)
        category: required, must be one of the 7 fixed categories (ALLOWED_CATEGORIES)
        date: required, must be a valid YYYY-MM-DD string (parse with datetime.strptime)
        description: optional; strip whitespace; store None if blank
        On any validation error, re-render the form with the error message and the submitted values pre-filled
    After a successful insert, redirect to url_for("profile") — do NOT render the form again
    Use url_for() for every internal link — never hardcode paths
    Use CSS variables — never hardcode hex values
    All templates extend base.html
    No inline styles
    Currency must always display as ₹ — never £ or $
    The form should display the same way as edit_expense.html (reuse the same CSS classes)

Tests to write

File: tests/test_add_expense.py
Unit tests

    add_expense — valid data: inserts row and returns the new row id
    add_expense — missing description: inserts row with description = None

Route tests

    GET /expenses/add — unauthenticated: redirects to /login (302)
    GET /expenses/add — authenticated: returns 200, renders blank form with all 7 category options
    POST /expenses/add — unauthenticated: redirects to /login (302)
    POST /expenses/add — authenticated, valid data: redirects to /profile (302), new row exists in database
    POST /expenses/add — authenticated, missing amount: re-renders with error, form values preserved
    POST /expenses/add — authenticated, amount = 0: re-renders with error
    POST /expenses/add — authenticated, non-numeric amount: re-renders with error
    POST /expenses/add — authenticated, invalid category: re-renders with error
    POST /expenses/add — authenticated, invalid date: re-renders with error
    POST /expenses/add — authenticated, no description: redirects to /profile, description stored as None

Definition of done

    Visiting /expenses/add while logged out redirects to /login
    Visiting /expenses/add while logged in shows a blank form with amount, category, date, and description fields
    The category dropdown contains 7 categories (Food, Transport, Bills, Health, Entertainment, Shopping, Other) plus a blank default option
    Submitting valid data redirects to /profile and the new expense appears in the transaction list
    Submitting with an invalid amount (missing, zero, non-numeric) re-renders the form with an error and retains submitted values
    Submitting with an invalid category re-renders the form with an error and retains the selected category
    Submitting with an invalid date re-renders the form with an error and retains the submitted date
    Submitting without a description inserts the expense with no description (no error)
    The form layout matches the design of edit_expense.html
