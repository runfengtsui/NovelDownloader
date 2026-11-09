import json
import math
import random
import re
import time
from typing import List, Optional
from urllib.parse import quote, urljoin

from lxml import etree

from noveldl.base import BROWSER_HEADERS, BaseDownloader, BaseSearcher, SearchResult

BASE_URL = "https://book.washai.net"
SITE_NAME = "书海阁"


class Washai(BaseDownloader):
    """书海阁 (https://book.washai.net) 免费小说爬虫.

    书海阁的章节目录按每页 100 章分页, 正文由服务端直接渲染 (SSR), 无需执行
    JavaScript. 请求通过公共请求层完成, 以降低单一 IP 被限流的风险.
    """

    retry_rounds = 3

    def __init__(self, bookurl: str, use_proxy: bool = False) -> None:
        match = re.search(r"/book/(?:indexList-|indexList/)?(\d+)", bookurl)
        if match is None:
            raise ValueError(f"无效的书海阁网址: {bookurl}")
        self.book_id = match.group(1)
        # 统一入口: 无论传入详情页还是任意一页目录, 都从第一页目录开始解析.
        super().__init__(f"{BASE_URL}/book/indexList-{self.book_id}.html", use_proxy=use_proxy)

    def _page_url(self, page: int) -> str:
        return f"{BASE_URL}/book/indexList/{self.book_id}/{page}.html"

    @staticmethod
    def _parse_index_page(html: str, page_url: str) -> List:
        parse_html = etree.HTML(html)
        chapters = []
        for link in parse_html.xpath('//ul[@id="bookIndexList"]/li/a[@href]'):
            # 只取 <a> 的直接文本, 从而排除 "<i>[免费]</i>" 之类的标记.
            title = (link.text or "").strip()
            href = link.get("href").strip()
            if not title or not href:
                continue
            chapters.append((title, urljoin(page_url, href)))
        return chapters

    def _total_pages(self, html: str) -> int:
        parse_html = etree.HTML(html)
        pager = parse_html.xpath('//div[@id="indexPager"]')
        if pager:
            total = (pager[0].get("data-total") or "").strip()
            page_size = (pager[0].get("data-page-size") or "").strip()
            if total.isdigit() and page_size.isdigit() and int(page_size) > 0:
                return max(1, math.ceil(int(total) / int(page_size)))
        # 兜底: 从页码信息 (如 "第1/5页") 中解析总页数.
        info = parse_html.xpath('string(//div[@id="indexPager"]//span[@class="pgInfo"])')
        matched = re.search(r"/(\d+)\s*页", info)
        return int(matched.group(1)) if matched else 1

    def _fetch_required(self, url: str, what: str, retries: int = 3) -> str:
        """代理模式下单次请求可能失败, 对目录页做有限重试, 不做直连回退."""
        for attempt in range(1, retries + 1):
            html = self.get_html_text(url)
            if html:
                return html
            if attempt < retries:
                print(f"{what}获取失败, 第 {attempt} 次重试...")
        raise RuntimeError(f"无法获取{what}: {url}")

    def parse_book(self) -> List:
        html = self._fetch_required(self.bookurl, "目录页")

        parse_html = etree.HTML(html)
        self.bookname = parse_html.xpath('string(//h1[@id="bookName"])').strip()
        if not self.bookname:
            raise RuntimeError(f"目录页中未找到书名: {self.bookurl}")

        chapters = self._parse_index_page(html, self.bookurl)
        total_pages = self._total_pages(html)
        for page in range(2, total_pages + 1):
            page_url = self._page_url(page)
            page_html = self._fetch_required(page_url, f"目录第 {page} 页")
            chapters.extend(self._parse_index_page(page_html, page_url))
            print(f"目录第 {page}/{total_pages} 页解析完成, 累计 {len(chapters)} 章.")

        # 以章节 URL 去重, 避免目录分页边界重复收录.
        unique_chapters, seen = [], set()
        for title, url in chapters:
            if url in seen:
                continue
            seen.add(url)
            unique_chapters.append((title, url))
        return unique_chapters

    def parse_chapters(self, chapter_url: str) -> Optional[List]:
        """返回 None 表示抓取失败 (可重试), 返回空列表表示页面无正文 (如 VIP 章节)."""
        html = self.get_html_text(chapter_url)
        if not html:
            return None
        parse_html = etree.HTML(html)
        content = [text.strip() for text in
                   parse_html.xpath('//div[@id="showReading"]//p//text()')]
        return [text for text in content if text]

    def crawl(self) -> None:
        pending = self.parse_book()
        print(f"《{self.bookname}》共 {len(pending)} 章, 开始下载...")

        for round_no in range(1, self.retry_rounds + 1):
            failed = []
            for chapter_name, url in pending:
                time.sleep(1 + random.random())
                chapter_content = self.parse_chapters(url)
                if chapter_content is None:
                    failed.append((chapter_name, url))
                    continue
                if not chapter_content:
                    print(f"{chapter_name} 正文为空 (可能为 VIP 章节), 已跳过!")
                    continue
                self.save_chapter(chapter_name, chapter_content)
                print(f"{chapter_name} 保存成功!")

            if not failed:
                pending = []
                break
            pending = failed
            if round_no < self.retry_rounds:
                print(f"第 {round_no} 轮下载结束: {len(failed)} 章抓取失败, "
                      f"10 秒后开始第 {round_no + 1} 轮补爬...")
                time.sleep(10)

        if pending:
            print(f"仍有 {len(pending)} 章未能下载:")
            for chapter_name, _ in pending:
                print(f"  - {chapter_name}")


class WashaiSearcher(BaseSearcher):
    """书海阁: 优先调用 JSON 搜索接口, 失败时回退解析服务端渲染页面."""

    key = "washai"
    site = SITE_NAME
    api_url = BASE_URL + "/book/searchByPage"
    page_size = 20

    def search(self, keyword: str, limit: Optional[int] = None,
               by: str = "title") -> List[SearchResult]:
        index_url = (f"{BASE_URL}/book/bookclass.html"
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
            "Referer": f"{BASE_URL}/book/bookclass.html?k={quote(keyword)}",
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
            url=f"{BASE_URL}/book/{book_id}.html",
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
                url=urljoin(BASE_URL + "/", href),
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