from noveldl.BaseTemplate import BaseTemplate
# from freeproxy import freeproxy
from lxml import etree
import time
import random


class BookTxt(BaseTemplate):

    def parse_book(self):
        html = self.get_html_text(self.bookurl)
        while html == "":
            html = self.get_html_text(self.bookurl)
        parse_html = etree.HTML(html)
        title_list = parse_html.xpath('//div[@id="list"]/dl/dd/a/text()')
        url_list = parse_html.xpath('//div[@id="list"]/dl/dd/a/@href')
        return zip(title_list, url_list)
    
    
    def parse_chapters(self, chapter_url):
        html = self.get_html_text(chapter_url)
        while html == "":
            # self.proxy = self.fp_client.getrandomproxy()
            html = self.get_html_text(chapter_url)
        parse_html = etree.HTML(html)
        content = parse_html.xpath('//*[@id="content"]/text()')
        return content
    
    def crawl_booktxt(self):
        start_time = time.time()
        chapters_list = self.parse_book()
        chapters_list = list(chapters_list)[6:]
        for chapter_name, url in chapters_list:
            time.sleep(random.random())
            chapter_content = self.parse_chapters("https://www.ddyueshu.com" + url)
            self.save_chapter(chapter_name, chapter_content)
            print(f"{chapter_name} 保存成功!")
        self.total_time = time.time() - start_time
        self.send_email()

