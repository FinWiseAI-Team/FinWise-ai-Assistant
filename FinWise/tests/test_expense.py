"""Expense-prediction tests. Run from the project folder (after python train_expense_prediction.py):

    python -m unittest discover -s tests -v
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app  # noqa: E402
from backend.prediction_expense import (  # noqa: E402
    forecast_next_month,
    predict_monthly_expenses,
    predict_transaction_cost,
)


class ExpensePredictionTests(unittest.TestCase):
    def test_monthly_prediction_is_sensible(self):
        r = predict_monthly_expenses({"monthly_income_usd": 4000})
        self.assertLess(r["range_low_usd"], r["predicted_expenses_usd"], r)
        self.assertLess(r["predicted_expenses_usd"], r["range_high_usd"], r)
        self.assertAlmostEqual(r["predicted_expenses_usd"] + r["predicted_savings_per_month_usd"], 4000, places=1)

    def test_higher_income_predicts_higher_expenses(self):
        low = predict_monthly_expenses({"monthly_income_usd": 2000})["predicted_expenses_usd"]
        high = predict_monthly_expenses({"monthly_income_usd": 8000})["predicted_expenses_usd"]
        self.assertGreater(high, low)

    def test_bad_profiles_are_rejected(self):
        for profile in [{}, {"monthly_income_usd": -5}, {"monthly_income_usd": "abc"},
                        {"monthly_income_usd": 4000, "region": "Mars"},
                        {"monthly_income_usd": 4000, "credit_score": 5}]:
            with self.subTest(profile=profile), self.assertRaises(ValueError):
                predict_monthly_expenses(profile)

    def test_transaction_cost(self):
        grocery = predict_transaction_cost("grocery")
        electronics = predict_transaction_cost("Electronics")
        self.assertEqual(grocery["category"], "Grocery")
        self.assertGreater(electronics["typical_cost_usd"], grocery["typical_cost_usd"])
        with self.assertRaises(ValueError):
            predict_transaction_cost("nonsense")

    def test_forecast(self):
        f = forecast_next_month()
        self.assertEqual(f["forecast_month"], "2019-10")
        self.assertGreater(f["predicted_total"], 0)


class ExpenseApiTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_predict_expense(self):
        r = self.client.post("/api/predict-expense", json={"monthly_income_usd": 3500, "region": "Africa"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("predicted_expenses_usd", r.get_json())

    def test_predict_expense_rejects_bad_input(self):
        self.assertEqual(self.client.post("/api/predict-expense", json={}).status_code, 400)
        self.assertEqual(self.client.post("/api/predict-expense", data="hi").status_code, 400)
        self.assertEqual(self.client.post("/api/predict-expense", json={"monthly_income_usd": -1}).status_code, 400)

    def test_forecast_and_transaction_endpoints(self):
        self.assertEqual(self.client.get("/api/expense-forecast").status_code, 200)
        self.assertEqual(self.client.get("/api/transaction-cost?category=Food").status_code, 200)
        self.assertEqual(self.client.get("/api/transaction-cost?category=zzz").status_code, 400)


if __name__ == "__main__":
    unittest.main()
