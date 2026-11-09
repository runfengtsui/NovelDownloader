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
noveldl/
├── network/
│   ├── proxy.py      # 免费代理池: 多源加载、去重、评分、轮换
│   └── http.py       # 本机 IP 直连: 限速与 429 退避
├── BaseTemplate.py   # 爬虫模板: 选择请求方式、保存、通用 crawl
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
> python3 download.py -h
usage: download.py [-h] -u URL [--proxy]

options:
  -h, --help            show this help message and exit
  -u URL, --url URL     novel download url
  --proxy               use free proxy pool (slower; default: direct connection)
```

使用 `-u` 或者 `--url` 参数传递要爬取的小说的网址(需要在支持内), 即可爬取相应的内容并保存在当前目录下:

```shell
python3 download.py -u url
```

## Todo

* 增加搜索小说的功能;
* 支持多线程爬虫;
