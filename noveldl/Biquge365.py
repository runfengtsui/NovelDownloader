from noveldl.BaseTemplate import BaseTemplate
from freeproxy import freeproxy
from lxml import etree
from typing import List


class Biquge365(BaseTemplate):

    def __init__(self, bookurl: str) -> None:
        self.bookname = ""
        if "newbook" not in bookurl:
            self.bookurl = bookurl.replace("book", "newbook")
        else:
            self.bookurl = bookurl
        proxy_sources = ['proxylistplus', 'kuaidaili']
        self.fp_client = freeproxy.FreeProxy(proxy_sources=proxy_sources)
        self.total_time = 0

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
        url = "https://www.biquge365.net" + chapter_url
        html = self.get_html_text(url)
        while html == "":
            html = self.get_html_text(url)
        parse_html = etree.HTML(html)
        content = parse_html.xpath('//*[@id="txt"]/text()')
        return content[1:]

