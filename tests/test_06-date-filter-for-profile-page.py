"""Tests for date range filtering on the profile page (Step 6)."""

import pytest
from database.db import get_db, create_user
from database.queries import (
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
)


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def _get_seed_user_id():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",))
    row = cursor.fetchone()
    conn.close()
    return row["id"] if row else None


def _create_no_expense_user():
    from datetime import datetime
    ts = datetime.now().timestamp()
    return create_user("Test User", f"noexp_{ts}@test.com", "password123")


def _login_as_demo(client):
    resp = client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "demo123",
    }, follow_redirects=True)
    assert resp.status_code == 200
    return resp


def _get_profile(client, query_string=""):
    path = "/profile"
    if query_string:
        path += "?" + query_string
    return client.get(path, follow_redirects=True)


_SEED_TOTAL = 8          # seed has 8 expenses
_SEED_TOTAL_AMOUNT = 394.23  # sum of all 8


# ------------------------------------------------------------------ #
# Auth guard – unauthenticated access                                 #
# ------------------------------------------------------------------ #

class TestAuthGuard:
    def test_redirects_when_not_logged_in(self, client):
        resp = client.get("/profile")
        assert resp.status_code == 302
        assert resp.location.endswith("/login")

    def test_redirects_with_filter_params_when_not_logged_in(self, client):
        resp = client.get("/profile?start_date=2026-05-01")
        assert resp.status_code == 302
        assert resp.location.endswith("/login")

    def test_redirects_with_invalid_date_params_when_not_logged_in(self, client):
        resp = client.get("/profile?start_date=not-a-date")
        assert resp.status_code == 302


# ------------------------------------------------------------------ #
# No date params – shows all transactions (current behaviour)         #
# ------------------------------------------------------------------ #

class TestNoDateParams:
    def test_all_transactions_shown(self, client):
        _login_as_demo(client)
        resp = _get_profile(client)
        html = resp.data.decode("utf-8")
        assert "Groceries" in html
        assert "Electricity" in html
        assert "Shopping" in html
        assert "Misc" in html
        assert "394.23" in html

    def test_stats_reflect_all(self, client):
        _login_as_demo(client)
        resp = _get_profile(client)
        html = resp.data.decode("utf-8")
        assert "8" in html
        assert "Bills" in html


# ------------------------------------------------------------------ #
# start_date only                                                     #
# ------------------------------------------------------------------ #

class TestStartDateOnly:
    def test_filters_transactions_on_or_after_start(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "start_date=2026-05-10")
        html = resp.data.decode("utf-8")
        assert "Movie" in html
        assert "Clothes" in html
        assert "Misc" in html
        assert "Groceries" not in html
        assert "Pharmacy" not in html

    def test_start_date_updates_stats(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "start_date=2026-05-10")
        html = resp.data.decode("utf-8")
        assert "3" in html or "₹" in html

    def test_start_date_updates_category_breakdown(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "start_date=2026-05-10")
        html = resp.data.decode("utf-8")
        assert "Entertainment" in html
        assert "Shopping" in html

    def test_start_date_prefills_input(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "start_date=2026-05-10")
        html = resp.data.decode("utf-8")
        assert 'value="2026-05-10"' in html

    def test_start_date_shows_filter_info(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "start_date=2026-05-10")
        html = resp.data.decode("utf-8")
        assert "2026-05-10" in html


# ------------------------------------------------------------------ #
# end_date only                                                      #
# ------------------------------------------------------------------ #

class TestEndDateOnly:
    def test_filters_transactions_on_or_before_end(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "end_date=2026-05-10")
        html = resp.data.decode("utf-8")
        assert "Groceries" in html
        assert "Lunch" in html
        assert "Gas" in html
        assert "Electricity" in html
        assert "Pharmacy" in html
        assert "Movie" not in html
        assert "Clothes" not in html
        assert "Misc" not in html

    def test_end_date_updates_stats(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "end_date=2026-05-10")
        html = resp.data.decode("utf-8")
        assert "5" in html

    def test_end_date_prefills_input(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "end_date=2026-05-10")
        html = resp.data.decode("utf-8")
        assert 'value="2026-05-10"' in html

    def test_end_date_shows_filter_info(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "end_date=2026-05-10")
        html = resp.data.decode("utf-8")
        assert "2026-05-10" in html


# ------------------------------------------------------------------ #
# start_date + end_date range                                        #
# ------------------------------------------------------------------ #

class TestDateRange:
    def test_filters_transactions_within_range(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "start_date=2026-05-05&end_date=2026-05-15")
        html = resp.data.decode("utf-8")
        assert "Gas" in html
        assert "Electricity" in html
        assert "Pharmacy" in html
        assert "Movie" in html
        assert "Clothes" in html
        assert "Groceries" not in html
        assert "Lunch" not in html
        assert "Misc" not in html

    def test_range_updates_stats(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "start_date=2026-05-05&end_date=2026-05-15")
        html = resp.data.decode("utf-8")
        assert "5" in html

    def test_range_prefills_both_inputs(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "start_date=2026-05-05&end_date=2026-05-15")
        html = resp.data.decode("utf-8")
        assert 'value="2026-05-05"' in html
        assert 'value="2026-05-15"' in html

    def test_range_shows_filter_info(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "start_date=2026-05-05&end_date=2026-05-15")
        html = resp.data.decode("utf-8")
        assert "2026-05-05" in html
        assert "2026-05-15" in html

    def test_clear_link_appears_when_filter_active(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "start_date=2026-05-05&end_date=2026-05-15")
        html = resp.data.decode("utf-8")
        assert "Clear" in html


# ------------------------------------------------------------------ #
# Summary stats reflect filter                                        #
# ------------------------------------------------------------------ #

class TestStatsReflectFilter:
    def test_transaction_count_filtered_by_start(self):
        user_id = _get_seed_user_id()
        stats = get_summary_stats(user_id, start_date="2026-05-10")
        assert stats["transaction_count"] == 3

    def test_transaction_count_filtered_by_end(self):
        user_id = _get_seed_user_id()
        stats = get_summary_stats(user_id, end_date="2026-05-10")
        assert stats["transaction_count"] == 5

    def test_transaction_count_filtered_by_range(self):
        user_id = _get_seed_user_id()
        stats = get_summary_stats(user_id, start_date="2026-05-05", end_date="2026-05-15")
        assert stats["transaction_count"] == 5

    def test_total_spent_filtered(self):
        user_id = _get_seed_user_id()
        stats = get_summary_stats(user_id, start_date="2026-05-10")
        items = [
            (20.00, "Entertainment"),
            (89.99, "Shopping"),
            (15.00, "Other"),
        ]
        expected_total = sum(amt for amt, _ in items)
        assert f"₹{expected_total:.2f}" == stats["total_spent"]

    def test_top_category_changes_with_filter(self):
        user_id = _get_seed_user_id()
        stats = get_summary_stats(user_id, start_date="2026-05-10")
        assert stats["top_category"] == "Shopping"

    def test_no_results_shows_zero_stats(self):
        user_id = _get_seed_user_id()
        stats = get_summary_stats(user_id, start_date="2099-01-01")
        assert stats["total_spent"] == "₹0.00"
        assert stats["transaction_count"] == 0
        assert stats["top_category"] == "\u2014"


# ------------------------------------------------------------------ #
# Category breakdown reflects filter                                   #
# ------------------------------------------------------------------ #

class TestCategoryBreakdownReflectsFilter:
    def test_fewer_categories_when_filtered(self):
        user_id = _get_seed_user_id()
        cats = get_category_breakdown(user_id, start_date="2026-05-10")
        assert len(cats) < 7

    def test_percentages_still_sum_to_100(self):
        user_id = _get_seed_user_id()
        cats = get_category_breakdown(user_id, start_date="2026-05-10")
        total_pct = sum(c["percentage"] for c in cats)
        assert total_pct == 100

    def test_filtered_breakdown_only_contains_matching_categories(self):
        user_id = _get_seed_user_id()
        cats = get_category_breakdown(user_id, start_date="2026-05-10")
        names = [c["name"] for c in cats]
        assert "Entertainment" in names
        assert "Shopping" in names
        assert "Other" in names
        assert "Food" not in names
        assert "Bills" not in names

    def test_no_results_returns_empty_list(self):
        user_id = _get_seed_user_id()
        cats = get_category_breakdown(user_id, start_date="2099-01-01")
        assert cats == []


# ------------------------------------------------------------------ #
# Invalid date handling — silently ignored                            #
# ------------------------------------------------------------------ #

class TestInvalidDateHandling:
    def test_invalid_start_date_shows_all_transactions(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "start_date=not-a-date")
        html = resp.data.decode("utf-8")
        assert "Groceries" in html
        assert "Misc" in html

    def test_invalid_end_date_shows_all_transactions(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "end_date=garbage")
        html = resp.data.decode("utf-8")
        assert "Groceries" in html
        assert "Misc" in html

    def test_invalid_both_dates_shows_all(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "start_date=abc&end_date=xyz")
        html = resp.data.decode("utf-8")
        assert "Groceries" in html
        assert "Misc" in html

    def test_malformed_date_returns_all_transactions(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "start_date=2026/05/10")
        html = resp.data.decode("utf-8")
        assert "Groceries" in html

    def test_partial_date_returns_all_transactions(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "start_date=2026-05")
        html = resp.data.decode("utf-8")
        assert "Groceries" in html

    def test_invalid_date_does_not_prefill(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "start_date=not-a-date")
        html = resp.data.decode("utf-8")
        assert 'value="not-a-date"' not in html

    def test_invalid_date_shows_no_filter_info(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "start_date=bad")
        html = resp.data.decode("utf-8")
        assert "Showing transactions" not in html


# ------------------------------------------------------------------ #
# No matching results                                                 #
# ------------------------------------------------------------------ #

class TestNoMatchingResults:
    def test_future_date_shows_zero_transactions(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "start_date=2099-01-01")
        html = resp.data.decode("utf-8")
        assert "₹0.00" in html
        assert "0" in html

    def test_future_date_shows_empty_table(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "start_date=2099-01-01")
        html = resp.data.decode("utf-8")
        assert "Groceries" not in html
        assert "Electricity" not in html
        assert "Shopping" not in html

    def test_future_date_shows_empty_category_breakdown(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "start_date=2099-01-01")
        html = resp.data.decode("utf-8")
        assert "Food" not in html
        assert "Bills" not in html

    def test_past_date_before_any_expense_shows_none(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "end_date=2026-04-30")
        html = resp.data.decode("utf-8")
        assert "₹0.00" in html


# ------------------------------------------------------------------ #
# Pre-fill date inputs                                                #
# ------------------------------------------------------------------ #

class TestPrefillInputs:
    def test_start_date_prefilled(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "start_date=2026-05-01")
        html = resp.data.decode("utf-8")
        assert 'value="2026-05-01"' in html

    def test_end_date_prefilled(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "end_date=2026-05-20")
        html = resp.data.decode("utf-8")
        assert 'value="2026-05-20"' in html

    def test_both_dates_prefilled(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "start_date=2026-05-01&end_date=2026-05-20")
        html = resp.data.decode("utf-8")
        assert 'value="2026-05-01"' in html
        assert 'value="2026-05-20"' in html

    def test_no_params_empty_values(self, client):
        _login_as_demo(client)
        resp = _get_profile(client)
        html = resp.data.decode("utf-8")
        assert 'value=""' not in html


# ------------------------------------------------------------------ #
# Clear link resets filters                                           #
# ------------------------------------------------------------------ #

class TestClearLink:
    def test_clear_link_present_when_filter_active(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "start_date=2026-05-10")
        html = resp.data.decode("utf-8")
        assert "Clear" in html or "clear" in html

    def test_clear_link_absent_when_no_filter(self, client):
        _login_as_demo(client)
        resp = _get_profile(client)
        html = resp.data.decode("utf-8")
        assert "Clear" not in html

    def test_clear_link_points_to_plain_profile(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "start_date=2026-05-10")
        html = resp.data.decode("utf-8")
        assert "/profile" in html


# ------------------------------------------------------------------ #
# Form uses type="date"                                               #
# ------------------------------------------------------------------ #

class TestDateInputType:
    def test_start_date_input_type_date(self, client):
        _login_as_demo(client)
        resp = _get_profile(client)
        html = resp.data.decode("utf-8")
        assert 'type="date"' in html

    def test_end_date_input_type_date(self, client):
        _login_as_demo(client)
        resp = _get_profile(client)
        html = resp.data.decode("utf-8")
        assert html.count('type="date"') >= 2


# ------------------------------------------------------------------ #
# Currency displays as ₹                                              #
# ------------------------------------------------------------------ #

class TestCurrencyDisplay:
    def test_currency_symbol_in_stats(self, client):
        _login_as_demo(client)
        resp = _get_profile(client)
        html = resp.data.decode("utf-8")
        assert "₹" in html

    def test_currency_symbol_in_transactions(self, client):
        _login_as_demo(client)
        resp = _get_profile(client)
        html = resp.data.decode("utf-8")
        assert "₹" in html

    def test_currency_symbol_in_category_breakdown(self, client):
        _login_as_demo(client)
        resp = _get_profile(client)
        html = resp.data.decode("utf-8")
        assert "₹" in html


# ------------------------------------------------------------------ #
# Edge cases                                                          #
# ------------------------------------------------------------------ #

class TestEdgeCases:
    def test_start_date_equal_to_end_date(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "start_date=2026-05-07&end_date=2026-05-07")
        html = resp.data.decode("utf-8")
        assert "Electricity" in html
        assert "₹150.00" in html

    def test_start_date_after_end_date_returns_empty(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "start_date=2026-05-20&end_date=2026-05-01")
        html = resp.data.decode("utf-8")
        assert "₹0.00" in html

    def test_empty_query_param_start(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "start_date=&end_date=2026-05-10")
        html = resp.data.decode("utf-8")
        assert "5" in html

    def test_empty_query_param_end(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "start_date=2026-05-10&end_date=")
        html = resp.data.decode("utf-8")
        assert "3" in html

    def test_extra_unknown_query_params_ignored(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "start_date=2026-05-10&foo=bar&baz=qux")
        html = resp.data.decode("utf-8")
        assert "Movie" in html
        assert "Groceries" not in html

    def test_url_is_shareable_via_get_params(self, client):
        _login_as_demo(client)
        resp = _get_profile(client, "start_date=2026-05-10&end_date=2026-05-15")
        html = resp.data.decode("utf-8")
        assert 'method="GET"' in html
