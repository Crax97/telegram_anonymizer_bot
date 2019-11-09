import storage
from telegram import ChatMember, TelegramError, InlineKeyboardButton, InlineKeyboardMarkup, TelegramError, MessageEntity
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
    data = "report,%d" % (id)
    keyboard = [[
        InlineKeyboardButton(storage.get_string("REPORT"),
                             callback_data=data)
    ]]
    return InlineKeyboardMarkup(keyboard)

def get_formatted_entities(message):
    formatted_entities = []
    entity_map = {
        MessageEntity.BOLD : ('*', '*'),
        MessageEntity.ITALIC : ('_', '_'),
        MessageEntity.TEXT_LINK : ('[', ']'),
        MessageEntity.CODE : ('`', '`'),
        MessageEntity.PRE : ('```', '```'),
    }
    entities = message.parse_entities()
    filtered_types = (MessageEntity.BOT_COMMAND, MessageEntity.CASHTAG, MessageEntity.EMAIL, MessageEntity.HASHTAG, MessageEntity.MENTION, MessageEntity.PHONE_NUMBER, MessageEntity.TEXT_MENTION)
    for key in filter(lambda ent: ent.type not in filtered_types, entities):
        begin = key.offset
        end = begin + key.length
        formats = entity_map.get(key.type, ("", ""))
        entity_text = entities[key]
        formatted_entity_text = formats[0] + entity_text + formats[1]
        if key.type == MessageEntity.TEXT_LINK:
            formatted_entity_text += "(" + key.url + ")"
        formatted_entities += [(begin, end, formatted_entity_text)]
    formatted_entities = sorted(formatted_entities, key= lambda ent: ent[0])
    return formatted_entities

def replace_formatted(original_text, formatted_entities):
    cur_begin = 0
    cur_end = 0
    formatted_message = ""
    for ent in formatted_entities:
        cur_end = ent[0]
        formatted_message += original_text[cur_begin: cur_end] + ent[2]
        cur_begin = ent[1]
    formatted_message += original_text[cur_begin: ]
    return formatted_message



def format_message(message):
    original_text = message.text
    formatted_entities = get_formatted_entities(message)
    return replace_formatted(original_text, formatted_entities)
    

def make_ban_keyboard(id):
    data = "ban,%s" % id
    print(data)
    button = [[
        InlineKeyboardButton(storage.get_string(
            "BAN"), callback_data=data)
    ]]
    return InlineKeyboardMarkup(button)
