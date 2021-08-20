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


logging.basicConfig(level=logging.INFO, filename='bot.log')

API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
cb = CallbackData('id', 'user_id', 'chat_id', 'chat_title')


@dp.message_handler(commands=['start'])
async def send_welcome(message):
    chat = message.chat
    chat_id = chat['id']
    chat_title = chat['title']
    user = message.from_user
    user_id = user['id']

    is_access = OperationUser.check_access(user_id)
    if not is_access:
        text = BaseAnswer.except_access()
        await message.answer(text)
        return

    try:
        user_name = user['username']
    except KeyError:
        user_name = None
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
    user = message.from_user
    user_id = user['id']
    user_name = user['username']
    chat = message.chat
    chat_id = chat['id']

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
    user = message.from_user
    user_id = user['id']
    chat = message.chat
    chat_id = chat['id']

    is_access = OperationUser.check_access(user_id)
    if not is_access:
        text = BaseAnswer.except_access()
        await message.answer(text)
        return

    if chat_id != user_id:
        text = BaseAnswer.except_command()
        await message.answer(text)
        return

    chat_with_db = OperationChatUser.get_user_chat(user_id)
    if chat_with_db:
        chat_id_with_db = chat_with_db.chat_id
    else:
        text = BaseAnswer.except_command_3()
        await message.answer(text)
        return

    try:
        keywords = re.findall(r'/set_keyword (\D+)', message.text)[0]
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
    user = message.from_user
    user_id = user['id']
    chat = message.chat
    chat_id = chat['id']

    is_access = OperationUser.check_access(user_id)
    if not is_access:
        text = BaseAnswer.except_access()
        await message.answer(text)
        return

    if chat_id != user_id:
        text = BaseAnswer.except_command()
        await message.answer(text)
        return

    chat_with_db = OperationChatUser.get_user_chat(user_id)
    if chat_with_db:
        chat_id_with_db = chat_with_db.chat_id
    else:
        text = BaseAnswer.except_command_3()
        await message.answer(text)
        return

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
    user = message.from_user
    user_id = user['id']
    chat = message.chat
    chat_id = chat['id']

    is_access = OperationUser.check_access(user_id)
    if not is_access:
        text = BaseAnswer.except_access()
        await message.answer(text)
        return

    if chat_id != user_id:
        text = BaseAnswer.except_command()
        await message.answer(text)
        return

    chat_with_db = OperationChatUser.get_user_chat(user_id)
    if chat_with_db:
        chat_id_with_db = chat_with_db.chat_id
    else:
        text = BaseAnswer.except_command_3()
        await message.answer(text)
        return

    try:
        keywords = re.findall(r'/set_keyword_old (\D+)', message.text)[0]
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
    user = message.from_user
    user_id = user['id']
    chat = message.chat
    chat_id = chat['id']

    is_access = OperationUser.check_access(user_id)
    if not is_access:
        text = BaseAnswer.except_access()
        await message.answer(text)
        return

    if chat_id != user_id:
        text = BaseAnswer.except_command()
        await message.answer(text)
        return

    chat_with_db = OperationChatUser.get_user_chat(user_id)
    if chat_with_db:
        chat_id_with_db = chat_with_db.chat_id
    else:
        text = BaseAnswer.except_command_3()
        await message.answer(text)
        return

    try:
        users = re.findall(r'/set_user_old (\D+)', message.text)[0]
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
    user = message.from_user
    user_id = user['id']
    chat = message.chat
    chat_id = chat['id']
    text = message.text
    message_id = message.message_id

    if user_id == chat_id:
        return

    msg_text = text.lower()
    hash_object = hashlib.md5(msg_text.encode())
    text_hash = hash_object.hexdigest()
    hash_limit_count_db = OperationText.get_id_hash_limit_count(chat_id)
    if not hash_limit_count_db:
        keywords = OperationKey.get_keywords(chat_id)
        if not keywords:
            save_text = OperationText.add_text(chat_id, text_hash, -1, msg_text)
            OperationMessage.add_message(chat_id, user_id, message_id, save_text.id)
            return
        for key in keywords:
            if key in msg_text:
                await bot.delete_message(chat.id, message_id)
                text = ChatAnswer.warning()
                await message.answer(text)
                return
            else:
                save_text = OperationText.add_text(chat_id, text_hash, -1, msg_text)
                OperationMessage.add_message(chat_id, user_id, message_id, save_text.id)
                return

    for i in hash_limit_count_db:
        if text_hash in i['hash']:
            count = i['count'] + 1
            if 0 < i['limit'] < count:
                await bot.delete_message(chat.id, message_id)
                OperationText.update_count(chat_id, i['hash'], count)
                text = ChatAnswer.warning()
                await message.answer(text)
                return
            else:
                OperationText.update_count(chat_id, i['hash'], count)
                keywords = OperationKey.get_keywords(chat_id)
                if not keywords:
                    OperationMessage.add_message(chat_id, user_id, message_id, i['id'])
                    return
                for key in keywords:
                    if key in msg_text:
                        await bot.delete_message(chat.id, message_id)
                        text = ChatAnswer.warning()
                        await message.answer(text)
                        return
                    else:
                        OperationMessage.add_message(chat_id, user_id, message_id, i['id'])
                        return

    save_text = OperationText.add_text(chat_id, text_hash, -1, msg_text)
    OperationMessage.add_message(chat_id, user_id, message_id, save_text.id)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
