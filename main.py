import telegram
import os
import psycopg2

from requests import get
from requests.auth import HTTPDigestAuth

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, Dispatcher, CommandHandler, RegexHandler, MessageHandler

from time import sleep, time    

def settings(bot, updater):
    bot.send_message(
            chat_id=updater.message.chat_id,
            text=text,
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    ['Change URL miner','Change URL Dwarfpool'],
                    ['Back']
                    ],
                resize_keyboard=True,
                one_time_keyboard=False,
                selective=True)
            )

def free(bot, updater):
    cur.execute('SELECT status FROM main WHERE id=%s;',[updater.message.chat_id])
    status = cur.fetchone()[0]
    if status == 0: # IDLE 
        send_buttons(bot, updater)
    elif status == 1: # Send URL miner
        cur.execute('UPDATE main SET url_mine=%s, status=0 WHERE id=%s;', [updater.message.text, updater.message.chat_id])
        db.commit()
    elif status == 2: # Send URL dwarfpool
        cur.execute('UPDATE main SET url_dw=%s, status=0 WHERE id=%s;', [updater.message.text, updater.message.chat_id])
        db.commit()

def send_buttons(bot, updater, text):
    bot.send_message(
            chat_id=updater.message.chat_id,
            text=text,
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    ['Status','Balance'],
                    ['Settings']
                    ],
                resize_keyboard=True,
                one_time_keyboard=False,
                selective=True)
            )

def start(bot, updater):
    try:
        cur.execute('INSERT INTO main(id) VALUES (%s);', [updater.message.chat_id])
        db.commit()
    finally:
        send_buttons(bot, updater, 'Hello, {0}!\n\nЕсли вы запускаете бота впервые, то настройте его'.format(updater.message.from_user['first_name']))
        

if __name__ == '__main__':
    if os.environ.get('TOKEN') != None:
        TOKEN = os.environ.get('TOKEN')
    else:
        print('NO TOKEN!!!')
        exit()
    updater = Updater(token=TOKEN)
    db = psycopg2.connect(database='datnhcfftfdohq',
                          user='mcqaooayohacll',
                          password='86a4178ca0a22c40050e87497dc644fd822dad4822cacea440b8c01b67e31ecf',
                          host='ec2-79-125-117-53.eu-west-1.compute.amazonaws.com',
                          port='5432')
    cur = db.cursor()
    dispatcher = updater.dispatcher
    bot = updater.bot
    handlers = [
        CommandHandler('start', start),
        RegexHandler('Settings', settings),
        MessageHandler(telegram.ext.filters.Filters.text, free),
        ]
    for i in handlers: dispatcher.add_handler(i)
    updater.start_polling()
    updater.idle()
