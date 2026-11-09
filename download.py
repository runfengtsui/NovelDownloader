import argparse
import sys
from noveldl.match import *
from noveldl.biquge import Biquge
from noveldl.washai import Washai


def download(url: str, use_proxy: bool = False) -> None:
    if is_biquge365_url(url):
        Biquge(url, use_proxy=use_proxy).crawl()
    elif is_washai_url(url):
        Washai(url, use_proxy=use_proxy).crawl()
    else:
        raise Exception("该网址无效或暂不支持该网站小说的下载!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", required=True, help="novel download url")
    parser.add_argument("--proxy", action="store_true",
                        help="use free proxy pool (slower; default: direct connection)")
    args = parser.parse_args()
    try:
        download(args.url, args.proxy)
    except RuntimeError as exc:
        print(f"错误: {exc}")
        sys.exit(1)

