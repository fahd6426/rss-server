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
        return text  # لو الترجمة فشلت ننشر النص الأصلي

def build_article(ar_title: str, ar_content: str) -> str:
    """نطوّل الخبر ونخليه مرتب."""
    intro_choices = [
        "في هذا الخبر نستعرض لكم أبرز ما جاء في التقارير الرياضية اليوم:",
        "متابعةً لآخر المستجدات الرياضية، إليكم التفاصيل:",
        "ضمن تغطيتنا اليومية لعالم الرياضة، نعرض لكم ما يلي:"
    ]
    outro_choices = [
        "تابعونا باستمرار لمعرفة آخر الأخبار والتقارير.",
        "نوافيكم بكل جديد لحظة بلحظة.",
        "زوروا المدونة باستمرار لمزيد من المواضيع الرياضية."
    ]

    intro = random.choice(intro_choices)
    outro = random.choice(outro_choices)

    # لو الوصف قصير جدًا نحاول نعيده مرتين عشان يصير أطول شوي
    body = ar_content.strip()
    if len(body) < 120:
        body = body + " " + ar_content.strip()

    # نكوّن ملخص بنقاط
    bullet_intro = "أهم ما جاء في الخبر:"
    bullets = [
        f"- العنوان: {ar_title}",
        "- الخبر من مصدر موثوق.",
        "- التفاصيل الكاملة بالأسفل."
    ]

    bullets_text = "\n".join(bullets)

    article = f"""{intro}

{body}

{bullet_intro}
{bullets_text}

{outro}
"""
    return article

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

        for item in items:
            title = item.title.get_text(strip=True) if item.title else ""
            description = item.description.get_text(strip=True) if item.description else ""

            # نحاول نجيب صورة من الـ enclosure
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

    # ترجمة العنوان والمحتوى
    title_ar = translate_text(article["title"])
    content_ar = translate_text(article["content"])

    # نبني مقالة أطول ومهيأة
    long_content = build_article(title_ar, content_ar)

    data = {
      "secret": WEBHOOK_SECRET,
      "title": title_ar,
      "content": long_content,
      "image": article["image"],
      "labels": ["رياضة"]
    }

    r = requests.post(WEBHOOK_URL, json=data)
    print(f"📨 أرسلنا: {title_ar[:60]} → الرد: {r.text}")

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
