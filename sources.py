import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from utils import safe_get

def _norm_num(text):
    m = re.search(r'(\d+(\.\d+)?)', text)
    return m.group(1) if m else "0"

def _mk(series, title, url, locked, site):
    return {
        "site": site,
        "series": series.strip() if series else "Unknown",
        "title": title.strip(),
        "url": url,
        "chapter_num": _norm_num(title),
        "locked": locked
    }

# ---------- AzoraMoon ----------
def azora():
    base = "https://azoramoon.com/"
    r = safe_get(base)
    if not r: return []
    s = BeautifulSoup(r.text, "html.parser")

    out = []
    # روابط الفصول تظهر غالبًا مع كلمة "الفصل"
    for a in s.select("a"):
        t = a.get_text(strip=True)
        if not t: continue
        if "الفصل" in t or "chapter" in t.lower():
            href = urljoin(base, a.get("href") or "")
            # اسم العمل غالبًا قبل -
            parts = t.split("-")
            series = parts[0] if parts else "Azora"
            # كشف القفل (وجود VIP/مدفوع/شراء)
            locked = any(k in t for k in ["VIP", "مقفل", "مدفوع", "شراء"])
            out.append(_mk(series, t, href, locked, "azora"))
    return out[:120]

# ---------- Dilar ----------
def dilar():
    base = "https://dilar.tube/"
    r = safe_get(base)
    if not r: return []
    s = BeautifulSoup(r.text, "html.parser")

    out = []
    for a in s.select("a"):
        t = a.get_text(strip=True)
        if not t: continue
        if "الفصل" in t or "chapter" in t.lower():
            href = urljoin(base, a.get("href") or "")
            series = t.split("-")[0]
            # ديلار: القفل غالبًا يظهر كـ VIP/مقفل
            locked = any(k in t for k in ["VIP", "مقفل"])
            out.append(_mk(series, t, href, locked, "dilar"))
    return out[:120]

# ---------- Meshmanga ----------
def mesh():
    base = "https://meshmanga.com/"
    r = safe_get(base)
    if not r: return []
    s = BeautifulSoup(r.text, "html.parser")

    out = []
    for a in s.select("a"):
        t = a.get_text(strip=True)
        if not t: continue
        if "الفصل" in t or "chapter" in t.lower():
            href = urljoin(base, a.get("href") or "")
            series = t.split("-")[0]
            # mesh غالبًا بدون قفل؛ نتحقق من كلمات
            locked = any(k in t for k in ["VIP", "مقفل"])
            out.append(_mk(series, t, href, locked, "mesh"))
    return out[:120]

# ---------- Hijala ----------
def hijala():
    base = "https://hijala.com/"
    r = safe_get(base)
    if not r: return []
    s = BeautifulSoup(r.text, "html.parser")

    out = []
    for a in s.select("a"):
        t = a.get_text(strip=True)
        if not t: continue
        if "الفصل" in t or "chapter" in t.lower():
            href = urljoin(base, a.get("href") or "")
            series = t.split("-")[0]
            # أحيانًا القفل = صفحة فاضية/طلب تسجيل، لكن هنا نعتمد الكلمات
            locked = any(k in t for k in ["VIP", "مقفل", "تسجيل"])
            out.append(_mk(series, t, href, locked, "hijala"))
    return out[:120]

# ---------- Olympus ----------
def olympus():
    base = "https://olympustaff.com/"
    r = safe_get(base)
    if not r: return []
    s = BeautifulSoup(r.text, "html.parser")

    out = []
    for a in s.select("a"):
        t = a.get_text(strip=True)
        if not t: continue
        if "الفصل" in t or "chapter" in t.lower():
            href = urljoin(base, a.get("href") or "")
            series = t.split("-")[0]
            locked = any(k in t for k in ["VIP", "مقفل", "شراء"])
            out.append(_mk(series, t, href, locked, "olympus"))
    return out[:120]

# مجمّع
def fetch_all():
    data = []
    for fn in (azora, dilar, mesh, hijala, olympus):
        try:
            data.extend(fn())
        except:
            pass
    return data
