import os

import psycopg2
import requests
import telegram
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, RegexHandler, MessageHandler, CallbackQueryHandler
from telegram.ext.filters import Filters

def settings(bot, updater):
    cur.execute('SELECT miners[1:][2] FROM main WHERE id=%s;', [updater.message.chat_id])
    miners = cur.fetchone()[0]
    if len(miners) == 0:
        bot.send_message(chat_id=updater.message.chat_id,
                         text='Кажеца у вас туть пуста',
                         reply_markup=InlineKeyboardMarkup(
                         inline_keyboard=[
                             [InlineKeyboardButton(text='Add new miner', callback_data='add')]
                         ]
                         ))
    else:
        text = 'Такс, што тут у нас есть: \n\n'
        for i in range(len(miners)):
            text += str(i + 1) + '. ' + miners[i][0] + ' - ' + miners[i][1] + '\n'
        bot.send_message(chat_id=updater.message.chat_id,
                         text=text,
                         reply_markup=InlineKeyboardMarkup(
                             inline_keyboard=[
                                 [InlineKeyboardButton(text='Add new miner', callback_data='add')],
                                 [InlineKeyboardButton(text='Delete miner', callback_data='del')]
                             ]
                         ))

def callback(bot, updater):
    if updater.callback_query.data == 'add':
        updater.callback_query.edit_message_text(text='Выбирай кого добавим сегодня',
                                                 reply_markup=InlineKeyboardMarkup(
                                                     inline_keyboard=[
                                                         [InlineKeyboardButton(text='XMRIG', callback_data='10')]
                                                     ]
                                                 ))
    elif updater.callback_query.data == 'del':
        cur.execute('UPDATE main SET status=999 WHERE id=%s', [updater.callback_query.message.chat_id])
        bot.send_message(chat_id=updater.callback_query.message.chat_id,
                         text='Кинь номер кого кастрируем сегодня',
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[
                                 ['Back']
                             ],
                             resize_keyboard=True,
                             one_time_keyboard=False,
                             selective=True)
                         )
    elif updater.callback_query.data == '10': # Добавление майнера XMRIG
        cur.execute('UPDATE main SET status=1 WHERE id=%s', [updater.callback_query.message.chat_id])
        bot.send_message(
            chat_id=updater.callback_query.message.chat_id,
            text='Вышли мне ссылачку!!!',
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    ['Back']
                ],
                resize_keyboard=True,
                one_time_keyboard=False,
                selective=True)
        )

def free(bot, updater):
    cur.execute('SELECT status FROM main WHERE id=%s;', [updater.message.chat_id])
    status = cur.fetchone()[0]
    if status == 0:  # IDLE
        send_buttons(bot, updater)
    elif status == 1:  #ADD XMRIG
        try:
            req = requests.get(updater.message.text).json()
            cur.execute('SELECT miners FROM main WHERE id=%s', [updater.message.chat_id])
            miners = cur.fetchone()[0]
            miners.append([req['worker_id'], 'XMRIG', updater.message.text])
            miners = repr(miners).replace('[', '{').replace(']', '}').replace("'", '')
            cur.execute('UPDATE main SET miners=%s WHERE id=%s', [miners, updater.message.chat_id])
            send_buttons(bot, updater, text='Отлично, мы добавили твою ссылку!!!')
            settings(bot, updater)
        except:
            bot.send_message(chat_id=updater.message.chat_id,
                             text='Ссылка ниработает')
    elif status == 999:
        cur.execute('SELECT miners FROM main WHERE id=%s', [updater.message.chat_id])
        miners = cur.fetchone()[0]
        data = list(map(int,str(updater.message.text).split()))
        data.sort(reverse=True)
        for num in data:
            try:
                miners.pop(num-1)
            except:
                bot.send_message(chat_id=updater.message.chat_id,
                                 text='Ну ты где-то косякнул, мда')
        miners = repr(miners).replace('[', '{').replace(']', '}').replace("'", '')
        cur.execute('UPDATE main SET miners=%s WHERE id=%s', [miners, updater.message.chat_id])
        send_buttons(bot, updater, text='Удолили')
        settings(bot, updater)

def send_buttons(bot, updater, text='Главное меню:'):
    cur.execute('UPDATE main SET status=0 WHERE id=%s;', [updater.message.chat_id])
    bot.send_message(
        chat_id=updater.message.chat_id,
        text=text,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                ['Status'],
                ['Settings']
            ],
            resize_keyboard=True,
            one_time_keyboard=False,
            selective=True)
    )

def start(bot, updater):
    try:
        cur.execute('INSERT INTO main(id) VALUES (%s);', [updater.message.chat_id])
    finally:
        send_buttons(bot, updater, text='Hello, {0}!\n\nЕсли вы запускаете бота впервые, то настройте его'.format(
            updater.message.from_user['first_name']))
        settings(bot, updater)

if __name__ == '__main__':
    if os.environ.get('TOKEN') != None:
        TOKEN = os.environ.get('TOKEN')
    else:
        print('NO TOKEN!!!')
        exit()
    updater = Updater(token=TOKEN)
    db = psycopg2.connect(database='d3s8e4vposarfr',
                          user='jcehqdoniwgelx',
                          password='3fa0a65e027f5ec0c42c5c03ae7a63958313745bc47cf3ec2b9c613a3a8b0229',
                          host='ec2-54-228-181-43.eu-west-1.compute.amazonaws.com',
                          port='5432')
    db.autocommit = True
    cur = db.cursor()
    dispatcher = updater.dispatcher
    bot = updater.bot
    handlers = [
        CommandHandler('start', start),
        CallbackQueryHandler(callback),
        RegexHandler('Settings', settings),
        RegexHandler('Back', send_buttons),
        MessageHandler(Filters.text, free),
    ]
    for i in handlers:
        dispatcher.add_handler(i)
    updater.start_polling()