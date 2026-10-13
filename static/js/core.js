/* FinWise front end | CORE | Author: Person 1 - NS Madiba (225144557)
   Chat engine, message rendering, API call. Loaded 1st. */
const messages = document.getElementById("messages");
const form = document.getElementById("chat-form");
const input = document.getElementById("question");
const sendButton = form.querySelector("button[type=submit]");
const counter = document.getElementById("counter");
const scrollDown = document.getElementById("scroll-down");
const suggestions = document.getElementById("suggestions");
const suggestionsTitle = document.getElementById("suggestions-title");
const suggestionsList = document.getElementById("suggestions-list");
const toolsPanel = document.getElementById("tools-panel");
const toolsToggle = document.getElementById("tools-toggle");

const STORE_KEY = "finwise.conversations";
const MAX_CONVOS = 50;
const REDUCE = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const MAX_LENGTH = Number(input.maxLength) || 500;

// ---- Topic shortcuts -------------------------------------------------------
const TOPICS = {
  budgeting: ["How do I create a budget?", "How can I reduce spending?", "What is the 50/30/20 rule?"],
  saving: ["How do I start saving in South Africa?", "How much should I save each month?", "How do I save when I have debt?"],
  investing: ["What is investing?", "What is a share?", "How do I check an investment company?"],
  banking: ["How do I stop a payment?", "How do I transfer money from FNB to another bank?", "What is a bank fee?"],
  credit: ["What is a credit score?", "How can I manage debt?", "What happens if I miss a loan payment?"],
  forex: ["What is forex?", "What is an international transfer exchange rate?", "How does a strong rand affect imports?"],
  insurance: ["What is an insurance excess?", "What should I check before buying insurance?", "How can I compare insurance policies?"],
  tax: ["What is taxable income?", "How do I pay SARS as an employee?", "What is my personal tax amount?"],
  safety: ["How do I spot a scam?", "How can I protect myself from identity theft?", "What should I do if I receive a suspicious message?"],
  atm: ["How do I use an ATM safely in South Africa?", "What should I do if an ATM keeps my card?", "Can I use another bank's ATM?"],
};
const TOPIC_LABELS = {
  budgeting: "Budgeting", saving: "Saving", investing: "Investing", banking: "Banking",
  credit: "Credit & debt", forex: "Forex", insurance: "Insurance", tax: "Tax",
  safety: "Scams & safety", atm: "ATM help",
};
// Map the intent returned by /api/chat to a topic, for follow-up suggestions.
const INTENT_TOPIC = {
  budgeting: "budgeting", saving: "saving", investing: "investing", banking: "banking",
  credit: "credit", forex: "forex", insurance: "insurance", south_african_tax: "tax",
  financial_safety: "safety", consumer_help: "safety", atm_support: "atm",
  fnb_banking: "banking", capitec_banking: "banking", absa_banking: "banking",
  standard_bank_banking: "banking", nedbank_banking: "banking", african_bank_banking: "banking",
  tymebank_banking: "banking", discovery_bank_banking: "banking",
};

// ---- Helpers ---------------------------------------------------------------
function timeNow() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function atBottom() {
  return messages.scrollHeight - messages.scrollTop - messages.clientHeight < 40;
}

function scrollToBottom() {
  messages.scrollTop = messages.scrollHeight;
}

function blankConvo() {
  return { id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6), title: "New chat", updated: Date.now(), messages: [] };
}

function loadConvos() {
  try {
    const data = JSON.parse(localStorage.getItem(STORE_KEY));
    return Array.isArray(data) ? data : [];
  } catch (err) {
    return [];
  }
}

let convos = loadConvos();     // saved conversations
let current = blankConvo();    // the conversation on screen
let temporary = false;         // temporary chats are never written to storage

function persist() {
  try {
    convos = convos.sort((x, y) => y.updated - x.updated).slice(0, MAX_CONVOS);
    localStorage.setItem(STORE_KEY, JSON.stringify(convos));
  } catch (err) {
    /* storage unavailable: chat still works, it just isn't remembered */
  }
}

function saveHistory(entry) {
  current.messages.push(entry);
  current.updated = Date.now();
  if (temporary) return; // memory only, never stored
  if (current.messages.length === 1 && entry.kind === "user") current.title = entry.text.slice(0, 60);
  if (!convos.includes(current)) convos.unshift(current);
  persist();
  renderList();
}

function followUps(intent, question) {
  const topic = INTENT_TOPIC[intent];
  if (!topic) return [];
  return TOPICS[topic].filter((q) => q.toLowerCase() !== question.toLowerCase()).slice(0, 2);
}

// ---- Rendering -------------------------------------------------------------
function addMessage(text, kind, options = {}) {
  const { time = timeNow(), save = false, intent = null, question = "", followup = true, animate = false } = options;
  const bubble = document.createElement("div");
  bubble.className = `msg msg--${kind}`;

  const topicLabel = intent === "calculations" ? "Calculation" : TOPIC_LABELS[INTENT_TOPIC[intent]];
  if (kind === "bot" && topicLabel) {
    const tag = document.createElement("span");
    tag.className = "tag";
    tag.textContent = topicLabel;
    bubble.appendChild(tag);
  }
  const p = document.createElement("p");
  const typed = animate && !REDUCE && kind === "bot";
  p.textContent = typed ? "" : text; // textContent: never render user or server text as HTML
  bubble.appendChild(p);

  const isBot = kind === "bot";
  const meta = document.createElement("div");
  meta.className = "msg__meta";
  const stamp = document.createElement("span");
  stamp.textContent = time;
  meta.appendChild(stamp);
  if (isBot) {
    const copy = document.createElement("button");
    copy.type = "button";
    copy.className = "copy";
    copy.textContent = "Copy";
    copy.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(text);
        copy.textContent = "Copied ✓";
      } catch (err) {
        copy.textContent = "Press Ctrl+C";
      }
      setTimeout(() => (copy.textContent = "Copy"), 1500);
    });
    meta.appendChild(copy);
  }
  bubble.appendChild(meta);

  if (isBot && followup) {
    const next = followUps(intent, question);
    if (next.length) {
      const chips = document.createElement("div");
      chips.className = "chips";
      next.forEach((q) => chips.appendChild(makeChip(q)));
      bubble.appendChild(chips);
    }
  }

  const stick = atBottom() || kind === "user";
  messages.appendChild(bubble);
  if (stick) scrollToBottom();
  if (typed) {
    bubble.classList.add("is-typing");
    typeOut(p, text, () => bubble.classList.remove("is-typing"));
  }

  if (save) saveHistory({ text, kind, time, intent, question });
  return bubble;
}

function makeChip(text) {
  const chip = document.createElement("button");
  chip.type = "button";
  chip.className = "chip";
  chip.textContent = text;
  return chip;
}

function typeOut(p, text, done) {
  let i = 0;
  const step = Math.max(2, Math.ceil(text.length / 80));
  const timer = setInterval(() => {
    i += step;
    p.textContent = text.slice(0, i);
    if (messages.scrollHeight - messages.scrollTop - messages.clientHeight < 140) scrollToBottom();
    if (i >= text.length) { clearInterval(timer); p.textContent = text; done(); }
  }, 16);
}

const THINKING = ["Understanding your question…", "Finding the best answer…", "Checking the facts…"];

function addTyping() {
  const bubble = document.createElement("div");
  bubble.className = "msg msg--bot msg--thinking";
  bubble.innerHTML = '<div class="typing" aria-label="FinWise is typing"><span></span><span></span><span></span></div><span class="typing__status"></span>';
  const status = bubble.querySelector(".typing__status");
  let step = 0;
  status.textContent = THINKING[0];
  bubble._timer = setInterval(() => { step = (step + 1) % THINKING.length; status.textContent = THINKING[step]; }, 900);
  messages.appendChild(bubble);
  scrollToBottom();
  return bubble;
}

function stopTyping(bubble) {
  clearInterval(bubble._timer);
  bubble.remove();
}

// ---- Chat ------------------------------------------------------------------
let previousQuestions = [];
let historyIndex = -1;

async function ask(question) {
  closeSuggestions();
  addMessage(question, "user", { save: true });
  previousQuestions.push(question);
  historyIndex = -1;
  const typing = addTyping();
  sendButton.disabled = true;

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await response.json();
    stopTyping(typing);
    if (!response.ok) {
      addMessage(data.error || "Something went wrong. Please try again.", "bot msg--error", { followup: false });
    } else {
      addMessage(data.answer, "bot", { save: true, intent: data.intent, question, animate: true });
    }
  } catch (err) {
    stopTyping(typing);
    addMessage("I couldn't reach the server. Please check your connection and try again.", "bot msg--error", { followup: false });
  } finally {
    sendButton.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const question = input.value.trim();
  if (!question) return;
  input.value = "";
  updateCounter();
  ask(question);
});

// Chips (welcome, follow-ups and topic suggestions) share one handler.
document.addEventListener("click", (event) => {
  const chip = event.target.closest(".chip, .starter");
  if (chip && !sendButton.disabled) ask(chip.dataset.q || chip.textContent);
});

