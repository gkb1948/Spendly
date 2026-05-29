# Expense Tracker — Agent Guide

This is a **Flask-based expense tracker** built as an educational learning project where features are implemented in numbered steps.

## Quick Start

**Run the app:**
```bash
python app.py
```
App runs on `http://localhost:5001` with debug mode enabled.

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Run tests:**
```bash
pytest
```

## Project Structure

- `app.py` — Main Flask application with route definitions
- `database/db.py` — Database setup (students implement `get_db()`, `init_db()`, `seed_db()`)
- `templates/` — HTML templates (base.html, landing.html, login.html, register.html, privacy.html, terms.html)
- `static/css/style.css` — Stylesheet
- `expense_tracker.db` — SQLite database (auto-created, in .gitignore)

## Key Conventions

### Routes Structure
Routes are organized in sections within `app.py`:
- **Core routes** (landing, register, login, terms, privacy) — fully implemented
- **Placeholder routes** (logout, profile, add_expense, edit_expense, delete_expense) — students implement these in steps

When implementing features, maintain this organization with section comments (`# ----`).

### Database
- Uses **SQLite** with connection stored as `expense_tracker.db`
- `database/db.py` provides the interface (students implement this in Step 1)
- Expected functions:
  - `get_db()` — Returns SQLite connection with row_factory and foreign keys enabled
  - `init_db()` — Creates all tables using `CREATE TABLE IF NOT EXISTS`
  - `seed_db()` — Inserts sample data for development

### Templates
- All templates inherit from `base.html`
- Use template variables for dynamic content
- Pages follow a consistent HTML structure

## Step-by-Step Implementation Plan

| Step | Feature | Route | Status |
|------|---------|-------|--------|
| 1 | Database setup | N/A | Template in `database/db.py` |
| 3 | User logout | `/logout` | Placeholder |
| 4 | User profile | `/profile` | Placeholder |
| 7 | Add expense | `/expenses/add` | Placeholder |
| 8 | Edit expense | `/expenses/<id>/edit` | Placeholder |
| 9 | Delete expense | `/expenses/<id>/delete` | Placeholder |

## Testing Approach

The project includes `pytest` and `pytest-flask`. When implementing features:
- Create test files for new functionality
- Test database operations, routes, and form handling
- Run `pytest` to verify all tests pass

## Implementation Guidelines

1. **Keep routes simple** — Delegate business logic to helper functions if needed
2. **Use templates consistently** — All HTML should inherit from `base.html`
3. **Database queries** — Should go through the `database/db.py` interface
4. **Environment setup** — Students should run `python app.py` and visit `http://localhost:5001`
5. **Placeholders are numbered** — The number indicates the implementation step order

When helping students, focus on guiding them to implement one step at a time, starting with Step 1 (database setup) before tackling other features.
