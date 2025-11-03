import os
import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import random

API_KEY = os.getenv("BLOGGER_API_KEY")
BLOG_ID = os.getenv("BLOG_ID")

URL = "https://www.yallakora.com"

# تحميل العناوين المنشورة مسبقًا لمنع التكرار
def load_posted_titles():
    try:
        with open("posted_titles.txt", "r", encoding="utf-8") as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()

# جلب الأخبار من الموقع
def fetch_articles():
    response = requests.get(URL)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    articles = []
    news_items = soup.find_all("div", class_="news-block")  # مثال، عدّل حسب الموقع
    for item in news_items:
        title_tag = item.find("h2")
        img_tag = item.find("img")
        summary_tag = item.find("p")
        category_tag = item.find("span", class_="category")

        if title_tag and img_tag and summary_tag and category_tag:
            article = {
                "title": title_tag.get_text(strip=True),
                "image": img_tag.get("src"),
                "content": summary_tag.get_text(strip=True),
                "category": category_tag.get_text(strip=True),
            }
            articles.append(article)
    return articles

# إعادة صياغة الخبر بإضافة جمل متنوعة
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

# نشر الخبر على Blogger
def post_to_blogger(article, posted_titles):
    if article["title"] in posted_titles:
        print(f'Skipping duplicate: {article["title"]}')
        return

    try:
        service = build('blogger', 'v3', developerKey=API_KEY)
        content = f'''
        <img src="{article["image"]}" style="max-width:100%;">
        <h2>{article["title"]}</h2>
        <p>{rephrase_content(article["content"])}</p>
        <ul>
            <li>تصنيف: {article["category"]}</li>
            <li>مصدر الخبر: YallaKora</li>
        </ul>
        <p>تابعنا للحصول على المزيد من الأخبار اليومية.</p>
        '''

        post_body = {
            "kind": "blogger#post",
            "title": article["title"],
            "content": content
        }
        post = service.posts().insert(blogId=BLOG_ID, body=post_body, isDraft=False).execute()
        print(f'Published: {post["title"]}')

        # حفظ العنوان لمنع التكرار
        posted_titles.add(article["title"])
        with open("posted_titles.txt", "a", encoding="utf-8") as f:
            f.write(article["title"] + "\n")

    except HttpError as e:
        print(f'Error publishing: {e}')

def main():
    posted_titles = load_posted_titles()
    articles = fetch_articles()
    for article in articles:
        post_to_blogger(article, posted_titles)

if __name__ == "__main__":
    main()
