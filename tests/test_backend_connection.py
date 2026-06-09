from datetime import datetime

from database.db import create_user
from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
)


# --- Helpers ---

def _get_seed_user_id():
    from database.db import get_db
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",))
    row = cursor.fetchone()
    conn.close()
    return row["id"] if row else None


def _create_no_expense_user():
    ts = datetime.now().timestamp()
    return create_user("Test User", f"test_{ts}@test.com", "password123")


# --- Unit tests: get_user_by_id ---

class TestGetUserById:
    def test_valid_user(self):
        user_id = _get_seed_user_id()
        user = get_user_by_id(user_id)
        assert user is not None
        assert user["name"] == "Demo User"
        assert user["email"] == "demo@spendly.com"
        parts = user["joined"].split()
        assert len(parts) == 2
        assert parts[0].isalpha()
        assert parts[1].isdigit() and len(parts[1]) == 4
        assert user["initials"] == "DU"

    def test_nonexistent_user(self):
        user = get_user_by_id(99999)
        assert user is None


# --- Unit tests: get_summary_stats ---

class TestGetSummaryStats:
    def test_with_expenses(self):
        user_id = _get_seed_user_id()
        stats = get_summary_stats(user_id)
        assert stats["transaction_count"] == 8
        assert stats["top_category"] == "Bills"
        assert "₹" in stats["total_spent"]

    def test_no_expenses(self):
        user_id = _create_no_expense_user()
        stats = get_summary_stats(user_id)
        assert stats["total_spent"] == "₹0.00"
        assert stats["transaction_count"] == 0
        assert stats["top_category"] == "\u2014"


# --- Unit tests: get_recent_transactions ---

class TestGetRecentTransactions:
    def test_with_expenses(self):
        user_id = _get_seed_user_id()
        txs = get_recent_transactions(user_id)
        assert len(txs) == 8
        assert txs[0]["date"] == "2026-05-20"
        assert txs[-1]["date"] == "2026-05-01"
        for tx in txs:
            assert "date" in tx
            assert "description" in tx
            assert "category" in tx
            assert "amount" in tx
            assert "₹" in tx["amount"]

    def test_no_expenses(self):
        user_id = _create_no_expense_user()
        txs = get_recent_transactions(user_id)
        assert txs == []


# --- Unit tests: get_category_breakdown ---

class TestGetCategoryBreakdown:
    def test_with_expenses(self):
        user_id = _get_seed_user_id()
        cats = get_category_breakdown(user_id)
        assert len(cats) == 7
        assert cats[0]["name"] == "Bills"
        assert cats[0]["count"] == 1
        assert "₹" in cats[0]["total"]
        total_pct = sum(c["percentage"] for c in cats)
        assert total_pct == 100

    def test_no_expenses(self):
        user_id = _create_no_expense_user()
        cats = get_category_breakdown(user_id)
        assert cats == []


# --- Route tests ---

class TestProfileRoute:
    def test_unauthenticated_redirect(self, client):
        resp = client.get("/profile")
        assert resp.status_code == 302
        assert resp.location.endswith("/login")

    def test_authenticated_profile(self, client):
        resp = client.post("/login", data={
            "email": "demo@spendly.com",
            "password": "demo123",
        }, follow_redirects=True)
        assert resp.status_code == 200

        resp = client.get("/profile", follow_redirects=True)
        assert resp.status_code == 200
        html = resp.data.decode("utf-8")

        assert "Demo User" in html
        assert "demo@spendly.com" in html
        assert "₹" in html
        assert "394.23" in html
        assert "Bills" in html
        assert "Groceries" in html
        assert "Electricity" in html
        assert "Shopping" in html
        assert "Food" in html
        assert "Health" in html
        assert "type=\"date\"" in html or "type=date" in html


# --- Unit tests: date filtering ---

class TestDateFilter:
    def test_filter_start_date(self):
        user_id = _get_seed_user_id()
        txs = get_recent_transactions(user_id, start_date="2026-05-10")
        assert len(txs) == 3
        for tx in txs:
            assert tx["date"] >= "2026-05-10"

    def test_filter_end_date(self):
        user_id = _get_seed_user_id()
        txs = get_recent_transactions(user_id, end_date="2026-05-10")
        assert len(txs) == 5
        for tx in txs:
            assert tx["date"] <= "2026-05-10"

    def test_filter_range(self):
        user_id = _get_seed_user_id()
        txs = get_recent_transactions(user_id, start_date="2026-05-05", end_date="2026-05-15")
        assert len(txs) == 5
        for tx in txs:
            assert "2026-05-05" <= tx["date"] <= "2026-05-15"

    def test_filter_stats_update(self):
        user_id = _get_seed_user_id()
        stats = get_summary_stats(user_id, start_date="2026-05-10")
        assert stats["transaction_count"] == 3

    def test_filter_no_results(self):
        user_id = _get_seed_user_id()
        txs = get_recent_transactions(user_id, start_date="2099-01-01")
        assert txs == []
        stats = get_summary_stats(user_id, start_date="2099-01-01")
        assert stats["transaction_count"] == 0
        assert stats["total_spent"] == "₹0.00"
        cats = get_category_breakdown(user_id, start_date="2099-01-01")
        assert cats == []

    def test_filter_category_breakdown(self):
        user_id = _get_seed_user_id()
        cats = get_category_breakdown(user_id, start_date="2026-05-10")
        assert len(cats) < 7
        total_pct = sum(c["percentage"] for c in cats)
        assert total_pct == 100

    def test_filter_route_with_params(self, client):
        resp = client.post("/login", data={
            "email": "demo@spendly.com",
            "password": "demo123",
        }, follow_redirects=True)
        assert resp.status_code == 200

        resp = client.get("/profile?start_date=2026-05-10", follow_redirects=True)
        assert resp.status_code == 200
        html = resp.data.decode("utf-8")
        assert "2026-05-10" in html
    