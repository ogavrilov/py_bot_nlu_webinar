from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from botEngine import botEngineClass

def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi!')

def help_command(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')

def use_bot(update, context):
    answer = botEngineObj.get_answer(update.message.text)
    update.message.reply_text(answer)
    print(update.message.text, answer)
    print(botEngineObj.stats)
    print()

def main():
    """Start the bot."""
    print('start...')
    with open('tokendata.txt', 'r') as tokenHandle:
        tokenValue = tokenHandle.read()
    updater = Updater(tokenValue, use_context=True)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, use_bot))

    print('ready')

    updater.start_polling()
    updater.idle()

print('prepare...')
botEngineObj = botEngineClass('final_config.py', 'dialogs1.txt')
main()