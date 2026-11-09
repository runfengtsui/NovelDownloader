import argparse
import json
import sys
from contextlib import redirect_stdout

from noveldl.registry import SITES, detect_site, search_all


def download(url: str, use_proxy: bool = False) -> None:
    site = detect_site(url)
    if site is None:
        raise Exception("该网址无效或暂不支持该网站小说的下载!")
    site.downloader(url, use_proxy=use_proxy).crawl()


def print_results(results) -> None:
    if not results:
        print("未找到匹配的小说.")
        return

    counts = {}
    for result in results:
        counts[result.site] = counts.get(result.site, 0) + 1

    current_site = None
    for index, result in enumerate(results, 1):
        if result.site != current_site:
            if current_site is not None:
                print()
            print(f"===== {result.site} ({counts[result.site]} 条) =====")
            current_site = result.site

        meta = [f"作者: {result.author or '未知'}"]
        if result.category:
            meta.append(f"分类: {result.category}")
        if result.status:
            meta.append(f"状态: {result.status}")
        if result.word_count:
            meta.append(f"字数: {result.word_count}")
        print(f"[{index}] {result.title}")
        print("    " + " | ".join([f"来源: {result.site}"] + meta))

        detail = []
        if result.latest_chapter:
            detail.append(f"最新: {result.latest_chapter}")
        if result.updated:
            detail.append(f"更新: {result.updated}")
        if detail:
            print("    " + " | ".join(detail))
        print(f"    链接: {result.url}")

    print()
    print(f"共 {len(results)} 条结果.")


def search(keyword: str, sites=None, use_proxy: bool = False, limit=None,
           by: str = "title", as_json: bool = False) -> int:
    if as_json:
        # JSON 模式下把请求过程输出(直连提示、代理池日志等)改到 stderr, 保证 stdout 只有 JSON.
        with redirect_stdout(sys.stderr):
            results, errors = search_all(keyword, sites=sites, use_proxy=use_proxy,
                                         limit=limit, by=by)
    else:
        results, errors = search_all(keyword, sites=sites, use_proxy=use_proxy,
                                     limit=limit, by=by)
    for site, message in errors:
        print(f"警告: {site} 搜索失败: {message}", file=sys.stderr)

    if as_json:
        print(json.dumps([result.to_dict() for result in results],
                         ensure_ascii=False, indent=2))
    else:
        print_results(results)

    if results:
        return 0
    return 1 if errors else 0


def positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("必须是正整数")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="免费小说下载与搜索工具.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    download_parser = subparsers.add_parser(
        "download", help="下载指定网址的小说")
    download_parser.add_argument("-u", "--url", required=True,
                                 help="novel download url")
    download_parser.add_argument("--proxy", action="store_true",
                                 help="use free proxy pool (slower; default: direct connection)")

    search_parser = subparsers.add_parser(
        "search", help="搜索已支持网站的小说")
    search_parser.add_argument("-k", "--keyword", required=True,
                               help="书名或作者关键词")
    search_parser.add_argument("-s", "--site", nargs="+", default=None,
                               choices=list(SITES) + ["all"],
                               help="搜索站点, 默认全部")
    search_parser.add_argument("-n", "--limit", type=positive_int, default=None,
                               help="每个站点最多返回的结果数, 默认全部")
    search_parser.add_argument("--by", choices=["title", "author"], default="title",
                               help="笔趣阁搜索字段: 书名或作者 (书海阁自动匹配书名/作者/关键字)")
    search_parser.add_argument("--proxy", action="store_true",
                               help="use free proxy pool (slower; default: direct connection)")
    search_parser.add_argument("--json", action="store_true", dest="as_json",
                               help="以 JSON 输出结果")

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "download":
            download(args.url, args.proxy)
            return 0
        return search(args.keyword, sites=args.site, use_proxy=args.proxy,
                      limit=args.limit, by=args.by, as_json=args.as_json)
    except Exception as exc:
        print(f"错误: {exc}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
