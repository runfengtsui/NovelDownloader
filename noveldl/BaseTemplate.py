import random
import time

from fake_useragent import UserAgent

from noveldl.network.http import DirectClient
from noveldl.network.proxy import ProxyPool


class BaseTemplate:

    def __init__(self, bookurl: str, use_proxy: bool = False) -> None:
        self.bookname = ""
        self.bookurl = bookurl
        self.use_proxy = use_proxy
        self.ua = UserAgent()
        self.fetcher = ProxyPool() if use_proxy else DirectClient()
        self.total_time = 0
        if not use_proxy:
            print(f"直连模式: 使用本机 IP 访问, 请求间隔 {self.fetcher.interval:.1f}s.")

    def get_html_text(self, url: str) -> str:
        text = self.fetcher.get(url, {'User-Agent': self.ua.random})
        if not text:
            print(f'网页：{url} 爬取失败!')
        return text

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