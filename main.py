from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, ForceReply, ReplyKeyboardMarkup, \
    InputTextMessageContent, ParseMode, TelegramError, Chat
from telegram.ext import Updater, CallbackQueryHandler, CommandHandler, InlineQueryHandler
from uuid import uuid4

import storage
import logging
import utils

logging.basicConfig(filename="bot_log.log", level=logging.DEBUG)

updater = Updater(storage.get_bot_token(), use_context=True)
bot = updater.bot

anonymize_cmd = "send"


def make_report_keyboard(id, text):
    keyboard = [[
        InlineKeyboardButton(storage.get_string("REPORT"),
                             callback_data="report,%d,%s" % (id, text))
    ]]
    return InlineKeyboardMarkup(keyboard)


def make_ban_keyboard(id):
    button = [[
        InlineKeyboardButton(storage.get_string(
            "BAN"), callback_data="ban,%s" % id)
    ]]
    return InlineKeyboardMarkup(button)


def strip_message_cmd(text):
    pos = text.find(' ')
    if pos == -1:
        return ''
    else:
        return text[pos:].strip()


def send_message(update, ctx):
    message_no_cmd = strip_message_cmd(update.message.text)
    if len(message_no_cmd) == 0:
        update.message.reply_text(storage.get_string("EMPTY_MSG"))
    else:
        try:
            bot.send_message(storage.get_target_chat(), message_no_cmd, reply_markup=make_report_keyboard(
                update.message.from_user.id, message_no_cmd))
            update.message.reply_text(storage.get_string("MSG_SENT"))
        except Exception as e:
            print(e)
            update.message.reply_text(
                storage.get_string("CANT_SEND"))


def anonymize(update, ctx):
    user = update.message.from_user
    if storage.is_banned(user.id):
        update.message.reply_text(storage.get_string("USER_IS_BANNED"))
    elif not utils.user_is_in_group(user.id, bot):
        update.message.reply_text(
            storage.get_string("GROUP_MEMS_ONLY"))
    else:
        send_message(update, ctx)


def send_to_admins(message, **kwargs):
    for admin in storage.get_admin_set():
        try:
            bot.send_message(
                admin,
                message,
                **kwargs,
            )
        except TelegramError as err:
            logging.error("Got telegram error: " + err.message)


def report_handler(update, ctx, args, query):
    keyboard = make_ban_keyboard(args[1])
    send_to_admins(
        storage.get_string("REPORTED_ADMIN_MSG") % args[2],
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN
    )
    query.edit_message_text(text=storage.get_string("REPORTED_REPLY"))


def ban_user(update, ctx, args, query):
    user_id = int(args[1])
    if storage.is_banned(user_id):
        query.edit_message_text(
            text=storage.get_string("USER_ALREADY_BANNED"))
    elif not storage.is_admin(user_id):
        storage.ban_user(user_id)
        logging.info("Banned user %s" % user_id)
        query.edit_message_text(text=storage.get_string("USER_BANNED"))
    else:
        query.edit_message_text(
            text=storage.get_string("USER_IS_ADMIN"))


def unban(update, ctx):
    message = update.message
    reply = message.reply_to_message
    if not reply:
        message.reply_text(
            storage.get_string("UNBAN_NO_REPLY"))
    else:
        reply_author = reply.from_user.id
        storage.unban_user(reply_author)
        message.reply_text(storage.get_string("UNBAN_OK"))


def button_handler(update, ctx):
    query = update.callback_query
    query_data = query.data
    args = query_data.split(',')
    if args[0] == "report":
        report_handler(update, ctx, args, query)
    elif args[0] == "ban":
        if storage.is_admin(query.from_user.id):
            ban_user(update, ctx, args, query)
        else:
            query.edit_message_text(text=storage.get_string("USER_NOT_ADMIN"))


def get_username(user_id):
    try:
        chat = bot.get_chat_member(storage.get_target_chat(), user_id)
        user = chat.user
        return (user.username, True) if user.username else (user.first_name + " " + user.last_name, False)
    except TelegramError as e:
        logging.error(
            "Error trying to get the chat member with id " + user_id + ": " + e.message)
    return "", False


def makeadmin(update, ctx):
    message = update.message
    reply = message.reply_to_message
    if not reply:
        message.reply_text(
            storage.get_string("MAKEADMIN_NO_REPLY"))
    else:
        reply_author = reply.from_user.id
        storage.add_admin(reply_author)
        username, has_username = get_username(reply_author)
        message.reply_text(storage.get_string("ADMIN_GREETING") %
                           ("@" + username if has_username else username))


def removeadmin(update, ctx):
    message = update.message
    reply = message.reply_to_message
    if not reply:
        message.reply_text(
            storage.get_string("REMOVEADMIN_NO_REPLY"))
    else:
        reply_author = reply.from_user.id
        if storage.is_admin(reply_author):
            if storage.is_manager(reply_author):
                message.reply_text(
                    storage.get_string("REMOVEADMIN_IS_MANAGER"))
            else:
                storage.remove_admin(reply_author)
                username, has_username = get_username(reply_author)
                message.reply_text(storage.get_string("REMOVEADMIN_SUCCESS") % (
                    "@" + username if has_username else username))
        else:
            message.reply_text(storage.get_string(
                "REMOVEADMIN_USER_NOT_ADMIN"))


def error(update, context):
    logging.warning('Update "%s" caused error "%s"', update, context.error)


def listadmins(update, ctx):
    message = update.message
    reply = storage.get_string("LIST_ADMINS_STRING")
    admins = ""
    founder_name, has_name = get_username(storage.get_bot_manager())
    for admin in storage.get_admin_set():
        admin_name, has_name = get_username(admin)
        admins += "\t" + admin_name + "\n"
    message.reply_text(reply % (founder_name, admins))


def setcurrentgroup(update, context):
    storage.set_target_chat(update.effective_chat.id)
    update.message.reply_text(
        storage.get_string("SET_GROUP_OK"))


def setlocale(update, context):
    locale = strip_message_cmd(update.message.text)
    if storage.set_locale(locale):
        update.message.reply_text(storage.get_string("LOCALE_SET"))
    else:
        update.message.reply_text(storage.get_string("LOCALE_NOT_PRESENT"))


if __name__ == "__main__":
    print("Starting bot")
    updater.dispatcher.add_handler(CommandHandler(anonymize_cmd, anonymize))
    updater.dispatcher.add_handler(CommandHandler(
        "setgroup", utils.admins_only(setcurrentgroup, bot)))
    updater.dispatcher.add_handler(CallbackQueryHandler(button_handler))
    updater.dispatcher.add_handler(CommandHandler(
        "makeadmin", utils.admins_only(makeadmin, bot)))
    updater.dispatcher.add_handler(CommandHandler(
        "removeadmin", utils.admins_only(removeadmin, bot)))
    updater.dispatcher.add_handler(CommandHandler(
        "listadmins", utils.admins_only(listadmins, bot)))
    updater.dispatcher.add_handler(CommandHandler(
        "unban", utils.admins_only(unban, bot)))
    updater.dispatcher.add_handler(CommandHandler(
        "setlocale", utils.admins_only(setlocale, bot)))
    updater.dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()
