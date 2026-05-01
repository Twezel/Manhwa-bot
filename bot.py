import time, threading, hashlib
from flask import Flask, request
import requests
import os

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

        old["last_seen"] = now()

        if old.get("locked") and not ch["locked"]:
            tg_send(f"🔓 <b>{ch['series']}</b>\n📖 {ch['title']}\nتم فتح الفصل!\n🔗 {ch['url']}")

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

def loop_locked():
    while True:
        try:
            ch = fetch_all()

            locked_keys = {
                k for k, v in db["chapters"].items() if v.get("locked")
            }

            ch2 = [c for c in ch if key_of(c) in locked_keys]

            if ch2:
                process(ch2)

        except Exception as e:
            print("LOCKED ERR:", e)

        time.sleep(CHECK_LOCKED)

# ========= WEB =========
@app.route("/", methods=["GET"])
def home():
    return "OK"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    return "ok"

# ========= BOT FUNCTIONS (FIXED INDENTATION ONLY) =========
def get_suggestions(name):
    pass

def get_info(name):
    pass

def get_cover(name):
    pass

# (هذه تعتمد على ask_gemini الموجودة عندك في ملفات أخرى)
def handle_search(chat_id, text):
    name = text.replace("/search", "").strip()

    if not name:
        tg_send("❗ اكتب اسم المانهوا بعد /search")
        return

    tg_send("🔎 جاري البحث...")

    results = get_suggestions(name)

    buttons = []
    for r in results:
        buttons.append([{
            "text": r,
            "callback_data": f"select::{r}"
        }])

    tg_send("📚 اختر العمل:")

def handle_select(chat_id, name):
    tg_send(f"📥 جاري جلب معلومات {name}...")

    info = get_info(name)
    cover = get_cover(name)

    msg = f"<b>📚 {name}</b>\n\n{info}\n\n🖼️ {cover}"
    tg_send(msg)

# ========= START =========
if __name__ == "__main__":
    threading.Thread(target=loop_new, daemon=True).start()
    threading.Thread(target=loop_locked, daemon=True).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
