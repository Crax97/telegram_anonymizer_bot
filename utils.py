import storage
from telegram import ChatMember


def admins_only(f, bot):
    def anonymized(update, context):
        if storage.is_admin(update.message.from_user.id):
            f(update, context)
        else:
            update.message.reply_text("Sorry, this action is for admins only")
    return anonymized


def user_is_in_group(user_id, bot):
    try:
        chat = bot.get_chat_member(storage.get_target_chat(), user_id)
        return chat.status != ChatMember.LEFT and chat.status != ChatMember.KICKED and chat.status != ChatMember.RESTRICTED
    except:
        return False
