"""Tests for deleting expenses (Step 9)."""

from datetime import datetime

from database.db import get_db, create_user
from database.queries import delete_expense, get_expense_by_id


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


class TestDeleteExpense:
    def test_deletes_own_expense(self):
        user_id = _get_seed_user_id()
        expense_ids = _get_seed_expense_ids(user_id)
        eid = expense_ids[0]
        rows = delete_expense(eid, user_id)
        assert rows == 1
        deleted = get_expense_by_id(eid, user_id)
        assert deleted is None

    def test_wrong_user_no_delete(self):
        user_id = _get_seed_user_id()
        other_id = _create_other_user()
        expense_ids = _get_seed_expense_ids(user_id)
        eid = expense_ids[0]
        rows = delete_expense(eid, other_id)
        assert rows == 0
        still_exists = get_expense_by_id(eid, user_id)
        assert still_exists is not None

    def test_nonexistent_expense(self):
        user_id = _get_seed_user_id()
        rows = delete_expense(99999, user_id)
        assert rows == 0


class TestDeleteRouteAuth:
    def test_post_redirects_when_not_logged_in(self, client):
        resp = client.post("/expenses/1/delete")
        assert resp.status_code == 302
        assert resp.location.endswith("/login")


class TestDeleteRoutePost:
    def test_deletes_own_expense(self, client):
        _login_as_demo(client)
        user_id = _get_seed_user_id()
        expense_ids = _get_seed_expense_ids(user_id)
        eid = expense_ids[0]
        resp = client.post(f"/expenses/{eid}/delete")
        assert resp.status_code == 302
        assert resp.location.endswith("/profile")
        deleted = get_expense_by_id(eid, user_id)
        assert deleted is None

    def test_404_for_other_users_expense(self, client):
        _login_as_demo(client)
        other_id = _create_other_user()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO expenses (user_id, amount, category, date) VALUES (?, ?, ?, ?)",
                       (other_id, 25.0, "Food", "2026-06-01"))
        other_exp_id = cursor.lastrowid
        conn.commit()
        conn.close()
        resp = client.post(f"/expenses/{other_exp_id}/delete")
        assert resp.status_code == 404
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM expenses WHERE id = ?", (other_exp_id,))
        assert cursor.fetchone() is not None
        conn.close()

    def test_404_for_non_existent(self, client):
        _login_as_demo(client)
        resp = client.post("/expenses/99999/delete")
        assert resp.status_code == 404


class TestDeleteRouteMethod:
    def test_get_returns_405(self, client):
        _login_as_demo(client)
        user_id = _get_seed_user_id()
        expense_ids = _get_seed_expense_ids(user_id)
        eid = expense_ids[0]
        resp = client.get(f"/expenses/{eid}/delete")
        assert resp.status_code == 405


class TestProfileDeleteButton:
    def test_delete_button_present_in_transactions(self, client):
        _login_as_demo(client)
        resp = client.get("/profile")
        html = resp.data.decode("utf-8")
        assert "/delete" in html
        assert "Delete this expense?" in html
