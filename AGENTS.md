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
- `noveldl/base.py`: 请求、下载与搜索的公共基类
- `noveldl/biquge.py` / `noveldl/washai.py`: 各站点的下载器与搜索器
- `noveldl/registry.py`: 站点注册表与统一搜索入口
- `main.py`: 命令行接口, 提供 `download` 与 `search` 两个子命令
