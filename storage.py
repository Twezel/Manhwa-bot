import json, os, time

DB_FILE = "db.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"chapters": {}}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(db):
    tmp = DB_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DB_FILE)

def now():
    return int(time.time())
