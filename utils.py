def is_manager(user_id, cfg):
    return user_id == cfg["BOT_MANAGER"]


def is_admin(user_id, cfg):
    return user_id in cfg["BOT_ADMINS"] or is_manager(user_id, cfg)


def is_banned(user_id, cfg):
    return user_id in cfg["BLACKLIST"]


def admins_only(f, cfg, bot):
    def anonymized(update, context):
        if is_admin(update.message.from_user.id, cfg):
            f(update, context)
        else:
            update.message.reply_text("Sorry, this action is for admins only")
    return anonymized


def user_is_in_group(user_id, cfg, bot):
    try:
        chat = bot.get_chat_member(cfg["TARGET_CHAT"], user_id)
        return chat != None
    except:
        return False
