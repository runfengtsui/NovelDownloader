# AGENTS.md
## 项目目标

本项目练习使用 Python 爬取免费小说静态网页.

## 技术栈

- `requests`: 获取页面
- `lxml`: 解析页面
- `fake_useragent`: 提供随机的浏览器头
- `pyfreeproxy`: 获取免费代理

## 关键目录文件

- `noveldl`: 爬虫核心功能
- `noveldl/network`: 网络直连和代理模式
- `noveldl/search.py`: 站点搜索功能
- `main.py`: 命令行接口, 提供 `download` 与 `search` 两个子命令
