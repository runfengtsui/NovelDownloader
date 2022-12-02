from noveldl.import BaseTemplate
# from freeproxy import freeproxy
from lxml import etree
import time
import random


class IBiQiuGe(BaseTemplate):

    def parse_book(self):
        html = self.get_html_text(self.bookurl)
        while html == "":
            html = self.get_html_text(self.bookurl)
        parse_html = etree.HTML(html)
        title_list = parse_html.xpath('/html/body/div[3]/div[2]/a/text()')
        url_list = parse_html.xpath('/html/body/div[3]/div[2]/a/@href')
        return zip(title_list, url_list)
    
    
    def parse_chapters(self, chapter_url):
        html = self.get_html_text(chapter_url)
        while html == "":
            # self.proxy = self.fp_client.getrandomproxy()
            html = self.get_html_text(chapter_url)
        parse_html = etree.HTML(html)
        content = parse_html.xpath('//*[@id="article"]/text()')
        return content
    
    def crawl_ibiqiuge(self):
        start_time = time.time()
        chapters_list = list(self.parse_book())
        for chapter_name, url in chapters_list:
            time.sleep(random.random())
            first_page = "https://www.ibiqiuge.com" + url
            chapter_content = self.parse_chapters(first_page)
            second_page = first_page.replace(".html", "_2.html")
            chapter_content += self.parse_chapters(second_page)
            self.save_chapter(chapter_name, chapter_content)
            print(f"{chapter_name} 保存成功!")
        self.total_time = time.time() - start_time
        self.send_email()

