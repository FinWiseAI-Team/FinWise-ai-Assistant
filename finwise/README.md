# FinWise – AI Financial Assistance Chatbot

A Flask web app that combines an NLP chatbot for financial education (budgeting, saving,
investing, banking, ATM help, credit, forex, insurance, South African tax and eight South
African banks) with expense prediction, a next-month spending forecast and USD to ZAR
conversion. It follows the architecture in the *FinWise System Functions, Architecture and
AI Concepts* documentation.

## How it works

```
question → TF-IDF → Logistic Regression (intent) → most similar stored question
         in that intent → its stored answer → JSON → chat page
```

- The reply is always a stored answer, never freely generated text.
- `X% of R Y` questions are calculated exactly (`backend/calculator.py`) instead of
  looked up, so the bot never returns a result for someone else's amount.
- Questions the model recognises as out of scope get a polite "I can't help with that" reply.
  Low-confidence questions get a safe fallback message.
- Questions are limited to 500 characters. No personal data is stored.

## Run it

Requires **Python 3.10 or newer** (the code uses `X | None` type hints).

**Easiest:** double-click `run.bat` (Windows) or run `python run.py`. It creates a virtual
environment, installs the requirements, trains any missing models, starts the app and opens
http://127.0.0.1:5000. See `README_RUN.txt`.

**Manually:**

```bash
pip install -r requirements.txt
python train_chatbot.py              # creates models/vectorizer.pkl, chatbot_model.pkl, chatbot_answers.pkl
python train_expense_prediction.py   # creates models/expense_model.pkl + expense_metrics.json
python app.py                        # http://127.0.0.1:5000
python -m unittest discover -s tests -v
python evaluate.py                   # chatbot accuracy report
```

Set the Rand rate with the `USD_ZAR_RATE` environment variable (default 18.0 per US dollar).

## Project layout

| Path | Purpose |
|---|---|
| `app.py` | Flask routes: `GET /`, `POST /api/chat`, `POST /api/predict-expense`, `GET /api/expense-forecast`, `GET /api/transaction-cost` |
| `run.py`, `run.bat`, `README_RUN.txt` | One-click launcher and instructions |
| `backend/chatbot.py` | Intent prediction, answer selection, fallback |
| `backend/calculator.py` | Exact percentage answers |
| `backend/text.py` | Question clean-up (normalisation) shared by training and prediction |
| `backend/prediction_expense.py` | Expense predictions (monthly expenses, purchase cost, next-month forecast) and USD to ZAR conversion |
| `train_chatbot.py` | Trains and saves `vectorizer.pkl`, `chatbot_model.pkl`, `chatbot_answers.pkl` |
| `train_expense_prediction.py` | Trains the expense models from `data/raw/*.csv` |
| `evaluate.py` | Chatbot evaluation (see Accuracy) |
| `data/processed/chatbot_training.csv` | 30,025 rows, 22 intents (`question,intent,answer`) |
| `data/raw/` | `forex.csv`, `personal_finance.csv`, `personal_finance_expenses.csv`, `personal_finance_ml.csv` |
| `models/` | Saved models and `expense_metrics.json` |
| `templates/index.html` | Chat page, including the Expense prediction window |
| `static/css/`, `static/js/` | Styling and scripts (`core.js`, `tools.js`, `history.js`, `expense.js`) |
| `tests/` | `test_chat.py`, `test_expense.py` |
| `EXPENSE_PREDICTION_UI.md` | Notes on the Expense prediction window |

## Intents

22 intents: `budgeting`, `saving`, `investing`, `credit`, `banking`, `forex`, `tax`,
`insurance`, `financial_safety`, `consumer_help`, `calculations`, `atm_support`, `greeting`,
`unknown_or_out_of_scope`, and eight bank-specific intents (`absa`, `african_bank`,
`capitec`, `discovery_bank`, `fnb`, `nedbank`, `standard_bank`, `tymebank`, each
`*_banking`).

## Accuracy (be careful how you read these)

| Test | Intent accuracy | Exact answer |
|---|---|---|
| Stratified random split (`evaluate.py`) | 100.0% | 85.3% |
| **Split by base question (realistic)**, mean of 3 runs | **99.2%** | **81.0%** |

The random split is inflated: most of the dataset is the same base question with filler
phrases added ("Hello FinWise,", "Sorry to bother,", "(I'm a beginner)", "asap"), so
near-copies sit in both train and test. The 30,025 rows hold only about 6,800 distinct
questions once that filler is removed. The realistic row removes the filler, groups rows by
the base question and keeps whole groups on one side of the split (80/20). Even so,
different wordings of the same topic share stored answers, so treat it as an upper estimate
for real users.

"Exact answer" means the returned answer matches the stored answer of the test row. Many
questions on one topic share several equally correct answers, so this understates how often
the reply is useful.

In the realistic split the main intent errors are `unknown_or_out_of_scope` questions
predicted as `greeting`, and `consumer_help` predicted as `banking`.

Note: the "curated holdout" and "curated grouped" tests that used to be in `evaluate.py`
split the file at a fixed row number (`CURATED_START`). The dataset has since been
regenerated and shuffled, so that row number no longer marks the curated questions and those
two results are not meaningful. The base-question split above should replace them.

## Expense prediction

| Endpoint | What it returns |
|---|---|
| `POST /api/predict-expense` `{"monthly_income_usd": 4000, "region": "Africa"}` | expected monthly expenses + 80% range + expected savings (only income is required) |
| `GET /api/transaction-cost?category=Grocery` | typical cost of one purchase + 10-90% range, in USD, ZAR and INR |
| `GET /api/expense-forecast` | next month's spending, total and per category |

The two USD-based predictions also return `*_zar` values and the `usd_zar_rate` used (18.0 by
default, not a live rate). The forecast has no stated currency, so it is plain numbers. In the
Expense prediction window (sidebar > Tools) amounts are shown in rand first with the dollar
amount underneath.

How the four datasets are used:

| File | Use |
|---|---|
| `personal_finance_ml.csv` | 32,424 profiles. Random Forest predicts the expense-to-income ratio from the profile (income, age, savings, loans, credit score, employment, education, region); result = ratio x income |
| `personal_finance_expenses.csv` | 8,000 INR transactions from 2025: typical cost per spending category (INR converted to USD) |
| `forex.csv` | latest USD/INR rate (82.73 on 2022-11-01) used for that conversion |
| `personal_finance.csv` | 21 months of spending (Jan 2018 to Sep 2019); the forecast method is picked by rolling backtest (median of the last 6 months won) |

Held-out results (`models/expense_metrics.json`):

| Model | MAE | R2 | Simple baseline MAE |
|---|---|---|---|
| Monthly expenses (Random Forest, 6,485 test rows) | $597 | 0.689 | $596 (income x typical ratio) |
| Purchase cost (category median, 1,600 test rows) | $75 | 0.714 | n/a (this is the baseline; a forest scored $78) |
| Next-month total (median of last 6 months) | 801 | n/a | 1,391 (last month repeated) |

The 80% range covers 80.0% of the test cases.

Read these honestly: in `personal_finance_ml.csv` expenses are almost exactly income x a
ratio between 0.3 and 0.9 with no relationship to any other column, so the forest can only
match the simple baseline. That is why predictions come with a range. The USD/INR rate is
from 2022 (the forex file ends there) while the transactions are from 2025, and the forecast
rests on only 21 months with two outlier months (May 2018 and June 2019, each about five
times a normal month), which is why a median beat a mean.

## Known limitations

- **Answers are generic.** Apart from `calculations`, there are only 5 to 17 unique answers
  per intent, except `budgeting` (166 unique answers over 5,631 rows). Each bank intent has
  10 answers over 98 rows, `forex` has 16 over 2,286 and `tax` 15 over 977. The bot picks the
  best of a few stored answers per topic. Writing more specific question/answer pairs is the
  best way to improve it.
- **Small intents:** `atm_support` has only 36 rows, and each bank intent has 98.
- **Repetitive training data:** most rows are the same base question with filler added, so
  accuracy on real users will be lower than the numbers above.
- **Greetings:** short inputs such as "hi" can be classified as out of scope (the model is
  confident for "hello" but not for "hi").
- Exchange rates are fixed values (USD/ZAR 18.0 by default, USD/INR from 2022), not live.
- Educational only: not financial advice. The bot never asks for PINs or passwords.
