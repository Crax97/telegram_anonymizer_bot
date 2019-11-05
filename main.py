from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, ForceReply, ReplyKeyboardMarkup, \
    InputTextMessageContent, ParseMode, TelegramError
from telegram.ext import Updater, CallbackQueryHandler, CommandHandler, InlineQueryHandler
from uuid import uuid4
from config import config

import logging
import utils

logging.basicConfig(filename="bot_log.log", level=logging.DEBUG)

updater = Updater(config["BOT_TOKEN"], use_context=True)
bot = updater.bot

anonymize_cmd = "send"


def make_report_keyboard(id, text):
    keyboard = [[
        InlineKeyboardButton("Report this message",
                             callback_data="report,%d,%s" % (id, text))
    ]]
    return InlineKeyboardMarkup(keyboard)


def make_ban_keyboard(id):
    button = [[
        InlineKeyboardButton("Ban this user", callback_data="ban,%s" % id)
    ]]
    return InlineKeyboardMarkup(button)


def strip_message_cmd(cmd, text):
    return text.lstrip("/" + cmd).lstrip()


def anonymize(update, ctx):
    user = update.message.from_user
    if utils.is_banned(user.id, config):
        update.message.reply_text("Sorry, you're banned from using this bot")
    elif utils.user_is_in_group(user.id, config, bot):
        message_no_cmd = strip_message_cmd(anonymize_cmd, update.message.text)
        if len(message_no_cmd) == 0:
            update.message.reply_text("Message is empty")
        else:
            try:
                bot.send_message(config["TARGET_CHAT"], message_no_cmd, reply_markup=make_report_keyboard(
                    update.message.from_user.id, message_no_cmd))
            except:
                update.message.reply_text(
                    "Sorry, can't send message to this chat")
    else:
        update.message.reply_text(
            "Sorry, this command is restricted to group members only")


def send_to_admins(message, **kwargs):
    print(config["BOT_ADMINS"])
    for admin in config["BOT_ADMINS"]:
        bot.send_message(
            admin,
            message,
            **kwargs,
        )


def report_handler(update, ctx, args, query):
    keyboard = make_ban_keyboard(args[1])
    send_to_admins(
        "*Someone reported this message:*\n\n%s" % args[2],
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN
    )
    query.edit_message_text(text="Message reported, thank you")


def ban_user(update, ctx, args, query):
    user_id = int(args[1])
    if utils.is_banned(user_id, config):
        query.edit_message_text(
            text="This user has already been banned by someone else")
    elif not utils.is_admin(user_id, config):
        config["BLACKLIST"] = {user_id} | set(config["BLACKLIST"])
        logging.info("Banned user %s" % user_id)
        query.edit_message_text(text="Ok, user banned")
    else:
        query.edit_message_text(
            text="Sorry, this user is one of the bot admins and can't therefore be banned")


def button_handler(update, ctx):
    query = update.callback_query
    query_data = query.data
    args = query_data.split(',')
    if args[0] == "report":
        report_handler(update, ctx, args, query)
    elif args[0] == "ban":
        utils.admins_only(ban_user, config, bot)(update, ctx, args, query)


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


def add_to_admins(user_id):
    config["BOT_ADMINS"] = set(config["BOT_ADMINS"]) | {user_id}


def get_username(user_id):
    try:
        chat = bot.get_chat_member(config["TARGET_CHAT"], user_id)
        user = chat.user
        return (user.username, True) if user.username else (user.first_name + " " + user.last_name, False)
    except TelegramError as e:
        logging.error(
            "Error trying to get the chat member with id " + user_id + ": " + e.message)
    return "User not found", False


def admin_button(update, ctx, args, query):
    user_id = update.message.from_user.id
    add_to_admins(user_id)


def makeadmin(update, ctx):
    message = update.message
    reply = message.reply_to_message
    if not reply:
        message.reply_text(
            "Reply to a message and the author will become admin")
    else:
        reply_author = reply.from_user.id
        config["BOT_ADMINS"] = set(config["BOT_ADMINS"]) | {reply_author}
        username, has_username = get_username(reply_author)
        message.reply_text("""Welcome %s to the admin team! Remember to start a private chat with me 
or you won't see reports and stuff!""" % ("@" + username if has_username else username))


def removeadmin(update, ctx):
    message = update.message
    reply = message.reply_to_message
    if not reply:
        message.reply_text(
            "Reply to a message and the author will become admin")
    else:
        reply_author = reply.from_user.id
        if utils.is_admin(reply_author, config):
            if utils.is_manager(reply_author, config):
                message.reply_text(
                    "Sorry, you can't remove the bot manager from the admins")
            else:
                config["BOT_ADMINS"] = set(
                    config["BOT_ADMINS"]) - {reply_author}
                username, has_username = get_username(reply_author)
                message.reply_text("%s lost the daddy privilege~!" % (
                    "@" + username if has_username else username))
        else:
            message.reply_text("This user is not an admin")


def error(update, context):
    logging.warning('Update "%s" caused error "%s"', update, context.error)


def listadmins(update, ctx):
    message = update.message
    reply = "List of current admins:\n"
    founder_name, has_name = get_username(config["BOT_MANAGER"])
    reply += "\tBot manager: " + founder_name + "\n"
    for admin in config["BOT_ADMINS"]:
        admin_name, has_name = get_username(admin)
        reply += "\t" + admin_name + "\n"
    message.reply_text(reply)


if __name__ == "__main__":
    print("Starting bot")
    updater.dispatcher.add_handler(CommandHandler(anonymize_cmd, anonymize))
    updater.dispatcher.add_handler(CommandHandler("info", chatinfo))
    updater.dispatcher.add_handler(InlineQueryHandler(inline_query))
    updater.dispatcher.add_handler(CallbackQueryHandler(button_handler))
    updater.dispatcher.add_handler(CommandHandler(
        "makeadmin", utils.admins_only(makeadmin, config, bot)))
    updater.dispatcher.add_handler(CommandHandler(
        "removeadmin", utils.admins_only(removeadmin, config, bot)))
    updater.dispatcher.add_handler(CommandHandler(
        "listadmins", utils.admins_only(listadmins, config, bot)))
    updater.dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()
