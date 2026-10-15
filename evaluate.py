"""Evaluate the chatbot pipeline two ways.

1. Stratified random split (80/20). Optimistic: much of the dataset is the same
   base question with filler phrases added, so near-copies land in both sets.
2. Curated holdout: train on the augmented rows and test on the short, curated
   questions at the end of the file. This is closer to what real users type.
"""

import sys

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GroupShuffleSplit, train_test_split

from train_chatbot import build_answer_index, load_data, make_classifier, make_vectorizer

CURATED_START = 10290  # curated base questions start near here in the file


def fit(train: pd.DataFrame):
    vec = make_vectorizer()
    X = vec.fit_transform(train["clean"])
    model = make_classifier().fit(X, train["intent"])
    return vec, model, build_answer_index(train.reset_index(drop=True), X)


def score(name: str, train: pd.DataFrame, test: pd.DataFrame) -> None:
    test = test[test["intent"].isin(train["intent"].unique())]
    vec, model, index = fit(train)
    X = vec.transform(test["clean"])
    pred = model.predict(X)
    answer_hits = 0
    for i, intent in enumerate(pred):
        sims = (index[intent]["matrix"] @ X[i].T).toarray().ravel()
        answer_hits += index[intent]["answers"][int(np.argmax(sims))] == test["answer"].iloc[i]
    print(f"\n{name}: train={len(train)} test={len(test)}")
    print(f"  intent accuracy : {accuracy_score(test['intent'], pred):.3f}")
    print(f"  intent macro-F1 : {f1_score(test['intent'], pred, average='macro'):.3f}")
    print(f"  exact answer    : {answer_hits / len(test):.3f}")


def main() -> None:
    df = load_data()
    train, test = train_test_split(df, test_size=0.2, stratify=df["intent"], random_state=42)
    score("Stratified random split", train, test)

    score("Curated holdout (no curated rows in training)", df.iloc[:CURATED_START], df.iloc[CURATED_START:])

    # Fairest estimate: curated questions are split by base question, so
    # "What is X?" and "What is X in South Africa?" never straddle train/test.
    augmented, curated = df.iloc[:CURATED_START], df.iloc[CURATED_START:]
    base = curated["clean"].str.replace(r" in south africa(?=\?|$)", "", regex=True)
    train_idx, test_idx = next(GroupShuffleSplit(1, test_size=0.3, random_state=42).split(curated, groups=base))
    score("Curated grouped split (realistic)", pd.concat([augmented, curated.iloc[train_idx]]), curated.iloc[test_idx])
    sys.exit(0)


if __name__ == "__main__":
    main()
