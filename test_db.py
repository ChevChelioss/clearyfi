from services.storage.subscriber_db import SubscriberDB

db = SubscriberDB()

print("=== Добавляем/обновляем юзера ===")
db.add_or_update_user(user_id=12345, chat_id=99999, username="tester")

print("=== Получаем данные юзера ===")
user = db.get_user(12345)
print(user)

print("=== Деактивация ===")
db.deactivate_user(12345)

print("=== После деактивации ===")
print(db.get_user(12345))

print("=== Активные подписчики ===")
print(db.get_active_subscribers())

db.close()
