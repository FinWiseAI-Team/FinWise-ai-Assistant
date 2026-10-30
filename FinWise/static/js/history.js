/* FinWise front end | HISTORY | Author: Person 3 - A Mene (240136306)
   Sidebar, saved chats, search, temporary chat. Loaded 3rd. */
// ---- Conversations: history drawer, search, temporary chat -----------------
const drawer = document.getElementById("drawer");
const historyToggle = document.getElementById("history-toggle");
const convoList = document.getElementById("convo-list");
const searchInput = document.getElementById("history-search");
const tempToggle = document.getElementById("temp-toggle");
const tempBanner = document.getElementById("temp-banner");
const clearAll = document.getElementById("clear-all");
const wide = () => window.matchMedia("(min-width: 900px)").matches;
function closeOnMobile() { if (!wide()) toggleDrawer(false); } // the sidebar stays open on desktop

function toggleDrawer(open) {
  drawer.hidden = !open;
  historyToggle.setAttribute("aria-expanded", String(open));
  if (open) { renderList(); searchInput.focus(); }
}

function syncMode() {
  tempBanner.hidden = !temporary;
  tempToggle.setAttribute("aria-pressed", String(temporary));
  tempToggle.textContent = temporary ? "Temporary chat: on" : "Temporary chat";
}

function resetView() {
  messages.querySelectorAll(".msg:not(#welcome)").forEach((m) => m.remove());
  closeSuggestions();
  scrollDown.hidden = true;
}

function newChat(isTemporary = false) {
  current = blankConvo();
  temporary = isTemporary;
  previousQuestions = [];
  historyIndex = -1;
  resetView();
  syncMode();
  renderList();
  input.focus();
}

function openConvo(id) {
  const found = convos.find((c) => c.id === id);
  if (!found) return;
  current = found;
  temporary = false;
  resetView();
  found.messages.forEach((m) =>
    addMessage(m.text, m.kind, { time: m.time, intent: m.intent, question: m.question, followup: false })
  );
  previousQuestions = found.messages.filter((m) => m.kind === "user").map((m) => m.text);
  syncMode();
  scrollToBottom();
  closeOnMobile();
}

function snippet(text, q) {
  const at = Math.max(0, text.toLowerCase().indexOf(q) - 20);
  return (at ? "…" : "") + text.slice(at, at + 70) + "…";
}

function renderList() {
  const q = searchInput.value.trim().toLowerCase();
  const rows = [];
  [...convos].sort((x, y) => y.updated - x.updated).forEach((c) => {
    if (!q || c.title.toLowerCase().includes(q)) return rows.push({ c, note: "" });
    const hit = c.messages.find((m) => m.text.toLowerCase().includes(q));
    if (hit) rows.push({ c, note: snippet(hit.text, q) });
  });

  convoList.replaceChildren();
  if (!rows.length) {
    const empty = document.createElement("p");
    empty.className = "convos__empty";
    empty.textContent = q ? "No conversations match your search." : "No saved conversations yet. Ask a question to start one.";
    convoList.appendChild(empty);
  }
  rows.forEach(({ c, note }) => {
    const row = document.createElement("div");
    row.className = "convo-row";

    const open = document.createElement("button");
    open.type = "button";
    open.className = "convo" + (c === current ? " is-current" : "");
    const title = document.createElement("span");
    title.className = "convo__title";
    title.textContent = c.title;
    const meta = document.createElement("span");
    meta.className = "convo__meta";
    meta.textContent = note || new Date(c.updated).toLocaleDateString([], { day: "numeric", month: "short" }) + " · " + c.messages.length + " messages";
    open.append(title, meta);
    open.addEventListener("click", () => openConvo(c.id));

    const del = document.createElement("button");
    del.type = "button";
    del.className = "convo__del";
    del.setAttribute("aria-label", "Delete conversation: " + c.title);
    del.textContent = "🗑";
    del.addEventListener("click", () => {
      convos = convos.filter((x) => x.id !== c.id);
      persist();
      if (c === current) newChat(false); else renderList();
    });

    row.append(open, del);
    convoList.appendChild(row);
  });
}

historyToggle.addEventListener("click", () => toggleDrawer(drawer.hidden));
document.getElementById("drawer-close").addEventListener("click", () => toggleDrawer(false));
document.getElementById("drawer-new").addEventListener("click", () => { newChat(false); closeOnMobile(); });
tempToggle.addEventListener("click", () => { newChat(!temporary); closeOnMobile(); });
searchInput.addEventListener("input", renderList);
document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !drawer.hidden && !wide()) toggleDrawer(false); });

// Two-step delete so one stray click cannot wipe everything.
let clearTimer;
clearAll.addEventListener("click", () => {
  if (clearAll.dataset.armed !== "1") {
    clearAll.dataset.armed = "1";
    clearAll.textContent = "Click again to confirm";
    clearTimer = setTimeout(() => { clearAll.dataset.armed = ""; clearAll.textContent = "Delete all history"; }, 3000);
    return;
  }
  clearTimeout(clearTimer);
  clearAll.dataset.armed = "";
  clearAll.textContent = "Delete all history";
  convos = [];
  persist();
  newChat(false);
});

drawer.hidden = !wide(); // open on desktop, closed on phones
historyToggle.setAttribute("aria-expanded", String(!drawer.hidden));
renderList();

// Time-of-day greeting on the welcome card.
(function () {
  const hour = new Date().getHours();
  const part = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  document.getElementById("hero-title").textContent = `${part}! I'm FinWise 👋`;
})();
