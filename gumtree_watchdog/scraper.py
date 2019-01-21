# -*- coding: utf-8 -*-
import scrapy
import gumtree_watchdog import db


class GumtreeSpider(scrapy.Spider):
    name = "gumtree_spider"
    custom_settings = {'DEPTH_LIMIT': '2'}

    def __init__(self, contract_id='', query_url='', **kwargs):
        self.start_urls = [query_url]
        super().__init__(**kwargs)
        self.contract_id = contract_id

    def parse(self, response):
        for listing in response.css('.result.pictures'):
            title = listing.css('.title a::text').extract_first()
            description = listing.css('.description::text').extract_first()
            img_src = listing.css('img::attr(src)').extract_first()
            url = response.urljoin(
                listing.css('.href-link::attr(href)').extract_first())
            ad_id = listing.css(
                '.result.pictures::attr(data-criteoadid)').extract_first()
            print("Listing " + img_src)
            db.insert_listing(self.contract_id, ad_id, url, title, description)

        next_page = response.css('a.next.follows::attr(href)').extract_first()
        if next_page:
            yield response.follow(next_page)

    def parse_listing_page(self, response):
        ad_id = response.css('.breadcrumbs.title::text').extract_first()
