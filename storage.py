import shelve
from config import config

storage = shelve.open("storage")


def add_admin(user_id):
    storage["BOT_ADMINS"] = storage.get("BOT_ADMINS", set({})) | {user_id}


def remove_admin(user_id):
    storage["BOT_ADMINS"] = storage.get("BOT_ADMINS", set({})) / {user_id}


def is_manager(user_id):
    return user_id == config["BOT_MANAGER"]


def get_bot_manager():
    return config["BOT_MANAGER"]


def ban_user(user_id):
    storage["BANNED_USERS"] = storage.get("BANNED_USERS", set({})) | {user_id}


def unban_user(user_id):
    storage["BANNED_USERS"] = storage.get("BANNED_USERS", set({})) / {user_id}


def is_banned(user_id):
    return user_id in storage.get("BANNED_USERS", set({}))


def is_admin(user_id):
    return user_id in storage.get("BOT_ADMINS", set({})) or is_manager(user_id)


def get_admin_set():
    return storage.get("BOT_ADMINS", set({}))


def get_target_chat():
    return storage.get("TARGET_CHAT", config["TARGET_CHAT"])


def set_target_chat(chat_id):
    storage["TARGET_CHAT"] = chat_id


def get_bot_token():
    return config["BOT_TOKEN"]
