"""Train the FinWise expense-prediction models.

Uses all four datasets in data/raw/:

    personal_finance_ml.csv        32k user profiles  -> Random Forest: monthly expenses from profile
    personal_finance_expenses.csv  8k INR transactions -> typical transaction cost per category (USD)
    forex.csv                      daily rates         -> USD/INR rate used to put the INR data in USD
    personal_finance.csv           21 months of spend  -> time-series forecast of next month's spending

Saves models/expense_model.pkl (everything the predictor needs) and
models/expense_metrics.json (the evaluation numbers).

Run:  python train_expense_prediction.py
"""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
MODEL_DIR = ROOT / "models"
RANDOM_STATE = 42

# Features for the profile model. gender / job_title are left out on purpose:
# expense advice should not depend on them.
PROFILE_NUMERIC = ["monthly_income_usd", "age", "savings_usd", "credit_score",
                   "loan_amount_usd", "monthly_emi_usd", "loan_interest_rate_pct"]
PROFILE_CATEGORICAL = ["employment_status", "education_level", "region", "has_loan"]
PROFILE_TARGET = "monthly_expenses_usd"

TXN_CATEGORICAL = ["Category", "MerchantType", "PaymentMethod", "TimeOfDay", "Weekday", "Month", "Location"]
TXN_TARGET = "AmountUSD"


def pipeline(numeric, categorical, min_leaf=5) -> Pipeline:
    prep = ColumnTransformer(
        [("cat", OneHotEncoder(handle_unknown="ignore"), categorical)],
        remainder="passthrough" if numeric else "drop",
    )
    rf = RandomForestRegressor(n_estimators=100, min_samples_leaf=min_leaf, n_jobs=-1,
                               random_state=RANDOM_STATE)
    return Pipeline([("prep", prep), ("rf", rf)])


def scores(y_true, y_pred) -> dict:
    return {"mae": round(float(mean_absolute_error(y_true, y_pred)), 2),
            "r2": round(float(r2_score(y_true, y_pred)), 4)}


# 1. Profile -> monthly expenses (personal_finance_ml.csv)
# The forest predicts the expense-to-income RATIO and the result is scaled by the
# person's income, so it works for any income level. Prediction ranges come from
# the spread of the errors on held-out users.
def train_profile_model() -> tuple[Pipeline, dict, dict]:
    df = pd.read_csv(RAW / "personal_finance_ml.csv", keep_default_na=False)
    X = df[PROFILE_NUMERIC + PROFILE_CATEGORICAL]
    ratio = df[PROFILE_TARGET] / df["monthly_income_usd"]
    X_tr, X_te, r_tr, r_te = train_test_split(X, ratio, test_size=0.2, random_state=RANDOM_STATE)
    income_te = X_te["monthly_income_usd"]

    model = pipeline(PROFILE_NUMERIC, PROFILE_CATEGORICAL, min_leaf=20).fit(X_tr, r_tr)
    pred_ratio = model.predict(X_te)
    actual = r_te * income_te

    # Baseline: income x the typical ratio. The forest has to beat (or at least match) this.
    baseline = r_tr.median() * income_te
    residual = r_te - pred_ratio
    interval = {"low": float(residual.quantile(0.10)), "high": float(residual.quantile(0.90))}
    inside = ((pred_ratio + interval["low"]) * income_te <= actual) & (actual <= (pred_ratio + interval["high"]) * income_te)

    metrics = {"rows": len(df), "test_rows": len(X_te),
               "random_forest": scores(actual, pred_ratio * income_te),
               "baseline_income_ratio": scores(actual, baseline),
               "range_80pct_coverage_on_test": round(float(inside.mean()), 3)}
    model = pipeline(PROFILE_NUMERIC, PROFILE_CATEGORICAL, min_leaf=20).fit(X, ratio)  # final: all rows
    return model, metrics, interval


# 2. Forex -> USD/INR rate (forex.csv)
def latest_usdinr() -> tuple[float, str]:
    fx = pd.read_csv(RAW / "forex.csv", usecols=["Date", "USDINR_Close"]).dropna()
    last = fx.iloc[-1]
    return float(last["USDINR_Close"]), str(last["Date"])[:10]


# 3. Transaction category -> typical cost (personal_finance_expenses.csv)
# A forest on category/merchant/payment/time features was evaluated too, but it did
# not beat the per-category median (the amount depends on the category only), so the
# shipped predictor is the median with a 10-90% range per category.
def train_transaction_model(usd_per_inr: float) -> tuple[dict, dict]:
    df = pd.read_csv(RAW / "personal_finance_expenses.csv")
    df = df[df["TransactionType"] == "Debit"].copy()
    df[TXN_TARGET] = df["Amount"] * usd_per_inr
    X, y = df[TXN_CATEGORICAL], df[TXN_TARGET]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=RANDOM_STATE)

    forest_eval = pipeline([], TXN_CATEGORICAL).fit(X_tr, y_tr)
    baseline = X_te["Category"].map(y_tr.groupby(X_tr["Category"]).median())
    metrics = {"rows": len(df), "test_rows": len(X_te),
               "random_forest_not_shipped": scores(y_te, forest_eval.predict(X_te)),
               "category_median_shipped": scores(y_te, baseline)}

    grouped = y.groupby(X["Category"])
    typical = {c: {"median": round(float(grouped.median()[c]), 2),
                   "low": round(float(grouped.quantile(0.10)[c]), 2),
                   "high": round(float(grouped.quantile(0.90)[c]), 2)} for c in grouped.groups}
    return typical, metrics


# 4. Time series: next month's spending (personal_finance.csv)
def load_monthly_spend() -> pd.DataFrame:
    """Monthly debit spend per category. Credit-card payments are excluded: they
    repay spending already counted on the card, so including them double counts."""
    df = pd.read_csv(RAW / "personal_finance.csv", sep="\t")
    df.columns = ["date", "description", "amount", "type", "category", "account", "month"]
    df["amount"] = pd.to_numeric(df["amount"].astype(str).str.replace(",", ".", regex=False))
    df = df[(df["type"] == "debit") & (df["category"] != "Credit Card Payment")]
    table = df.pivot_table(index="month", columns="category", values="amount",
                           aggfunc="sum", fill_value=0.0).sort_index()
    table["TOTAL"] = table.sum(axis=1)
    return table


FORECASTERS = {
    "last_month": lambda h: h[-1],
    "mean_3": lambda h: np.mean(h[-3:]),
    "median_3": lambda h: np.median(h[-3:]),
    "mean_6": lambda h: np.mean(h[-6:]),
    "median_6": lambda h: np.median(h[-6:]),
}
MIN_HISTORY = 6


def backtest(series: np.ndarray) -> dict:
    """Rolling-origin one-step-ahead MAE for each method."""
    out = {}
    for name, fn in FORECASTERS.items():
        errors = [abs(series[t] - fn(series[:t])) for t in range(MIN_HISTORY, len(series))]
        out[name] = round(float(np.mean(errors)), 2)
    return out


def train_forecaster() -> dict:
    table = load_monthly_spend()
    results = backtest(table["TOTAL"].to_numpy())
    best = min(results, key=results.get)
    return {"table": table, "method": best, "backtest_mae": results,
            "months": len(table), "last_month": str(table.index[-1]),
            "backtest_points": len(table) - MIN_HISTORY}


def main() -> None:
    profile_model, profile_metrics, interval = train_profile_model()
    rate, rate_date = latest_usdinr()
    typical, txn_metrics = train_transaction_model(usd_per_inr=1.0 / rate)
    ts = train_forecaster()

    raw = pd.read_csv(RAW / "personal_finance_ml.csv", keep_default_na=False)
    profile_choices = {c: sorted(raw[c].astype(str).unique().tolist()) for c in PROFILE_CATEGORICAL}

    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump({
        "profile_model": profile_model,
        "profile_features": PROFILE_NUMERIC + PROFILE_CATEGORICAL,
        "profile_choices": profile_choices,
        "profile_ratio_interval": interval,
        "typical_transaction_usd": typical,
        "usd_inr_rate": rate,
        "usd_inr_rate_date": rate_date,
        "forecast_table": ts["table"],
        "forecast_method": ts["method"],
    }, MODEL_DIR / "expense_model.pkl", compress=3)

    metrics = {
        "profile_model": profile_metrics,
        "transaction_model": txn_metrics,
        "forex": {"usd_inr_rate": round(rate, 4), "rate_date": rate_date},
        "time_series": {"months": ts["months"], "last_month": ts["last_month"],
                        "backtest_points": ts["backtest_points"],
                        "backtest_mae_by_method": ts["backtest_mae"], "chosen": ts["method"]},
    }
    (MODEL_DIR / "expense_metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
