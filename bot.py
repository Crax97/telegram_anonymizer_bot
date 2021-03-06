import storage
import utils
import logging

from string import Template
from telegram import ParseMode, Chat, InlineKeyboardMarkup, TelegramError
from telegram.ext import Updater, CallbackQueryHandler, CommandHandler, \
    MessageHandler, Filters

updater = Updater(storage.get_bot_token(), use_context=True)
bot = updater.bot

awaiting_warn_reason = {}


def start(update, ctx):
    chat = update.effective_chat
    if chat.type == Chat.GROUP:
        update.message.reply_text(storage.get_string("BOT_GREETING_GROUP"))
    else:
        update.message.reply_text(storage.get_string("BOT_GREETING_USER"))


def listadmins(update, ctx):
    message = update.message
    reply = storage.get_string("LIST_ADMINS_STRING")
    admins = ""
    for admin in storage.get_admin_set():
        admin_name = utils.get_username(admin, bot)
        print(admin_name)
        admins += "\t" + admin_name + "\n"
    template = Template(reply)
    message.reply_text(template.safe_substitute(
        admins=admins), parse_mode=ParseMode.HTML)


def setcurrentgroup(update, context):
    storage.set_target_chat(update.effective_chat.id)
    update.message.reply_text(
        storage.get_string("SET_GROUP_OK"))


def setlocale(update, context):
    locale = utils.strip_message_cmd(update.message.text)
    if storage.set_locale(locale):
        update.message.reply_text(storage.get_string("LOCALE_SET"))
    else:
        update.message.reply_text(storage.get_string("LOCALE_NOT_PRESENT"))


def makeadmin(update, ctx):
    message = update.message
    reply = message.reply_to_message
    if not reply:
        message.reply_text(
            storage.get_string("MAKEADMIN_NO_REPLY"))
    else:
        reply_author = reply.from_user.id
        if reply_author != bot.id:
            storage.add_admin(reply_author)
            username = utils.get_username(reply_author, bot)
            template = Template(storage.get_string("ADMIN_GREETING"))
            message.reply_text(template.safe_substitute(
                               admin=username), parse_mode=ParseMode.HTML)
        else:
            message.reply_text(storage.get_string("REPLY_ID_SAME_AS_BOT"))


def removeadmin(update, ctx):
    message = update.message
    reply = message.reply_to_message
    if not reply:
        message.reply_text(
            storage.get_string("REMOVEADMIN_NO_REPLY"))
    else:
        reply_author = reply.from_user.id
        username = utils.get_username(reply_author, bot)
        if storage.is_admin(reply_author):
            if storage.is_manager(reply_author):
                message.reply_text(
                    storage.get_string("REMOVEADMIN_IS_MANAGER"))
            else:
                storage.remove_admin(reply_author)
                string_template = Template(
                    storage.get_string("REMOVEADMIN_SUCCESS"))
                message.reply_text(string_template.safe_substitute(
                    username=username), parse_mode=ParseMode.HTML)
        else:
            string_template = Template(
                storage.get_string("REMOVEADMIN_USER_NOT_ADMIN"))
            message.reply_text(string_template.safe_substitute(
                username=username), parse_mode=ParseMode.HTML)


def send_message(update, ctx):
    message_text = utils.format_message(update.message)
    if len(message_text) == 0:
        update.message.reply_text(storage.get_string("EMPTY_MSG"))
    else:
        try:
            bot.send_message(storage.get_target_chat(), message_text, reply_markup=utils.make_report_keyboard(
                update.message.from_user.id), parse_mode=ParseMode.HTML)
            update.message.reply_text(storage.get_string("MSG_SENT"))
        except Exception as e:
            template = Template(storage.get_string("CANT_SEND"))
            update.message.reply_text(
                template.safe_substitute(message=e.message))


def anonymize(update, ctx):
    user = update.message.from_user

    if user.id in awaiting_warn_reason:
        get_reason_and_warn(update, ctx)
    else:
        if storage.is_banned(user.id):
            update.message.reply_text(storage.get_string("USER_IS_BANNED"))
        elif not utils.user_is_in_group(user.id, bot):
            update.message.reply_text(
                storage.get_string("GROUP_MEMS_ONLY"))
        else:
            if not update.message.text:
                update.message.reply_text(storage.get_string("ONLY_TEXT"))
            else:
                send_message(update, ctx)


def get_reporter_and_user_handles(rep_id, author_id):
    username = utils.get_username(author_id, bot)
    reporter_name = utils.get_username(rep_id, bot)

    return (reporter_name, username)


def report_handler(update, ctx, args, query):
    user_id = int(args[1])
    reporter_id = query.from_user.id
    message_id = query.message.message_id
    keyboard = utils.make_admin_keyboard(user_id, reporter_id, message_id)

    reporter_handle, user_handle = get_reporter_and_user_handles(
        reporter_id, user_id)

    template = Template(storage.get_string("REPORTED_ADMIN_MSG"))
    utils.send_to_admins(
        template.safe_substitute(
            message=query.message.text, username=user_handle,
            reporter=reporter_handle),
        bot,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )
    query.edit_message_reply_markup(InlineKeyboardMarkup([[]]))


def ban_user(update, ctx, args, query):
    user_id = int(args[1])
    msg_id = int(args[2])
    bot.delete_message(storage.get_target_chat(), msg_id)
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


def warn_user(update, ctx, args, query):
    user_id = int(args[1])
    msg_id = int(args[2])
    should_hide_msg = bool(int(args[3]))
    warns = storage.get_warns_for_user(user_id)
    if user_id in storage.get_admin_set():
            query.edit_message_text(
                text=storage.get_string("USER_IS_ADMIN"))
    else:
        if msg_id in warns:
            query.edit_message_text(
                text=storage.get_string("WARN_WARNED_ALREADY_2"))
        else:
            query.edit_message_text(
                text=storage.get_string("WARN_WRITE_REASON"))
            warn_initiator = query.from_user.id
            awaiting_warn_reason[warn_initiator] = (user_id, msg_id)
        if should_hide_msg:
            bot.delete_message(storage.get_target_chat(), msg_id)


def send_to_user_or_group(user_id, message):
    try:
        bot.send_message(user_id, message)
    except TelegramError as e:
        try:
            print(e)
            formatted_msg = utils.get_username(user_id, bot) + ": " + message
            bot.send_message(storage.get_target_chat(),
                             formatted_msg, parse_mode=ParseMode.HTML)
        except TelegramError as e:
            print("Well i tried hard enough " + e.message)


def get_reason_and_warn(update, ctx):
    reason = update.message.text
    warn_initiator = update.effective_user.id
    user_id, timestamp = awaiting_warn_reason[warn_initiator]
    warns = storage.get_warns_for_user(user_id)
    if timestamp in warns:
        update.reply_text(
            storage.get_string("WARNED_WARNED_ALREADY_1"))
    else:
        warn_count = storage.add_warn_to_user(user_id, timestamp)
        template = Template(storage.get_string("WARN_WARNED"))
        username = utils.get_username(user_id, bot)
        update.message.reply_text(
            template.safe_substitute(username=username, warns=warn_count, max=storage.get_max_warns()))
        if warn_count == storage.get_max_warns():
            send_to_user_or_group(
                user_id, storage.get_string("WARN_BANNED"))
        else:
            template_user = Template(storage.get_string("WARN_WARNED_USER"))
            send_to_user_or_group(user_id, template_user.safe_substitute(
                reason = reason, warns = warn_count, max = storage.get_max_warns()))

        del awaiting_warn_reason[warn_initiator]


def button_handler(update, ctx):
    query = update.callback_query
    query_data = query.data
    args = query_data.split(',')
    if args[0] == "report":
        report_handler(update, ctx, args, query)
    elif storage.is_admin(query.from_user.id):
        if args[0] == "ban":
            ban_user(update, ctx, args, query)
        elif args[0] == "warn":
            return warn_user(update, ctx, args, query)
    else:
        query.edit_message_text(text=storage.get_string("USER_NOT_ADMIN"))


def unban(update, ctx):
    message = update.message
    reply = message.reply_to_message
    if not reply:
        message.reply_text(
            storage.get_string("UNBAN_NO_REPLY"))
    else:
        reply_author = reply.from_user.id
        storage.unban_user(reply_author)
        storage.clear_warnings(reply_author)
        message.reply_text(storage.get_string("UNBAN_OK"))


def error(update, context):
    string = 'Update "%s" caused error "%s", ctx: "%s' % (update, context.error, context)
    logging.warning(string)
    utils.send_to_manager(string, bot)


def remove_warns(update, ctx):
    message = update.message
    reply = message.reply_to_message
    if not reply:
        message.reply_text(
            storage.get_string("UNWARN_NO_REPLY"))
    else:
        reply_author = reply.from_user.id
        username = utils.get_username(reply_author, bot)
        template = Template(storage.get_string("UNWARN_OK"))
        storage.clear_warnings(reply_author)
        message.reply_text(template.safe_substitute(username=username))

def setup():
    # Non-admins
    updater.dispatcher.add_handler(MessageHandler(
        Filters.private & (~Filters.command), anonymize))
    updater.dispatcher.add_handler(CommandHandler(
        "listadmins", listadmins))
    updater.dispatcher.add_handler(CommandHandler(
        "start", start))

    # Admins-only commands
    updater.dispatcher.add_handler(CommandHandler(
        "setgroup", utils.admins_only(setcurrentgroup, bot)))
    updater.dispatcher.add_handler(
        CallbackQueryHandler(button_handler))
    updater.dispatcher.add_handler(CommandHandler(
        "makeadmin", utils.admins_only(makeadmin, bot)))
    updater.dispatcher.add_handler(CommandHandler(
        "removeadmin", utils.admins_only(removeadmin, bot)))
    updater.dispatcher.add_handler(CommandHandler(
        "unban", utils.admins_only(unban, bot)))
    updater.dispatcher.add_handler(CommandHandler(
        "setlocale", utils.admins_only(setlocale, bot)))
    updater.dispatcher.add_handler(CommandHandler(
        "removewarns", utils.admins_only(remove_warns, bot)))

    # Error handler
    updater.dispatcher.add_error_handler(error)

    return updater
