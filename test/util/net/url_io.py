import urllib2

def get_handle(url):
    return urllib2.urlopen(url)
