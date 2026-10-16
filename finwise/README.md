# FinWise – AI Financial Assistance Chatbot

A Flask web app with an NLP chatbot for financial education (budgeting, saving,
investing, banking, ATM help, credit, forex, insurance, South African tax).
It follows the architecture in the *FinWise System Functions, Architecture and AI
Concepts* documentation.

## How it works

```
question → TF-IDF → Logistic Regression (intent) → most similar stored question
         in that intent → its stored answer → JSON → chat page
```

- The reply is always a stored answer, never freely generated text.
- `X% of R Y` questions are calculated exactly (`backend/calculator.py`) instead of
  looked up, so the bot never returns a result for someone else's amount.
- Low-confidence questions get a safe fallback message.

## Run it

```bash
pip install -r requirements.txt
python train_chatbot.py      # creates models/*.pkl
python train_expense_prediction.py   # creates models/expense_model.pkl + expense_metrics.json
python app.py                # http://127.0.0.1:5000
python -m unittest discover -s tests -v
python evaluate.py           # accuracy report
```

## Project layout

| Path | Purpose |
|---|---|
| `app.py` | Flask routes: `GET /`, `POST /api/chat` |
| `backend/chatbot.py` | Intent prediction, answer selection, fallback |
| `backend/calculator.py` | Exact percentage answers |
| `backend/prediction_expense.py` | Expense predictions (monthly expenses, purchase cost, next-month forecast) |
| `train_expense_prediction.py` | Trains the expense models from `data/raw/*.csv` |
| `data/raw/` | `forex.csv`, `personal_finance.csv`, `personal_finance_expenses.csv`, `personal_finance_ml.csv` |
| `train_chatbot.py` | Trains and saves `vectorizer.pkl`, `chatbot_model.pkl`, `chatbot_answers.pkl` |
| `evaluate.py` | Three evaluation setups (see below) |
| `data/processed/chatbot_training.csv` | 11,363 rows, 22 intents (`question,intent,answer`) |
| `templates/`, `static/` | Chat page |

## Accuracy (be careful how you read these)

| Test | Intent accuracy | Exact answer |
|---|---|---|
| Stratified random split | 99.3% | 96.0% |
| Curated holdout (no curated rows in training) | 73.7% | 27.8% |
| **Curated grouped split (realistic)** | **90.8%** | **49.1%** |

The random split is inflated: most of the dataset is the same base question with
filler phrases added ("Can you explain that briefly?"), so near-copies sit in both
train and test. Use the realistic row. The main confusion is `banking` vs
`financial_safety`, which genuinely overlap.

## Expense prediction

| Endpoint | What it returns |
|---|---|
| `POST /api/predict-expense` `{"monthly_income_usd": 4000, "region": "Africa"}` | expected monthly expenses + 80% range (only income is required) |
| `GET /api/transaction-cost?category=Grocery` | typical cost of one purchase + 10-90% range, in USD and INR |
| `GET /api/expense-forecast` | next month's spending, total and per category |

How the four datasets are used:

| File | Use |
|---|---|
| `personal_finance_ml.csv` | Random Forest predicts the expense-to-income ratio from the profile (income, age, savings, loans, credit score, employment, education, region); result = ratio x income |
| `personal_finance_expenses.csv` | typical cost per spending category (INR converted to USD) |
| `forex.csv` | latest USD/INR rate (2022-11-01) used for that conversion |
| `personal_finance.csv` | 21 months of spending; the forecast method is picked by rolling backtest (median of the last 6 months won) |

Held-out results (`models/expense_metrics.json`):

| Model | MAE | R2 | Simple baseline MAE |
|---|---|---|---|
| Monthly expenses (Random Forest) | $597 | 0.690 | $596 (income x typical ratio) |
| Purchase cost (category median) | $75 | 0.714 | n/a (this is the baseline; a forest scored $78) |
| Next-month total (median of last 6 months) | 801 | n/a | 1,391 (last month repeated) |

Read these honestly: in `personal_finance_ml.csv` expenses are almost exactly income x a
ratio between 0.3 and 0.9 with no relationship to any other column, so the forest can only
match the simple baseline. That is why predictions come with a range. The USD/INR rate is
from 2022 (the forex file ends there) while the transactions are from 2025, and the forecast
rests on only 21 months with one outlier month (June 2019).

## Known limitations

- **Answers are generic.** `budgeting` has 5 unique answers over 1,865 rows, `forex` 2,
  `south_african_tax` 1. The bot picks the best of a few stored answers per topic.
  Writing more specific question/answer pairs is the best way to improve it.
- **Small intents:** `atm_support` has only 34 rows.
- Educational only: not financial advice. The bot never asks for PINs or passwords.
