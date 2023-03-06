import requests
import re
import datetime
import pdb
import arxiv
from bs4 import BeautifulSoup
from googletrans import Translator
from time import strftime

# 爬虫


def crawl_arxiv(keyword, url):
    # 当前日期
    now = datetime.datetime.now()

    # 发送请求，获取响应
    response = requests.get(url)
    response.encoding = response.apparent_encoding
    html = response.text.split("\n")

    # 获取 arxiv_id
    arXiv_ids = get_arxiv_ids_from_html(html)

    # 获取 arxiv 信息
    papers = arxiv.Search(id_list=arXiv_ids)
    papers_list = []
    papers_temp = []
    for paper in papers.results():
        abstract = paper.summary
        abstract = re.sub(r'\n {2}', r'\n###', abstract)
        abstract = re.sub(r'\n', r' ', abstract)
        abstract = re.sub(r'###', r'\n', abstract)

        # 判断摘要中是否存在关键词
        for keyword in keywords:
            if keyword in abstract.lower():
                paper_info = {
                    "time": str(paper.updated.year)+"-"+str(paper.updated.month).zfill(2)+"-"+str(paper.updated.day).zfill(2),
                    "title": paper.title,
                    "link": paper.links[1],
                    "authors": ', '.join([author.name for author in paper.authors]),
                    "abstract": abstract
                }
                if paper_info["title"] not in papers_temp:
                    papers_list.append(paper_info)
                    papers_temp.append(paper_info["title"])
                    if paper_info["time"] == now.strftime("%Y-%m-%d"):
                        print(">>> Today Update: " + paper_info["title"])
    papers_list.sort(key=lambda k: (k.get('time', 0)))

    # 调用 Google Translate
    papers_list = google_translator(papers_list)

    # 保存到 markdown 文件
    save_markdown(papers_list)

# response.text 中提取 arxiv_id


def get_arxiv_ids_from_html(html):
    arxiv_ids = []
    for item in html:
        r = r'href="/pdf/(\d*.\d*)"'
        ids = re.search(r, item)
        if ids:
            arxiv_ids.append(ids.group(1))
    return arxiv_ids

# 保存成 markdown 文件


def save_markdown(papers_list):
    filename = str(datetime.date.today())+'.md'
    print("Saving: "+filename)
    f = open("2023/"+filename, "wb")
    for paper in papers_list:
        md = '## [{}]({})\n\n{}\n\n*{}*\n\n{}\n\n{}\n\n{}\n\n'.format(paper['title'], paper['title_cn'],
                                                                      paper['time'], paper['link'], paper['authors'], paper['abstract'], paper['abstract_cn'])
        f.write('{}\n'.format(md).encode())
    f.close()

# 调用 Google 翻译


def google_translator(papers_list):
    translator = Translator()
    for paper in papers_list:
        paper["title_cn"] = translator.translate(
            paper["title"], dest='zh-cn').text
        paper["abstract_cn"] = translator.translate(
            paper["abstract"], dest='zh-cn').text
    return papers_list


if __name__ == "__main__":
    # 关键字和爬取链接
    keywords = ["differential privacy", "local differential privacy"]
    url = "https://arxiv.org/list/cs.CR/pastweek?show=100"

    print("Seaching: ", keywords)
    # 主方法入口
    crawl_arxiv(keywords, url)

    print("Finished")
