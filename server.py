import logging
import os
from views import BaseAnswer, StartAnswer, AdminAnswer, SelectAnswer, \
                  KeyAnswer, FrequencyAnswer, KeyOldAnswer, UserOldAnswer, ChatAnswer
from models import OperationUser, OperationChat, OperationChatUser, OperationKey, OperationText, OperationMessage

from aiogram import Bot, Dispatcher, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

import re
import hashlib

# logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.INFO, filename='bot.log')

API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
cb = CallbackData('id', 'user_id', 'chat_id', 'chat_title')


@dp.message_handler(commands=['start'])
async def send_welcome(message):
    user_id, chat_id, chat_title, user_name = init_msg(message)

    is_access = OperationUser.check_access(user_id)
    if not is_access:
        text = BaseAnswer.except_access()
        await message.answer(text)
        return

    if chat_id == user_id:
        text = StartAnswer.except_1()
        await message.answer(text)
    else:
        chat = OperationChat.get_chat(chat_id)
        if chat and chat.admin_id == user_id:
            flag = True
        else:
            flag = False
        if flag:
            text = StartAnswer.except_2()
            await message.answer(text)
        else:
            user = OperationUser.add_user(user_id, user_name)
            OperationChat.add_chat(chat_id, chat_title, user)
            text = StartAnswer.success(user_name or user_id, chat_title)
            await message.answer(text)


@dp.message_handler(commands=['admin'])
async def admin(message):
    user_id, chat_id, chat_title, user_name = init_msg(message)

    is_access = OperationUser.check_access(user_id)
    if not is_access:
        text = BaseAnswer.except_access()
        await message.answer(text)
        return

    if chat_id != user_id:
        text = BaseAnswer.except_command()
        await message.answer(text)
        return

    user = OperationUser.get_user(user_id)
    if user:
        chats = OperationUser.get_user_chat(user_id)
    else:
        text = BaseAnswer.except_access()
        await message.answer(text)
        return

    buttons = []
    for chat in chats:
        buttons.append(InlineKeyboardButton(text=f'{chat["title"]}', callback_data=cb.new(user_id=user_id,
                                                                                          chat_id=chat["id"],
                                                                                          chat_title=chat["title"])))
    keyboard = InlineKeyboardMarkup(row_width=1)
    inline_kb = keyboard.add(*buttons)

    text = AdminAnswer.success(user_name or user_id)
    await message.answer(text, reply_markup=inline_kb)


@dp.callback_query_handler(cb.filter())
async def get_chat(call, callback_data):
    chat_id = int(callback_data['chat_id'])
    user_id = int(callback_data['user_id'])
    chat_title = callback_data['chat_title']
    add_user = OperationChatUser.add_user_chat(user_id, chat_id)
    if add_user:
        await bot.answer_callback_query(call.id)
        text = SelectAnswer.success(chat_title)
        await call.message.answer(text)


@dp.message_handler(commands=['1'])
async def set_key_new_msg(message):
    user_id, chat_id, chat_title, user_name = init_msg(message)

    pre_check = check(user_id, chat_id)
    if pre_check:
        await message.answer(pre_check)
        return

    chat_with_db = OperationChatUser.get_user_chat(user_id)
    chat_id_with_db = chat_with_db.chat_id

    try:
        keywords = re.findall(r'/1 (\D+)', message.text)[0]
    except IndexError:
        text = BaseAnswer.except_command_2()
        await message.answer(text)
        return

    keywords = keywords.split(',')
    OperationKey.add_keywords(keywords, chat_id_with_db)
    OperationChatUser.delete_user_chat(user_id)
    text = KeyAnswer.success()
    await message.answer(text)


@dp.message_handler(commands=['2'])
async def set_limit(message):
    user_id, chat_id, chat_title, user_name = init_msg(message)

    pre_check = check(user_id, chat_id)
    if pre_check:
        await message.answer(pre_check)
        return

    chat_with_db = OperationChatUser.get_user_chat(user_id)
    chat_id_with_db = chat_with_db.chat_id

    try:
        msg = re.findall(r'{(\D+)}', message.text)[0]
        limit = int(re.findall(r'}(-?\d+)', message.text)[0])
    except IndexError:
        text = BaseAnswer.except_command_2()
        await message.answer(text)
        return

    hash_with_db = OperationText.get_hash(chat_id_with_db)

    msg = msg.lower()
    hash_object = hashlib.md5(msg.encode())
    text_hash = hash_object.hexdigest()
    if text_hash in hash_with_db:
        OperationText.update_frequency(chat_id_with_db, text_hash, limit)
        OperationChatUser.delete_user_chat(user_id)
    else:
        OperationText.add_text(chat_id_with_db, text_hash, limit, msg)
        OperationChatUser.delete_user_chat(user_id)
    text = FrequencyAnswer.success()
    await message.answer(text)


@dp.message_handler(commands=['3'])
async def set_key_old(message):
    user_id, chat_id, chat_title, user_name = init_msg(message)

    pre_check = check(user_id, chat_id)
    if pre_check:
        await message.answer(pre_check)
        return

    chat_with_db = OperationChatUser.get_user_chat(user_id)
    chat_id_with_db = chat_with_db.chat_id

    try:
        keywords = re.findall(r'/3 (\D+)', message.text)[0]
    except IndexError:
        text = BaseAnswer.except_command_2()
        await message.answer(text)
        return

    keywords = keywords.split(',')
    messages = OperationMessage.get_message(chat_id_with_db)
    count = 0
    for msg in messages:
        for key in keywords:
            if key in msg['text'].lower():
                await bot.delete_message(chat_id_with_db, (msg['message_id']))
                OperationMessage.delete_message(chat_id_with_db, msg['text_id'])
                count += 1

    OperationChatUser.delete_user_chat(user_id)
    text = KeyOldAnswer.success(count)
    await message.answer(text)


@dp.message_handler(commands=['4'])
async def set_user_old(message):
    user_id, chat_id, chat_title, user_name = init_msg(message)

    pre_check = check(user_id, chat_id)
    if pre_check:
        await message.answer(pre_check)
        return

    chat_with_db = OperationChatUser.get_user_chat(user_id)
    chat_id_with_db = chat_with_db.chat_id

    try:
        users = re.findall(r'/4 (\D+)', message.text)[0]
    except IndexError:
        text = BaseAnswer.except_command_2()
        await message.answer(text)
        return

    users = users.split(',')
    messages = OperationMessage.get_message(chat_id_with_db)
    count = 0
    for msg in messages:
        for user in users:
            if user in msg['user_name']:
                await bot.delete_message(chat_id_with_db, (msg['message_id']))
                OperationMessage.delete_user_message(chat_id_with_db, msg['user_id'])
                count += 1

    OperationChatUser.delete_user_chat(user_id)
    text = UserOldAnswer.success(count)
    await message.answer(text)


@dp.message_handler()
async def listen_msg(message):
    user_id, chat_id, chat_title, user_name = init_msg(message)
    text = message.text
    message_id = message.message_id

    if user_id == chat_id:
        return

    is_chat = OperationChat.get_chat(chat_id)
    if not is_chat:
        text = BaseAnswer.except_command_4()
        await message.answer(text)
        return

    msg_text = text.lower()
    hash_object = hashlib.md5(msg_text.encode())
    text_hash = hash_object.hexdigest()

    is_keyword = check_keywords(msg_text, chat_id)

    is_limit = check_limit(user_id, chat_id, msg_text, text_hash, message_id)

    if is_keyword or is_limit:
        await bot.delete_message(chat_id, message_id)
        text = ChatAnswer.warning()
        await message.answer(text)
        return


def check_keywords(msg_text, chat_id):
    keywords = OperationKey.get_keywords(chat_id)
    if not keywords:
        return False
    for key in keywords:
        if key in msg_text:
            return True

    return False


def check_limit(user_id, chat_id, msg_text, text_hash, message_id, ):
    hash_limit_count_db = OperationText.get_id_hash_limit_count(chat_id)
    if not hash_limit_count_db:
        save_text = OperationText.add_text(chat_id, text_hash, -1, msg_text)
        OperationMessage.add_message(chat_id, user_id, message_id, save_text.id)
        return False
    for i in hash_limit_count_db:
        if text_hash in i['hash']:
            count = i['count'] + 1
            if 0 < i['limit'] < count:
                return True
            else:
                OperationText.update_count(chat_id, i['hash'], count)
                OperationMessage.add_message(chat_id, user_id, message_id, i['id'])
                return False

    save_text = OperationText.add_text(chat_id, text_hash, -1, msg_text)
    OperationMessage.add_message(chat_id, user_id, message_id, save_text.id)
    return False


def check(user_id, chat_id):
    is_access = OperationUser.check_access(user_id)
    if not is_access:
        text = BaseAnswer.except_access()
        return text

    if chat_id != user_id:
        text = BaseAnswer.except_command()
        return text

    chat_with_db = OperationChatUser.get_user_chat(user_id)
    if not chat_with_db:
        text = BaseAnswer.except_command_3()
        return text

    return False


def init_msg(message):
    chat = message.chat
    chat_id = chat['id']
    chat_title = chat['title']
    user = message.from_user
    user_id = user['id']
    try:
        user_name = user['username']
    except KeyError:
        user_name = None
    return user_id, chat_id, chat_title, user_name


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
