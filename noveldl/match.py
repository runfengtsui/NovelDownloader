import re


def is_booktxt_url(url: str) -> bool:
    return None != re.match("https:\/\/www.ddyueshu.com\/[0-9\_]+\/", url)

def is_81zw_url(url: str) -> bool:
    return None != re.match("https:\/\/www.81zw.app\/book\/[0-9]+\/", url)

