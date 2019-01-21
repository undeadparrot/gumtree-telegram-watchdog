import multiprocessing
import gumtree_watchdog.scraper
from gumtree_watchdog import db, scraper


def crawl_gumtree(contract_id, query_url):
    import logging
    scraper.Spider(contract_id=contract_id, query_url=query_url).run()


def main():
    for contract in db.get_open_contracts():
        print("Contract: %s" % contract)
        crawl_gumtree(contract['contract_id'], contract['query'])


if __name__ == '__main__':
    main()
