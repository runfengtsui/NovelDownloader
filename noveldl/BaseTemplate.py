import requests
from fake_useragent import UserAgent
from freeproxy import freeproxy
import time
import random


class BaseTemplate:

    def __init__(self, bookurl: str) -> None:
        self.bookname = ""
        self.bookurl = bookurl
        proxy_sources = ['proxylistplus', 'kuaidaili']
        self.fp_client = freeproxy.FreeProxy(proxy_sources=proxy_sources)
        self.total_time = 0
        
    def get_html_text(self, url: str) -> str:
        try:
            ua = UserAgent()
            proxy = self.fp_client.getrandomproxy()
            r = requests.get(url, headers={'User-Agent': ua.random}, proxies=proxy)
            r.raise_for_status()
            r.encoding = r.apparent_encoding
            return r.text
        except:
            print(f'网页：{url} 爬取失败!')
            return ""
    
    def save_chapter(self, chapter_name, chapter_content) -> None:
        with open(f"{self.bookname}.txt", 'a', encoding='utf-8') as f:
            f.write(chapter_name + '\n')
            for sentence in chapter_content:
                f.write(sentence + '\n')
            f.write('\n' * 2)

    def crawl(self) -> None:
        chapters_list = self.parse_book()
        for chapter_name, url in chapters_list:
            time.sleep(random.random())
            chapter_content = self.parse_chapters(url)
            self.save_chapter(chapter_name, chapter_content)
            print(f"{chapter_name} 保存成功!")

