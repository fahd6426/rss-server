import os
import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import random

# =========================
# المفاتيح من GitHub Secrets
# =========================
API_KEY = os.getenv("BLOGGER_API_KEY")
BLOG_ID = os.getenv("BLOG_ID")

# ✅ مصادر RSS مفتوحة
RSS_FEEDS = [
    "https://www.kooora.com/rss/default.aspx",     # كووورة
    "https://www.espn.com/espn/rss/news",           # ESPN أخبار عامة
]

# =========================
# تحميل العناوين القديمة
# =========================
def load_posted_titles():
    try:
        with open("posted_titles.txt", "r", encoding="utf-8") as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()

# =========================
# جلب الأخبار من كل المصادر
# =========================
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

        # نستخدم lxml-xml لأننا ثبتناه في الـ workflow
        soup = BeautifulSoup(resp.content, "lxml-xml")
        items = soup.find_all("item")
        print(f"➡️ وجدنا {len(items)} خبر في هذا المصدر")

        for item in items:
            title = item.title.get_text(strip=True) if item.title else None
            description = item.description.get_text(strip=True) if item.description else ""
            # صورة لو فيه
            image_url = ""
            enclosure = item.find("enclosure")
            if enclosure and enclosure.get("url"):
                image_url = enclosure.get("url")

            if title:
                all_articles.append({
                    "title": title,
                    "content": description,
                    "image": image_url,
                    "category": "رياضة"
                })

    print(f"📦 إجمالي الأخبار اللي جمعناها من كل المصادر: {len(all_articles)}")
    return all_articles

# =========================
# إعادة صياغة بسيطة
# =========================
def rephrase_content(content):
    intros = [
        "نقدم لكم تفاصيل الخبر التالي: ",
        "في متابعة لآخر المستجدات الرياضية: ",
        "إليكم أبرز ما ورد: "
    ]
    endings = [
        "تابعونا للمزيد من الأخبار اليومية.",
        "زوروا المدونة للمزيد.",
        "نوافيكم بكل جديد."
    ]
    return f"{random.choice(intros)}{content} {random.choice(endings)}"

# =========================
# نشر على Blogger
# =========================
def post_to_blogger(article, posted_titles):
    # لو العنوان مكرر لا تنشر
    if article["title"] in posted_titles:
        print(f'⏭ تخطّي خبر مكرر: {article["title"]}')
        return

    try:
        service = build("blogger", "v3", developerKey=API_KEY)

        parts = []
        if article["image"]:
            parts.append(f'<img src="{article["image"]}" style="max-width:100%;">')
        parts.append(f'<h2>{article["title"]}</h2>')
        parts.append(f'<p>{rephrase_content(article["content"])}</p>')
        parts.append(f'<p>التصنيف: {article["category"]}</p>')
        parts.append('<p>المصدر: مصادر رياضية</p>')

        content_html = "\n".join(parts)

        post_body = {
            "kind": "blogger#post",
            "title": article["title"],
            "content": content_html,
        }

        post = service.posts().insert(
            blogId=BLOG_ID,
            body=post_body,
            isDraft=False
        ).execute()

        print(f'✅ تم نشر الخبر: {post["title"]}')

        # نحفظه في الملف
        posted_titles.add(article["title"])
        with open("posted_titles.txt", "a", encoding="utf-8") as f:
            f.write(article["title"] + "\n")

    except HttpError as e:
        # هنا لو طلع 403 خلاص نعرف إن المفتاح ما يسمح بالنشر
        print(f"❌ خطأ أثناء النشر على Blogger: {e}")

# =========================
# الدالة الرئيسية
# =========================
def main():
    print("🟣 تشغيل السكربت...")
    posted_titles = load_posted_titles()
    articles = fetch_articles()

    if not articles:
        print("❌ ما قدرنا نجيب أخبار من أي مصدر. جرب رابط RSS مختلف.")
        return

    # نشيل التكرار بالعنوان
    unique_articles = []
    seen_titles = set()
    for art in articles:
        if art["title"] not in seen_titles:
            unique_articles.append(art)
            seen_titles.add(art["title"])

    # ننشر أول 5 بس
    for article in unique_articles[:5]:
        post_to_blogger(article, posted_titles)

    print("✅ انتهى السكربت.")

if __name__ == "__main__":
    main()
