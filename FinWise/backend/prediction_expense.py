"""FinWise expense prediction (uses the models saved by train_expense_prediction.py).

    predict_monthly_expenses(profile)  -> expected monthly expenses + 80% range (Random Forest)
    predict_transaction_cost(category) -> typical cost of one purchase + 10-90% range
    forecast_next_month()              -> next month's spending from past months (time series)
    usd_to_zar(amount)                 -> convert USD to South African Rand

Amounts are USD unless the key says otherwise (the next-month forecast is in the
currency of personal_finance.csv, which the file does not state). The two USD-based
predictions also include Rand (_zar) values. Educational estimates only.
"""

import os
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

# ---- Currency conversion (USD -> ZAR) -------------------------------------------------
# Update this rate when needed, or set the USD_ZAR_RATE environment variable.
USD_ZAR_RATE = float(os.environ.get("USD_ZAR_RATE", 18.0))


def usd_to_zar(amount_usd, rate: float | None = None):
    """Convert USD to Rands. Works on a number, list, numpy array or pandas Series."""
    rate = USD_ZAR_RATE if rate is None else float(rate)
    if rate <= 0:
        raise ValueError("rate must be greater than 0.")
    if isinstance(amount_usd, (list, tuple)):
        return [round(float(a) * rate, 2) for a in amount_usd]
    result = amount_usd * rate
    return round(float(result), 2) if np.isscalar(result) else result.round(2)


def add_zar(result: dict, rate: float | None = None) -> dict:
    """Return a copy of `result` with a *_zar value next to every *_usd value."""
    rate = USD_ZAR_RATE if rate is None else float(rate)
    converted = dict(result)
    for key, value in result.items():
        if key.endswith("_usd") and isinstance(value, (int, float)):
            converted[key[:-4] + "_zar"] = usd_to_zar(value, rate)
    converted["usd_zar_rate"] = round(rate, 4)
    return converted


# ---- Model loading ----------------------------------------------------------------------
def _find_model() -> Path:
    """Locate models/expense_model.pkl whether this runs as a script, a module or in a notebook."""
    here = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
    cwd = Path.cwd()
    candidates = [here.parent / "models", here / "models", cwd / "models",
                  cwd / "finwise" / "models", cwd.parent / "models"]
    for folder in candidates:
        if (folder / "expense_model.pkl").exists():
            return folder / "expense_model.pkl"
    return candidates[0] / "expense_model.pkl"


MODEL_PATH = _find_model()

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


def predict_monthly_expenses(profile: dict, rate: float | None = None) -> dict:
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
    return add_zar({
        "predicted_expenses_usd": round(ratio * income, 2),
        "range_low_usd": round(max(0.0, (ratio + interval["low"]) * income), 2),
        "range_high_usd": round((ratio + interval["high"]) * income, 2),
        "expense_to_income_ratio": round(ratio, 3),
        "predicted_savings_per_month_usd": round(income - ratio * income, 2),
    }, rate)


def predict_transaction_cost(category: str, rate: float | None = None) -> dict:
    """Typical cost of a single purchase in a category (from the INR transaction data)."""
    bundle = _bundle()
    typical = bundle["typical_transaction_usd"]
    match = {name.lower(): name for name in typical}.get(str(category).strip().lower())
    if match is None:
        raise ValueError(f"category must be one of: {', '.join(sorted(typical))}.")
    stats, inr_rate = typical[match], bundle["usd_inr_rate"]
    return add_zar({
        "category": match,
        "typical_cost_usd": stats["median"],
        "range_low_usd": stats["low"],
        "range_high_usd": stats["high"],
        "typical_cost_inr": round(stats["median"] * inr_rate, 2),
        "usd_inr_rate": round(inr_rate, 2),
        "usd_inr_rate_date": bundle["usd_inr_rate_date"],
    }, rate)


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
