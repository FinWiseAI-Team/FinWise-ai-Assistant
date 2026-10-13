# FinWise: Front end (interface)

The FinWise chat interface was designed and built by the three front-end team members below.
Each member owns separate files, and every file starts with a comment naming its author.

## Front-end team

| Person | Name | Student number | Area | Files |
|---|---|---|---|---|
| 1 | NS Madiba | 225144557 | Chat core: messages, typing effect, `/api/chat` call, errors, copy button, follow-up chips | `static/js/core.js`, `static/css/chat.css` |
| 2 | K Rathabani | 225003503 | Input and tools: composer, topics, suggestions, calculators | `static/js/tools.js`, `static/css/tools.css` |
| 3 | A Mene | 240136306 | Sidebar and history: new/temporary chat, saved chats, search, mobile layout, final QA | `static/js/history.js`, `static/css/history.css` |

Shared files: `templates/index.html` (page layout) and `static/css/style.css` (base styles).

## Work method
- Tools used: Git, GitHub and VS Code, with Python (Flask) serving the page.
- Branch `frontend` holds the interface. Each member worked on their own branch
  (`frontend-chat`, `frontend-tools`, `frontend-history`) and submitted a pull request into `frontend`.
- The commit history and pull requests show who did which part.

## How the interface connects to the AI backend
- `GET /` returns `templates/index.html`.
- `POST /api/chat` receives `{"question": "..."}` and returns `{"answer": "...", "intent": "..."}`
  (or `{"error": "..."}`). See `README_BACKEND_CONNECTION.md` for details and the intent names.

## Folder structure
```
templates/index.html
static/css/   style.css, chat.css, tools.css, history.css
static/js/    core.js, tools.js, history.js
```
