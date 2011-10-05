import sys
from lxml import html

def run_xpath(xpath_expression, tree):
    return tree.xpath(xpath_expression)


def parse_content(content):
    return html.fromstring(content)


def main():
    path = sys.argv[1]
    xpath = sys.argv[2]

    f = open(path, "rb")
    content = f.read()
    f.close()

    tree = parse_content(content)
    print run_xpath(xpath, tree)


if __name__ == "__main__":
    main()
