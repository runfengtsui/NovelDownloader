import time

import requests


class DirectClient:
    """使用本机 IP 直连目标网站, 内置请求间隔与 429/503 退避重试."""

    def __init__(self, interval: float = 2.0, timeout: float = 20, retries: int = 4) -> None:
        self.interval = interval
        self.timeout = timeout
        self.retries = retries
        self.session = requests.Session()
        self._last_request_at = 0.0

    def cookie(self, name: str) -> str:
        return self.session.cookies.get(name, "")

    def _request(self, method: str, url: str, headers: dict, data=None) -> str:
        """发送请求, 失败返回空字符串."""
        wait = self.interval - (time.monotonic() - self._last_request_at)
        if wait > 0:
            time.sleep(wait)
        for attempt in range(self.retries):
            self._last_request_at = time.monotonic()
            try:
                r = self.session.request(method, url, headers=headers, data=data,
                                         timeout=self.timeout)
                if r.status_code in (429, 503):
                    time.sleep(5 * (attempt + 1))
                    continue
                r.raise_for_status()
                r.encoding = r.encoding or r.apparent_encoding
                return r.text
            except requests.RequestException:
                time.sleep(1 + attempt)
        return ""

    def get(self, url: str, headers: dict) -> str:
        """获取网页文本, 失败返回空字符串."""
        return self._request("GET", url, headers)

    def post(self, url: str, headers: dict, data: dict) -> str:
        """提交表单并获取网页文本, 失败返回空字符串."""
        return self._request("POST", url, headers, data)
