import os
import re
from flask import Flask, request, jsonify, Response

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Reply engine
# ---------------------------------------------------------------------------
# This is a tiny rule-based bot so the app runs with no API key.
# To use a real LLM, replace the body of generate_reply() — see the comment
# at the bottom of this function.
# ---------------------------------------------------------------------------
def generate_reply(message: str) -> str:
    text = message.lower().strip()

    if not text:
        return "Say something and I'll reply!"

    rules = [
        (r"\b(hi|hello|hey)\b", "Hey there! How can I help you today?"),
        (r"\bhow are you\b", "I'm just a few lines of Python in a container, but I'm running great!"),
        (r"\b(your name|who are you)\b", "I'm DockerBot, a small demo chatbot."),
        (r"\b(bye|goodbye|see you)\b", "Goodbye! Come back anytime."),
        (r"\b(thanks|thank you)\b", "You're welcome!"),
        (r"\b(help|what can you do)\b",
         "I'm a demo bot. Try saying hello, asking my name, or asking how I am."),
        (r"\btime\b", "I can't read the clock yet, but I could if you wired me to one."),
    ]

    for pattern, reply in rules:
        if re.search(pattern, text):
            return reply

    # Default fallback: a friendly echo.
    return f'You said: "{message}". I\'m a simple demo bot, so that\'s about all I\'ve got!'

    # ---- To use a real LLM instead, do something like: --------------------
    # from anthropic import Anthropic
    # client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    # resp = client.messages.create(
    #     model="claude-sonnet-4-6",
    #     max_tokens=1000,
    #     messages=[{"role": "user", "content": message}],
    # )
    # return resp.content[0].text
    # -----------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return Response(INDEX_HTML, mimetype="text/html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "")
    reply = generate_reply(message)
    return jsonify({"reply": reply})


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# ---------------------------------------------------------------------------
# Frontend (kept inline so the whole app is a single file)
# ---------------------------------------------------------------------------
INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>DockerBot</title>
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0; font-family: system-ui, -apple-system, sans-serif;
      background: #0f172a; color: #e2e8f0; height: 100vh;
      display: flex; align-items: center; justify-content: center;
    }
    .chat {
      width: 100%; max-width: 480px; height: 80vh; background: #1e293b;
      border-radius: 16px; display: flex; flex-direction: column;
      overflow: hidden; box-shadow: 0 20px 50px rgba(0,0,0,.4);
    }
    .header {
      padding: 16px 20px; background: #334155; font-weight: 600;
      border-bottom: 1px solid #475569;
    }
    .messages {
      flex: 1; padding: 16px; overflow-y: auto;
      display: flex; flex-direction: column; gap: 10px;
    }
    .msg { padding: 10px 14px; border-radius: 14px; max-width: 80%; line-height: 1.4; }
    .user { background: #6366f1; color: #fff; align-self: flex-end; border-bottom-right-radius: 4px; }
    .bot  { background: #334155; align-self: flex-start; border-bottom-left-radius: 4px; }
    .input-row { display: flex; padding: 12px; gap: 8px; border-top: 1px solid #475569; }
    input {
      flex: 1; padding: 12px 14px; border-radius: 10px; border: none;
      background: #0f172a; color: #e2e8f0; font-size: 15px; outline: none;
    }
    button {
      padding: 12px 18px; border: none; border-radius: 10px; cursor: pointer;
      background: #6366f1; color: #fff; font-weight: 600; font-size: 15px;
    }
    button:hover { background: #4f46e5; }
  </style>
</head>
<body>
  <div class="chat">
    <div class="header">🤖 DockerBot</div>
    <div class="messages" id="messages">
      <div class="msg bot">Hi! I'm DockerBot. Say hello to get started.</div>
    </div>
    <div class="input-row">
      <input id="input" placeholder="Type a message..." autocomplete="off">
      <button onclick="send()">Send</button>
    </div>
  </div>

  <script>
    const messages = document.getElementById('messages');
    const input = document.getElementById('input');

    function addMessage(text, who) {
      const div = document.createElement('div');
      div.className = 'msg ' + who;
      div.textContent = text;
      messages.appendChild(div);
      messages.scrollTop = messages.scrollHeight;
    }

    async function send() {
      const text = input.value.trim();
      if (!text) return;
      addMessage(text, 'user');
      input.value = '';
      try {
        const res = await fetch('/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text })
        });
        const data = await res.json();
        addMessage(data.reply, 'bot');
      } catch (e) {
        addMessage('Error reaching the server.', 'bot');
      }
    }

    input.addEventListener('keydown', e => { if (e.key === 'Enter') send(); });
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    # 0.0.0.0 is required so the app is reachable from outside the container.
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
