# FinWise front end: how to connect your backend

Front-end team: NS Madiba (225144557), K Rathabani (225003503), A Mene (240136306). See `README_FRONTEND.md`.

## Folder layout (copy these into your Flask project)
```
templates/index.html
static/css/style.css, chat.css, tools.css, history.css
static/js/core.js, tools.js, history.js
```
Keep the folder names `templates/` and `static/`, because `index.html` loads its CSS and JS with
Flask's `url_for('static', filename=...)`.

## What your backend must provide

**1. `GET /`** returns the page:
```python
@app.get("/")
def index():
    return render_template("index.html")
```

**2. `POST /api/chat`**

Request (JSON):
```json
{ "question": "What is investing?" }
```
Success response (HTTP 200):
```json
{ "answer": "Investing means ...", "intent": "investing", "confidence": 0.93 }
```
- `answer` (string, required): the text shown in the chat.
- `intent` (string or null): used for the category tag and follow-up suggestions.
  Use `null` when the bot doesn't understand (the fallback message).
- `confidence` is optional and not shown.

Error response (HTTP 400 / 503):
```json
{ "error": "Please type a question." }
```
The page shows `error` in a red bubble. If the server is unreachable it shows a "couldn't reach the server" message.

## Intent names the front end recognises
`budgeting, saving, investing, banking, credit, forex, insurance, south_african_tax,
financial_safety, consumer_help, atm_support, calculations, greeting,
fnb_banking, capitec_banking, absa_banking, standard_bank_banking, nedbank_banking,
african_bank_banking, tymebank_banking, discovery_bank_banking, unknown_or_out_of_scope`

Any other intent name still works, but it won't get a category tag or follow-up suggestions.
To add one, edit `INTENT_TOPIC` in `static/js/core.js`.

## Not using Flask?
Replace the `{{ url_for(...) }}` links in `templates/index.html` with plain paths,
e.g. `href="/static/css/style.css"` and `src="/static/js/core.js"`, and make sure your server serves
the `static/` folder.

## Run the front end alone (fake backend)
```
pip install -r requirements.txt
python preview_server.py     # then open http://127.0.0.1:5000
```
`preview_server.py` only fakes `/api/chat`. Replace it with the real backend (same two routes).
Use **Ctrl+F5** in the browser after changing CSS/JS so the old files aren't cached.
