import os
import requests
from bs4 import BeautifulSoup
import random

# ناخذ الرابط والسر من سيكرتس جithub
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

# مصادر RSS مع اسم المصدر
RSS_FEEDS = [
    ("https://feeds.bbci.co.uk/sport/rss.xml", "BBC Sport"),
    ("https://feeds.skynews.com/feeds/rss/sports.xml", "Sky News - Sports"),
]

def translate_text(text, target_lang="ar"):
    """ترجمة بسيطة عبر خدمة جوجل المجانية."""
    if not text:
        return ""
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "auto",
        "tl": target_lang,
        "dt": "t",
        "q": text
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        return "".join([part[0] for part in data[0]])
    except Exception:
        # لو فشلت الترجمة ننشر النص الأصلي
        return text

def build_article(ar_title: str, ar_content: str, source_name: str) -> str:
    """نطوّل الخبر ونضيف نقاط ومصدر."""
    intros = [
        "نقدّم لكم ملخص الخبر الرياضي التالي:",
        "ضمن متابعتنا اليومية لأهم الأخبار الرياضية:",
        "إليكم تفاصيل الخبر كما ورد:"
    ]
    outros = [
        "تابعونا لمزيد من الأخبار الرياضية أولاً بأول.",
        "نوافيكم بكل جديد حال صدوره.",
        "زوروا المدونة باستمرار للمزيد."
    ]

    intro = random.choice(intros)
    outro = random.choice(outros)

    # لو المحتوى قصير نكرّره عشان يصير أطول
    body = ar_content.strip()
    if len(body) < 150:
        body = body + "\n\n" + ar_content.strip()

    bullets = [
        "أهم النقاط في الخبر:",
        f"- العنوان: {ar_title}",
        "- الخبر من مصدر موثوق.",
        "- التفاصيل الكاملة مذكورة أعلاه."
    ]
    bullets_text = "\n".join(bullets)

    source_line = f"\nالمصدر: {source_name}"

    article = f"""{intro}

{body}

{bullets_text}

{outro}
{source_line}
"""
    return article

def fetch_articles():
    all_articles = []
    print("🚀 بدء جلب الأخبار من المصادر ...")
    for feed_url, source_name in RSS_FEEDS:
        print(f"📡 جلب من: {feed_url}")
        try:
            resp = requests.get(feed_url, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"❌ فشل جلب المصدر {feed_url}: {e}")
            continue

        soup = BeautifulSoup(resp.content, "lxml-xml")
        items = soup.find_all("item")

        for item in items:
            title = item.title.get_text(strip=True) if item.title else ""
            description = item.description.get_text(strip=True) if item.description else ""

            # حاول نلقط صورة
            image_url = ""
            enclosure = item.find("enclosure")
            if enclosure and enclosure.get("url"):
                image_url = enclosure.get("url")

            if title:
                all_articles.append({
                    "title": title,
                    "content": description,
                    "image": image_url,
                    "source": source_name
                })
    print(f"📦 إجمالي الأخبار: {len(all_articles)}")
    return all_articles
