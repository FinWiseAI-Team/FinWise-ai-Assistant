"""Safe handling of "X% of R Y" questions.

The training data contains computed answers for specific amounts (for example
"15% of R12,000.00 is R1,800.00"). A classifier must never reuse one of those
for a different amount, so such answers are calculated here instead.
"""

import re

_AMOUNT = r"(\d{1,3}(?:[ ,]\d{3})+|\d+)(\.\d+)?"
_PERCENT_OF = re.compile(
    rf"(\d+(?:\.\d+)?)\s*(?:%|percent)\s*of\s*(?:r\s*)?{_AMOUNT}"
)
_COMPUTED_RESULT = re.compile(r"^[\d.,]+% of R")


def answer_is_computed_result(answer: str) -> bool:
    """True for stored answers that hold a result for one specific amount."""
    return bool(_COMPUTED_RESULT.match(answer))


def percent_of(question: str) -> str | None:
    """Answer questions like "What is 15% of R2000?" or return None."""
    match = _PERCENT_OF.search(question.lower())
    if not match:
        return None
    percent = float(match.group(1))
    amount = float(re.sub(r"[ ,]", "", match.group(2)) + (match.group(3) or ""))
    result = amount * percent / 100
    pct = f"{percent:g}"
    return (
        f"{pct}% of R{amount:,.2f} is R{result:,.2f}. "
        f"Calculation: {amount:,.2f} × {pct} ÷ 100."
    )
