import logging
import requests
from telegram.ext import Application, MessageHandler, filters, CommandHandler
from telegram import ReplyKeyboardMarkup
import sqlite3
import schedule
import time
from threading import Thread
from datetime import datetime

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)

reply_keyboard = [['/help']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)

con = sqlite3.connect('info.db')
cur = con.cursor()
# cur.execute("""CREATE TABLE IF NOT EXISTS 'every_day' (
#           'chat_id' STRING PRIMARY KEY,
#          'currencies' STRING,
#         'valuta' STRING,
#        'time' STRING,
#       'active' INT
# );
#   """)
con.commit()


async def start(update, context):
    user = update.effective_user
    await update.message.reply_html(
        f"Привет {user.mention_html()}! Я бот Crypto.\nЯ отлично разбираюсь в криптовалютах\nЧтобы узнать, "
        f"что я умею, напишите команду/используйте кнопку /help", reply_markup=markup
    )


async def every_day_1(update, context):
    if update.message.text[0] == '/':
        context.user_data['locality'] = update.message.text
        await update.message.reply_text('Перечислите криптовалюты через пробел, '
                                        'информацию о цене которых вы хотите получать')
        await context.bot.send_photo(chat_id=update.effective_chat.id,
                                     photo='https://1.bp.blogspot.com/-NQbAx8h-SUM/YTEBXsw5v7I/AAAAAAAAHec/'
                                           '-OO_JHGX5MUJ9lljQxdZduyO7XEZUvzYQCLcBGAsYHQ/s1483/Gate3939364464664.jpg')
    else:
        context.user_data['locality'] = 'ed1'
        context.user_data['currencies'] = update.message.text.split()
        await update.message.reply_text('Укажите валюту, в которой вы хотите получать цены')


async def every_day_2(update, context):
    context.user_data['locality'] = 'ed2'
    context.user_data['valuta'] = update.message.text
    await update.message.reply_text('Укажите время, в которое вам удобно получать цены (формат "21:00")')


async def every_day_3(update, context):
    sl = context.user_data
    flag = True
    if update.message.text == '/off_every_day':
        flag = False
        await update.message.reply_text('Ежедневное оповещение отключено')
        cur.execute(f"""UPDATE every_day SET active = 0 WHERE chat_id = '{str(update.effective_chat.id)}'""")
        context.user_data.clear()

    if flag:
        await update.message.reply_text('Пробное оповещение:')
        for el in sl['currencies']:
            url = f'https://api.coinbase.com/v2/exchange-rates?currency={el.upper()}'
            response = requests.get(url)
            data = response.json()
            try:
                await update.message.reply_text(el.upper() + ' ' +
                                                str(round(float(data['data']['rates'][sl['valuta'].upper()]), 5))
                                                + ' ' + sl['valuta'])
            except Exception:
                await update.message.reply_text(
                    'Извини, но я тебя не понимаю. Возможно, ты некорректно указываешь названия валют.'
                )
                flag = False
        if flag:
            cur.execute(f"""INSERT INTO every_day (chat_id, currencies, valuta, time, active) 
            VALUES('{str(update.effective_chat.id)}', '{' '.join(sl['currencies'])}', '{sl['valuta'].upper()}', 
            '{update.message.text}', 1)""")
            con.commit()
            time = str(cur.execute(f"""SELECT time FROM every_day WHERE chat_id = 
            '{update.effective_chat.id}'"""))
            schedule.every().day.at(time).do(send_messange_every_day(update, context))
            Thread(target=schedule_checker).start()
        # if flag:
        #   while True:
        # time = str(cur.execute(f"""SELECT every_day, time FROM every_day WHERE chat_id = '{update.effective_chat.id}
        #         '"""))
        # if time in str(datetime.now()):
        #   await send_messange_every_day(update, context)
        #   time.sleep(120)


async def send_messange_every_day(update, context):
    if int(cur.execute(f"""SELECT active FROM every_day WHERE chat_id = '{update.effective_chat.id}'""")) == 1:
        await update.message.reply_text('Ежедневное оповещение:')
        currencies = str(
            cur.execute(f"""SELECT currencies FROM every_day WHERE chat_id = '{update.effective_chat.id}
        '""")).split()
        valuta = str(cur.execute(f"""SELECT valuta FROM every_day WHERE chat_id = '{update.effective_chat.id}
        '"""))

        for el in currencies:
            url = f'https://api.coinbase.com/v2/exchange-rates?currency={el.upper()}'
            response = requests.get(url)
            data = response.json()
            await update.message.reply_text(el.upper() + ' ' +
                                            str(round(float(data['data']['rates'][valuta.upper()]), 5))
                                            + ' ' + valuta)


async def help_command(update, context):
    await update.message.reply_text("Вот что я умею:\n/price - узнать актуальную цену интересующей вас криптовалюты\n"
                                    "/every_day - получать каждый день цены интересующих криптовалют "
                                    "в определённое время\n/off_every_day - отключить ежедневное оповещение")


async def find_out_the_price(update, context):
    if update.message.text == '/price':
        context.user_data['locality'] = update.message.text
        await update.message.reply_text("Чтобы узнать цену криптовалюты, сначала введите её обозначение, "
                                        "а далее через пробел обозначение валюты, в которой вы хотите получить цену."
                                        "\nНапример: BTC USD\n\n"
                                        "На картинке приведены примеры обозначения криптовалют ;)")
        await context.bot.send_photo(chat_id=update.effective_chat.id,
                                     photo='https://1.bp.blogspot.com/-NQbAx8h-SUM/YTEBXsw5v7I/AAAAAAAAHec/'
                                           '-OO_JHGX5MUJ9lljQxdZduyO7XEZUvzYQCLcBGAsYHQ/s1483/Gate3939364464664.jpg')
    url = f'https://api.coinbase.com/v2/exchange-rates?currency={update.message.text.split()[0].upper()}'
    response = requests.get(url)
    data = response.json()
    if update.message.text[0] != '/':
        try:
            await update.message.reply_text(
                str(round(float(data['data']['rates'][update.message.text.split()[1].upper()]), 5))
                + ' ' + update.message.text.split()[1])
        except Exception:
            await update.message.reply_text(
                'Извини, но я тебя не понимаю. Возможно, ты неккоректно указываешь названия валют.')


async def inputtt(update, context):
    if context.user_data['locality'] == '/price':
        context.user_data.clear()
        await find_out_the_price(update, context)
    elif context.user_data['locality'] == '/every_day':
        await every_day_1(update, context)
    elif 'ed1' == context.user_data['locality']:
        await every_day_2(update, context)
    elif 'ed2' == context.user_data['locality']:
        await every_day_3(update, context)


async def schedule_checker():
    while True:
        schedule.run_pending()
        time.sleep(1)


def main():
    application = Application.builder().token('6128097431:AAEb4zV_p9pn1WDLdkgm7PtkMIhaUgvntng').build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("price", find_out_the_price))
    application.add_handler(CommandHandler("every_day", every_day_1))
    application.add_handler(CommandHandler("off_every_day", every_day_3))
    text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, inputtt)
    application.add_handler(text_handler)
    application.run_polling()


if __name__ == '__main__':
    main()
