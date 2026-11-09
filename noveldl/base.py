from fake_useragent import UserAgent

from noveldl.network.http import DirectClient
from noveldl.network.proxy import ProxyPool


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
