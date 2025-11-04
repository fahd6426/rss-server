import os
import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import random

API_KEY = os.getenv("BLOGGER_API_KEY")
BLOG_ID = os.getenv("BLOG_ID")

URL = "https://www.yallakora.com"

def load_posted_titles():
    try:
        with open("posted_titles.txt", "r", encoding="utf-8") as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()

def fetch_articles():
    # بعض المواقع ما تعطيك المحتوى إلا لو جت من متصفح
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ فشل جلب الصفحة: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    articles = []
    # هنا انت كنت حاط class اسمه news-block، لو الموقع غير شكله ما راح يرجع شي
    news_items = soup.find_all("div", class_="news-block")

    print(f"ℹ️ الأخبار اللي لقيتها في الصفحة: {len(news_items)}")

    for item in news_items:
        title_tag = item.find("h2")
        img_tag = item.find("img")
        summary_tag = item.find("p")
        category_tag = item.find("span", class_="category")

        if title_tag and img_tag and summary_tag:
            article = {
                "title": title_tag.get_text(strip=True),
                "image": img_tag.get("src"),
                "content": summary_tag.get_text(strip=True),
                "category": category_tag.get_text(strip=True) if category_tag else "رياضة",
            }
            articles.append(article)

    return articles

def rephrase_content(content):
    intros = [
        "نقدم لكم أبرز الأحداث: ",
        "تقرير اليوم عن الخبر التالي: ",
        "في متابعة لأهم الأخبار: "
    ]
    conclusions = [
        "تابعونا لمزيد من التفاصيل اليومية.",
        "هذا كان ملخص الخبر، لمعرفة المزيد تابعوا موقعنا.",
        "نستمر بتغطية كل جديد في عالم الرياضة."
    ]
    intro = random.choice(intros)
    conclusion = random.choice(conclusions)
    return f"{intro}{content} {conclusion}"

def post_to_blogger(article, posted_titles):
    if article["title"] in posted_titles:
        print(f'⏭ تخطي مكرر: {article["title"]}')
        return

    try:
        service = build('blogger', 'v3', developerKey=API_KEY)

        content = f'''
        <img src="{article["image"]}" style="max-width:100%;">
        <h2>{article["title"]}</h2>
        <p>{rephrase_content(article["content"])}</p>
        <p>تصنيف: {article["category"]}</p>
        <p>المصدر: YallaKora</p>
        '''

        post_body = {
            "kind": "blogger#post",
            "title": article["title"],
            "content": content
        }

        post = service.posts().insert(blogId=BLOG_ID, body=post_body, isDraft=False).execute()
        print(f'✅ تم نشر الخبر: {post["title"]}')

        posted_titles.add(article["title"])
        with open("posted_titles.txt", "a", encoding="utf-8") as f:
            f.write(article["title"] + "\n")

    except HttpError as e:
        print(f'❌ خطأ أثناء النشر على Blogger: {e}')

def main():
    print("🚀 بدء تشغيل سكربت جلب الأخبار...")
    posted_titles = load_posted_titles()
    articles = fetch_articles()

    if not articles:
        print("❌ ما تم العثور على أي أخبار من الموقع. تأكد من الـ selector أو من أن الموقع ما يحجب البوت.")
        return

    for article in articles:
        post_to_blogger(article, posted_titles)

    print("✅ انتهى السكربت.")

if __name__ == "__main__":
    main()
