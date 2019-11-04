from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Updater, CallbackQueryHandler, CommandHandler, InlineQueryHandler
from uuid import uuid4
from config import config

import telegram
import logging

logging.basicConfig(filename="bot_log.log", level=logging.DEBUG)

updater = Updater(config["BOT_TOKEN"], use_context=True)
bot = updater.bot

anonymize_cmd = "send"

def make_keyboard(id, text):
    keyboard = [[
        InlineKeyboardButton("Report this message", callback_data="report,%d,%s" % (id, text))
    ]]

    return InlineKeyboardMarkup(keyboard)

def strip_message_cmd(cmd, text):
    return text.lstrip("/" + cmd).lstrip()

def anonymize(update, ctx):
    user = update.message.from_user
    if user.id in config["BLACKLIST"]:
        update.message.reply_text("Sorry, you're banned from using this bot")
    else:
        message_no_cmd = strip_message_cmd(anonymize_cmd, update.message.text)
        if len(message_no_cmd) == 0:
            update.message.reply_text("Message is empty")
        else:
            try:
                bot.send_message(config["TARGET_CHAT"], message_no_cmd, reply_markup=make_keyboard(update.message.from_user.id, message_no_cmd))
            except:
                update.message.reply_text("Sorry, can't send message to this chat")


def report_handler(update, ctx, args, query):
        button = [[
            InlineKeyboardButton("Ban this user", callback_data="ban,%s" % args[1])
        ]]
        query.edit_message_text(text="Message reported, thank you")
        bot.send_message(
            config["BOT_ADMIN"], 
            "**Someone reported this message:**\n%s" % args[2],
            reply_markup = InlineKeyboardMarkup(button),
            parse_mode='Markdown')

def ban_user(update, ctx, args, query):
    user_id = int(args[1])
    config["BLACKLIST"] = {user_id} | set(config["BLACKLIST"])
    logging.info("Banned user %s" % user_id)
    query.edit_message_text(text="Ok, user banned")

def button_handler(update, ctx):
    query = update.callback_query
    query_data = query.data
    args = query_data.split(',')
    if args[0] == "report":
        report_handler(update, ctx, args, query)
    elif args[0] == "ban":
        ban_user(update, ctx, args, query)
    

def inline_query(update, ctx):
    query = update.inline_query.query
    result = [
        InlineQueryResultArticle(
            id=uuid4(),
            title="Anonymized message",
                        input_message_content=InputTextMessageContent(
                            query)
        )
    ]
    update.inline_query.answer(result)

def chatinfo(update, ctx):
    if update.effective_chat:
        chat = update.effective_chat
        print(chat)
        update.message.reply_text("Wrote data to stdout")
    else:
        update.message.reply_text("Can't read chat info")

def error(update, context):
    logging.warning('Update "%s" caused error "%s"', update, context.error)

updater.dispatcher.add_handler(CommandHandler(anonymize_cmd, anonymize))
updater.dispatcher.add_handler(CommandHandler("info", chatinfo))
updater.dispatcher.add_handler(InlineQueryHandler(inline_query))
updater.dispatcher.add_handler(CallbackQueryHandler(button_handler))
updater.dispatcher.add_error_handler(error)

updater.start_polling()
updater.idle()