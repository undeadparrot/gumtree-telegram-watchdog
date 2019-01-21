# -*- coding: utf-8 -*-
import urllib.request
from urllib.parse import urlparse, urljoin
from typing import Generator
from bs4 import BeautifulSoup
from gumtree_watchdog.types import Listing, Contract

MAX_DEPTH = 3


def absolute_link(base: str, link: str) -> str:
    """ Takes a starting like like https://www.xyz.com/blah/blah/blah
    and joins it to a relative link like /a/b/c
    to return https://www.xyz.com/a/b/c
    """
    parsed = urlparse(base)
    return urljoin(f'{parsed.scheme}://{parsed.netloc}', link)


def listing_from_soup(element, contract_id: str, query_url: str) -> Listing:
    img = element.select_one('img')
    return Listing(
        contract_id=contract_id,
        ad_id=element.select_one('.addAdTofav').attrs['data-adid'],
        title=element.select_one('.title a').text,
        description=element.select_one('.description').text,
        img_src=img.attrs['src'] if img else '',
        url=absolute_link(
            query_url,
            element.select_one('.href-link').attrs['href']),
    )


def yield_listings_from_soup(contract_id, url: str, depth: int = 0) -> Generator[Listing, None, None]:
    response = BeautifulSoup(urllib.request.urlopen(url))
    for element in response.select('.result.pictures'):
        listing = listing_from_soup(element, contract_id, url)
        yield listing

    next_page = response.select_one('a.next.follows')
    if next_page and depth < MAX_DEPTH:
        yield from yield_listings_from_soup(contract_id, absolute_link(url, next_page.attrs['href']), depth=depth+1)
