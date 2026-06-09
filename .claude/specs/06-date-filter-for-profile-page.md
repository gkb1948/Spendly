Spec: Date Filter for Profile Page
Overview

This feature adds date range filtering to the profile page. Users can select a start date and/or end date to narrow down which transactions appear, and all three data sections — summary stats, transaction history, and category breakdown — update to reflect only the filtered date range. When no dates are provided, all transactions are shown (preserving current behavior). The filter is implemented via GET query parameters so the filtered state is URL-shareable and bookmarkable.
Depends on

    Step 1: Database setup (expenses table with date column)
    Step 2: Registration (user accounts must exist)
    Step 3: Login + Logout (session must be set; /profile is a protected route)
    Step 4: Profile page static UI (template renders all four sections)
    Step 5: Backend Connection (queries.py functions exist and return real data)

Routes

    GET /profile — render profile page with optional date filtering — logged-in only
        Query parameters:
            start_date — YYYY-MM-DD format, inclusive lower bound (optional)
            end_date — YYYY-MM-DD format, inclusive upper bound (optional)
        When absent, all transactions are returned (current behavior unchanged)

Database changes

No database changes. The expenses table already has a date column (TEXT, YYYY-MM-DD).
Templates

    Modify: templates/profile.html
        Add a date filter form above the transaction history table
        The form uses GET method targeting /profile
        Two date input fields: start_date and end_date
        A "Filter" submit button and a "Clear" link/button that resets to /profile
        Pre-fill the date inputs with the current query parameter values when present
        The form and table should sit inside a shared container for visual grouping

Files to change

    app.py — update profile() to read start_date and end_date from request.args and pass them to the query functions
    database/queries.py — add optional start_date and end_date parameters to get_summary_stats(), get_recent_transactions(), and get_category_breakdown()
    templates/profile.html — add the date filter form with date inputs

Files to create

No new files.
New dependencies

No new dependencies.
Rules for implementation

    No SQLAlchemy or ORMs — raw sqlite3 only via get_db()
    Parameterised queries only — never string-format values into SQL
    Use CSS variables — never hardcode hex values
    All templates extend base.html
    Use url_for() for every internal link — never hardcode URLs
    The filter form must use GET method with query parameters (not POST)
    Date inputs must use type="date" for native browser date picker
    Validate dates server-side — if an invalid date is provided, ignore the parameter (do not error)
    Build WHERE clauses dynamically by appending conditions only when a date parameter is present; always use parameterised queries
    The date comparison in SQL must work with YYYY-MM-DD text format (SQLite date comparison is lexicographic but correct for ISO 8601)
    Show the currently active date range as readable text (e.g. "Showing transactions from 2026-05-01 to 2026-05-15") when a filter is active
    Currency must always display as ₹

Definition of done

    Visiting /profile with no filter params shows all transactions (8 for seed user)
    Visiting /profile?start_date=2026-05-10 shows only transactions on or after May 10 (3 of 8 seed transactions)
    Visiting /profile?end_date=2026-05-10 shows only transactions on or before May 10 (5 of 8 seed transactions)
    Visiting /profile?start_date=2026-05-05&end_date=2026-05-15 shows transactions in that range (5 of 8 seed transactions)
    Summary stats (total_spent, transaction_count, top_category) reflect only the filtered transactions
    Category breakdown reflects only the filtered transactions
    The date inputs are pre-filled with the current filter values from the URL
    A "Clear" link resets all filters and returns to /profile
    An invalid date parameter is silently ignored (falls back to unfiltered)
    A date range with no matching results shows zero stats and an empty transaction table
