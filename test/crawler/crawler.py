import sys
from util.content_processor import processor
from util.url_fetcher import fetcher

def crawl_page_title(url):
    content = fetcher.fetch_url(url)
    tree = processor.parse_content(content)
    return processor.run_xpath("//title/text()", tree)

def main():
    print crawl_page_title(sys.argv[1])

if __name__ == "__main__":
    main()
