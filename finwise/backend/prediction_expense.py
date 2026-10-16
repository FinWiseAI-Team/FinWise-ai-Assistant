"""FinWise expense prediction (uses the models saved by train_expense_prediction.py).

    predict_monthly_expenses(profile)  -> expected monthly expenses + 80% range (Random Forest)
    predict_transaction_cost(category) -> typical cost of one purchase + 10-90% range
    forecast_next_month()              -> next month's spending from past months (time series)

Amounts are USD unless the key says otherwise (the next-month forecast is in the
currency of personal_finance.csv, which the file does not state). Educational estimates only.
"""

from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "expense_model.pkl"

# Defaults for optional profile fields (population medians of the training data).
DEFAULTS = {
    "age": 43, "savings_usd": 200000.0, "credit_score": 575,
    "loan_amount_usd": 0.0, "monthly_emi_usd": 0.0, "loan_interest_rate_pct": 0.0,
    "employment_status": "Employed", "education_level": "Bachelor",
    "region": "Other", "has_loan": "No",
}


@lru_cache(maxsize=1)
def _bundle() -> dict:
    try:
        return joblib.load(MODEL_PATH)
    except FileNotFoundError as exc:
        raise RuntimeError("Expense model not found. Run: python train_expense_prediction.py") from exc


def _number(value, name: str, minimum: float, maximum: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a number.") from None
    if not np.isfinite(number) or not minimum <= number <= maximum:
        raise ValueError(f"{name} must be between {minimum:g} and {maximum:g}.")
    return number


def predict_monthly_expenses(profile: dict) -> dict:
    """Predict monthly expenses from a profile. Only monthly_income_usd is required."""
    bundle = _bundle()
    if "monthly_income_usd" not in profile:
        raise ValueError("monthly_income_usd is required.")

    row = {**DEFAULTS, **{k: v for k, v in profile.items() if v is not None}}
    row["monthly_income_usd"] = _number(row["monthly_income_usd"], "monthly_income_usd", 1, 1_000_000)
    row["age"] = _number(row["age"], "age", 16, 100)
    row["savings_usd"] = _number(row["savings_usd"], "savings_usd", 0, 1e9)
    row["credit_score"] = _number(row["credit_score"], "credit_score", 300, 850)
    for key in ("loan_amount_usd", "monthly_emi_usd"):
        row[key] = _number(row[key], key, 0, 1e9)
    row["loan_interest_rate_pct"] = _number(row["loan_interest_rate_pct"], "loan_interest_rate_pct", 0, 100)
    for key, allowed in bundle["profile_choices"].items():
        if str(row[key]) not in allowed:
            raise ValueError(f"{key} must be one of: {', '.join(allowed)}.")

    features = pd.DataFrame([row])[bundle["profile_features"]]
    ratio = float(bundle["profile_model"].predict(features)[0])
    income = row["monthly_income_usd"]
    interval = bundle["profile_ratio_interval"]
    return {
        "predicted_expenses_usd": round(ratio * income, 2),
        "range_low_usd": round(max(0.0, (ratio + interval["low"]) * income), 2),
        "range_high_usd": round((ratio + interval["high"]) * income, 2),
        "expense_to_income_ratio": round(ratio, 3),
        "predicted_savings_per_month_usd": round(income - ratio * income, 2),
    }


def predict_transaction_cost(category: str) -> dict:
    """Typical cost of a single purchase in a category (from the INR transaction data)."""
    bundle = _bundle()
    typical = bundle["typical_transaction_usd"]
    match = {name.lower(): name for name in typical}.get(str(category).strip().lower())
    if match is None:
        raise ValueError(f"category must be one of: {', '.join(sorted(typical))}.")
    stats, rate = typical[match], bundle["usd_inr_rate"]
    return {
        "category": match,
        "typical_cost_usd": stats["median"],
        "range_low_usd": stats["low"],
        "range_high_usd": stats["high"],
        "typical_cost_inr": round(stats["median"] * rate, 2),
        "usd_inr_rate": round(rate, 2),
        "usd_inr_rate_date": bundle["usd_inr_rate_date"],
    }


def forecast_next_month() -> dict:
    """Next month's spending: robust median of recent months (method chosen by backtest)."""
    bundle = _bundle()
    table: pd.DataFrame = bundle["forecast_table"]
    window = 6 if bundle["forecast_method"].endswith("6") else 3
    use = np.mean if bundle["forecast_method"].startswith("mean") else np.median
    if bundle["forecast_method"] == "last_month":
        window, use = 1, np.mean

    recent = table.tail(window)
    by_category = {c: round(float(use(recent[c])), 2) for c in table.columns if c != "TOTAL"}
    last = pd.Period(table.index[-1], freq="M")
    return {
        "forecast_month": str(last + 1),
        "predicted_total": round(float(use(recent["TOTAL"])), 2),
        "by_category": dict(sorted(by_category.items(), key=lambda kv: -kv[1])),
        "method": bundle["forecast_method"],
        "based_on_months": f"{recent.index[0]} to {recent.index[-1]}",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(predict_monthly_expenses({"monthly_income_usd": 4000}), indent=2))
    print(json.dumps(predict_transaction_cost("Grocery"), indent=2))
    print(json.dumps(forecast_next_month(), indent=2))
