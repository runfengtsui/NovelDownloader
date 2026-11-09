import os

# 关闭 pyfreeproxy 内部 IP 定位的进度条, 保持命令行输出整洁.
os.environ.setdefault('TQDM_DISABLE', '1')

import random
import sys
import threading
import time
from collections import defaultdict

import requests
from freeproxy import freeproxy

# 排除依赖浏览器、需要授权或抓取时会无限挂起的代理源.
DEFAULT_EXCLUDED_SOURCES = (
    'IP3366ProxiedSession',         # 依赖 DrissionPage, 可能自动下载浏览器
    'IPRoyalProxiedSession',        # 需要授权 token
    'DatabayProxiedSession',        # 抓取时无超时挂起
    'IPLocateProxiedSession',       # 抓取时无超时挂起
    'TheSpeedXProxiedSession',      # 抓取时无超时挂起
    'DpangestuwProxiedSession',     # 抓取时无超时挂起
    'OpenProxyListProxiedSession',  # 抓取时无超时挂起
    'ProxySpaceProxiedSession',     # 抓取时无超时挂起
)


class ProxyPool:
    """免费代理池, 仅通过代理访问目标网站.

    多源并发抓取免费代理并全局去重, 按各源历史成功率加权选择代理; 已验证可用的
    代理会被优先复用. 代理不可用时返回空字符串, 不做直连回退.
    """

    # 仅使用 HTTP 代理: 实测 https 协议代理对目标站基本不可用, SOCKS 还需额外依赖.
    protocol = 'http'
    # 每个源抓取页数与并发源数.
    pages = 1
    workers = 12
    init_wait = 60
    # 单次请求最多尝试的代理数、单个代理超时与总耗时上限.
    max_attempts = 8
    timeout = 8
    budget = 90

    def __init__(self, excluded_sources=DEFAULT_EXCLUDED_SOURCES, verbose: bool = True) -> None:
        self.excluded_sources = excluded_sources
        self.verbose = verbose
        self.sources = self._default_sources()
        self.pools = defaultdict(list)
        self.source_stats = defaultdict(lambda: [1, 2])  # [成功次数, 尝试次数], 带拉普拉斯先验
        self.working_proxies = []
        self.working_proxy_keys = set()
        self._seen_proxy_keys = set()
        self._sessions = {}
        self._lock = threading.Lock()
        self._sessions_lock = threading.Lock()
        self._loading = False
        self._last_refresh = 0.0
        # 使用同一个 Session 保存 Cookie (如书海阁的浏览器令牌), 代理仍按请求轮换.
        self.session = requests.Session()
        self._load_proxies()

    def _log(self, message: str) -> None:
        if self.verbose:
            # 日志走 stderr, 避免后台线程输出污染 --json 的 stdout.
            print(message, file=sys.stderr)

    def _default_sources(self) -> list:
        return [source for source in freeproxy.ProxiedSessionBuilder.REGISTERED_MODULES
                if source not in self.excluded_sources]

    def size(self) -> int:
        with self._lock:
            return sum(len(proxies) for proxies in self.pools.values())

    def _add_proxies(self, proxies) -> None:
        with self._lock:
            for proxy in proxies:
                if proxy.protocol != self.protocol:
                    continue
                key = (proxy.protocol, proxy.ip, proxy.port)
                if key in self._seen_proxy_keys:
                    continue
                self._seen_proxy_keys.add(key)
                self.pools[proxy.source].append(proxy)

    def _load_source(self, source: str, semaphore: threading.Semaphore) -> None:
        with semaphore:
            try:
                session = freeproxy.BuildProxiedSession({
                    'type': source,
                    'max_pages': self.pages,
                    'disable_print': True,
                })
                proxies = session.refreshproxies() or []
            except Exception:
                return
            with self._sessions_lock:
                self._sessions[source] = session
            self._add_proxies(proxies)

    def _load_proxies(self) -> None:
        if not self.sources:
            return
        started = time.monotonic()
        semaphore = threading.Semaphore(self.workers)
        threads = []
        # 各代理源彼此独立, 使用守护线程并发抓取, 避免个别源超时拖慢启动.
        for source in self.sources:
            thread = threading.Thread(target=self._load_source, args=(source, semaphore), daemon=True)
            thread.start()
            threads.append(thread)
        # 只等待一小段时间, 慢速源继续在后台补充, 不阻塞后续下载.
        deadline = started + self.init_wait
        for thread in threads:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            thread.join(remaining)
        still_loading = any(thread.is_alive() for thread in threads)
        self._log(f"代理池初始化完成: {len(self._sessions)}/{len(self.sources)} 个源, "
                  f"{self.size()} 个 HTTP 代理, 耗时 {time.monotonic() - started:.1f}s"
                  f"{' (慢速源仍在后台加载)' if still_loading else ''}.")
        if self.size() < 100:
            self._log("警告: 当前可用代理数量较少, 代理模式可能无法获取页面.")

    def _refresh_source(self, session, semaphore: threading.Semaphore) -> None:
        with semaphore:
            try:
                proxies = session.refreshproxies() or []
            except Exception:
                return
            self._add_proxies(proxies)

    def _refresh_worker(self) -> None:
        try:
            with self._sessions_lock:
                sessions = list(self._sessions.values())
            semaphore = threading.Semaphore(self.workers)
            threads = []
            for session in sessions:
                thread = threading.Thread(target=self._refresh_source, args=(session, semaphore), daemon=True)
                thread.start()
                threads.append(thread)
            for thread in threads:
                thread.join(120)
            self._log(f"代理池已在后台刷新: 当前候选 {self.size()} 个.")
        finally:
            self._loading = False

    def _refresh_proxies_async(self) -> None:
        # 免费代理会不断失效, 候选池耗尽时在后台重新拉取, 不阻塞当前请求.
        if self._loading or time.monotonic() - self._last_refresh < 60:
            return
        self._last_refresh = time.monotonic()
        self._loading = True
        threading.Thread(target=self._refresh_worker, daemon=True).start()

    def take(self):
        with self._lock:
            available = [(source, proxies) for source, proxies in self.pools.items() if proxies]
        # 优先复用已经验证可用的代理, 同时保留一定概率尝试新代理.
        if self.working_proxies and (not available or random.random() < 0.85):
            return self.working_proxies.pop(random.randrange(len(self.working_proxies)))
        if not available:
            self._refresh_proxies_async()
            with self._lock:
                available = [(source, proxies) for source, proxies in self.pools.items() if proxies]
        if available:
            # 按各源的历史成功率加权选择, 成功率越高的源被选中的概率越大.
            weights = [max(0.01, self.source_stats[source][0] / self.source_stats[source][1])
                       for source, _ in available]
            _, proxies = random.choices(available, weights=weights, k=1)[0]
            return proxies.pop()
        if self.working_proxies:
            return self.working_proxies.pop(random.randrange(len(self.working_proxies)))
        return None

    def _record(self, proxy, success: bool) -> None:
        stats = self.source_stats[proxy.source]
        stats[1] += 1
        if not success:
            return
        stats[0] += 1
        key = (proxy.protocol, proxy.ip, proxy.port)
        if key in self.working_proxy_keys or len(self.working_proxies) >= 100:
            return
        self.working_proxy_keys.add(key)
        self.working_proxies.append(proxy)

    def get(self, url: str, headers: dict) -> str:
        """依次尝试代理获取网页, 全部失败返回空字符串."""
        return self._request("GET", url, headers)

    def post(self, url: str, headers: dict, data: dict) -> str:
        """通过代理提交表单, 全部失败返回空字符串."""
        return self._request("POST", url, headers, data)

    def cookie(self, name: str) -> str:
        return self.session.cookies.get(name, "")

    def _request(self, method: str, url: str, headers: dict, data=None) -> str:
        deadline = time.monotonic() + self.budget
        for attempt in range(self.max_attempts):
            if time.monotonic() > deadline:
                break
            proxy = self.take()
            if proxy is None:
                break
            try:
                r = self.session.request(
                    method,
                    url,
                    headers=headers,
                    data=data,
                    proxies=proxy.requests_format_proxy,
                    timeout=self.timeout,
                )
                if r.status_code in (429, 503):
                    self._record(proxy, False)
                    time.sleep(2 * (attempt + 1))
                    continue
                r.raise_for_status()
                self._record(proxy, True)
                r.encoding = r.encoding or r.apparent_encoding
                return r.text
            except requests.RequestException:
                self._record(proxy, False)
                continue
        return ""