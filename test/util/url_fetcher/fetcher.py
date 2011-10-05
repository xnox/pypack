import sys
import urllib2

from util.net.url_io import get_handle

def fetch_url(url):
    return get_handle(url).read()

def save_content(content, path):
    f = open(path, "wb")
    f.write(content)
    f.close()

def main():
    path = sys.argv[1]
    url = sys.argv[2]

    content = fetch_url(url)
    save_content(content, path)

if __name__ == "__main__":
    main()
