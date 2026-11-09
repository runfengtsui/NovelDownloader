"""终端搜索: 在已支持的小说网站中按书名/作者检索作品."""

import json
import math
from dataclasses import asdict, dataclass
from typing import List, Optional
from urllib.parse import quote, urljoin

from lxml import etree

from noveldl.base import FetcherBase
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
    key = ""
    site = ""

    def search(self, keyword: str, limit: Optional[int] = None,
               by: str = "title") -> List[SearchResult]:
        raise NotImplementedError

    @staticmethod
    def _text(node, path: str) -> str:
        texts = node.xpath(f'{path}/text()')
        return texts[0].strip() if texts else ""


class BiqugeSearcher(BaseSearcher):
    """笔趣阁: 搜索接口为表单 POST, 结果直接渲染在 HTML 中."""

    key = "biquge"
    site = "笔趣阁"
    base_url = "https://www.biquge365.net"
    search_url = base_url + "/s.php"

    def search(self, keyword: str, limit: Optional[int] = None,
               by: str = "title") -> List[SearchResult]:
        headers = dict(BROWSER_HEADERS)
        headers.update({
            "Referer": self.base_url + "/",
            "Origin": self.base_url,
        })
        html = self.post_html_text(self.search_url, {
            "type": "author" if by == "author" else "articlename",
            "s": keyword,
            "submit": "",
        }, headers)
        if not html:
            raise RuntimeError("搜索请求失败")
        return self._parse(html, limit)

    def _parse(self, html: str, limit: Optional[int]) -> List[SearchResult]:
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
                url=urljoin(self.base_url + "/", href),
                category=self._text(item, './/span[contains(@class, "lei")]/a').strip("[]"),
                latest_chapter=self._text(item, './/span[contains(@class, "jie")]/a'),
                updated=self._text(item, './/span[contains(@class, "time")]'),
            ))
            if limit is not None and len(results) >= limit:
                break
        return results


class WashaiSearcher(BaseSearcher):
    """书海阁: 优先调用 JSON 搜索接口, 失败时回退解析服务端渲染页面."""

    key = "washai"
    site = "书海阁"
    base_url = "https://book.washai.net"
    api_url = base_url + "/book/searchByPage"
    page_size = 20

    def search(self, keyword: str, limit: Optional[int] = None,
               by: str = "title") -> List[SearchResult]:
        index_url = (f"{self.base_url}/book/bookclass.html"
                     f"?k={quote(keyword)}")
        token = self.get_cookie("novel_browser_token")
        html = ""
        if not token:
            html = self.get_html_text(index_url, dict(BROWSER_HEADERS))
            token = self.get_cookie("novel_browser_token")
        if token:
            try:
                return self._search_api(keyword, token, limit)
            except Exception as exc:
                print(f"书海阁搜索接口不可用, 改为解析网页: {exc}")
        if not html:
            html = self.get_html_text(index_url, dict(BROWSER_HEADERS))
        if not html:
            raise RuntimeError("搜索请求失败")
        return self._parse_index(html, limit)

    def _search_api(self, keyword: str, token: str,
                    limit: Optional[int]) -> List[SearchResult]:
        headers = dict(BROWSER_HEADERS)
        headers.update({
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "X-Browser-Token": token,
            "Referer": f"{self.base_url}/book/bookclass.html?k={quote(keyword)}",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
        })
        results: List[SearchResult] = []
        page, total_pages = 1, 1
        while page <= total_pages:
            url = (f"{self.api_url}?curr={page}&limit={self.page_size}"
                   f"&keyword={quote(keyword)}")
            text = self.fetcher.get(url, headers)
            if not text:
                raise RuntimeError(f"第 {page} 页请求失败")
            payload = json.loads(text)
            if payload.get("code") != 200:
                raise RuntimeError(payload.get("msg") or f"接口返回 {payload.get('code')}")
            data = payload.get("data") or {}
            rows = data.get("list") or []
            total = int(data.get("total") or 0)
            size = int(data.get("pageSize") or self.page_size) or self.page_size
            total_pages = max(1, math.ceil(total / size))
            for row in rows:
                result = self._from_api_row(row)
                if result is None:
                    continue
                results.append(result)
                if limit is not None and len(results) >= limit:
                    return results
            if not rows:
                break
            page += 1
        return results

    def _from_api_row(self, row: dict) -> Optional[SearchResult]:
        book_id = str(row.get("id") or "").strip()
        title = str(row.get("bookName") or "").strip()
        if not book_id or not title:
            return None
        status = "已完结" if int(row.get("bookStatus") or 0) == 1 else "连载中"
        word_count = int(row.get("wordCount") or 0)
        return SearchResult(
            site=self.site,
            title=title,
            author=str(row.get("authorName") or "").strip(),
            url=f"{self.base_url}/book/{book_id}.html",
            category=str(row.get("catName") or "").strip(),
            status=status,
            word_count=f"{word_count / 10000:.2f}万字" if word_count else "",
            latest_chapter=str(row.get("lastIndexName") or "").strip(),
            updated=str(row.get("lastIndexUpdateTime") or "").strip(),
            description=str(row.get("bookDesc") or "").strip(),
        )

    def _parse_index(self, html: str, limit: Optional[int]) -> List[SearchResult]:
        tree = etree.HTML(html)
        results = []
        for card in tree.xpath('//article[contains(@class, "classBookCard")]'):
            link = card.xpath('.//h3[contains(@class, "classBookTitle")]/a[@href]')
            if not link:
                continue
            anchor = link[0]
            title = (anchor.text or "").strip() or (anchor.get("title") or "").strip()
            href = (anchor.get("href") or "").strip()
            if not title or not href:
                continue
            status, _, word_count = self._text(
                card, './/p[contains(@class, "classBookMeta")]').partition("·")
            results.append(SearchResult(
                site=self.site,
                title=title,
                author=self._text(card, './/p[contains(@class, "classBookAuthor")]/a'),
                url=urljoin(self.base_url + "/", href),
                category=self._text(card, './/a[contains(@class, "classCoverCat")]'),
                status=status.strip(),
                word_count=word_count.strip(),
                latest_chapter=self._text(card, './/p[contains(@class, "classBookChapter")]/a'),
                updated=self._text(card, './/p[contains(@class, "classBookTime")]'),
                description=self._text(card, './/p[contains(@class, "classBookDesc")]'),
            ))
            if limit is not None and len(results) >= limit:
                break
        return results


SEARCHERS = {
    BiqugeSearcher.key: BiqugeSearcher,
    WashaiSearcher.key: WashaiSearcher,
}


def search_all(keyword: str, sites: Optional[List[str]] = None,
               use_proxy: bool = False, limit: Optional[int] = None,
               by: str = "title"):
    """依次搜索各站点, 返回 (结果列表, 错误列表[(站点名, 错误信息)])."""
    if not sites or "all" in sites:
        selected = list(SEARCHERS)
    else:
        selected = [key for key in SEARCHERS if key in sites]

    shared_fetcher = None
    if len(selected) > 1:
        # 代理池初始化较慢, 多站搜索时共用一个请求器.
        shared_fetcher = ProxyPool() if use_proxy else DirectClient()

    results: List[SearchResult] = []
    errors = []
    for key in selected:
        searcher = SEARCHERS[key](use_proxy=use_proxy, fetcher=shared_fetcher)
        try:
            results.extend(searcher.search(keyword, limit=limit, by=by))
        except Exception as exc:
            errors.append((searcher.site, str(exc)))
    return results, errors
