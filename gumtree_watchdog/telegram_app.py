# -*- coding: utf-8 -*-
import os
import logging
import sqlite3
import threading
import telegram
from telegram.ext import Updater, MessageHandler, CommandHandler

from gumtree_watchdog import spider, db
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

NOTIFICATION_CHECK_INTERVAL = 60.0 # seconds

def handle_message(bot, update):
    """ Log an unrecognised message
    """
    db.insert_inbound_msg(update.message.chat_id, update.message.text)


message_handler = MessageHandler([], handle_message)

#

def watch(bot, update, args):
    """ Create a new contract for a user
    """
    logger.warning("/watch %s", args)
    url = args[0] if len(args) == 1 else 'None'
    if 'https://' not in args[0]:
        update.message.reply_text(
            'Please send "/watch <url>" with a valid Gumtree url like: \n\n'
            '/watch https://www.gumtree.co.za/s-furniture/western-cape/chair/v1c9181l3100001q0p1'
        )

    try:
        with db.get_connection() as conn:
            contract_id = db.insert_contract(conn, update.message.chat_id, url)
    except sqlite3.IntegrityError:
        update.message.reply_text('You are already watching that url')
        return

    update.message.reply_text(
        'Understood, doing a preliminary scrape of the page now')
    for listing in spider.yield_listings_from_soup(contract_id, url):

    with db.get_connection() as conn:
        db.mark_contract_active(conn, contract_id)
    update.message.reply_text('Done.')


watch_handler = CommandHandler('watch', watch, pass_args=True)

#


def stop(bot, update, args):
    """ Deactivate a contract for a user
    """
    logger.warning("/stop %s", args)
    if not len(args) == 1 or not args[0].isdigit:
        update.message.reply_text('Please send "/stop <id>" with a valid id')
    with db.get_connection() as conn:
        db.deactivate_contract(conn, update.message.chat_id, args[0])
    update.message.reply_text('Done.')


stop_handler = CommandHandler('stop', stop, pass_args=True)

#


def handle_list_open_contracts(bot, update):
    """ Lists all contracts that are active
    """
    with db.get_connection() as conn:
        for contract in db.get_open_contracts_for_user(conn, update.message.chat_id):
            bot.send_message(
                contract.chat_id,
                f'Contract for url {contract.query}  \nTo stop watching it, send "/stop {contract.contract_id}"'
            )


list_open_contracts_handler = CommandHandler(
    'list', handle_list_open_contracts)

#


def make_callback_minute(bot):
    """ Runs regularly to check for listings that have appeared but not
    yet been sent to the user
    """
    def callback_minute():
        logging.debug("Checking for notifications to send")
        with db.get_connection() as conn:
            for listing in db.get_unsent_listing_notifications(conn, ):
                bot.send_message(
                    listing.chat_id,
                    text=f'There is a new listing: {listing.title} \n {listing.url}')
                db.mark_listing_as_sent(conn, listing.listing_id)
        t = threading.Timer(NOTIFICATION_CHECK_INTERVAL, callback_minute)
        t.start()
    return callback_minute

#


def main():
    # initialize the db if it doesn't yet exist
    db.initialize()

    # create the bot, using environment variable for the token
    TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
    if not TELEGRAM_TOKEN:
        raise Exception(
            "Please specify Telegram bot token as environment variable TELEGRAM_TOKEN")
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    updater = Updater(token=TELEGRAM_TOKEN)

    # register handlers for commands, convenient!
    updater.dispatcher.add_handler(watch_handler)
    updater.dispatcher.add_handler(stop_handler)
    updater.dispatcher.add_handler(list_open_contracts_handler)
    updater.dispatcher.add_handler(message_handler)
    updater.start_polling()

    # start checking for listings that need notifications sent
    make_callback_minute(bot)()
