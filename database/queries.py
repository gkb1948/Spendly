from datetime import datetime

from database.db import get_db


def _apply_date_filter(base_query, params, start_date, end_date):
    """Insert optional date range conditions into the WHERE clause.
    Mutates `params` in place by appending date values."""
    if not start_date and not end_date:
        return base_query
    conditions = []
    if start_date:
        conditions.append("date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("date <= ?")
        params.append(end_date)
    clause = " AND " + " AND ".join(conditions)
    # Insert before GROUP BY, ORDER BY, or LIMIT if present
    for keyword in ("GROUP BY", "ORDER BY", "LIMIT"):
        pos = base_query.upper().rfind(" " + keyword)
        if pos != -1:
            return base_query[:pos] + clause + " " + base_query[pos + 1:]
    return base_query + clause


def get_user_by_id(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if not user:
        return None
    user = dict(user)
    initials = "".join(part[0].upper() for part in user["name"].split() if part)
    dt = datetime.strptime(user["created_at"], "%Y-%m-%d %H:%M:%S")
    user["joined"] = dt.strftime("%B %Y")
    user["initials"] = initials
    return user


def get_expense_by_id(expense_id, user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, user_id)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_expense(expense_id, user_id, amount, category, date, description):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE expenses
           SET amount = ?, category = ?, date = ?, description = ?
           WHERE id = ? AND user_id = ?""",
        (amount, category, date, description, expense_id, user_id)
    )
    conn.commit()
    rows = cursor.rowcount
    conn.close()
    return rows


def add_expense(user_id, amount, category, date, description=None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO expenses (user_id, amount, category, date, description)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, amount, category, date, description),
    )
    conn.commit()
    expense_id = cursor.lastrowid
    conn.close()
    return expense_id


def get_summary_stats(user_id, start_date=None, end_date=None):
    conn = get_db()
    cursor = conn.cursor()
    params = [user_id]
    query = "SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = ?"
    query = _apply_date_filter(query, params, start_date, end_date)
    cursor.execute(query, params)
    count, total = cursor.fetchone()
    params = [user_id]
    query = """
        SELECT category, SUM(amount) as cat_total
        FROM expenses WHERE user_id = ?
        GROUP BY category ORDER BY cat_total DESC LIMIT 1
    """
    query = _apply_date_filter(query, params, start_date, end_date)
    cursor.execute(query, params)
    top_row = cursor.fetchone()
    conn.close()
    return {
        "total_spent": f"₹{total:.2f}",
        "transaction_count": count,
        "top_category": top_row["category"] if top_row else "\u2014",
    }


def get_recent_transactions(user_id, limit=10, start_date=None, end_date=None):
    conn = get_db()
    cursor = conn.cursor()
    params = [user_id]
    query = """
        SELECT id, date, description, category, amount
        FROM expenses WHERE user_id = ?
    """
    query = _apply_date_filter(query, params, start_date, end_date)
    query += " ORDER BY date DESC, created_at DESC LIMIT ?"
    params.append(limit)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r, amount=f"₹{r['amount']:.2f}") for r in rows]


def get_category_breakdown(user_id, start_date=None, end_date=None):
    conn = get_db()
    cursor = conn.cursor()
    params = [user_id]
    query = """
        SELECT category, COUNT(*) as cnt, SUM(amount) as total
        FROM expenses WHERE user_id = ?
        GROUP BY category ORDER BY total DESC
    """
    query = _apply_date_filter(query, params, start_date, end_date)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return []
    grand_total = sum(r["total"] for r in rows)
    breakdown = [
        {
            "name": r["category"],
            "count": r["cnt"],
            "total": f"₹{r['total']:.2f}",
            "percentage": round(r["total"] / grand_total * 100),
        }
        for r in rows
    ]
    total_pct = sum(b["percentage"] for b in breakdown)
    if total_pct != 100:
        breakdown[0]["percentage"] += 100 - total_pct
    return breakdown
