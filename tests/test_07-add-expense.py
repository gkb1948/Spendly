"""Tests for adding expenses (Step 7)."""

from database.db import get_db


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def _login_as_demo(client):
    resp = client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "demo123",
    }, follow_redirects=True)
    assert resp.status_code == 200
    return resp


def _get_last_expense():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


_PROFILE_REDIRECT = "/profile"


# ------------------------------------------------------------------ #
# Auth guard                                                          #
# ------------------------------------------------------------------ #

class TestAuthGuard:
    def test_redirects_to_login_on_get(self, client):
        resp = client.get("/expenses/add")
        assert resp.status_code == 302
        assert resp.location.endswith("/login")

    def test_redirects_to_login_on_post(self, client):
        resp = client.post("/expenses/add", data={"amount": "10", "category": "Food", "date": "2026-06-01"})
        assert resp.status_code == 302
        assert resp.location.endswith("/login")


# ------------------------------------------------------------------ #
# GET form                                                            #
# ------------------------------------------------------------------ #

class TestGetForm:
    def test_form_renders(self, client):
        _login_as_demo(client)
        resp = client.get("/expenses/add")
        html = resp.data.decode("utf-8")
        assert resp.status_code == 200
        assert 'name="amount"' in html
        assert 'name="category"' in html
        assert 'name="date"' in html
        assert 'name="description"' in html

    def test_form_has_select_for_category(self, client):
        _login_as_demo(client)
        resp = client.get("/expenses/add")
        html = resp.data.decode("utf-8")
        assert '<select' in html and 'name="category"' in html
        for cat in ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]:
            assert f'value="{cat}"' in html

    def test_form_has_submit_button(self, client):
        _login_as_demo(client)
        resp = client.get("/expenses/add")
        html = resp.data.decode("utf-8")
        assert "Add Expense" in html

    def test_form_has_back_link(self, client):
        _login_as_demo(client)
        resp = client.get("/expenses/add")
        html = resp.data.decode("utf-8")
        assert "/profile" in html


# ------------------------------------------------------------------ #
# Successful submission                                               #
# ------------------------------------------------------------------ #

class TestSuccessfulSubmission:
    def test_adds_expense_to_database(self, client):
        _login_as_demo(client)
        before = _get_last_expense()
        client.post("/expenses/add", data={
            "amount": "99.99", "category": "Shopping", "date": "2026-06-15", "description": "Test item"
        })
        after = _get_last_expense()
        assert after is not None
        if before:
            assert after["id"] > before["id"]
        assert after["amount"] == 99.99
        assert after["category"] == "Shopping"
        assert after["description"] == "Test item"

    def test_redirects_to_profile_after_success(self, client):
        _login_as_demo(client)
        resp = client.post("/expenses/add", data={
            "amount": "50.00", "category": "Food", "date": "2026-06-10"
        })
        assert resp.status_code == 302
        assert _PROFILE_REDIRECT in resp.location

    def test_optional_description_can_be_empty(self, client):
        _login_as_demo(client)
        resp = client.post("/expenses/add", data={
            "amount": "25.00", "category": "Transport", "date": "2026-06-12", "description": ""
        })
        assert resp.status_code == 302
        expense = _get_last_expense()
        assert expense["description"] is None

    def test_optional_description_can_be_omitted(self, client):
        _login_as_demo(client)
        resp = client.post("/expenses/add", data={
            "amount": "30.00", "category": "Bills", "date": "2026-06-14"
        })
        assert resp.status_code == 302
        expense = _get_last_expense()
        assert expense["description"] is None


# ------------------------------------------------------------------ #
# Validation errors                                                   #
# ------------------------------------------------------------------ #

class TestValidationErrors:
    def test_missing_amount_shows_error(self, client):
        _login_as_demo(client)
        resp = client.post("/expenses/add", data={"category": "Food", "date": "2026-06-01"})
        html = resp.data.decode("utf-8")
        assert resp.status_code == 200
        assert "Amount" in html

    def test_non_numeric_amount_shows_error(self, client):
        _login_as_demo(client)
        resp = client.post("/expenses/add", data={
            "amount": "abc", "category": "Food", "date": "2026-06-01"
        })
        html = resp.data.decode("utf-8")
        assert resp.status_code == 200
        assert "Amount must be a positive number" in html or "Amount" in html

    def test_negative_amount_shows_error(self, client):
        _login_as_demo(client)
        resp = client.post("/expenses/add", data={
            "amount": "-10", "category": "Food", "date": "2026-06-01"
        })
        html = resp.data.decode("utf-8")
        assert resp.status_code == 200
        assert "positive" in html.lower()

    def test_zero_amount_shows_error(self, client):
        _login_as_demo(client)
        resp = client.post("/expenses/add", data={
            "amount": "0", "category": "Food", "date": "2026-06-01"
        })
        html = resp.data.decode("utf-8")
        assert resp.status_code == 200
        assert "positive" in html.lower()

    def test_missing_category_shows_error(self, client):
        _login_as_demo(client)
        resp = client.post("/expenses/add", data={"amount": "10", "date": "2026-06-01"})
        html = resp.data.decode("utf-8")
        assert resp.status_code == 200
        assert "Category" in html

    def test_missing_date_shows_error(self, client):
        _login_as_demo(client)
        resp = client.post("/expenses/add", data={"amount": "10", "category": "Food"})
        html = resp.data.decode("utf-8")
        assert resp.status_code == 200
        assert "Date" in html

    def test_invalid_date_shows_error(self, client):
        _login_as_demo(client)
        resp = client.post("/expenses/add", data={
            "amount": "10", "category": "Food", "date": "not-a-date"
        })
        html = resp.data.decode("utf-8")
        assert resp.status_code == 200
        assert "date" in html.lower()

    def test_remembers_form_data_on_error(self, client):
        _login_as_demo(client)
        resp = client.post("/expenses/add", data={
            "amount": "42.50", "category": "Food", "date": "", "description": "Some note"
        })
        html = resp.data.decode("utf-8")
        assert resp.status_code == 200
        assert 'value="42.50"' in html
        assert "Some note" in html

    def test_stays_on_same_page_on_error(self, client):
        _login_as_demo(client)
        resp = client.post("/expenses/add", data={"amount": "", "category": "", "date": ""})
        assert resp.status_code == 200


# ------------------------------------------------------------------ #
# Invalid category                                                    #
# ------------------------------------------------------------------ #

class TestCategorySelectOptions:
    def test_invalid_category_rejected(self, client):
        _login_as_demo(client)
        resp = client.post("/expenses/add", data={
            "amount": "10", "category": "InvalidCat", "date": "2026-06-01"
        })
        html = resp.data.decode("utf-8")
        assert resp.status_code == 200
        assert "Invalid category" in html or "Category" in html
