"""公共基类: 请求、下载与搜索."""

import random
import time
from dataclasses import asdict, dataclass
from typing import List, Optional

from fake_useragent import UserAgent

from noveldl.network.http import DirectClient
from noveldl.network.proxy import ProxyPool

# 书海阁会依据浏览器特征下发 novel_browser_token, 普通 UA 会被拒绝.
BROWSER_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
              "image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
    "Upgrade-Insecure-Requests": "1",
}


class FetcherBase:
    """请求基类: 选择直连或代理, 统一提供 GET/POST 与 Cookie 访问."""

    def __init__(self, use_proxy: bool = False, fetcher=None, ua=None) -> None:
        self.use_proxy = use_proxy
        self.ua = ua or UserAgent()
        self.fetcher = fetcher or (ProxyPool() if use_proxy else DirectClient())
        if fetcher is None and not use_proxy:
            print(f"直连模式: 使用本机 IP 访问, 请求间隔 {self.fetcher.interval:.1f}s.")

    def get_html_text(self, url: str, headers: dict = None) -> str:
        text = self.fetcher.get(url, headers or {'User-Agent': self.ua.random})
        if not text:
            print(f'网页：{url} 爬取失败!')
        return text

    def post_html_text(self, url: str, data: dict, headers: dict = None) -> str:
        text = self.fetcher.post(url, headers or {'User-Agent': self.ua.random}, data)
        if not text:
            print(f'网页：{url} 爬取失败!')
        return text

    def get_cookie(self, name: str) -> str:
        return self.fetcher.cookie(name)


class BaseDownloader(FetcherBase):
    """下载模板: 保存章节并串行抓取全书."""

    def __init__(self, bookurl: str, use_proxy: bool = False) -> None:
        super().__init__(use_proxy)
        self.bookname = ""
        self.bookurl = bookurl

    def parse_book(self) -> List:
        """返回 [(章节名, 章节 URL), ...]."""
        raise NotImplementedError

    def parse_chapters(self, chapter_url: str) -> List:
        """返回单章正文段落列表."""
        raise NotImplementedError

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


@dataclass
class SearchResult:
    site: str
    title: str
    author: str
    url: str
    category: str = ""
    status: str = ""
    word_count: str = ""
    latest_chapter: str = ""
    updated: str = ""
    description: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class BaseSearcher(FetcherBase):
    """搜索模板: 子类实现 search(), 返回统一的 SearchResult 列表."""

    key = ""
    site = ""

    def search(self, keyword: str, limit: Optional[int] = None,
               by: str = "title") -> List[SearchResult]:
        raise NotImplementedError

    @staticmethod
    def _text(node, path: str) -> str:
        texts = node.xpath(f'{path}/text()')
        return texts[0].strip() if texts else ""