"""FinWise NLP chatbot: intent classification + answer selection.

1. TF-IDF turns the question into numeric features.
2. Logistic Regression predicts the intent.
3. Within that intent, the answer of the most similar training question is
   returned (cosine similarity), so the reply is never generated freely.
4. If the model is not confident enough, a safe fallback is returned.
"""

from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np

from backend.calculator import percent_of
from backend.text import normalise

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"

MIN_INTENT_CONFIDENCE = 0.30   # below this the intent prediction is unreliable
MIN_ANSWER_SIMILARITY = 0.10   # below this no stored question is close enough
OUT_OF_SCOPE_INTENT = "unknown_or_out_of_scope"

FALLBACK_ANSWER = (
    "I'm not sure I understood that. I can help with budgeting, saving, investing, "
    "banking, credit, forex, insurance and tax. Try asking something like "
    "\"What is investing?\" or \"How do I create a budget?\""
)


@lru_cache(maxsize=1)
def _load():
    """Load the saved models once (they are created by train_chatbot.py)."""
    try:
        return (
            joblib.load(MODEL_DIR / "vectorizer.pkl"),
            joblib.load(MODEL_DIR / "chatbot_model.pkl"),
            joblib.load(MODEL_DIR / "chatbot_answers.pkl"),
        )
    except FileNotFoundError as exc:
        raise RuntimeError("Model files not found. Run: python train_chatbot.py") from exc


def get_chatbot_response(question: str) -> dict:
    """Return {"answer", "intent", "confidence"} for a user question."""
    clean = normalise(question)
    if not clean:
        return {"answer": FALLBACK_ANSWER, "intent": None, "confidence": 0.0}

    vectorizer, model, answers = _load()
    features = vectorizer.transform([clean])

    probabilities = model.predict_proba(features)[0]
    best = int(np.argmax(probabilities))
    intent, confidence = str(model.classes_[best]), float(probabilities[best])

    # Exact arithmetic is calculated, never looked up.
    calculated = percent_of(question)
    if calculated:
        return {"answer": calculated, "intent": "calculations", "confidence": 1.0}

    entry = answers[intent]
    similarities = (entry["matrix"] @ features.T).toarray().ravel()  # rows are L2-normalised
    # A stored result for someone else's amount would be wrong, so skip those.
    similarities = np.where(entry["computed"], -1.0, similarities)
    nearest = int(np.argmax(similarities))
    similarity = float(similarities[nearest])

    if intent != OUT_OF_SCOPE_INTENT and (
        confidence < MIN_INTENT_CONFIDENCE or similarity < MIN_ANSWER_SIMILARITY
    ):
        return {"answer": FALLBACK_ANSWER, "intent": None, "confidence": round(confidence, 3)}

    return {
        "answer": entry["answers"][nearest],
        "intent": intent,
        "confidence": round(confidence, 3),
    }
