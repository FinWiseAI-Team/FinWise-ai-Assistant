"""Train the FinWise NLP chatbot.

Pipeline (as described in the FinWise documentation):
    question -> TF-IDF vectorizer -> Logistic Regression intent classifier
and, for answer selection, a per-intent index of the training questions so the
chatbot can return the stored answer of the most similar question.

Saves three files in models/:
    vectorizer.pkl, chatbot_model.pkl, chatbot_answers.pkl
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from backend.calculator import answer_is_computed_result
from backend.text import normalise

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "processed" / "chatbot_training.csv"
MODEL_DIR = ROOT / "models"


def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    if list(df.columns) != ["question", "intent", "answer"]:
        raise ValueError(f"Expected columns question,intent,answer; got {list(df.columns)}")
    df["clean"] = df["question"].map(normalise)
    return df


def make_vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, strip_accents="unicode")


def make_classifier() -> LogisticRegression:
    return LogisticRegression(max_iter=2000, C=10, class_weight="balanced")


def build_answer_index(df: pd.DataFrame, X) -> dict:
    """Per intent: TF-IDF matrix of its training questions + their answers."""
    index = {}
    for intent, rows in df.groupby("intent").indices.items():
        answers = df["answer"].to_numpy()[rows].tolist()
        index[intent] = {
            "matrix": X[rows],
            "answers": answers,
            # results tied to one specific amount must not be reused for other amounts
            "computed": np.array([answer_is_computed_result(a) for a in answers]),
        }
    return index


def main() -> None:
    df = load_data()
    vectorizer = make_vectorizer()
    X = vectorizer.fit_transform(df["clean"])
    model = make_classifier().fit(X, df["intent"])

    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump(vectorizer, MODEL_DIR / "vectorizer.pkl")
    joblib.dump(model, MODEL_DIR / "chatbot_model.pkl")
    joblib.dump(build_answer_index(df, X), MODEL_DIR / "chatbot_answers.pkl")
    print(f"Trained on {len(df)} rows, {df['intent'].nunique()} intents -> {MODEL_DIR}")


if __name__ == "__main__":
    main()
