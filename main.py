import bot
import logging

logging.basicConfig(filename="bot_log.log",
                    level=logging.WARNING, filemode='w')

if __name__ == "__main__":
    print("Starting bot")
    updater = bot.setup()

    updater.start_polling()
    updater.idle()
