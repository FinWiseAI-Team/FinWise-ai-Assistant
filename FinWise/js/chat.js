/* =========================================================
   FINWISE — CHAT ENGINE
   ========================================================= */

const sendButton = document.getElementById("sendButton");
const voiceButton = document.getElementById("voiceButton");

const input = document.getElementById("messageInput");
const messages = document.getElementById("chatMessages");
const welcome = document.getElementById("welcomeContent");


/* =========================================================
   FINANCIAL RESPONSE DATABASE
   ========================================================= */

const responses = {

    budget: {
        keywords: [
            "budget",
            "expenses",
            "cash flow",
            "income",
            "spending"
        ],

        response:
            "A good starting point is to separate your business finances into three areas: income, fixed expenses and variable expenses. Once these are clear, you can identify how much cash is available each month and where spending can be reduced."
    },


    investment: {
        keywords: [
            "invest",
            "investment",
            "stocks",
            "shares",
            "portfolio"
        ],

        response:
            "Before investing, it is useful to make sure your business has enough cash available for normal operating expenses. You can then consider how much risk you are comfortable with, your investment timeframe and whether diversification is appropriate."
    },


    market: {
        keywords: [
            "market",
            "trend",
            "forecast",
            "economy",
            "economic"
        ],

        response:
            "Market conditions can affect businesses through customer demand, interest rates, inflation and supplier costs. A useful approach is to monitor the indicators that have the biggest impact on your particular business rather than trying to predict every market movement."
    },


    learning: {
        keywords: [
            "learn",
            "teach",
            "explain",
            "finance",
            "financial"
        ],

        response:
            "Absolutely. Financial management becomes easier when you understand a few key concepts: cash flow, profit, expenses, budgeting and financial forecasting. I can explain each concept using practical business examples."
    }

};


/* =========================================================
   DEFAULT RESPONSE
   ========================================================= */

const defaultResponse =
    "I can help you with budgeting, cash flow, market trends, investment planning and financial learning. Try asking me something such as “How can I improve my monthly cash flow?”";


/* =========================================================
   SEND MESSAGE
   ========================================================= */

function sendMessage() {

    const text =
        input.value.trim();


    if (!text) {
        return;
    }


    welcome.style.display = "none";

    messages.style.display = "flex";


    addUserMessage(text);


    input.value = "";


    showTyping();


    setTimeout(() => {

        removeTyping();

        addAIMessage(
            generateResponse(text)
        );

    }, 900);

}


/* =========================================================
   USER MESSAGE
   ========================================================= */

function addUserMessage(text) {

    const message =
        document.createElement("div");

    message.className =
        "chat-message user-message";


    message.innerHTML = `

        <div class="message-avatar">
            You
        </div>

        <div class="message-content">

            <div class="message-bubble">
                ${escapeHTML(text)}
            </div>

            <span class="message-time">
                Just now
            </span>

        </div>

    `;


    messages.appendChild(message);

    scrollChat();

}


/* =========================================================
   AI MESSAGE
   ========================================================= */

function addAIMessage(text) {

    const message =
        document.createElement("div");

    message.className =
        "chat-message ai-message";


    message.innerHTML = `

        <div class="message-avatar ai-avatar">
            FW
        </div>

        <div class="message-content">

            <div class="message-name">
                FinWise AI
            </div>

            <div class="message-bubble">
                ${text}
            </div>

            <span class="message-time">
                Just now
            </span>

        </div>

    `;


    messages.appendChild(message);

    scrollChat();

}


/* =========================================================
   GENERATE RESPONSE
   ========================================================= */

function generateResponse(text) {

    const lowerText =
        text.toLowerCase();


    for (const category of Object.values(responses)) {

        const match =
            category.keywords.some(keyword =>
                lowerText.includes(keyword)
            );


        if (match) {
            return category.response;
        }

    }


    return defaultResponse;

}


/* =========================================================
   TYPING INDICATOR
   ========================================================= */

function showTyping() {

    const typing =
        document.createElement("div");

    typing.id =
        "typingIndicator";

    typing.className =
        "chat-message ai-message";


    typing.innerHTML = `

        <div class="message-avatar ai-avatar">
            FW
        </div>

        <div class="message-content">

            <div class="message-name">
                FinWise AI
            </div>

            <div class="typing-bubble">

                <span></span>
                <span></span>
                <span></span>

            </div>

        </div>

    `;


    messages.appendChild(typing);

    scrollChat();

}


/* =========================================================
   REMOVE TYPING
   ========================================================= */

function removeTyping() {

    const typing =
        document.getElementById(
            "typingIndicator"
        );


    if (typing) {
        typing.remove();
    }

}


/* =========================================================
   ENTER KEY
   ========================================================= */

input.addEventListener(
    "keydown",
    event => {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            sendMessage();

        }

    }
);


/* =========================================================
   SEND BUTTON
   ========================================================= */

sendButton.addEventListener(
    "click",
    sendMessage
);


/* =========================================================
   VOICE BUTTON
   ========================================================= */

voiceButton.addEventListener(
    "click",
    () => {

        input.placeholder =
            "Voice input is coming soon...";

        setTimeout(() => {

            input.placeholder =
                "Ask FinWise about your finances...";

        }, 1800);

    }
);

/* =========================================================
   SCROLL CHAT
   ========================================================= */

function scrollChat() {

    messages.scrollTo({
        top: messages.scrollHeight,
        behavior: "smooth"
    });

}


/* =========================================================
   HTML SAFETY
   ========================================================= */

function escapeHTML(text) {

    const element =
        document.createElement("div");

    element.textContent = text;

    return element.innerHTML;

}