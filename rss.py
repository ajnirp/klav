from bs4 import BeautifulSoup as bs
from datetime import datetime

import feedparser
import re
import time

class RssReader:
    def __init__(self, urls):
        self.last_updated = {
            url : datetime.fromtimestamp(0) for url in urls
        }
        self.pattern = 'https?:\/\/i\.redd\.it/'

    def extract_link(entry):
        summary = entry['summary']
        soup = bs(summary)
        first_span = soup.find('span')
        try:
            link = first_span.a['href']
            return link
        except (AttributeError, TypeError, KeyError):
            return None

    def update(self, url):
        feed = feedparser.parse(url)
        newest_entry = feed.entries[1]
        updated_at = time.mktime(newest_entry['updated_parsed'])
        updated_at = datetime.fromtimestamp(updated_at)
        if updated_at > self.last_updated[url]:
            self.last_updated[url] = updated_at
        return newest_entry
