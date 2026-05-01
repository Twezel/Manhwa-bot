import time, threading, hashlib
from flask import Flask, request
import requests

from sources import fetch_all
from storage import load_db, save_db, now
from utils import sleep_jitter

# ========= CONFIG =========
BOT_TOKEN = "8764498926:AAFbn6g676haDMqXZPAIHipiAsSdH0Ky94U"
CHAT_ID   = "8309836593"

CHECK_NEW = 300      # فصول جديدة كل 5 دقائق
CHECK_LOCKED = 900   # إعادة فحص المقفلة كل 15 دقيقة

app = Flask(__name__)
db = load_db()

# ========= TELEGRAM =========
def tg_send(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    })

# ========= KEYS =========
def key_of(ch):
    raw = f"{ch['site']}::{ch['series']}::{ch['chapter_num']}"
    return hashlib.md5(raw.encode()).hexdigest()

# ========= LOGIC =========
def process(chapters):
    global db
    store = db["chapters"]

    for ch in chapters:
        k = key_of(ch)

        if k not in store:
            store[k] = {
                "site": ch["site"],
                "series": ch["series"],
                "title": ch["title"],
                "url": ch["url"],
                "locked": ch["locked"],
                "first_seen": now(),
                "last_seen": now()
            }
            tg_send(f"🆕 <b>{ch['series']}</b>\n📖 {ch['title']}\n🔗 {ch['url']}")
            continue

        old = store[k]

        # تحديث
        old["last_seen"] = now()

        # 🔓 فتح فصل
        if old.get("locked") and not ch["locked"]:
            tg_send(f"🔓 <b>{ch['series']}</b>\n📖 {ch['title']}\nتم فتح الفصل!\n🔗 {ch['url']}")

        # حدّث الحالة
        old["locked"] = ch["locked"]
        old["title"]  = ch["title"]
        old["url"]    = ch["url"]

    save_db(db)

# ========= LOOPS =========
def loop_new():
    while True:
        try:
            ch = fetch_all()
            process(ch)
        except Exception as e:
            print("NEW ERR:", e)
        time.sleep(CHECK_NEW)

# إعادة فحص المقفلة فقط (تقليل الضغط)
def loop_locked():
    while True:
        try:
            ch = fetch_all()
            # فلترة: فقط الفصول التي كانت مقفلة سابقًا
            locked_keys = {k for k,v in db["chapters"].items() if v.get("locked")}
            ch2 = []
            for c in ch:
                if key_of(c) in locked_keys:
                    ch2.append(c)
            if ch2:
                process(ch2)
        except Exception as e:
            print("LOCKED ERR:", e)
        time.sleep(CHECK_LOCKED)

# ========= WEBHOOK =========
@app.route("/", methods=["GET"])
def home():
    return "OK"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    # (اختياري) أوامر لاحقًا
    return "ok"

# ========= START =========
if __name__ == "__main__":
    threading.Thread(target=loop_new, daemon=True).start()
    threading.Thread(target=loop_locked, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)def get_suggestions(name):
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
def get_suggestions(name):
    pass

def get_info(name):
    pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
