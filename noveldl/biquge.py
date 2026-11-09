from noveldl.BaseTemplate import BaseTemplate
from lxml import etree
from typing import List


class Biquge(BaseTemplate):

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
        url = "https://www.biquge365.net" + chapter_url
        html = self.get_html_text(url)
        while html == "":
            html = self.get_html_text(url)
        parse_html = etree.HTML(html)
        content = parse_html.xpath('//*[@id="txt"]/text()')
        return content[1:]

