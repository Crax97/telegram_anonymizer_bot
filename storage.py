import shelve
from config import config
import utils

storage = shelve.open("storage")

def add_admin(user_id):
    storage["BOT_ADMINS"] = (storage.get(
        "BOT_ADMINS", set({})) | {user_id}) - {config["BOT_MANAGER"]}


def remove_admin(user_id):
    storage["BOT_ADMINS"] = storage.get("BOT_ADMINS", set({})) - {user_id}


def is_manager(user_id):
    return user_id == config["BOT_MANAGER"]


def get_bot_manager():
    return config["BOT_MANAGER"]


def ban_user(user_id):
    storage["BANNED_USERS"] = storage.get("BANNED_USERS", set({})) | {user_id}


def unban_user(user_id):
    storage["BANNED_USERS"] = storage.get("BANNED_USERS", set({})) - {user_id}


def is_banned(user_id):
    return user_id in storage.get("BANNED_USERS", set({}))


def is_admin(user_id):
    return user_id in storage.get("BOT_ADMINS", set({})) or is_manager(user_id)


def get_admin_set():
    return storage.get("BOT_ADMINS", set({})) | {config["BOT_MANAGER"]}


def get_target_chat():
    return storage.get("TARGET_CHAT", 0)


def set_target_chat(chat_id):
    storage["TARGET_CHAT"] = chat_id


def get_bot_token():
    return config["BOT_TOKEN"]


def get_string(string):
    locale = storage.get("LOCALE", "en")
    string = config["TRANSLATIONS"][locale].get(string, string)
    return string


def get_warns_for_user(user_id):
    return storage.get("WARNS", {}).get(user_id, set({}))


def get_max_warns():
    return config["MAX_WARNS"]


def add_warn_to_user(user_id, message_id):
    ## TODO: Ew
    warns_dict = storage.get(
        "WARNS", {})
    warns_updated_for_user = get_warns_for_user(user_id) | {message_id}
    warns_dict[user_id] = warns_updated_for_user
    storage["WARNS"] = warns_dict
    if len(warns_updated_for_user) == get_max_warns():
        ban_user(user_id)
    return len(warns_updated_for_user)

def clear_warnings(user_id):
    warns_dict = storage.get(
        "WARNS", {})
    warns_dict[user_id] = set({})
    storage["WARNS"] = warns_dict

def set_locale(newlocale):
    if newlocale in config["TRANSLATIONS"]:
        storage["LOCALE"] = newlocale
        return True
    return False
