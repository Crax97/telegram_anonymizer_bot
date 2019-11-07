import storage
from telegram import ChatMember, TelegramError, InlineKeyboardButton, InlineKeyboardMarkup, TelegramError
import logging


def admins_only(f, bot, *largs):
    def anonymized(update, context, *largs):
        if storage.is_admin(update.message.from_user.id):
            f(update, context, *largs)
        else:
            update.message.reply_text(storage.get_string("USER_NOT_ADMIN"))
    return anonymized


def send_to_admins(message, bot, **kwargs):
    for admin in storage.get_admin_set():
        try:
            bot.send_message(
                admin,
                message,
                **kwargs,
            )
        except TelegramError as err:
            logging.error("Got telegram error: " + err.message)


def send_to_manager(message, bot, **kwargs):
    try:
        bot.send_message(
            storage.get_bot_manager(),
            message,
            **kwargs,
        )
    except TelegramError as err:
        logging.error("Got telegram error: " + err.message)


def user_is_in_group(user_id, bot):
    try:
        chat = bot.get_chat_member(storage.get_target_chat(), user_id)
        return chat.status != ChatMember.LEFT and chat.status != ChatMember.KICKED and chat.status != ChatMember.RESTRICTED
    except TelegramError as e:
        return False


def strip_message_cmd(text):
    pos = text.find(' ')
    if pos == -1:
        return ''
    else:
        return text[pos:].strip()


def get_username(user_id, bot):
    try:
        chat = bot.get_chat_member(storage.get_target_chat(), user_id)
        user = chat.user
        return (user.username, True) if user.username else (user.first_name + " " + user.last_name, False)
    except TelegramError as e:
        logging.error(
            "Error trying to get the chat member with id " + user_id + ": " + e.message)
    return "", False


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
