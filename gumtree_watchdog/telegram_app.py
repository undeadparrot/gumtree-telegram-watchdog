# -*- coding: utf-8 -*-
import os
import logging
import sqlite3
import threading
import telegram
from telegram.ext import Updater, MessageHandler, CommandHandler

import gumtree_watchdog.cron_app
import gumtree_watchdog import db
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')

bot = telegram.Bot(token=TELEGRAM_TOKEN)

db.initialize()


def handle_message(bot, update):
    db.insert_inbound_msg(update.message.chat_id, update.message.text)


message_handler = MessageHandler([], handle_message)


def watch(bot, update, args):
    logger.warning("/watch %s", args)
    if not len(args) == 1 or 'https://' not in args[0]:
        update.message.reply_text(
            'Please send "/watch <url>" with a valid Gumtree url like: \n\n/watch https://www.gumtree.co.za/s-furniture/western-cape/chair/v1c9181l3100001q0p1'
        )

    try:
        contract_id = db.insert_contract(update.message.chat_id, args[0])
    except sqlite3.IntegrityError:
        update.message.reply_text('You are already watching that url')
        return

    update.message.reply_text(
        'Understood, doing a preliminary scrape of the search now')
    gumtree_watchdog.cron_app.run_contract(contract_id, args[0])
    db.mark_contract_active(contract_id)
    update.message.reply_text('Done.')


watch_handler = CommandHandler('watch', watch, pass_args=True)


def stop(bot, update, args):
    logger.warning("/stop %s", args)
    if not len(args) == 1 or not args[0].isdigit:
        update.message.reply_text('Please send "/stop <id>" with a valid id')

    db.deactivate_contract(update.message.chat_id, args[0])
    update.message.reply_text('Done.')


stop_handler = CommandHandler('stop', stop, pass_args=True)


def handle_list_open_contracts(bot, update):
    for contract in db.get_open_contracts_for_user(update.message.chat_id):
        #update.message.reply_text(f'Contract for url {contract["query"]}')
        bot.send_message(
            contract["chat_id"],
            f'Contract for url {contract["query"]}  \nTo stop watching it, send "/stop {contract["contract_id"]}"'
        )


list_open_contracts_handler = CommandHandler('list',
                                             handle_list_open_contracts)


def callback_minute():
    for listing in db.get_unsent_listing_notifications():
        bot.send_message(
            listing['chat_id'],
            text=
            f'There is a new listing: {listing["title"]} \n {listing["url"]}')
        db.mark_listing_as_sent(listing['listing_id'])
    t = threading.Timer(15.0, callback_minute)
    t.start()


updater = Updater(token=TELEGRAM_TOKEN)
updater.dispatcher.add_handler(watch_handler)
updater.dispatcher.add_handler(stop_handler)
updater.dispatcher.add_handler(list_open_contracts_handler)
updater.dispatcher.add_handler(message_handler)
updater.start_polling()
callback_minute()
