"""Smoke tests. Run from the project folder (after python train_chatbot.py):

    python -m unittest discover -s tests -v
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app  # noqa: E402
from backend.calculator import percent_of  # noqa: E402


class ChatApiTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def ask(self, question):
        return self.client.post("/api/chat", json={"question": question})

    def test_homepage_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"FinWise", response.data)

    def test_intents(self):
        cases = [
            ("What is investing?", "investing"),
            ("How do I create a budget?", "budgeting"),
            ("What is a credit score?", "credit"),
            ("What is forex?", "forex"),
            ("What should I do if an ATM keeps my card?", "atm_support"),
            ("hi", "greeting"),
        ]
        for question, intent in cases:
            with self.subTest(question=question):
                data = self.ask(question).get_json()
                self.assertEqual(data["intent"], intent)
                self.assertTrue(data["answer"])

    def test_percentage_is_calculated_not_looked_up(self):
        data = self.ask("What is 15% of R2000?").get_json()
        self.assertIn("R300.00", data["answer"])

    def test_percent_of_handles_spaces_and_decimals(self):
        self.assertIn("R900.00", percent_of("what's 7.5 percent of R 12 000"))
        self.assertIsNone(percent_of("what is investing"))

    def test_gibberish_gets_fallback(self):
        data = self.ask("asdfgh qwerty").get_json()
        self.assertIsNone(data["intent"])
        self.assertIn("not sure", data["answer"])

    def test_bad_input_is_rejected(self):
        for payload in [{}, {"question": ""}, {"question": "   "}, {"question": 5}]:
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post("/api/chat", json=payload).status_code, 400)

    def test_non_json_body_is_rejected(self):
        self.assertEqual(self.client.post("/api/chat", data="hello").status_code, 400)

    def test_overlong_question_is_rejected(self):
        self.assertEqual(self.ask("a" * 501).status_code, 400)


if __name__ == "__main__":
    unittest.main()
