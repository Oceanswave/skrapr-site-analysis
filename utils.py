from urllib.parse import urlparse


def is_absolute(url):
    return bool(urlparse(url).netloc)
