from gumtree_watchdog import db, spider


def main():
    with db.get_connection() as conn:
        contracts = db.get_open_contracts(conn)
        for contract in contracts:
            for listing in spider.yield_listings_from_soup(contract_id=contract.contract_id,
                                                           url=contract.query):
                db.insert_listing(conn, listing)


if __name__ == '__main__':
    main()
