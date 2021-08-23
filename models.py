from peewee import *
import datetime
import os

DB_NAME = os.getenv('POSTGRES_DB')
USER = os.getenv('POSTGRES_USER')
PASSWORD = os.getenv('POSTGRES_PASSWORD')
HOST = os.getenv('HOST_DB')
PORT = os.getenv('PORT_DB')

db = PostgresqlDatabase(DB_NAME, user=USER, password=PASSWORD, host=HOST, port=PORT)


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    user_id = BigIntegerField(primary_key=True)
    user_name = CharField(max_length=255, null=True)
    is_access = BooleanField(default=False)


class Chat(BaseModel):
    chat_id = BigIntegerField(primary_key=True)
    title = CharField(max_length=255)
    admins = ManyToManyField(User, backref='chats')


User_Chat = Chat.admins.get_through_model()


class Text(BaseModel):
    text = TextField()
    hash = CharField(max_length=255)
    chat_id = ForeignKeyField(Chat, backref='text')
    frequency_limit = IntegerField(default=-1)
    count = IntegerField(default=0)


class Message(BaseModel):
    message_id = IntegerField()
    user_id = ForeignKeyField(User, backref='messages')
    chat_id = ForeignKeyField(Chat, backref='messages')
    text_id = ForeignKeyField(Text, backref='messages')
    is_delete = BooleanField(default=False)
    date_create = DateTimeField()


class Key(BaseModel):
    text = CharField(max_length=255)
    chat_id = ForeignKeyField(Chat, backref='keys')


class UserChat(BaseModel):
    user_id = ForeignKeyField(User, backref='user_chat')
    chat_id = ForeignKeyField(Chat, backref='user_chat')


class OperationUser:
    @staticmethod
    def add_user(user_id, user_name):
        user = OperationUser.get_user(user_id)
        if not user:
            user = User.create(user_id=user_id, user_name=user_name)
        return user

    @staticmethod
    def get_user(user_id):
        try:
            user = User.get(User.user_id == user_id)
        except User.DoesNotExist:
            user = None
        return user

    @staticmethod
    def get_user_chat(user_id):
        query = Chat.select().join(User_Chat).join(User).where(User.user_id == user_id)
        # query = Chat.select().where(Chat.admin_id == user_id).order_by(Chat.chat_id)
        chats = []
        for i in query:
            chat = {'title': i.title, 'id': i.chat_id}
            chats.append(chat)
        return chats

    @staticmethod
    def check_access(user_name):
        users = []
        with open('config.ini', 'r') as f:
            for line in f.readlines():
                users.append(line.rstrip())
        if str(user_name) in users:
            is_access = True
        else:
            is_access = False

        return is_access


class OperationChat:
    @staticmethod
    def add_chat(chat_id, title, user):
        chat = OperationChat.get_chat(chat_id)
        if not chat:
            chat = Chat.create(chat_id=chat_id, title=title)
            chat.admins.add(user)
        else:
            chat.admins.add(user)
        return chat

    @staticmethod
    def get_chat(chat_id):
        try:
            chat = Chat.get(Chat.chat_id == chat_id)
        except Chat.DoesNotExist:
            chat = None
        return chat

    @staticmethod
    def get_chat_admins(chat_id):
        query = User_Chat.select().where(User_Chat.chat_id == chat_id)
        admins = []
        for i in query:
            admins.append(i.user_id)
        return admins


class OperationChatUser:
    @staticmethod
    def add_user_chat(user_id, chat_id):
        user_chat = OperationChatUser.get_user_chat(user_id)
        if user_chat:
            OperationChatUser.delete_user_chat(user_id)
        UserChat.create(user_id=user_id, chat_id=chat_id)
        return True

    @staticmethod
    def get_user_chat(user_id):
        user_chat = UserChat.get_or_none(UserChat.user_id == user_id)
        return user_chat

    @staticmethod
    def delete_user_chat(user_id):
        q = UserChat.delete().where(UserChat.user_id == user_id)
        q.execute()
        return True


class OperationKey:
    @staticmethod
    def add_keywords(list_keywords, chat_id):
        for keyword in list_keywords:
            keyword = keyword.lower()
            key_with_db = OperationKey.get_keyword(keyword)
            if key_with_db:
                continue
            else:
                Key.create(text=keyword, chat_id=chat_id)

    @staticmethod
    def delete_keywords(list_keywords, chat_id):
        for keyword in list_keywords:
            keyword = keyword.lower()
            key_with_db = OperationKey.get_keyword(keyword)
            if key_with_db:
                q = Key.delete().where(Key.chat_id == chat_id, Key.text == keyword)
                q.execute()

    @staticmethod
    def get_keyword(keyword):
        key_with_db = Key.get_or_none(Key.text == keyword)
        return key_with_db

    @staticmethod
    def get_keywords(chat_id):
        query = Key.select().where(Key.chat_id == chat_id)
        keywords = []
        for i in query:
            keywords.append(i.text)
        return keywords


class OperationText:
    @staticmethod
    def get_hash(chat_id):
        query = Text.select().where(Text.chat_id == chat_id)
        hash_text = []
        for i in query:
            hash_text.append(i.hash)
        return hash_text

    @staticmethod
    def update_frequency(chat_id, text_hash, limit):
        query = Text.update(frequency_limit=limit, count=0).where(Text.hash == text_hash, Text.chat_id == chat_id)
        query.execute()

    @staticmethod
    def update_count(chat_id, text_hash, count):
        query = Text.update(count=count).where(Text.hash == text_hash, Text.chat_id == chat_id)
        query.execute()

    @staticmethod
    def add_text(chat_id, text_hash, limit, text):
        text = Text.create(chat_id=chat_id, hash=text_hash, frequency_limit=limit, text=text)
        return text

    @staticmethod
    def get_id_hash_limit_count(chat_id):
        query = Text.select().where(Text.chat_id == chat_id)
        hash_limit_count = []
        for i in query:
            item = {'id': i.id, 'hash': i.hash, 'limit': i.frequency_limit, 'count': i.count}
            hash_limit_count.append(item)
        return hash_limit_count


class OperationMessage:
    @staticmethod
    def get_message(chat_id):
        date_time = datetime.datetime.now()
        date_time_start = date_time - datetime.timedelta(days=2)
        query = Message.select().where(fn.date_trunc('minute', Message.date_create) > date_time_start,
                                       Message.chat_id == chat_id, Message.is_delete == 0)
        messages = []
        for i in query:
            message = {'message_id': i.message_id, 'text_id': i.text_id.id,
                       'text': i.text_id.text, 'user_name': i.user_id.user_name, 'user_id': i.user_id.user_id}
            messages.append(message)
        return messages

    @staticmethod
    def delete_message(chat_id, text_id):
        query = Message.update(is_delete=True).where(Message.chat_id == chat_id, Message.text_id == text_id)
        query.execute()

    @staticmethod
    def delete_user_message(chat_id, user_id):
        query = Message.update(is_delete=True).where(Message.chat_id == chat_id, Message.user_id == user_id)
        query.execute()

    @staticmethod
    def add_message(chat_id, user_id, user_name, message_id, text_id):
        date_time = datetime.datetime.now()
        user = OperationUser.add_user(user_id, user_name)
        msg = Message.create(chat_id=chat_id, user_id=user, message_id=message_id,
                             text_id=text_id, date_create=date_time)
        return msg


def create_tables():
    with db:
        db.create_tables([User, Chat, Text, Message, Key, UserChat, User_Chat])


if __name__ == '__main__':
    create_tables()
    print('Таблицы созданы')
