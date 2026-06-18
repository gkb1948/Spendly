"""Tests for editing expenses (Step 8)."""

from datetime import datetime

from database.db import get_db, create_user
from database.queries import get_expense_by_id, update_expense


def _get_seed_user_id():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",))
    row = cursor.fetchone()
    conn.close()
    return row["id"] if row else None


def _get_seed_expense_ids(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM expenses WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [r["id"] for r in rows]


def _create_other_user():
    ts = datetime.now().timestamp()
    return create_user("Other User", f"other_{ts}@test.com", "password123")


def _login_as_demo(client):
    resp = client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "demo123",
    }, follow_redirects=True)
    assert resp.status_code == 200
    return resp


class TestGetExpenseById:
    def test_own_expense(self):
        user_id = _get_seed_user_id()
        expense_ids = _get_seed_expense_ids(user_id)
        expense = get_expense_by_id(expense_ids[0], user_id)
        assert expense is not None
        assert expense["id"] == expense_ids[0]
        assert expense["user_id"] == user_id
        assert "amount" in expense
        assert "category" in expense
        assert "date" in expense

    def test_wrong_user_returns_none(self):
        user_id = _get_seed_user_id()
        other_id = _create_other_user()
        expense_ids = _get_seed_expense_ids(user_id)
        expense = get_expense_by_id(expense_ids[0], other_id)
        assert expense is None

    def test_nonexistent_expense(self):
        expense = get_expense_by_id(99999, _get_seed_user_id())
        assert expense is None


class TestUpdateExpense:
    def test_updates_own_expense(self):
        user_id = _get_seed_user_id()
        expense_ids = _get_seed_expense_ids(user_id)
        eid = expense_ids[0]
        rows = update_expense(eid, user_id, 99.99, "Shopping", "2026-06-01", "Updated item")
        assert rows == 1
        updated = get_expense_by_id(eid, user_id)
        assert updated["amount"] == 99.99
        assert updated["category"] == "Shopping"
        assert updated["date"] == "2026-06-01"
        assert updated["description"] == "Updated item"

    def test_wrong_user_no_update(self):
        user_id = _get_seed_user_id()
        other_id = _create_other_user()
        expense_ids = _get_seed_expense_ids(user_id)
        eid = expense_ids[0]
        original = get_expense_by_id(eid, user_id)
        rows = update_expense(eid, other_id, 99.99, "Shopping", "2026-06-01", "Hacked")
        assert rows == 0
        unchanged = get_expense_by_id(eid, user_id)
        assert unchanged["amount"] == original["amount"]

    def test_optional_description_stores_none(self):
        user_id = _get_seed_user_id()
        expense_ids = _get_seed_expense_ids(user_id)
        eid = expense_ids[0]
        update_expense(eid, user_id, 10.0, "Food", "2026-06-01", None)
        updated = get_expense_by_id(eid, user_id)
        assert updated["description"] is None


class TestEditRouteAuth:
    def test_get_redirects_when_not_logged_in(self, client):
        resp = client.get("/expenses/1/edit")
        assert resp.status_code == 302
        assert resp.location.endswith("/login")

    def test_post_redirects_when_not_logged_in(self, client):
        resp = client.post("/expenses/1/edit", data={"amount": "10"})
        assert resp.status_code == 302
        assert resp.location.endswith("/login")


class TestEditRouteGet:
    def test_404_for_non_existent(self, client):
        _login_as_demo(client)
        resp = client.get("/expenses/99999/edit")
        assert resp.status_code == 404

    def test_404_for_other_users_expense(self, client):
        _login_as_demo(client)
        other_id = _create_other_user()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO expenses (user_id, amount, category, date) VALUES (?, ?, ?, ?)",
                       (other_id, 10.0, "Food", "2026-06-01"))
        other_exp_id = cursor.lastrowid
        conn.commit()
        conn.close()
        resp = client.get(f"/expenses/{other_exp_id}/edit")
        assert resp.status_code == 404

    def test_form_prefilled(self, client):
        _login_as_demo(client)
        user_id = _get_seed_user_id()
        expense_ids = _get_seed_expense_ids(user_id)
        eid = expense_ids[0]
        resp = client.get(f"/expenses/{eid}/edit")
        html = resp.data.decode("utf-8")
        assert resp.status_code == 200
        assert "Edit Expense" in html
        assert "Save Changes" in html


class TestEditRoutePost:
    def test_valid_update_redirects(self, client):
        _login_as_demo(client)
        user_id = _get_seed_user_id()
        expense_ids = _get_seed_expense_ids(user_id)
        eid = expense_ids[0]
        resp = client.post(f"/expenses/{eid}/edit", data={
            "amount": "77.50",
            "category": "Transport",
            "date": "2026-06-15",
            "description": "Edited expense",
        })
        assert resp.status_code == 302
        assert resp.location.endswith("/profile")
        updated = get_expense_by_id(eid, user_id)
        assert updated["amount"] == 77.50
        assert updated["category"] == "Transport"

    def test_post_404_for_other_users_expense(self, client):
        _login_as_demo(client)
        other_id = _create_other_user()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO expenses (user_id, amount, category, date) VALUES (?, ?, ?, ?)",
                       (other_id, 25.0, "Food", "2026-06-01"))
        other_exp_id = cursor.lastrowid
        conn.commit()
        conn.close()
        resp = client.post(f"/expenses/{other_exp_id}/edit", data={
            "amount": "50.00",
            "category": "Transport",
            "date": "2026-06-15",
            "description": "Should not update",
        })
        assert resp.status_code == 404

    def test_missing_amount_rerenders_with_error(self, client):
        _login_as_demo(client)
        user_id = _get_seed_user_id()
        expense_ids = _get_seed_expense_ids(user_id)
        eid = expense_ids[0]
        resp = client.post(f"/expenses/{eid}/edit", data={
            "amount": "",
            "category": "Food",
            "date": "2026-06-15",
            "description": "",
        })
        html = resp.data.decode("utf-8")
        assert resp.status_code == 200
        assert "error" in html.lower() or "Error" in html

    def test_zero_amount_rerenders_with_error(self, client):
        _login_as_demo(client)
        user_id = _get_seed_user_id()
        expense_ids = _get_seed_expense_ids(user_id)
        eid = expense_ids[0]
        resp = client.post(f"/expenses/{eid}/edit", data={
            "amount": "0",
            "category": "Food",
            "date": "2026-06-15",
            "description": "",
        })
        html = resp.data.decode("utf-8")
        assert resp.status_code == 200
        assert "error" in html.lower() or "Error" in html

    def test_non_numeric_amount_rerenders_with_error(self, client):
        _login_as_demo(client)
        user_id = _get_seed_user_id()
        expense_ids = _get_seed_expense_ids(user_id)
        eid = expense_ids[0]
        resp = client.post(f"/expenses/{eid}/edit", data={
            "amount": "abc",
            "category": "Food",
            "date": "2026-06-15",
            "description": "",
        })
        html = resp.data.decode("utf-8")
        assert resp.status_code == 200
        assert "error" in html.lower() or "Error" in html

    def test_invalid_category_rerenders_with_error(self, client):
        _login_as_demo(client)
        user_id = _get_seed_user_id()
        expense_ids = _get_seed_expense_ids(user_id)
        eid = expense_ids[0]
        resp = client.post(f"/expenses/{eid}/edit", data={
            "amount": "10",
            "category": "InvalidCat",
            "date": "2026-06-15",
            "description": "",
        })
        html = resp.data.decode("utf-8")
        assert resp.status_code == 200
        assert "error" in html.lower() or "Error" in html

    def test_invalid_date_rerenders_with_error(self, client):
        _login_as_demo(client)
        user_id = _get_seed_user_id()
        expense_ids = _get_seed_expense_ids(user_id)
        eid = expense_ids[0]
        resp = client.post(f"/expenses/{eid}/edit", data={
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
        user_id = _get_seed_user_id()
        expense_ids = _get_seed_expense_ids(user_id)
        eid = expense_ids[0]
        resp = client.post(f"/expenses/{eid}/edit", data={
            "amount": "15.00",
            "category": "Other",
            "date": "2026-06-01",
            "description": "",
        })
        assert resp.status_code == 302
        updated = get_expense_by_id(eid, user_id)
        assert updated["description"] is None

    def test_form_data_preserved_on_error(self, client):
        _login_as_demo(client)
        user_id = _get_seed_user_id()
        expense_ids = _get_seed_expense_ids(user_id)
        eid = expense_ids[0]
        resp = client.post(f"/expenses/{eid}/edit", data={
            "amount": "",
            "category": "Bills",
            "date": "2026-07-01",
            "description": "Should be kept",
        })
        html = resp.data.decode("utf-8")
        assert resp.status_code == 200
        assert 'value="Bills"' in html or "Bills" in html
        assert 'value="2026-07-01"' in html
        assert "Should be kept" in html
        assert "error" in html.lower() or "Error" in html


class TestProfileEditLink:
    def test_edit_link_present_in_transactions(self, client):
        _login_as_demo(client)
        resp = client.get("/profile")
        html = resp.data.decode("utf-8")
        assert "/expenses/" in html
        assert "/edit" in html
