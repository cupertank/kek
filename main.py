import os
import psycopg2
import requests
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, RegexHandler, MessageHandler, CallbackQueryHandler
from telegram.ext.filters import Filters


def get_json(url):
    return requests.get(url).json()


def status(bot, updater):
    cur.execute('SELECT miners FROM main WHERE id=%s;', [updater.message.chat_id])
    miners = cur.fetchone()[0]
    if len(miners) == 0:
        bot.send_message(chat_id=updater.message.chat_id,
                         text='*You do not have any miners, add them in the settings.*',
                         parse_mode='Markdown')
        settings(bot, updater)
    else:
        for i in miners:
            json = get_json(i[2])
            text = '''*Worker:* _{0}_

📈 *Hashrate:*
⭐ _60s - {1}_
⭐ _2m - {2}_
⭐ _15m - {3}_

🔥 *Highest:* _{4}_

☄ *Difficult:* _{5}_
⏳ *Average time:* _{6}_
✅ *Shares:* _{7}/{8}_
⚡ *Pool:* _{9}_
🏓 *Ping:* _{10}ms_'''.format(json['worker_id'],
                       *json['hashrate']['total'],
                       json['hashrate']['highest'],
                       json['results']['diff_current'],
                       json['results']['avg_time'],
                       json['results']['shares_good'],
                       json['results']['shares_total'],
                       json['connection']['pool'],
                       json['connection']['ping'])
            bot.send_message(chat_id=updater.message.chat_id,
                             text=text,
                             parse_mode='Markdown')

def settings(bot, updater):
    cur.execute('SELECT miners[1:][2] FROM main WHERE id=%s;', [updater.message.chat_id])
    miners = cur.fetchone()[0]
    if len(miners) == 0:
        bot.send_message(chat_id=updater.message.chat_id,
                         text='☁ *So far, this is empty.*',
                         parse_mode='Markdown',
                         reply_markup=InlineKeyboardMarkup(
                             inline_keyboard=[
                                 [InlineKeyboardButton(text='➕ Add miner', callback_data='add')]
                             ]
                         ))
    else:
        text = '⏬ *Miners:*\n\n'
        for i in range(len(miners)):
            text += '🔴 *' + str(i + 1) + '. ' + miners[i][0] + ' - ' + miners[i][1] + '*' + '\n'
        bot.send_message(chat_id=updater.message.chat_id,
                         text=text,
                         parse_mode='Markdown',
                         reply_markup=InlineKeyboardMarkup(
                             inline_keyboard=[
                                 [InlineKeyboardButton(text='➕ Add new miner', callback_data='add')],
                                 [InlineKeyboardButton(text='❌ Delete miners', callback_data='del')]
                             ]
                         ))


def callback(bot, updater):
    if updater.callback_query.data == 'add': #ADD
        updater.callback_query.edit_message_text(text='⚡ Choose your miner',
                                                 reply_markup=InlineKeyboardMarkup(
                                                     inline_keyboard=[
                                                         [InlineKeyboardButton(text='✅ XMRIG', callback_data='10')]
                                                     ]
                                                 ))
    elif updater.callback_query.data == 'del': #Delete
        cur.execute('UPDATE main SET status=999 WHERE id=%s', [updater.callback_query.message.chat_id])
        bot.send_message(chat_id=updater.callback_query.message.chat_id,
                         text='❌ *Send the numbers of the miners you need to delete*',
                         parse_mode='Markdown',
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[
                                 ['⬅']
                             ],
                             resize_keyboard=True,
                             one_time_keyboard=False,
                             selective=True)
                         )
    elif updater.callback_query.data == '10':  # Добавление майнера XMRIG
        cur.execute('UPDATE main SET status=1 WHERE id=%s', [updater.callback_query.message.chat_id])
        bot.send_message(
            chat_id=updater.callback_query.message.chat_id,
            text='*Send me a link to the API*\n\ne.g. _http://0.0.0.0:1564_',
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    ['⬅']
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
    elif status == 1:  # ADD XMRIG
        try:
            req = requests.get(updater.message.text).json()
            cur.execute('SELECT miners FROM main WHERE id=%s', [updater.message.chat_id])
            miners = cur.fetchone()[0]
            miners.append([req['worker_id'], 'XMRIG', updater.message.text])
            miners = repr(miners).replace('[', '{').replace(']', '}').replace("'", '')
            cur.execute('UPDATE main SET miners=%s WHERE id=%s', [miners, updater.message.chat_id])
            send_buttons(bot, updater, text='✅ *Your link has been added*')
            settings(bot, updater)
        except:
            bot.send_message(chat_id=updater.message.chat_id,
                             text='*Link does not work, try again*',
                             parse_mode='Markdown')
    elif status == 999:
        cur.execute('SELECT miners FROM main WHERE id=%s', [updater.message.chat_id])
        miners = cur.fetchone()[0]
        data = list(map(int, str(updater.message.text).split()))
        data.sort(reverse=True)
        for num in data:
            try:
                miners.pop(num - 1)
            except:
                bot.send_message(chat_id=updater.message.chat_id,
                                 text='*Error, try again*',
                                 parse_mode='Markdown')
        miners = repr(miners).replace('[', '{').replace(']', '}').replace("'", '')
        cur.execute('UPDATE main SET miners=%s WHERE id=%s', [miners, updater.message.chat_id])
        send_buttons(bot, updater, text='❎ Deleted')
        settings(bot, updater)
    elif status == 228:
        send_buttons(bot, updater, text='✳ *Thanks for the feedback*')
        bot.send_message(chat_id=163327661,
                         text=updater.message.chat_id)
        bot.forward_message(chat_id=163327661,
                            from_chat_id=updater.message.chat_id,
                            message_id=updater.message.message_id)


def send_buttons(bot, updater, text='🏁 *Main menu:*'):
    cur.execute('UPDATE main SET status=0 WHERE id=%s;', [updater.message.chat_id])
    bot.send_message(
        chat_id=updater.message.chat_id,
        text=text,
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                ['📈 Status'],
                ['🔧 Settings', '✏ Feedback']
            ],
            resize_keyboard=True,
            one_time_keyboard=False,
            selective=True)
    )


def start(bot, updater):
    try:
        cur.execute('INSERT INTO main(id) VALUES (%s);', [updater.message.chat_id])
    finally:
        send_buttons(bot, updater,
                     text='*Hello, {0}!*\n\n*If you start the bot for the first time, then configure it*'.format(updater.message.from_user['first_name']),)
        settings(bot, updater)


def feedback(bot, updater):
    cur.execute('UPDATE main SET status=228 WHERE id=%s', [updater.message.chat_id])
    bot.send_message(chat_id=updater.message.chat_id,
                     text='☎ Write your wishes or describe the problem',
                     reply_markup=ReplyKeyboardMarkup(
                         keyboard=[
                             ['⬅']
                         ],
                         resize_keyboard=True,
                         one_time_keyboard=False,
                         selective=True)
                     )


if __name__ == '__main__':
    try:
        TOKEN = os.environ['TOKEN']
        DB = os.environ['DB']
        USER = os.environ['USER']
        PASS = os.environ['PASS']
        HOST = os.environ['HOST']
        PORTDB = os.environ['PORTDB']
    except:
        print('Чего-то не хвататет, чекай переменные')
        exit()
    updater = Updater(token=TOKEN)
    db = psycopg2.connect(database=DB,
                          user=USER,
                          password=PASS,
                          host=HOST,
                          port=PORTDB)
    db.autocommit = True
    cur = db.cursor()
    dispatcher = updater.dispatcher
    bot = updater.bot
    handlers = [
        CallbackQueryHandler(callback),

        RegexHandler('🔧 Settings', settings),
        RegexHandler('⬅', send_buttons),
        RegexHandler('📈 Status', status),
        RegexHandler('✏ Feedback', feedback),
        #RegexHandler('About', about),

        CommandHandler('start', start),

        MessageHandler(Filters.text, free),
    ]
    for i in handlers:
        dispatcher.add_handler(i)
    updater.start_polling()
