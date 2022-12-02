import requests
from fake_useragent import UserAgent
from freeproxy import freeproxy


class BaseTemplate:

    def __init__(self, bookname, bookurl) -> None:
        self.bookname = bookname
        self.bookurl = bookurl
        proxy_sources = ['proxylistplus', 'kuaidaili']
        self.fp_client = freeproxy.FreeProxy(proxy_sources=proxy_sources)
        self.total_time = 0
        # self.proxy = self.fp_client.getrandomproxy()
        
    def get_html_text(self, url):
        try:
            ua = UserAgent()
            proxy = self.fp_client.getrandomproxy()
            r = requests.get(url, headers={'User-Agent': ua.random}, proxies=proxy)
            r.raise_for_status()
            r.encoding = r.apparent_encoding
            return r.text
        except:
            print(f'网页：{url}爬取失败!')
            return ""
    
    def save_chapter(self, chapter_name, chapter_content):
        with open(f"{self.bookname}.txt", 'a', encoding='utf-8') as f:
            f.write(chapter_name + '\n')
            for sentence in chapter_content[:-1]:
                f.write(sentence + '\n')
            f.write('\n' * 2)

