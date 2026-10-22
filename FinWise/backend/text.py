"""Text normalisation shared by training and the live chatbot."""

import re

_SPACES = re.compile(r"\s+")


def normalise(text: str) -> str:
    """Lowercase and collapse whitespace so training and runtime match."""
    return _SPACES.sub(" ", str(text)).strip().lower()
