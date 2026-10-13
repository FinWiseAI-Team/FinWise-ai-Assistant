# FinWise front end: work split (3 people)

## Team
- Person 1: NS Madiba (225144557)
- Person 2: K Rathabani (225003503)
- Person 3: A Mene (240136306)


The interface is split into files so that each person works in **their own files**
and Git never has to merge two people editing the same lines.

| | Person 1: Chat core | Person 2: Input & tools | Person 3: Sidebar & history |
|---|---|---|---|
| **JS** | `static/js/core.js` | `static/js/tools.js` | `static/js/history.js` |
| **New CSS goes in** | `static/css/chat.css` | `static/css/tools.css` | `static/css/history.css` |
| **HTML area** (`templates/index.html`) | header, `#messages`, welcome card | `#suggestions`, composer form, tools/calculator panel, Topics buttons | `<aside id="drawer">` (new chat, temp chat, search, history list), `#temp-banner`, footer |

`static/css/style.css` is the shared base. Don't rewrite it; put changes in your own CSS file.
`app.py` and `backend/` belong to the backend team. Don't edit them.

## Person 1: Chat core (`core.js`)
- Message bubbles, bot/user styling, welcome card and starter cards
- Typing/"thinking" indicator and typewriter effect
- The `fetch("/api/chat")` call and error messages (400 / 503 / server down)
- Copy button, category tag on each answer, follow-up suggestion chips
- Saving each message into history (`saveHistory`)
- Integration owner: confirm the API contract `{answer, intent, confidence}` with the backend team

## Person 2: Input & tools (`tools.js`)
- Composer: character counter, Up/Down arrow question recall, Enter/Escape behaviour
- Scroll-to-latest button
- Topics buttons and the suggestions panel
- Calculators: "% of amount" and savings-growth calculator (check the maths, validate empty/negative input)

## Person 3: Sidebar & history (`history.js`)
- Sidebar open/close, New chat, Temporary chat (never saved)
- Saved conversations list, open, delete, search, "Delete all history"
- Responsive layout (desktop vs phone), keyboard and accessibility checks
- Final cross-browser/phone QA of the whole page before submission

## Shared rule
Scripts load in order: `core.js` -> `tools.js` -> `history.js` and share global variables
(`convos`, `current`, `temporary`, `messages`, `input`...). **Do not rename or delete a
function/variable that another person's file uses.** If you must, tell the group first.

## Run it locally
```bash
python -m venv .venv
.venv\Scripts\activate            # Windows  (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python train_chatbot.py           # creates models/*.pkl (needed once)
python app.py                     # open http://127.0.0.1:5000
python -m unittest discover -s tests -v
```
