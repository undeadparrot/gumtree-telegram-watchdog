# -*- coding: utf-8 -*-
import urllib.request
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from gumtree_watchdog import db

def absolute_link(base, link):
    parsed = urlparse(base)
    return urljoin(f'{parsed.scheme}://{parsed.netloc}', link)

class Spider():

    def __init__(self, contract_id, query_url):
        self.query_url = query_url
        self.contract_id = contract_id

    def run(self):
        return list(self.parse(self.query_url))

    def parse(self, url, depth=0):
        response = BeautifulSoup(urllib.request.urlopen(url))
        for listing in response.select('.result.pictures'):
            title = listing.select_one('.title a').text
            description = listing.select_one('.description').text
            img = listing.select_one('img')
            img_src = img.attrs['src'] if img else ''
            url = absolute_link(
                self.query_url,
                listing.select_one('.href-link').attrs['href'])
            ad_id = listing.select_one('.addAdTofav').attrs['data-adid']
            db.insert_listing(self.contract_id, ad_id, url, title, description)
            yield (self.contract_id, ad_id, url, title, description)

        next_page = response.select_one('a.next.follows')
        if next_page and depth < 3:
            yield from self.parse(absolute_link(self.query_url, next_page.attrs['href']), depth=depth+1)

    def parse_listing_page(self, response):
        ad_id = response.css('.breadcrumbs.title::text').extract_first()
