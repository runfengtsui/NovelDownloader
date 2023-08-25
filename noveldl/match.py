import re


def is_booktxt_url(url: str) -> bool:
    return None != re.match("https:\/\/www.ddyueshu.com\/[0-9\_]+\/", url)

def is_81zw_url(url: str) -> bool:
    return None != re.match("https:\/\/www.81zw.app\/book\/[0-9]+\/", url)

def is_biquge365_url(url: str) -> bool:
    return (None != re.match("https:\/\/www.biquge365.net\/newbook\/[0-9]+\/", url) or 
            None != re.match("https:\/\/www.biquge365.net\/book\/[0-9]+\/", url))

