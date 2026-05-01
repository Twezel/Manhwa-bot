import requests
from flask import Flask, request
import google.generativeai as genai

# ================= CONFIG =================
BOT_TOKEN = "8764498926:AAFbn6g676haDMqXZPAIHipiAsSdH0Ky94U"
GEMINI_KEY = "AIzaSyDoRtPqoOmzSQ2T91jzxdD7YUAdiYhy3kE"

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

app = Flask(__name__)

# ================= TELEGRAM =================
def send(chat_id, text, buttons=None):
    url = f"https://api.telegram.org/bot{8764498926:AAFbn6g676haDMqXZPAIHipiAsSdH0Ky94U}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    if buttons:
        payload["reply_markup"] = {"inline_keyboard": buttons}

    requests.post(url, json=payload)

# ================= GEMINI =================
def ask_gemini(prompt):
    try:
        res = model.generate_content(prompt)
        return res.text
    except:
        return "❌ فشل في جلب المعلومات"

def get_suggestions(name):
    prompt = f"""
    اعطني 5 اسماء مانهوا قريبة من: {name}
    فقط الاسماء كل اسم في سطر
    """
    res = ask_gemini(prompt)
    return list(dict.fromkeys([x.strip() for x in res.split("\n") if x.strip()]))[:5]

def get_info(name):
    prompt = f"""
    اعطني معلومات عن {name}:

    - وصف قصير
    - الحالة (مستمر / متوقف / منتهي)
    - اخر فصل كوري
    - اخر موسم
    - هل متوقف؟ ولماذا

    اجب بالعربية بشكل منظم
    """
    return ask_gemini(prompt)

def get_cover(name):
    return ask_gemini(f"اعطني رابط صورة غلاف مانهوا {name} فقط")

# ================= SEARCH =================
def handle_search(chat_id, text):
    name = text.replace("/search", "").strip()

    if not name:
        send(chat_id, "❗ اكتب اسم المانهوا بعد /search")
        return

    send(chat_id, "🔎 جاري البحث...")

    results = get_suggestions(name)

    buttons = []
    for r in results:
        buttons.append([{
            "text": r,
            "callback_data": f"select::{r}"
        }])

    send(chat_id, "📚 اختر العمل:", buttons)

def handle_select(chat_id, name):
    send(chat_id, f"📥 جاري جلب معلومات {name}...")

    info = get_info(name)
    cover = get_cover(name)

    msg = f"<b>📚 {name}</b>\n\n{info}\n\n🖼️ {cover}"

    send(chat_id, msg)

# ================= WEBHOOK =================
@app.route("/", methods=["GET"])
def home():
    return "Bot is running"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    # رسالة
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text.startswith("/search"):
            handle_search(chat_id, text)

    # ضغط زر
    if "callback_query" in data:
        chat_id = data["callback_query"]["message"]["chat"]["id"]
        cb = data["callback_query"]["data"]

        if cb.startswith("select::"):
            name = cb.split("::")[1]
            handle_select(chat_id, name)

    return "ok"

# ================= START =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
