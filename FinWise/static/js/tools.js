/* FinWise front end | TOOLS | Author: Person 2 - K Rathabani (225003503)
   Composer extras, topics bar, calculators. Loaded 2nd. */
// ---- Composer extras -------------------------------------------------------
function updateCounter() {
  const left = MAX_LENGTH - input.value.length;
  counter.textContent = input.value.length >= MAX_LENGTH - 100 ? String(left) : "";
  counter.classList.toggle("is-near", left <= 50);
}
input.addEventListener("input", updateCounter);

// Up/Down arrows step through earlier questions, like a terminal.
input.addEventListener("keydown", (event) => {
  if (event.key === "ArrowUp" && previousQuestions.length) {
    event.preventDefault();
    historyIndex = Math.min(historyIndex + 1, previousQuestions.length - 1);
    input.value = previousQuestions[previousQuestions.length - 1 - historyIndex];
    updateCounter();
  } else if (event.key === "ArrowDown" && historyIndex >= 0) {
    event.preventDefault();
    historyIndex -= 1;
    input.value = historyIndex < 0 ? "" : previousQuestions[previousQuestions.length - 1 - historyIndex];
    updateCounter();
  } else if (event.key === "Escape") {
    closeSuggestions();
  }
});

// ---- Scroll-to-latest button ----------------------------------------------
messages.addEventListener("scroll", () => {
  scrollDown.hidden = atBottom();
});
scrollDown.addEventListener("click", scrollToBottom);

// ---- Topic bar -------------------------------------------------------------
const topicButtons = document.querySelectorAll(".topic");

function openSuggestions(topic) {
  suggestionsTitle.textContent = `${TOPIC_LABELS[topic]}: tap a question`;
  suggestionsList.replaceChildren(...TOPICS[topic].map(makeChip));
  suggestions.hidden = false;
  topicButtons.forEach((b) => b.classList.toggle("is-active", b.dataset.topic === topic));
}

function closeSuggestions() {
  suggestions.hidden = true;
  topicButtons.forEach((b) => b.classList.remove("is-active"));
}

topicButtons.forEach((button) => {
  button.addEventListener("click", () => {
    if (button.classList.contains("is-active")) closeSuggestions();
    else openSuggestions(button.dataset.topic);
  });
});
document.getElementById("suggestions-close").addEventListener("click", closeSuggestions);

// ---- Calculators -----------------------------------------------------------
toolsToggle.addEventListener("click", () => {
  const open = toolsPanel.hidden;
  toolsPanel.hidden = !open;
  toolsToggle.setAttribute("aria-expanded", String(open));
});

// Percentage: sent through the chatbot so the answer comes from the backend calculator.
document.getElementById("percent-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const rate = document.getElementById("pct-rate").value;
  const amount = document.getElementById("pct-amount").value;
  if (rate === "" || amount === "") return;
  ask(`What is ${rate}% of R${amount}?`);
  event.target.reset();
});

// Savings growth: simple monthly-compounding estimate, calculated in the browser.
const rand = new Intl.NumberFormat("en-ZA", { style: "currency", currency: "ZAR", maximumFractionDigits: 0 });

document.getElementById("savings-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const start = Number(document.getElementById("sv-start").value) || 0;
  const monthly = Number(document.getElementById("sv-monthly").value) || 0;
  const rate = Number(document.getElementById("sv-rate").value) || 0;
  const years = Number(document.getElementById("sv-years").value) || 0;
  const result = document.getElementById("sv-result");
  if (years <= 0) return;

  const n = years * 12;
  const i = rate / 100 / 12;
  const growth = i === 0 ? start + monthly * n : start * (1 + i) ** n + monthly * (((1 + i) ** n - 1) / i);
  const paidIn = start + monthly * n;

  result.textContent =
    `After ${years} year${years === 1 ? "" : "s"} you could have about ${rand.format(growth)}.\n` +
    `You would pay in ${rand.format(paidIn)} and earn about ${rand.format(growth - paidIn)} in interest.\n` +
    "This is an estimate: real rates, fees and tax will change it.";
});

