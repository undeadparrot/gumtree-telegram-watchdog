import os
import os.path
import sqlite3
import logging

def get_connection():
    conn = sqlite3.connect(os.environ.get('GUMTREE_DB', "gumtree.db"))
    conn.row_factory = sqlite3.Row
    return conn

def initialize():
    if os.path.isfile("gumtree.db"):
        logging.info("Sqlite3 database found.")
        return 
        
    logging.warning("Sqlite3 database not found, will initialize.")
    
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE contract(
                contract_id integer primary key autoincrement,
                query text not null,
                chat_id integer not null,
                is_active bool default 0,
                UNIQUE(chat_id, query)
            );
        """)    
        conn.execute("""
            CREATE TABLE listing(
                listing_id integer primary key autoincrement,
                contract_id integer not null,
                ad_id text not null,
                title text not null,
                description text not null,
                url text,
                img_src text,
                must_notify_user bool default 1,
                FOREIGN KEY(contract_id) REFERENCES contract(contract_id),
                UNIQUE(contract_id, ad_id)
            );
        """)    
        conn.execute("""
            CREATE TABLE inbound_msg(
                inbound_msg_id integer primary key autoincrement,
                chat_id integer not null,
                message text not null
            );
        """)

def insert_inbound_msg(chat_id: int, message: str):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO inbound_msg (chat_id, message) VALUES (:chat_id, :message)
        """, dict(
            chat_id=chat_id,
            message=message
        ))

def insert_contract(chat_id: int, query: str):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO contract (chat_id, query) VALUES (:chat_id, :query)
        """, dict(
            chat_id=chat_id,
            query=query
        ))
        return cur.lastrowid

def insert_listing(contract_id: int, ad_id: str, url: str, title: str, description: str):
    with get_connection() as conn:
        existing_results = conn.execute("""
            SELECT listing_id 
            FROM listing 
            WHERE contract_id = :contract_id AND ad_id = :ad_id
        """, dict(
            contract_id=contract_id,
            ad_id=ad_id
        )).fetchall()
        if existing_results:
            return False
            
        conn.execute("""
            INSERT INTO listing 
            (contract_id, ad_id, url, title, description) 
            VALUES 
            (:contract_id, :ad_id, :url,:title, :description)
        """, dict(
            contract_id=contract_id,
            ad_id=ad_id,
            url=url,
            title=title,
            description=description
        ))
        return True

def get_open_contracts():
    with get_connection() as conn:
        return conn.execute("""
            SELECT * FROM contract WHERE is_active = 1; 
        """).fetchall()
        
def get_open_contracts_for_user(chat_id: int):
    with get_connection() as conn:
        return conn.execute("""
            SELECT * FROM contract WHERE is_active = 1 and chat_id = :chat_id ; 
        """, dict(
            chat_id=chat_id
        )).fetchall()

def get_unsent_listing_notifications():
    with get_connection() as conn:
        return conn.execute("""
            SELECT listing_id, chat_id, url, title, description 
            FROM listing 
            JOIN contract USING (contract_id) 
            WHERE must_notify_user = 1
            AND contract.is_active = 1  ; 
        """).fetchall()

def mark_listing_as_sent(listing_id):
    with get_connection() as conn:
        return conn.execute("""
            UPDATE listing SET must_notify_user = 0 WHERE listing_id = :listing_id  ; 
        """, dict(listing_id=listing_id))

def deactivate_contract(chat_id: str, contract_id: int):
    with get_connection() as conn:
        conn.execute("""
            UPDATE contract SET is_active = 0 WHERE contract_id = :contract_id AND chat_id = :chat_id
        """, dict(contract_id=contract_id, chat_id=chat_id))
        
def mark_contract_active(contract_id: int):
    with get_connection() as conn:
        conn.execute("""
            UPDATE listing SET must_notify_user = 0 WHERE contract_id = :contract_id
        """, dict(contract_id=contract_id))
        conn.execute("""
            UPDATE contract SET is_active = 1 WHERE contract_id = :contract_id
        """, dict(contract_id=contract_id))
