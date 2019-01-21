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
HELP_TEXT = ('Please send "/watch <url>" with a valid Gumtree url like: \n\n' + 
            '/watch https://www.gumtree.co.za/s-furniture/western-cape/chair/v1c9181l3100001q0p1')

from functools import wraps
def with_db_connection(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        with db.get_connection() as conn:
            kwargs['conn'] = conn
            return f(*args, **kwargs)
    return wrapped

def handle_message(bot, update):
    """ Log an unrecognised message
    """
    with db.get_connection() as conn:
        db.insert_inbound_msg(conn, update.message.chat_id, update.message.text)


#


def start(bot, update):
    """ Handle a new user session
    """
    logger.warning("/start %s", update.message.chat_id)
    update.message.reply_text(f'Welcome! 🐶 \n{HELP_TEXT}')


@with_db_connection
def watch(bot, update, args, conn):
    """ Create a new contract for a user
    """
    logger.warning("/watch %s", args)
    url = args[0] if len(args) == 1 else 'None'
    if 'https://' not in args[0]:
        update.message.reply_text(HELP_TEXT)

    try:
        contract_id = db.insert_contract(conn, update.message.chat_id, url)
    except sqlite3.IntegrityError:
        update.message.reply_text('You are already watching that url')
        return

    update.message.reply_text('Added to your watch list 👍')
    # TODO: this could be moved to run async or something
    for _ in spider.yield_listings_from_soup(contract_id, url):
        pass
    db.mark_contract_active(conn, contract_id)


@with_db_connection
def stop(bot, update, args, conn):
    """ Deactivate a contract for a user
    """
    logger.warning("/stop %s", args)
    if not len(args) == 1 or not args[0].isdigit:
        update.message.reply_text('Please send "/stop <id>" with a valid id')
    db.deactivate_contract(conn, update.message.chat_id, args[0])
    update.message.reply_text('Stopped ✋')
    

@with_db_connection
def handle_list(bot, update, conn):
    """ Lists all contracts that are active
    """
    for contract in db.get_open_contracts_for_user(conn, update.message.chat_id):
        bot.send_message(
            contract.chat_id,
            f'Contract for url {contract.query}  \nTo stop watching it, send "/stop {contract.contract_id}"'
        )


def make_callback_minute(bot):
    """ Runs regularly to check for listings that have appeared but not
    yet been sent to the user
    """
    def callback_minute():
        logging.warning("Checking for notifications to send")
        with db.get_connection() as conn:
            for listing in db.get_unsent_listing_notifications(conn, ):
                bot.send_message(
                    listing.chat_id,
                    text=f'There is a new listing: {listing.title} \n {listing.url}')
                db.mark_listing_as_sent(conn, listing.listing_id)
        t = threading.Timer(NOTIFICATION_CHECK_INTERVAL, callback_minute)
        t.start()
    return callback_minute


def main():
    # initialize the db if it doesn't yet exist
    db.initialize()

    # create the bot, using environment variable for the token
    TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
    if not TELEGRAM_TOKEN:
        raise Exception("environment variable TELEGRAM_TOKEN should be Telegram bot token")
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    updater = Updater(token=TELEGRAM_TOKEN)

    # register handlers for commands, convenient!
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('watch', watch, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('stop', stop, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('list', handle_list))
    updater.dispatcher.add_handler(MessageHandler([], handle_message))
    updater.start_polling()

    # start checking for listings that need notifications sent
    make_callback_minute(bot)()
