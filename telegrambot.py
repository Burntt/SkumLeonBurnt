import requests
import config
from datetime import datetime
from telegram.ext import *
import subprocess


telegram_api_key = config.authenticate._telegram_key


def sample_responses(input_text):
    user_message = str(input_text).lower()

    if user_message in ('hello', 'hi', 'sup', 'hey'):
        return 'Hey, how are you today?'

    if user_message in ('who are you?', 'who are you'):
        return 'I am SkumLeonBot'

    if user_message in ('time', 'time?'):
        now = datetime.now()
        date_time = now.strftime('%d/%m/%y, %H:%M:%S')
        return date_time

    return 'Man you are talking some rubbish'


print('Bot started...')


def start_command(update, context):
    update.message.reply_text('Type something random to get started!')


def rebootSkumLeon(update, context):
    send_msg('TelegramBot orders start subprocess: SkumLeonBot')
    SkumLeon = subprocess.Popen(['python3', 'openTwitterStream.py'])


def help_command(update, context):
    send_msg('/reboot for booting or rebooting the crypto trade bot')


def handle_message(update, context):
    text = str(update.message.text).lower()
    response = sample_responses(text)
    update.message.reply_text(response)


def send_msg(text):
    chat_id = '1346459589'
    #chat_id = '-588603813'
    url_req = 'https://api.telegram.org/bot' + telegram_api_key + '/sendMessage' + '?chat_id=' + chat_id + '&text=' + text
    results = requests.get(url_req)
    print('Send a message to Telegram')


def error(update, context):
    print(f"Update {update} caused error {context.error}")


def launchBot():
    send_msg('******* SKUMLEON MSG BOT ONLINE ******* \n'
             '               Ready for your commands, sir!      ')
    updater = Updater(telegram_api_key, use_context=True)

    # Dispatcher
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start_command))
    dp.add_handler(CommandHandler('reboot', rebootSkumLeon))
    dp.add_handler(CommandHandler('help', help_command))

    dp.add_handler(MessageHandler(Filters.text, handle_message))

    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()
    print('Closed Connection to Telegram')


if __name__ == "__main__":
    try:
        launchBot()
    except Exception as e:
        print('TelegramBot Crashed, re-running it')
        launchBot()