from datetime import datetime

from database.db import get_db


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


def get_summary_stats(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = ?",
        (user_id,),
    )
    count, total = cursor.fetchone()
    cursor.execute(
        """
        SELECT category, SUM(amount) as cat_total
        FROM expenses WHERE user_id = ?
        GROUP BY category ORDER BY cat_total DESC LIMIT 1
    """,
        (user_id,),
    )
    top_row = cursor.fetchone()
    conn.close()
    return {
        "total_spent": f"₹{total:.2f}",
        "transaction_count": count,
        "top_category": top_row["category"] if top_row else "\u2014",
    }


def get_recent_transactions(user_id, limit=10):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT date, description, category, amount
        FROM expenses WHERE user_id = ?
        ORDER BY date DESC, created_at DESC LIMIT ?
    """,
        (user_id, limit),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r, amount=f"₹{r['amount']:.2f}") for r in rows]


def get_category_breakdown(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT category, COUNT(*) as cnt, SUM(amount) as total
        FROM expenses WHERE user_id = ?
        GROUP BY category ORDER BY total DESC
    """,
        (user_id,),
    )
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
