class BaseAnswer:
    @staticmethod
    def except_access():
        text = 'У вас не достаточно прав для управления ботом'
        return text

    @staticmethod
    def except_command():
        text = 'Используйте команды в личной переписке с ботом'
        return text

    @staticmethod
    def except_command_2():
        text = 'Команда введена не верно'
        return text

    @staticmethod
    def except_command_3():
        text = 'Выбирите чат'
        return text


class StartAnswer:
    @staticmethod
    def except_1():
        text = 'Данная команда необходима для регистрации пользователя в качестве администратора бота для ' \
               'конкретного чата. Её необходимо отправлять в чате, а не в личной переписке c ботом'
        return text

    @staticmethod
    def except_2():
        text = 'Вы уже зарегистрированы в качестве администратора'
        return text

    @staticmethod
    def success(user, chat):
        text = f'Пользователь {user} зарегистрирован администратором бота для чата {chat}'
        return text


class AdminAnswer:
    @staticmethod
    def success(user):
        text = f'Пользователь {user} вы являетесь администратором следующих чатов:\n'
        return text


class SelectAnswer:
    @staticmethod
    def success(chat):
        text = f'Вы выбрали чат: {chat}\n' \
               f'Введите одну из команд:\n' \
               f'Задать ключевые слова по которым будут удаляться новые сообщения:\n' \
               f'/1 слово, слово,...\n\n' \
               f'Задать лимит повторов сообщения после которого новые сообщения будут удаляться.\n' \
               f'Если хотите снять лимит, то установите -1:\n' \
               f'/2 {{сообщение}}лимит\n\n' \
               f'Задать ключевые слова по которым удалить старые сообщения:\n' \
               f'/3 слово, слово,...\n\n' \
               f'Задать пользователей чьи сообщения необходимо удалить, без @:\n' \
               f'/4 пользователь1, пользователь2,...'
        return text


class KeyAnswer:
    @staticmethod
    def success():
        text = 'Ключевые слова добавлены'
        return text


class FrequencyAnswer:
    @staticmethod
    def success():
        text = 'Лимиты установлены'
        return text


class KeyOldAnswer:
    @staticmethod
    def success(count):
        text = f'{count} было удалено'
        return text


class UserOldAnswer:
    @staticmethod
    def success(count):
        text = f'{count} было удалено'
        return text


class ChatAnswer:
    @staticmethod
    def warning():
        text = 'Сообщение удалено так как нарушает правила чата'
        return text
