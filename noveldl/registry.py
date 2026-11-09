"""站点注册表: 统一管理已支持网站的下载器、搜索器与网址匹配."""

from dataclasses import dataclass
from typing import Callable, List, Optional, Type

from noveldl.base import BaseDownloader, BaseSearcher, SearchResult
from noveldl.biquge import Biquge, BiqugeSearcher
from noveldl.match import is_biquge365_url, is_washai_url
from noveldl.network.http import DirectClient
from noveldl.network.proxy import ProxyPool
from noveldl.washai import Washai, WashaiSearcher


@dataclass(frozen=True)
class Site:
    key: str
    downloader: Type[BaseDownloader]
    searcher: Type[BaseSearcher]
    matcher: Callable[[str], bool]

    @property
    def name(self) -> str:
        return self.searcher.site


# 注册顺序决定搜索结果的站点顺序.
SITES = {
    "biquge": Site("biquge", Biquge, BiqugeSearcher, is_biquge365_url),
    "washai": Site("washai", Washai, WashaiSearcher, is_washai_url),
}


def detect_site(url: str) -> Optional[Site]:
    for site in SITES.values():
        if site.matcher(url):
            return site
    return None


def search_all(keyword: str, sites: Optional[List[str]] = None,
               use_proxy: bool = False, limit: Optional[int] = None,
               by: str = "title"):
    """依次搜索各站点, 返回 (结果列表, 错误列表[(站点名, 错误信息)])."""
    if not sites or "all" in sites:
        selected = list(SITES)
    else:
        selected = [key for key in SITES if key in sites]

    shared_fetcher = None
    if len(selected) > 1:
        # 代理池初始化较慢, 多站搜索时共用一个请求器.
        shared_fetcher = ProxyPool() if use_proxy else DirectClient()

    results: List[SearchResult] = []
    errors = []
    for key in selected:
        searcher = SITES[key].searcher(use_proxy=use_proxy, fetcher=shared_fetcher)
        try:
            results.extend(searcher.search(keyword, limit=limit, by=by))
        except Exception as exc:
            errors.append((searcher.site, str(exc)))
    return results, errors