"""FinWise Flask application.

Routes
    GET  /                    the chat page
    POST /api/chat            {"question": "..."} -> {"answer", "intent", "confidence"}
    POST /api/predict-expense {"monthly_income_usd": 4000, ...} -> expected monthly expenses + range
    GET  /api/expense-forecast                       -> next month's spending forecast
    GET  /api/transaction-cost?category=Grocery      -> typical cost of one purchase
"""

from flask import Flask, jsonify, render_template, request

from backend.chatbot import get_chatbot_response
from backend.prediction_expense import (
    forecast_next_month,
    predict_monthly_expenses,
    predict_transaction_cost,
)

MAX_QUESTION_LENGTH = 500

app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    question = payload.get("question")

    if not isinstance(question, str) or not question.strip():
        return jsonify(error="Please type a question."), 400
    if len(question) > MAX_QUESTION_LENGTH:
        return jsonify(error=f"Questions are limited to {MAX_QUESTION_LENGTH} characters."), 400

    try:
        return jsonify(get_chatbot_response(question))
    except RuntimeError as exc:  # model files missing
        app.logger.error("%s", exc)
        return jsonify(error="The chatbot is not ready. Train it first with: python train_chatbot.py"), 503


NOT_TRAINED = "Expense models are not ready. Train them first with: python train_expense_prediction.py"


def _expense_call(fn, *args):
    try:
        return jsonify(fn(*args))
    except ValueError as exc:  # bad input
        return jsonify(error=str(exc)), 400
    except RuntimeError as exc:  # model file missing
        app.logger.error("%s", exc)
        return jsonify(error=NOT_TRAINED), 503


@app.post("/api/predict-expense")
def predict_expense():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="Send a JSON object, e.g. {\"monthly_income_usd\": 4000}."), 400
    return _expense_call(predict_monthly_expenses, payload)


@app.get("/api/expense-forecast")
def expense_forecast():
    return _expense_call(forecast_next_month)


@app.get("/api/transaction-cost")
def transaction_cost():
    return _expense_call(predict_transaction_cost, request.args.get("category", ""))


if __name__ == "__main__":
    app.run(debug=True)
