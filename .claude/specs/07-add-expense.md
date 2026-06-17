# Spec: Add Expense

## Overview

This feature allows a logged-in user to submit a new expense via a form at `/expenses/add`.
The form collects amount, category, date, and an optional description, validates the input
server-side, inserts the record into the `expenses` table, and redirects to the profile page
on success. It is the first write-path feature in Spendly and establishes the pattern that
Edit (Step 8) and Delete (Step 9) will follow.

## Depends on

- Step 1 — Database setup (`expenses` table, `get_db()`)
- Step 3 — Logout (session guard pattern)
- Step 4 / Step 5 — Profile page (redirect destination after save)

## Routes

| Method | Path | Description | Access |
|--------|------|-------------|--------|
| GET | `/expenses/add` | Render the blank add-expense form | Logged-in only |
| POST | `/expenses/add` | Validate and insert the expense, then redirect | Logged-in only |

Both routes must redirect to `/login` if `session.get("user_id")` is falsy.

## Database changes

No new tables or columns. The `expenses` table already exists in `database/db.py`:

```
expenses (id, user_id, amount, category, date, description, created_at)
```

Add one new helper function to `database/db.py`:

```python
def add_expense(user_id, amount, category, date, description):
    """Insert one expense row. Raises ValueError on bad input."""
```

## Templates

- **Create:** `templates/add_expense.html`
  - Extends `base.html`
  - Form fields: amount (number, step 0.01, required), category (select, required),
    date (date input, required, defaults to today), description (textarea, optional)
  - Shows inline error message when validation fails (re-renders with user values preserved)
  - Active nav item: none (or highlight a future "Add" nav link if base.html has one)

- **Modify:** none

## Files to change

| File | Change |
|------|--------|
| `app.py` | Replace the stub `add_expense()` route with GET + POST handlers |
| `database/db.py` | Add `add_expense()` helper function |

## Files to create

| File | Purpose |
|------|---------|
| `templates/add_expense.html` | Form template |

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs — raw `sqlite3` with parameterised queries only (`?` placeholders)
- Use CSS variables — never hardcode hex colour values in the template
- All templates extend `base.html`
- Server-side validation must cover:
  - `amount` — must be a positive number greater than 0
  - `category` — must be one of the allowed values (see list below)
  - `date` — must be a valid `YYYY-MM-DD` string (use `datetime.strptime`)
  - `description` — optional, strip whitespace, store `None` if blank
- Allowed categories (match the seed data in `db.py`):
  `Food`, `Transport`, `Bills`, `Health`, `Entertainment`, `Shopping`, `Other`
- On validation error: re-render the form with the error message and the user's entered values preserved
- On success: `redirect(url_for("profile"))`
- Import `add_expense` from `database.db` in `app.py`

## Definition of done

- [ ] Visiting `/expenses/add` without being logged in redirects to `/login`
- [ ] Visiting `/expenses/add` while logged in shows a form with fields: amount, category, date, description
- [ ] Submitting the form with valid data inserts one row into `expenses` and redirects to `/profile`
- [ ] The new expense appears in the transactions list on the profile page immediately after redirect
- [ ] Submitting with a missing or zero amount re-renders the form with an error message
- [ ] Submitting with an invalid date re-renders the form with an error message
- [ ] All previously entered values are preserved when the form re-renders after an error
- [ ] `pytest` passes with no errors after implementation
