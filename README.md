# Novel Downloader

本项目为练习 Python 爬虫所作. 目前实现了以下网站的爬取:
* [笔趣阁](https://www.biquge365.net/)
* [书海阁](https://book.washai.net)

## 克隆下载

通过 `git` 克隆本项目源代码:
```git
git clone https://github.com/runfengtsui/NovelDownloader.git
```

项目结构如下:

```text
main.py               # 命令行入口: download / search 两个子命令
noveldl/
├── network/
│   ├── proxy.py      # 免费代理池: 多源加载、去重、评分、轮换
│   └── http.py       # 本机 IP 直连: 限速与 429 退避
├── base.py           # 请求基类: 直连/代理选择、GET/POST、Cookie
├── BaseTemplate.py   # 爬虫模板: 保存章节、通用 crawl
├── search.py         # 站点搜索: 笔趣阁、书海阁
├── washai.py         # 书海阁
├── biquge.py         # 笔趣阁
└── match.py          # 网址匹配
```

## 虚拟环境

使用 `venv` 虚拟环境并激活:
```shell
python3 -m venv .venv
# for Windows
source .venv\Scripts\Activate.ps1
# for Linux
source .venv/bin/activate
```

## 依赖管理

`Python` 版本要求为 `3.10+`，项目所使用的第三方包依赖见 `pyproject.toml`，使用 `pip3` 安装:
```shell
pip3 install -e .
```

## 命令行使用帮助

本项目目前为命令行工具, 须在终端中使用，可以通过 `-h` 参数查看帮助:
```shell
> python3 main.py -h
usage: main.py [-h] {download,search} ...

> python3 main.py download -h
usage: main.py download [-h] -u URL [--proxy]

> python3 main.py search -h
usage: main.py search [-h] -k KEYWORD [-s {biquge,washai,all} ...]
                      [-n LIMIT] [--by {title,author}] [--proxy] [--json]
```

### 下载小说

使用 `download` 子命令和 `-u` 或者 `--url` 参数传递要爬取的小说的网址(需要在支持内), 即可爬取相应的内容并保存在当前目录下:

```shell
python3 main.py download -u url
```

### 搜索小说

使用 `search` 子命令和 `-k` 或者 `--keyword` 参数在已支持的网站中检索小说:

```shell
# 搜索全部站点
python3 main.py search -k 剑来

# 只搜索笔趣阁, 并按作者检索
python3 main.py search -k 烽火戏诸侯 -s biquge --by author

# 每个站点最多显示 10 条, 并以 JSON 输出
python3 main.py search -k 都市 -n 10 --json
```

搜索结果会给出书名、作者、分类、状态、最新章节、更新时间与详情页链接, 其中的链接可直接作为 `download` 子命令的 `-u` 参数使用. 默认返回每个站点的全部结果, 可通过 `-n/--limit` 限制数量.

## Todo

* 支持多线程爬虫;
