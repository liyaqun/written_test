import re
import csv
import time
import os
from playwright.sync_api import sync_playwright

# ========== 配置 ==========
BASE_URL = "https://mitadmissions.org/blogs/"
MAX_PAGE = 490   # 最后一页页码
PAGE_DELAY = 1   # 每页爬取间隔（秒）
OUTPUT_CSV = "mit_blogs_playwright.csv"


def extract_number(text):
    """从文本中提取数字，用于评论数"""
    if not text:
        return 0
    num = re.findall(r"\d+", text)
    return int(num[0]) if num else 0


def main():
    with sync_playwright() as p:
        # 启动浏览器（headless=True 可改为无头后台运行）
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        headers = ["Title", "Author", "Comment Count", "Time", "Article Content", "Images In Article"]
        crawled_titles = set()
        file_exists = os.path.exists(OUTPUT_CSV)

        if file_exists:
            with open(OUTPUT_CSV, "r", encoding="utf-8-sig") as f_read:
                reader = csv.DictReader(f_read)
                for row in reader:
                    crawled_titles.add(row["Title"])
            print(f"检测到历史记录，已爬取 {len(crawled_titles)} 篇，将自动跳过重复\n")

        with open(OUTPUT_CSV, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(headers)

            for page_num in range(1, MAX_PAGE + 1):
                try:
                    # 构造当前页URL
                    if page_num == 1:
                        url = BASE_URL
                    else:
                        url = f"{BASE_URL}page/{page_num}/"

                    # 访问列表页，等待元素加载
                    page.goto(url, wait_until="domcontentloaded")
                    page.wait_for_selector(".tease-feed-item", timeout=10000)

                    # 提取当前页所有文章卡片
                    post_cards = page.locator(".tease-feed-item").all()
                    print(f"第 {page_num}/{MAX_PAGE} 页，找到 {len(post_cards)} 篇文章")

                    # 遍历当前页每篇文章
                    for card in post_cards:
                        try:
                            title_ele = card.locator(".post-tease__title")
                            title = title_ele.inner_text().strip() if title_ele.count() > 0 else "无标题"

                            # 断点续爬判断
                            if title in crawled_titles:
                                print(f"  已爬过，跳过：{title}")
                                continue

                            title_href_ele = card.locator(".post-tease__h__link")
                            detail_url = title_href_ele.get_attribute("href") if title_href_ele.count() > 0 else ""
                            if detail_url and detail_url.startswith("/"):
                                detail_url = "https://mitadmissions.org" + detail_url

                            meta_ul = card.locator(".post-tease__meta-list")
                            if meta_ul.count() > 0:
                                author_ele = meta_ul.locator("li").nth(0)
                                author_raw = author_ele.inner_text().strip() if author_ele.count() > 0 else "未知作者"

                                res = re.search(r"by\s+(.*?)\s+'\d+", author_raw)
                                author_name = res.group(1).strip() if res else author_raw.replace("by ", "", 1).strip()

                                time_ele = meta_ul.locator("li").nth(1)
                                publish_time = time_ele.inner_text().strip() if time_ele.count() > 0 else "未知时间"
                            else:
                                author_name = "未知作者"
                                publish_time = "未知时间"

                            detail_page = browser.new_page()
                            detail_page.goto(detail_url, wait_until="domcontentloaded")
                            detail_page.wait_for_selector(".main .article-outer", timeout=10000)

                            article_content = ""
                            outer_ele = detail_page.locator(".main .article-outer")
                            if outer_ele.count() > 0:
                                try:
                                    content_container = outer_ele.locator("> *").nth(0) \
                                                      .locator("> *").nth(0) \
                                                      .locator("> *").nth(2) \
                                                      .locator("> *").nth(1)
                                    if content_container.count() > 0:
                                        p_list = content_container.locator("p").all()
                                        article_content = "\n\n".join(
                                            [p.inner_text().strip() for p in p_list if p.inner_text().strip()]
                                        )
                                except Exception:
                                    p_list = outer_ele.locator("p").all()
                                    article_content = "\n\n".join(
                                        [p.inner_text().strip() for p in p_list if p.inner_text().strip()]
                                    )

                            comment_count = 0

                            img_urls = []
                            if outer_ele.count() > 0:
                                gallery_divs = outer_ele.locator(".wysiwyg-gallery").all()
                                for gallery in gallery_divs:
                                    img_eles = gallery.locator(".wysiwyg-gallery__img-mod .flickity-lazyloaded").all()
                                    for img_ele in img_eles:
                                        src = img_ele.get_attribute("src")
                                        if src:
                                            img_urls.append(src)

                            # 关闭详情页
                            detail_page.close()

                            writer.writerow([
                                title, author_name, comment_count,
                                publish_time, article_content, "; ".join(img_urls)
                            ])
                            f.flush()

                            crawled_titles.add(title)
                            print(f"  ✓ 已写入：{title}")

                        except Exception as e:
                            print(f"  ✗ 单篇失败：{title if 'title' in dir() else '未知'}，错误：{e}")
                            try:
                                detail_page.close()
                            except:
                                pass
                            continue

                    # 每页爬完间隔
                    time.sleep(PAGE_DELAY)

                except Exception as e:
                    print(f"✗ 第 {page_num} 页爬取失败，跳过：{e}")
                    continue

        print(f"\n全部爬取完成！共累计 {len(crawled_titles)} 篇文章，已保存到 {OUTPUT_CSV}")
        browser.close()


if __name__ == "__main__":
    main()
