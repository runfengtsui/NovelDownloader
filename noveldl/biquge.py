from typing import List, Optional
from urllib.parse import urljoin

from lxml import etree

from noveldl.base import BROWSER_HEADERS, BaseDownloader, BaseSearcher, SearchResult

BASE_URL = "https://www.biquge365.net"
SITE_NAME = "笔趣阁"


class Biquge(BaseDownloader):

    def __init__(self, bookurl: str, use_proxy: bool = False) -> None:
        if "newbook" not in bookurl:
            bookurl = bookurl.replace("book", "newbook")
        super().__init__(bookurl, use_proxy=use_proxy)

    def parse_book(self) -> List:
        html = self.get_html_text(self.bookurl)
        while html == "":
            html = self.get_html_text(self.bookurl)
        parse_html = etree.HTML(html)
        self.bookname = parse_html.xpath('//*[@class="right_border"]/h1/text()')[0]
        title_list = parse_html.xpath('//div[@class="border"]/ul/li/a/text()')
        url_list = parse_html.xpath('//div[@class="border"]/ul/li/a/@href')
        return list(zip(title_list, url_list))

    def parse_chapters(self, chapter_url: str) -> List:
        url = BASE_URL + chapter_url
        html = self.get_html_text(url)
        while html == "":
            html = self.get_html_text(url)
        parse_html = etree.HTML(html)
        content = parse_html.xpath('//*[@id="txt"]/text()')
        return content[1:]


class BiqugeSearcher(BaseSearcher):
    """笔趣阁: 搜索接口为表单 POST, 结果直接渲染在 HTML 中."""

    key = "biquge"
    site = SITE_NAME
    search_url = BASE_URL + "/s.php"

    def search(self, keyword: str, limit: Optional[int] = None,
               by: str = "title") -> List[SearchResult]:
        headers = dict(BROWSER_HEADERS)
        headers.update({
            "Referer": BASE_URL + "/",
            "Origin": BASE_URL,
        })
        html = self.post_html_text(self.search_url, {
            "type": "author" if by == "author" else "articlename",
            "s": keyword,
            "submit": "",
        }, headers)
        if not html:
            raise RuntimeError("搜索请求失败")
        return self._parse(html, limit)

    def _parse(self, html: str, limit: Optional[int] = None) -> List[SearchResult]:
        tree = etree.HTML(html)
        results = []
        for item in tree.xpath('//ul[contains(@class, "search")]/li'):
            link = item.xpath('.//span[contains(@class, "name")]/a[@href]')
            if not link:
                continue
            anchor = link[0]
            title = (anchor.text or "").strip() or (anchor.get("title") or "").strip()
            href = (anchor.get("href") or "").strip()
            if not title or not href:
                continue
            results.append(SearchResult(
                site=self.site,
                title=title,
                author=self._text(item, './/span[contains(@class, "zuo")]/a'),
                url=urljoin(BASE_URL + "/", href),
                category=self._text(item, './/span[contains(@class, "lei")]/a').strip("[]"),
                latest_chapter=self._text(item, './/span[contains(@class, "jie")]/a'),
                updated=self._text(item, './/span[contains(@class, "time")]'),
            ))
            if limit is not None and len(results) >= limit:
                break
        return results