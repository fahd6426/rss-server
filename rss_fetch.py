import os
import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import random

# =========================
# إعدادات من GitHub Secrets
# =========================
API_KEY = os.getenv("BLOGGER_API_KEY")
BLOG_ID = os.getenv("BLOG_ID")

# رابط الـ RSS من يلا كورة
RSS_URL = "https://www.yallakora.com/rss/latest-posts"


# =========================================
# تحميل العناوين اللي نشرناها قبل (عشان ما نكرر)
# =========================================
def load_posted_titles():
    try:
        with open("posted_titles.txt", "r", encoding="utf-8") as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()


# =========================================
# جلب الأخبار من RSS
# =========================================
def fetch_articles():
    print("🚀 بدء جلب الأخبار من خلاصة RSS ...")
    try:
        resp = requests.get(RSS_URL, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"❌ فشل في تحميل الخلاصة: {e}")
        return []

    # نقرأ الـ XML
    soup = BeautifulSoup(resp.content, "xml")
    items = soup.find_all("item")
    print(f"📡 عدد الأخبار الموجودة في الخلاصة: {len(items)}")

    articles = []
    for item in items:
        title = item.title.get_text(strip=True) if item.title else None
        description = item.description.get_text(strip=True) if item.description else ""
        # نحاول نجيب صورة لو موجودة
        image_url = ""
        enclosure = item.find("enclosure")
        if enclosure and enclosure.get("url"):
            image_url = enclosure.get("url")

        if title:
            articles.append({
                "title": title,
                "content": description,
                "image": image_url,
                "category": "رياضة"
            })

    return articles


# =========================================
# إعادة صياغة بسيطة
# =========================================
def rephrase_content(content):
    intros = [
        "نقدم لكم أبرز ما جاء في الخبر التالي: ",
        "في متابعة لأهم أخبار الكرة: ",
        "تفاصيل الخبر الرياضي التالي: "
    ]
    endings = [
        "تابعونا للمزيد من التغطيات اليومية.",
        "لمزيد من الأخبار الرياضية زوروا المدونة.",
        "نوافيكم بكل جديد أولاً بأول."
    ]
    intro = random.choice(intros)
    ending = random.choice(endings)
    return f"{intro}{content} {ending}"


# =========================================
# نشر الخبر على Blogger
# =========================================
def post_to_blogger(article, posted_titles):
    # لو العنوان مكرر لا تنشره
    if article["title"] in posted_titles:
        print(f'⏭ تم تخطي خبر مكرر: {article["title"]}')
        return

    try:
        service = build("blogger", "v3", developerKey=API_KEY)

        # نبني المحتوى
        html_parts = []

        if article["image"]:
            html_parts.append(f'<img src="{article["image"]}" style="max-width:100%;">')

        html_parts.append(f'<h2>{article["title"]}</h2>')
        html_parts.append(f'<p>{rephrase_content(article["content"])}</p>')
        html_parts.append(f'<p>التصنيف: {article["category"]}</p>')
        html_parts.append('<p>المصدر: يلا كورة</p>')

        content_html = "\n".join(html_parts)

        post_body = {
            "kind": "blogger#post",
            "title": article["title"],
            "content": content_html,
        }

        post = service.posts().insert(
            blogId=BLOG_ID,
            body=post_body,
            isDraft=False  # لو تبيها مسودة خله True
        ).execute()

        print(f'✅ تم نشر الخبر: {post["title"]}')

        # نحفظ العنوان في الملف
        posted_titles.add(article["title"])
        with open("posted_titles.txt", "a", encoding="utf-8") as f:
            f.write(article["title"] + "\n")

    except HttpError as e:
        # هنا غالباً لو طلع 403 يكون من صلاحيات Blogger أو إن الـ API key ما يكفي
        print(f"❌ خطأ أثناء النشر على Blogger: {e}")


# =========================================
# الدالة الرئيسية
# =========================================
def main():
    print("🟣 تشغيل السكربت...")
    posted_titles = load_posted_titles()
    articles = fetch_articles()

    if not articles:
        print("❌ ما فيه أخبار نستوردها من الـ RSS. تأكد من الرابط أو جرب مصدر ثاني.")
        return

    for article in articles[:5]:  # ننشر أول 5 بس عشان ما يطفح
        post_to_blogger(article, posted_titles)

    print("✅ انتهى السكربت.")


if __name__ == "__main__":
    main()
