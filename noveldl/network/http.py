import time

import requests


class DirectClient:
    """使用本机 IP 直连目标网站, 内置请求间隔与 429/503 退避重试."""

    def __init__(self, interval: float = 2.0, timeout: float = 20, retries: int = 4) -> None:
        self.interval = interval
        self.timeout = timeout
        self.retries = retries
        self._last_request_at = 0.0

    def get(self, url: str, headers: dict) -> str:
        """获取网页文本, 失败返回空字符串."""
        wait = self.interval - (time.monotonic() - self._last_request_at)
        if wait > 0:
            time.sleep(wait)
        for attempt in range(self.retries):
            self._last_request_at = time.monotonic()
            try:
                r = requests.get(url, headers=headers, timeout=self.timeout)
                if r.status_code in (429, 503):
                    time.sleep(5 * (attempt + 1))
                    continue
                r.raise_for_status()
                r.encoding = r.encoding or r.apparent_encoding
                return r.text
            except requests.RequestException:
                time.sleep(1 + attempt)
        return ""