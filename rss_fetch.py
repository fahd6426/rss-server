import os
import requests
from bs4 import BeautifulSoup
import random

# ناخذ الرابط والسر من سيكرتس جithub
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

# مصادر RSS
RSS_FEEDS = [
    "https://feeds.bbci.co.uk/sport/rss.xml",
    "https://feeds.skynews.com/feeds/rss/sports.xml",
]

def translate_text(text, target_lang="ar"):
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

def fetch_articles():
    all_articles = []
    print("🚀 بدء جلب الأخبار من المصادر ...")
    for feed_url in RSS_FEEDS:
        print(f"📡 جلب من: {feed_url}")
        try:
            resp = requests.get(feed_url, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"❌ فشل جلب المصدر {feed_url}: {e}")
            continue

        soup = BeautifulSoup(resp.content, "lxml-xml")
        items = soup.find_all("item")
        print(f"➡️ وجدنا {len(items)} خبر في هذا المصدر")

        for item in items:
            title = item.title.get_text(strip=True) if item.title else ""
            description = item.description.get_text(strip=True) if item.description else ""

            # نحاول نجيب صورة
            image_url = ""
            enclosure = item.find("enclosure")
            if enclosure and enclosure.get("url"):
                image_url = enclosure.get("url")

            if title:
                all_articles.append({
                    "title": title,
                    "content": description,
                    "image": image_url
                })
    print(f"📦 إجمالي الأخبار: {len(all_articles)}")
    return all_articles

def send_to_webhook(article):
    if not WEBHOOK_URL:
        print("❌ WEBHOOK_URL مفقود")
        return

    # نترجم للغة العربية
    title_ar = translate_text(article["title"])
    content_ar = translate_text(article["content"])

    data = {
        "secret": WEBHOOK_SECRET,
        "title": title_ar,
        "content": content_ar,
        "image": article["image"],
        "labels": ["رياضة"]
    }

    r = requests.post(WEBHOOK_URL, json=data)
    print(f"📨 أرسلنا: {title_ar[:50]} → الرد: {r.text}")

def main():
    articles = fetch_articles()
    if not articles:
        print("❌ ما فيه أخبار")
        return

    # ننشر خبر واحد فقط
    first_article = articles[0]
    send_to_webhook(first_article)

    print("✅ انتهى السكربت.")

if __name__ == "__main__":
    main()
