import scrapy
import multiprocessing
import gumtree_watchdog.scraper
from gumtree_watchdog import db


def crawl_gumtree(contract_id, query_url):
    from scrapy.crawler import CrawlerProcess
    from gumtree_watchdog import db
    import logging
    proc = CrawlerProcess()
    proc.crawl(
        scraper.GumtreeSpider, contract_id=contract_id, query_url=query_url)
    proc.start()


def run_contract(contract_id: int, query_url: str):
    p = multiprocessing.Process(
        target=crawl_gumtree, args=(contract_id, query_url))
    p.start()
    p.join()


def main():
    for contract in db.get_open_contracts():
        run_contract(contract['contract_id'], contract['query'])


if __name__ == '__main__':
    main()
