"""FinWise one-click launcher.

Double-click run.bat (Windows) or run:  python run.py
It creates a virtual environment, installs the requirements, trains any missing
models, starts the app and opens http://127.0.0.1:5000 in your browser.
"""
import os
import subprocess
import sys
import threading
import time
import venv
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
VENV = HERE / ".venv"
PY = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
URL = "http://127.0.0.1:5000"

MODELS = {  # model file -> script that creates it
    "models/chatbot_model.pkl": "train_chatbot.py",
    "models/expense_model.pkl": "train_expense_prediction.py",
}


def run(*args):
    subprocess.check_call([str(a) for a in args], cwd=HERE)


def main():
    if sys.version_info < (3, 9):
        sys.exit("Please install Python 3.9 or newer from python.org (tick 'Add Python to PATH').")

    if not PY.exists():
        print("Creating virtual environment (first run only)...")
        venv.create(VENV, with_pip=True)

    print("Checking requirements (the first run takes a few minutes)...")
    run(PY, "-m", "pip", "install", "-q", "-r", "requirements.txt")

    for model, script in MODELS.items():
        if not (HERE / model).exists():
            print(f"Training {model} ...")
            run(PY, script)

    threading.Thread(target=lambda: (time.sleep(2.5), webbrowser.open(URL)), daemon=True).start()
    print(f"\nFinWise is running at {URL}  (press Ctrl+C to stop)\n")
    try:
        run(PY, "app.py")
    except (KeyboardInterrupt, subprocess.CalledProcessError):
        pass


if __name__ == "__main__":
    main()
