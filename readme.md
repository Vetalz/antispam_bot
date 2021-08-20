# Antispam bot

Телеграм бот для управления чатом

## Функции

- Админ меню по команде /admin (доступ только пользователям указанным в config.ini) 
- Функция удаления новых сообщений по ключевым словам
- Функция удаления новых сообщений, если те часто повторяются
- Функция удаления старых сообщений по ключевым словам
- Функция удаления старых сообщений по пользователю
- Бот уведомляет о всех совершаемых действиях


## Стек

- [Aiogram](https://docs.aiogram.dev/en/latest/) - Бот
- [Peewee](http://docs.peewee-orm.com/en/latest/) - ORM
- [postgresql](https://www.postgresql.org/) - DB

## Использование

1. Добавить @vz_antispam_bot в чат телеграма
2. Назначить бота администратором. Чтобы у него была возможность удалять сообщения
3. Написать в чате команду /start
4. Для управления используется команда /admin