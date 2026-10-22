/* FinWise front end | EXPENSE PREDICTION window
   Opens from Sidebar > Expense prediction and talks to three backend routes:
     POST /api/predict-expense   monthly expenses from an income/profile
     GET  /api/expense-forecast  next month's spending forecast
     GET  /api/transaction-cost  typical cost of one purchase in a category
   Loaded last. Everything is wrapped in a function so it cannot clash with the
   variables in core.js / tools.js / history.js. */
(function () {
  "use strict";

  const dialog = document.getElementById("expense-dialog");
  if (!dialog) return;

  const openButton = document.getElementById("expense-open");
  const closeButton = document.getElementById("ex-close");
  const tabs = Array.from(dialog.querySelectorAll(".ex__tab"));
  const panels = {
    monthly: document.getElementById("ex-panel-monthly"),
    forecast: document.getElementById("ex-panel-forecast"),
    purchase: document.getElementById("ex-panel-purchase"),
  };
  const out = {
    monthly: document.getElementById("ex-monthly-out"),
    forecast: document.getElementById("ex-forecast-out"),
    purchase: document.getElementById("ex-purchase-out"),
  };

  const usd0 = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
  const usd2 = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const zar0 = new Intl.NumberFormat("en-ZA", { style: "currency", currency: "ZAR", maximumFractionDigits: 0 });
  const zar2 = new Intl.NumberFormat("en-ZA", { style: "currency", currency: "ZAR", minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const plain0 = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
  const inr = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 });

  let forecastLoaded = false;

  // ---- Small helpers -------------------------------------------------------
  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text; // textContent only: never insert server text as HTML
    return node;
  }

  function showMessage(target, text, kind) {
    target.replaceChildren(el("p", "ex__msg ex__msg--" + kind, text));
  }

  function setBusy(button, busy, idleText, busyText) {
    button.disabled = busy;
    button.textContent = busy ? busyText : idleText;
  }

  // One place for every request: turns network failures and backend {error} replies into messages.
  async function api(url, options) {
    let response;
    try {
      response = await fetch(url, options);
    } catch (err) {
      throw new Error("Couldn't reach the server. Check that the backend is running and try again.");
    }
    let data = null;
    try {
      data = await response.json();
    } catch (err) {
      /* body was not JSON */
    }
    if (!response.ok) {
      throw new Error((data && data.error) || "Something went wrong (error " + response.status + "). Please try again.");
    }
    return data;
  }

  function stat(label, value) {
    const box = el("div", "ex__stat");
    box.append(el("span", "ex__stat-label", label), el("strong", "ex__stat-value", value));
    return box;
  }

  // ---- Open / close --------------------------------------------------------
  openButton.addEventListener("click", () => {
    if (typeof dialog.showModal === "function") dialog.showModal();
    else dialog.setAttribute("open", ""); // very old browsers
  });
  closeButton.addEventListener("click", () => dialog.close());
  // Click on the dark backdrop closes the window.
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });

  // ---- Tabs ----------------------------------------------------------------
  function selectTab(name, focus) {
    tabs.forEach((tab) => {
      const active = tab.dataset.panel === name;
      tab.setAttribute("aria-selected", String(active));
      tab.tabIndex = active ? 0 : -1;
      if (active && focus) tab.focus();
    });
    Object.entries(panels).forEach(([key, panel]) => {
      panel.hidden = key !== name;
    });
    if (name === "forecast" && !forecastLoaded) loadForecast();
  }

  tabs.forEach((tab, index) => {
    tab.addEventListener("click", () => selectTab(tab.dataset.panel, false));
    tab.addEventListener("keydown", (event) => {
      let next = null;
      if (event.key === "ArrowRight") next = (index + 1) % tabs.length;
      else if (event.key === "ArrowLeft") next = (index - 1 + tabs.length) % tabs.length;
      if (next !== null) {
        event.preventDefault();
        selectTab(tabs[next].dataset.panel, true);
      }
    });
  });

  // ---- 1. Monthly expenses -------------------------------------------------
  const monthlyForm = document.getElementById("ex-monthly-form");
  const monthlySubmit = monthlyForm.querySelector(".ex__submit");
  const currencySelect = document.getElementById("ex-currency");

  // form field id -> backend key. Empty fields are left out so the backend uses its defaults.
  const NUMBER_FIELDS = {
    "ex-income": "monthly_income_usd",
    "ex-age": "age",
    "ex-savings": "savings_usd",
    "ex-credit": "credit_score",
    "ex-loan": "loan_amount_usd",
    "ex-emi": "monthly_emi_usd",
    "ex-rate": "loan_interest_rate_pct",
  };
  const CHOICE_FIELDS = {
    "ex-employment": "employment_status",
    "ex-education": "education_level",
    "ex-region": "region",
    "ex-hasloan": "has_loan",
  };
  // The backend works in US dollars, so these amounts are converted from rand before sending.
  const MONEY_KEYS = new Set(["monthly_income_usd", "savings_usd", "loan_amount_usd", "monthly_emi_usd"]);
  // Backend error messages use field names like monthly_income_usd; show friendly names instead.
  const FRIENDLY = {
    monthly_income_usd: "Monthly income", savings_usd: "Savings", loan_amount_usd: "Loan amount",
    monthly_emi_usd: "Monthly loan payment", loan_interest_rate_pct: "Loan interest", credit_score: "Credit score",
    age: "Age", employment_status: "Employment", education_level: "Education", region: "Region", has_loan: "Loan answer",
  };
  function friendly(message) {
    return Object.entries(FRIENDLY).reduce((text, [key, name]) => text.split(key).join(name), message);
  }

  // The rand rate lives in the backend (USD_ZAR_RATE). A tiny request for a 1-dollar income returns it.
  let zarRate = null;
  async function getRate() {
    if (zarRate) return zarRate;
    const probe = await api("/api/predict-expense", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ monthly_income_usd: 1 }),
    });
    if (!probe.usd_zar_rate) throw new Error("This backend does not give a rand rate yet. Switch the currency to US dollars.");
    zarRate = Number(probe.usd_zar_rate);
    return zarRate;
  }

  function buildProfile(rate) {
    const profile = {};
    for (const [id, key] of Object.entries(NUMBER_FIELDS)) {
      const raw = document.getElementById(id).value.trim();
      if (raw === "") continue;
      let value = Number(raw);
      if (rate && MONEY_KEYS.has(key)) value = Math.round((value / rate) * 100) / 100;
      profile[key] = value;
    }
    for (const [id, key] of Object.entries(CHOICE_FIELDS)) {
      const value = document.getElementById(id).value;
      if (value !== "") profile[key] = value;
    }
    // If they gave a loan amount or payment but did not answer "Do you have a loan?", assume Yes.
    if (!profile.has_loan && (profile.loan_amount_usd > 0 || profile.monthly_emi_usd > 0)) profile.has_loan = "Yes";
    return profile;
  }

  function renderMonthly(r) {
    // Newer backends send *_zar values next to *_usd. Show rand when it is there, dollars if not.
    const hasZar = typeof r.predicted_expenses_zar === "number";
    const fmt = hasZar ? zar0 : usd0;
    const pick = (name) => (hasZar ? r[name + "_zar"] : r[name + "_usd"]);
    const predicted = pick("predicted_expenses");
    const low = pick("range_low");
    const high = pick("range_high");

    const span = high - low;
    const marker = span > 0 ? Math.min(100, Math.max(0, ((predicted - low) / span) * 100)) : 50;

    const card = el("div", "ex__card");
    card.append(el("p", "ex__label", "You will probably spend about"));
    card.append(el("p", "ex__big", fmt.format(predicted) + " per month"));

    const range = el("div", "ex__range");
    const bar = el("div", "ex__range-bar");
    const dot = el("span", "ex__range-dot");
    dot.style.left = marker + "%";
    bar.append(dot);
    const ends = el("div", "ex__range-ends");
    ends.append(el("span", "", fmt.format(low)), el("span", "", fmt.format(high)));
    range.append(bar, ends);
    card.append(range);
    card.append(el("p", "ex__hint", "Likely range (about 80% of similar people fall in it): " +
      fmt.format(low) + " to " + fmt.format(high) + "."));

    const stats = el("div", "ex__stats");
    stats.append(
      stat("Spent of income", Math.round(r.expense_to_income_ratio * 100) + "%"),
      stat("Left over to save", fmt.format(pick("predicted_savings_per_month")) + " / month")
    );
    card.append(stats);
    if (hasZar) {
      card.append(el("p", "ex__hint", "That is about " + usd0.format(r.predicted_expenses_usd) +
        " in US dollars. Converted at R" + r.usd_zar_rate + " per US dollar."));
    }
    out.monthly.replaceChildren(card);
  }

  monthlyForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const typedIncome = Number(document.getElementById("ex-income").value);
    if (!(typedIncome > 0)) {
      showMessage(out.monthly, "Please enter your monthly income (a number above 0).", "error");
      document.getElementById("ex-income").focus();
      return;
    }
    setBusy(monthlySubmit, true, "Predict my expenses", "Predicting…");
    showMessage(out.monthly, "Working it out…", "info");
    try {
      const rate = currencySelect.value === "ZAR" ? await getRate() : null;
      const profile = buildProfile(rate);
      // The model understands incomes from 1 to 1,000,000 US dollars a month.
      if (profile.monthly_income_usd < 1 || profile.monthly_income_usd > 1000000) {
        const fmt = rate ? zar0 : usd0;
        const unit = rate || 1;
        showMessage(out.monthly, "Please enter a monthly income between " + fmt.format(unit) +
          " and " + fmt.format(unit * 1000000) + ".", "error");
        return;
      }
      renderMonthly(await api("/api/predict-expense", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profile),
      }));
    } catch (err) {
      showMessage(out.monthly, friendly(err.message), "error");
    } finally {
      setBusy(monthlySubmit, false, "Predict my expenses", "Predicting…");
    }
  });

  // ---- 2. Next-month forecast ----------------------------------------------
  function monthName(period) {
    // "2019-10" -> "October 2019"
    const [year, month] = String(period).split("-").map(Number);
    if (!year || !month) return String(period);
    return new Date(year, month - 1, 1).toLocaleDateString("en-US", { month: "long", year: "numeric" });
  }

  function renderForecast(f) {
    const card = el("div", "ex__card");
    card.append(el("p", "ex__label", "Forecast for " + monthName(f.forecast_month)));
    card.append(el("p", "ex__big", plain0.format(f.predicted_total) + " total"));

    const entries = Object.entries(f.by_category || {}).filter(([, value]) => value > 0); // hide categories with nothing forecast
    const top = entries.reduce((max, [, value]) => Math.max(max, value), 0) || 1;
    const list = el("ul", "ex__bars");
    entries.forEach(([name, value]) => {
      const row = el("li", "ex__bar-row");
      const track = el("span", "ex__bar-track");
      const fill = el("span", "ex__bar-fill");
      fill.style.width = Math.max(2, (value / top) * 100) + "%";
      track.append(fill);
      row.append(el("span", "ex__bar-name", name), track, el("span", "ex__bar-value", plain0.format(value)));
      list.append(row);
    });
    card.append(list);
    card.append(el("p", "ex__hint", "Based on the months " + f.based_on_months +
      ". The currency of this data is not stated, so amounts are shown as plain numbers."));
    out.forecast.replaceChildren(card);
  }

  async function loadForecast() {
    showMessage(out.forecast, "Loading forecast…", "info");
    try {
      renderForecast(await api("/api/expense-forecast"));
      forecastLoaded = true;
    } catch (err) {
      const retry = el("button", "btn-ghost ex__retry", "Try again");
      retry.type = "button";
      retry.addEventListener("click", loadForecast);
      out.forecast.replaceChildren(el("p", "ex__msg ex__msg--error", err.message), retry);
    }
  }

  // ---- 3. One purchase -----------------------------------------------------
  const purchaseForm = document.getElementById("ex-purchase-form");
  const purchaseSubmit = purchaseForm.querySelector(".ex__submit");

  function renderPurchase(r) {
    const hasZar = typeof r.typical_cost_zar === "number";
    const fmt = hasZar ? zar2 : usd2;
    const pick = (name) => (hasZar ? r[name + "_zar"] : r[name + "_usd"]);
    const card = el("div", "ex__card");
    card.append(el("p", "ex__label", "A typical " + r.category + " purchase costs about"));
    card.append(el("p", "ex__big", fmt.format(pick("typical_cost"))));
    card.append(el("p", "ex__hint", "Most purchases fall between " + fmt.format(pick("range_low")) +
      " and " + fmt.format(pick("range_high")) + "."));
    const stats = el("div", "ex__stats");
    if (hasZar) stats.append(stat("In US dollars", usd2.format(r.typical_cost_usd)));
    stats.append(stat("In Indian rupees", inr.format(r.typical_cost_inr)));
    card.append(stats);
    card.append(el("p", "ex__hint", (hasZar ? "Rand amounts use R" + r.usd_zar_rate + " per US dollar. " : "") +
      "The data is from transactions recorded in INR, converted at " + r.usd_inr_rate +
      " INR per USD (rate from " + r.usd_inr_rate_date + ")."));
    out.purchase.replaceChildren(card);
  }

  purchaseForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const category = document.getElementById("ex-category").value;
    if (!category) {
      showMessage(out.purchase, "Please choose a category first.", "error");
      return;
    }
    setBusy(purchaseSubmit, true, "Show typical cost", "Checking…");
    showMessage(out.purchase, "Checking…", "info");
    try {
      renderPurchase(await api("/api/transaction-cost?category=" + encodeURIComponent(category)));
    } catch (err) {
      showMessage(out.purchase, err.message, "error");
    } finally {
      setBusy(purchaseSubmit, false, "Show typical cost", "Checking…");
    }
  });
})();
