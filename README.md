# Novel Downloader

本项目为练习 Python 爬虫所作. 目前实现了以下网站的爬取:

* [八一中文网](https://www.81zw.com)
* [顶点小说](https://www.booktxt.com)
* [笔趣阁](https://www.ibiqiuge.com)

## 下载

运行以下命令下载本项目:

```git
git clone https://github.com/RunfengTsui/NovelDownloader.git
```

## 第三方库

本项目使用 `poetry` 管理第三方库, 其中 `requests` 库获取页面, `lxml` 库解析页面. 同时, 本项目使用了 `fake_useragent` 库来提供随机的浏览器头, `pyfreeproxy` [获取免费代理](https://freeproxy.readthedocs.io/en/latest/Quickstart.html#id2).

直接运行下述命令安装所需要的第三方库:

```shell
poetry install
```

(也可以使用 `pip3` 分别进行安装).

## 使用

本项目目前为命令行工具, 须在终端中使用.

```shell
cd NovelDownloader
poetry shell    # 激活虚拟环境, 如果使用 pip3 安装第三方库则不需要
```

通过 `-h` 参数查看帮助:

```shell
> python3 download.py -h
usage: download.py [-h] -u URL

options:
  -h, --help         show this help message and exit    
  -u URL, --url URL  novel download url
```

使用 `-u` 或者 `--url` 参数传递要爬取的小说的网址(需要在支持内), 即可爬取相应的内容并保存在当前目录下:

```shell
python3 download.py -u url
```

## Todo

* 支持更多的网站;
* 增加搜索小说的功能;
* 支持多线程爬虫;
