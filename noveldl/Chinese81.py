from noveldl.BaseTemplate import BaseTemplate
from lxml import etree
from typing import List


class Chinese81(BaseTemplate):

    def parse_book(self) -> List:
        html = self.get_html_text(self.bookurl)
        while html == "":
            html = self.get_html_text(self.bookurl)
        parse_html = etree.HTML(html)
        self.bookname = parse_html.xpath('//*[@id="info"]/h1/text()')[0]
        title_list = parse_html.xpath('//div[@id="list"]/dl/dd/a/text()')
        url_list = parse_html.xpath('//div[@id="list"]/dl/dd/a/@href')
        return list(zip(title_list, url_list))
    
    
    def parse_chapters(self, chapter_url: str) -> List:
        url = "https://www.81zw.app" + chapter_url
        html = self.get_html_text(url)
        while html == "":
            html = self.get_html_text(url)
        parse_html = etree.HTML(html)
        content = parse_html.xpath('//*[@id="content"]/text()')
        return content[:-33]

