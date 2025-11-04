import os
import requests
from bs4 import BeautifulSoup
import random

# ناخذ الرابط والسر من الـ secrets
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

# مصادر RSS شغالة
RSS_FEEDS = [
    "https://feeds.bbci.co.uk/sport/rss.xml",
    "https://feeds.skynews.com/feeds/rss/sports.xml",
]

def rephrase_content(content):
    intros = [
        "إليكم تفاصيل الخبر:",
        "فيما يلي أبرز ما جاء:",
        "ضمن متابعتنا للأخبار الرياضية:"
    ]
    endings = [
        "تابعونا لكل جديد.",
        "لمزيد من الأخبار زوروا المدونة.",
        "نوافيكم بالتفاصيل أولاً بأول."
    ]
    return f"{random.choice(intros)} {content} {random.choice(endings)}"

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

        for item in items[:5]:
            title = item.title.get_text(strip=True) if item.title else None
            description = item.description.get_text(strip=True) if item.description else ""
            image_url = ""
            enclosure = item.find("enclosure")
            if enclosure and enclosure.get("url"):
                image_url = enclosure.get("url")

            if title:
                all_articles.append({
                    "title": title,
                    "content": rephrase_content(description),
                    "image": image_url,
                    "labels": ["رياضة"]
                })

    print(f"📦 إجمالي الأخبار التي جمعناها: {len(all_articles)}")
    return all_articles

def send_to_webhook(article):
    if not WEBHOOK_URL:
        print("❌ مافيه WEBHOOK_URL")
        return
    data = {
        "secret": WEBHOOK_SECRET,
        "title": article["title"],
        "content": article["content"],
        "image": article["image"],
        "labels": article["labels"],
    }
    r = requests.post(WEBHOOK_URL, json=data)
    print(f"📨 أرسلنا: {article['title']} → الرد: {r.text}")

def main():
    articles = fetch_articles()
    if not articles:
        print("❌ ما فيه أخبار")
        return

    # نرسل أول 5 بس
    for art in articles[:5]:
        send_to_webhook(art)

    print("✅ انتهى السكربت.")

if __name__ == "__main__":
    main()
