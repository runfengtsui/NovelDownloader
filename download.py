import argparse
from noveldl.match import *
from noveldl.Chinese81 import Chinese81
from noveldl.BookTxt import BookTxt


def download(url: str) -> None:
    if is_booktxt_url(url):
        BookTxt(url).crawl()
    elif is_81zw_url(url):
        Chinese81(url).crawl()
    else:
        raise Exception("该网址无效或暂不支持该网站小说的下载!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", required=True, help="novel download url")
    args = parser.parse_args()
    download(args.url)
