import os
import requests
from bs4 import BeautifulSoup

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

# المصادر مع اسم المصدر
RSS_FEEDS = [
    ("https://feeds.bbci.co.uk/sport/rss.xml", "BBC Sport"),
    ("https://feeds.skynews.com/feeds/rss/sports.xml", "Sky News Sports"),
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
        return text

def clean_bullets(text_ar: str):
    # نقسم لجمل ونأخذ أول 3 جمل مختلفة
    sentences = [s.strip() for s in text_ar.replace("،", ".").split(".") if s.strip()]
    bullets = []
    for s in sentences:
        if len(bullets) >= 3:
            break
        bullets.append(f"- {s}")
    if not bullets:
        bullets = ["- تفاصيل الخبر في الأعلى."]
    return "\n".join(bullets)

def build_article(title_ar: str, body_ar: str, source_name: str) -> str:
    intro = "فيما يلي تفاصيل الخبر الرياضي المترجم:"
    bullets = clean_bullets(body_ar)
    source_line = f"\nالمصدر: {source_name}"
    article = f"""{intro}

{body_ar}

أبرز ما ورد في الخبر:
{bullets}
{source_line}
"""
    return article

def fetch_articles():
    all_articles = []
    for feed_url, source_name in RSS_FEEDS:
        try:
            resp = requests.get(feed_url, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"❌ فشل جلب {feed_url}: {e}")
            continue

        soup = BeautifulSoup(resp.content, "lxml-xml")
        for item in soup.find_all("item"):
            title = item.title.get_text(strip=True) if item.title else ""
            desc = item.description.get_text(strip=True) if item.description else ""

            image_url = ""
            enclosure = item.find("enclosure")
            if enclosure and enclosure.get("url"):
                image_url = enclosure.get("url")

            if title:
                all_articles.append({
                    "title": title,
                    "content": desc,
                    "image": image_url,
                    "source": source_name
                })
    return all_articles

def send_to_webhook(article):
    if not WEBHOOK_URL:
        print("❌ WEBHOOK_URL مفقود")
        return

    title_ar = translate_text(article["title"])
    content_ar = translate_text(article["content"])

    article_html = build_article(title_ar, content_ar, article["source"])

    payload = {
        "secret": WEBHOOK_SECRET,
        "title": title_ar,
        "content": article_html,
        "image": article["image"],
        "labels": ["رياضة"]
    }

    resp = requests.post(WEBHOOK_URL, json=payload)
    print(f"📨 أرسلنا: {title_ar[:60]} → الرد: {resp.text}")

def main():
    articles = fetch_articles()
    if not articles:
        print("❌ ما فيه أخبار")
        return

    # خبر واحد فقط
    send_to_webhook(articles[0])
    print("✅ انتهى السكربت.")

if __name__ == "__main__":
    main()
