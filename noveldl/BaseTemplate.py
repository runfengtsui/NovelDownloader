import random
import time

from noveldl.base import FetcherBase


class BaseTemplate(FetcherBase):

    def __init__(self, bookurl: str, use_proxy: bool = False) -> None:
        super().__init__(use_proxy)
        self.bookname = ""
        self.bookurl = bookurl
        self.total_time = 0

    def save_chapter(self, chapter_name, chapter_content) -> None:
        with open(f"{self.bookname}.txt", 'a', encoding='utf-8') as f:
            f.write(chapter_name + '\n')
            for sentence in chapter_content:
                f.write(sentence + '\n')
            f.write('\n' * 2)

    def crawl(self) -> None:
        chapters_list = self.parse_book()
        for chapter_name, url in chapters_list:
            time.sleep(random.random())
            chapter_content = self.parse_chapters(url)
            self.save_chapter(chapter_name, chapter_content)
            print(f"{chapter_name} 保存成功!")