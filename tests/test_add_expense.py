"""Tests for adding expenses (Step 7)."""

from database.db import get_db
from database.queries import add_expense


def _get_seed_user_id():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",))
    row = cursor.fetchone()
    conn.close()
    return row["id"] if row else None


def _login_as_demo(client):
    resp = client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "demo123",
    }, follow_redirects=True)
    assert resp.status_code == 200
    return resp


class TestAddExpense:
    def test_valid_insert_returns_id(self):
        user_id = _get_seed_user_id()
        expense_id = add_expense(user_id, 25.00, "Food", "2026-06-18", "Test meal")
        assert expense_id is not None
        assert isinstance(expense_id, int)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
        row = cursor.fetchone()
        conn.close()
        assert row is not None
        assert row["amount"] == 25.00
        assert row["category"] == "Food"
        assert row["description"] == "Test meal"

    def test_missing_description_stores_none(self):
        user_id = _get_seed_user_id()
        expense_id = add_expense(user_id, 10.00, "Transport", "2026-06-18")
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT description FROM expenses WHERE id = ?", (expense_id,))
        row = cursor.fetchone()
        conn.close()
        assert row["description"] is None


class TestAddRouteAuth:
    def test_get_redirects_when_not_logged_in(self, client):
        resp = client.get("/expenses/add")
        assert resp.status_code == 302
        assert resp.location.endswith("/login")

    def test_post_redirects_when_not_logged_in(self, client):
        resp = client.post("/expenses/add", data={"amount": "10"})
        assert resp.status_code == 302
        assert resp.location.endswith("/login")


class TestAddRouteGet:
    def test_form_renders_when_logged_in(self, client):
        _login_as_demo(client)
        resp = client.get("/expenses/add")
        html = resp.data.decode("utf-8")
        assert resp.status_code == 200
        assert "Add Expense" in html
        assert 'name="amount"' in html
        assert 'name="category"' in html
        assert 'name="date"' in html
        assert 'name="description"' in html

    def test_form_has_all_categories(self, client):
        _login_as_demo(client)
        resp = client.get("/expenses/add")
        html = resp.data.decode("utf-8")
        expected_categories = [
            "Food", "Transport", "Bills", "Health",
            "Entertainment", "Shopping", "Other",
        ]
        for cat in expected_categories:
            assert cat in html


class TestAddRoutePost:
    def test_valid_insert_redirects_to_profile(self, client):
        _login_as_demo(client)
        resp = client.post("/expenses/add", data={
            "amount": "99.99",
            "category": "Shopping",
            "date": "2026-06-15",
            "description": "Test item",
        })
        assert resp.status_code == 302
        assert resp.location.endswith("/profile")
        user_id = _get_seed_user_id()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM expenses WHERE user_id = ? AND amount = ? AND description = ?",
            (user_id, 99.99, "Test item"),
        )
        row = cursor.fetchone()
        conn.close()
        assert row is not None

    def test_missing_amount_rerenders_with_error(self, client):
        _login_as_demo(client)
        resp = client.post("/expenses/add", data={
            "amount": "",
            "category": "Food",
            "date": "2026-06-18",
            "description": "",
        })
        html = resp.data.decode("utf-8")
        assert resp.status_code == 200
        assert "error" in html.lower() or "Error" in html

    def test_zero_amount_rerenders_with_error(self, client):
        _login_as_demo(client)
        resp = client.post("/expenses/add", data={
            "amount": "0",
            "category": "Food",
            "date": "2026-06-18",
            "description": "",
        })
        html = resp.data.decode("utf-8")
        assert resp.status_code == 200
        assert "error" in html.lower() or "Error" in html

    def test_non_numeric_amount_rerenders_with_error(self, client):
        _login_as_demo(client)
        resp = client.post("/expenses/add", data={
            "amount": "abc",
            "category": "Food",
            "date": "2026-06-18",
            "description": "",
        })
        html = resp.data.decode("utf-8")
        assert resp.status_code == 200
        assert "error" in html.lower() or "Error" in html

    def test_invalid_category_rerenders_with_error(self, client):
        _login_as_demo(client)
        resp = client.post("/expenses/add", data={
            "amount": "10",
            "category": "InvalidCat",
            "date": "2026-06-18",
            "description": "",
        })
        html = resp.data.decode("utf-8")
        assert resp.status_code == 200
        assert "error" in html.lower() or "Error" in html

    def test_invalid_date_rerenders_with_error(self, client):
        _login_as_demo(client)
        resp = client.post("/expenses/add", data={
            "amount": "10",
            "category": "Food",
            "date": "not-a-date",
            "description": "",
        })
        html = resp.data.decode("utf-8")
        assert resp.status_code == 200
        assert "error" in html.lower() or "Error" in html

    def test_no_description_saves_with_null(self, client):
        _login_as_demo(client)
        resp = client.post("/expenses/add", data={
            "amount": "15.00",
            "category": "Other",
            "date": "2026-06-18",
            "description": "",
        })
        assert resp.status_code == 302
        user_id = _get_seed_user_id()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT description FROM expenses WHERE user_id = ? AND amount = ? AND category = ? ORDER BY id DESC LIMIT 1",
            (user_id, 15.00, "Other"),
        )
        row = cursor.fetchone()
        conn.close()
        assert row["description"] is None

    def test_form_data_preserved_on_error(self, client):
        _login_as_demo(client)
        resp = client.post("/expenses/add", data={
            "amount": "",
            "category": "Bills",
            "date": "2026-07-01",
            "description": "Should be kept",
        })
        html = resp.data.decode("utf-8")
        assert resp.status_code == 200
        assert "Bills" in html
        assert 'value="2026-07-01"' in html
        assert "Should be kept" in html
        assert "error" in html.lower() or "Error" in html
