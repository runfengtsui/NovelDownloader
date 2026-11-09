import re


def is_biquge365_url(url: str) -> bool:
    return (None != re.match(r"https://www\.biquge365\.net/newbook/\d+/", url) or
            None != re.match(r"https://www\.biquge365\.net/book/\d+/", url))

def is_washai_url(url: str) -> bool:
    return None != re.match(r"https://book\.washai\.net/book/(?:indexList-|indexList/)?\d+(?:/\d+)?\.html", url)

