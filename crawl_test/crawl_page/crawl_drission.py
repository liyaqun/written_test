import re
import csv
import time
import os  
from DrissionPage import ChromiumPage

# ========== 配置 ==========
BASE_URL = "https://mitadmissions.org/blogs/"
MAX_PAGE = 490   # 最后一页页码
PAGE_DELAY = 1  # 每页爬取间隔（秒）
OUTPUT_CSV = "mit_blogs_all_pages.csv"

def extract_number(text):
    """从文本中提取数字，用于评论数"""
    if not text:
        return 0
    num = re.findall(r"\d+", text)
    return int(num[0]) if num else 0

def main():
    page = ChromiumPage()
    headers = ["Title", "Author", "Comment Count", "Time", "Article Content", "Images In Article"]

    crawled_titles = set()
    file_exists = os.path.exists(OUTPUT_CSV)

    # 读取已有的爬取记录
    if file_exists:
        with open(OUTPUT_CSV, "r", encoding="utf-8-sig") as f_read:
            reader = csv.DictReader(f_read)
            for row in reader:
                crawled_titles.add(row["Title"])
        print(f"检测到历史记录，已爬取 {len(crawled_titles)} 篇，将自动跳过重复\n")

    # 提前打开CSV，全程复用
    # 新文件写表头；旧文件追加写入，不重复写表头
    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(headers)

        # 分页循环
        for page_num in range(1, MAX_PAGE + 1):
            try:
                # 构造当前页URL
                if page_num == 1:
                    url = BASE_URL
                else:
                    url = f"{BASE_URL}page/{page_num}/"

                # 访问列表页
                page.get(url)
                page.wait.load_start()

                # 提取当前页所有文章卡片
                post_cards = page.eles(".tease-feed-item")
                print(f"第 {page_num}/{MAX_PAGE} 页，找到 {len(post_cards)} 篇文章")

                # 遍历当前页每篇文章
                for card in post_cards:
                    try:
                        # 列表页基础信息
                        title_ele = card.ele(".post-tease__title")
                        title = title_ele.text.strip() if title_ele else "无标题"

                        # 断点续爬判断 
                        if title in crawled_titles:
                            print(f"  已爬过，跳过：{title}")
                            continue

                        title_href_ele = card.ele(".post-tease__h__link")
                        detail_url = title_href_ele.attr("href") if title_href_ele else ""
                        if detail_url and detail_url.startswith("/"):
                            detail_url = "https://mitadmissions.org" + detail_url

                        meta_ul = card.ele(".post-tease__meta-list")
                        # print(meta_ul)
                        if meta_ul:
                            # 作者
                            author_a =meta_ul.child(index=1) # meta_ul.ele(".post-tease__meta-item--author")
                            # print(author_a)
                            author = author_a.text.strip() if author_a else "未知作者"
                            res = re.search(r"by\s+(.*?)\s+'\d+", author)
                            if res:
                                author_name = res.group(1).strip()
                            else:
                                author_name = author
                            # print(author_name) # Taylor L.
                            # 时间
                            time_li =meta_ul.child(index=2) # meta_ul.ele(".tease__meta-item--date")
                            # print(time_li)
                            publish_time = time_li.text.strip() if time_li else "未知时间"
                        else:
                            author = "未知作者"
                            publish_time = "未知时间"


                        # 打开详情页
                        tab = page.new_tab(detail_url)
                        tab.wait.load_start()

                        # 提取正文（只取p标签，过滤图注、引用等）
                        # print("tab", tab)
                        content_ele = tab.ele(".main")
                        # print("content_ele", content_ele)
                        content_ele = content_ele.ele(".article-outer")
                        # print("content_ele", content_ele)
                        content_ele = content_ele.child().child().child(index=3)
                        content_ele =content_ele.child(index=2)


                        # print("content_ele", content_ele)
                        if content_ele:
                            p_list = content_ele.eles("p")
                            article_content = "\n\n".join([p.text.strip() for p in p_list if p.text.strip()])
                        else:
                            article_content = ""

                        # 评论数
                        comment_count = 0
                        # comment_ele = tab.ele(".comments-count", timeout=2)
                        # comment_count = extract_number(comment_ele.text) if comment_ele else 0


                        # 提取文章内图片
                        # print("content_ele", content_ele)
                        img_urls= []
                        if content_ele:
                            div_list = content_ele.eles(".wysiwyg-gallery") # 
                            # print("div_list", div_list)
                            if div_list:
                                for  i in range(len(div_list)):
                                    img_element=div_list[i].ele(".wysiwyg-gallery__img-mod").ele(".flickity-lazyloaded")
                                    img_urls.append(img_element.attr("src") if img_element else "" )
                            # print(img_urls)

                            
                            
                        
                        tab.close()

                        writer.writerow([
                            title, author_name, comment_count,
                            publish_time, article_content, img_urls
                        ])
                        f.flush()  # 强制刷入磁盘，程序崩溃也不丢数据
                        crawled_titles.add(title)  # 标记为已爬

                        print(f"  ✓ 已写入：{title}")

                    except Exception as e:
                        print(f"  ✗ 单篇失败：{title if 'title' in dir() else '未知'}，错误：{e}")
                        continue

                # 每页爬完间隔
                time.sleep(PAGE_DELAY)

            except Exception as e:
                print(f"✗ 第 {page_num} 页爬取失败，跳过：{e}")
                continue

    print(f"\n全部爬取完成！共累计 {len(crawled_titles)} 篇文章，已保存到 {OUTPUT_CSV}")
    page.quit()

if __name__ == "__main__":
    main()



# import re
# import csv
# import time
# from DrissionPage import ChromiumPage

# # ========== 新增：分页配置 ==========
# BASE_URL = "https://mitadmissions.org/blogs/"
# MAX_PAGE = 1  # 最后一页页码
# PAGE_DELAY = 1  # 每页爬取间隔（秒），防止请求过快被限制
# OUTPUT_CSV = "mit_blogs_all_pages.csv"
# # ==================================

# def extract_number(text):
#     """从文本中提取数字，用于评论数"""
#     if not text:
#         return 0
#     num = re.findall(r"\d+", text)
#     return int(num[0]) if num else 0

# def main():
#     page = ChromiumPage()
#     headers = ["Title", "Author", "Comment Count", "Time", "Article Content", "Images In Article"]
#     all_result = []  # 存储所有页的所有文章

#     # ========== 新增：分页循环 ==========
#     for page_num in range(1, MAX_PAGE + 1):
#         try:
#             # 构造当前页URL
#             if page_num == 1:
#                 url = BASE_URL
#             else:
#                 url = f"{BASE_URL}page/{page_num}/"

#             # 访问列表页
#             page.get(url)
#             page.wait.load_start()

#             # 提取当前页所有文章卡片
#             post_cards = page.eles(".tease-feed-item")
#             print(f"第 {page_num}/{MAX_PAGE} 页，找到 {len(post_cards)} 篇文章")

#             # 遍历当前页每篇文章
#             for card in post_cards:
#                 try:
#                     # 列表页基础信息
#                     title_ele = card.ele(".post-tease__title")
#                     # 标题：Title
#                     title = title_ele.text.strip()
#                     title_href_ele=card.ele(".post-tease__h__link")
#                     detail_url = title_href_ele.attr("href")
#                     if detail_url.startswith("/"):
#                         detail_url ="https://mitadmissions.org" + detail_url

#                     # 作者：Author
#                     author_ele = card.ele(".post-tease__meta-item.post-tease__meta-item--author a")
#                     author = author_ele.text.strip() if author_ele else ""
#                     # 时间：Time
#                     time_ele = card.ele(".post-tease__meta-item.tease__meta-item--date")
#                     publish_time = time_ele.text.strip() if time_ele else ""

#                     # 打开详情页
#                     tab = page.new_tab(detail_url)
#                     tab.wait.load_start()

#                     # 提取正文
#                     # 文章内容： Article Content
#                     # content_ele = tab.ele(".article__body")
#                     # article_content = content_ele.text.strip() if content_ele else ""
#                     content_ele = tab.ele(".article__body")
#                     if content_ele:
#                         # 只取正文p标签，过滤掉图注、引用等
#                         p_list = content_ele.eles("p")
#                         article_content = "\n\n".join([p.text.strip() for p in p_list if p.text.strip()])
#                     else:
#                         article_content = ""

#                     # 提取评论数
#                     # comment_ele = tab.ele(".comments-count", timeout=2)
#                     # comment_count = extract_number(comment_ele.text) if comment_ele else 0
#                     comment_count=0

#                     # 提取文章内图片
#                     if content_ele:
#                         # 拿到正文容器里所有 img 标签
#                         img_eles = content_ele.eles("img")
#                         img_links = []
                        
#                         for img in img_eles:
#                             # 优先取懒加载真实大图地址，没有再回退到 src
#                             img_url = img.attr("data-flickity-lazyload-src") or img.attr("src")
                            
#                             # 过滤无效内容：空链接、base64小图标、emoji表情图、装饰箭头
#                             if (not img_url 
#                                 or img_url.startswith("data:") 
#                                 or "emoji" in img_url
#                                 or "icon" in img_url):
#                                 continue
                                
#                             # 补全相对路径为绝对可访问链接
#                             if img_url.startswith("/"):
#                                 img_url = "https://mitadmissions.org" + img_url
                                
#                             img_links.append(img_url)
                        
#                         # 去重：同一张图可能有多个尺寸副本
#                         img_links = list(dict.fromkeys(img_links))
                        
#                         # 按题目要求用分号分隔，存入 CSV
#                         images_in_article = "; ".join(img_links)
#                     else:
#                         images_in_article = ""

#                     # 加入总结果
#                     all_result.append([
#                         title, author, comment_count,
#                         publish_time, article_content, images_in_article
#                     ])

#                     tab.close()

#                 except Exception as e:
#                     print(f"  单篇爬取失败：{title if 'title' in dir() else '未知'}，错误：{e}")
#                     continue

#             # 每页爬完间隔，避免请求过快
#             time.sleep(PAGE_DELAY)

#         except Exception as e:
#             print(f"第 {page_num} 页爬取失败，跳过：{e}")
#             continue
#     # ==================================

#     # 统一写入CSV
#     with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
#         writer = csv.writer(f)
#         writer.writerow(headers)
#         writer.writerows(all_result)

#     print(f"\n全部爬取完成！共 {len(all_result)} 篇文章，已保存到 {OUTPUT_CSV}")
#     page.quit()

# if __name__ == "__main__":
#     main()
