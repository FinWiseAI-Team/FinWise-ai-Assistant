# FinWise front end: Expense prediction window (Issue #1)

Adds an **Expense prediction** window to the FinWise interface. It only calls routes the backend
already provides; no backend code was changed.

## How to open it
Sidebar > **Tools** > **Expense prediction**. The window has three tabs.

| Tab | What the user does | Backend route | What is shown |
|---|---|---|---|
| My monthly expenses | Chooses rand or dollars, enters monthly income (required) and, optionally, age, savings, credit score, employment, education, region and loan details | `POST /api/predict-expense` | Expected monthly spending, likely range, % of income spent, amount left to save (rand, with the dollar amount) |
| Next month | Nothing (loads automatically) | `GET /api/expense-forecast` | Forecast month, total, and a bar per spending category |
| One purchase | Picks a category | `GET /api/transaction-cost?category=...` | Typical cost of one purchase and likely range in rand, plus the dollar and rupee amounts |

## Files
| File | Change |
|---|---|
| `templates/index.html` | **Edited**: added the CSS link, the sidebar button, the `<dialog id="expense-dialog">` window and the script tag |
| `static/js/expense.js` | **New**: all the logic for the window |
| `static/css/expense.css` | **New**: all the styling for the window |
| `EXPENSE_PREDICTION_UI.md` | **New**: this document |

No existing JS or CSS file was changed, so this does not clash with `core.js`, `tools.js` or `history.js`.

## Design notes
- Empty optional fields are not sent, so the backend fills in its own defaults.
- Server text is shown with `textContent` (never as HTML).
- Handles errors: empty input, backend `400` messages (shown in a red box), `503` (models not trained), and server down.
- Works with the keyboard (arrow keys switch tabs, Esc closes) and on phone screens.
- **Rand (ZAR):** the backend (`backend/prediction_expense.py`) returns `*_zar` values next to the `*_usd` ones, plus `usd_zar_rate` (default R18.00 per US dollar, changeable with the `USD_ZAR_RATE` environment variable). The window shows rand first and the US dollar amount underneath.
- The user can type amounts in rand (default) or US dollars with the currency box. The backend only accepts dollars, so rand amounts are divided by `usd_zar_rate` before sending. The rate is read from the backend (one tiny request), so the window never has its own copy of it.
- If the backend has no `*_zar` fields (an older version), the window falls back to US dollars.
- The forecast data has no stated currency, so it is shown as plain numbers.
- The numbers are educational estimates from a model trained on sample data, not financial advice.

## How it was tested
Frontend and backend were run together (`python app.py`). Every tab was exercised in a desktop and a phone-sized browser: valid input, empty input, invalid input, optional fields, and Esc to close. No console errors. The existing backend tests (`python -m unittest discover -s tests -v`) still pass (8 tests in `tests/test_expense.py`).

## Run it
```
pip install -r requirements.txt
python train_expense_prediction.py   # once, if models/expense_model.pkl is missing
python app.py                        # open http://127.0.0.1:5000
```
