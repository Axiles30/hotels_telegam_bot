import json
import os

import redis
from telebot.types import Message, CallbackQuery
import datetime
from loader import bot
from utils.misc.models import UserModel, UserSearchHistory, db
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()


@bot.callback_query_handler(func=lambda call: call.data == 'history')
def history_start(call: CallbackQuery):
    user_id = call.from_user.id
    user_name = call.from_user.username
    get_history_from_redis(call.message, user_id, user_name)


def get_history_from_redis(message: Message, user_id, user_name) -> None:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST'),
        port=os.getenv('REDIS_PORT'),
        password=os.getenv('REDIS_PASSWORD'),
    )

    user_data_keys = redis_client.keys(f'users:{user_name}--{user_id}:*')
    all_data = []
    if user_data_keys:
        # Получаем данные для каждого ключа
        for key in user_data_keys:
            data = redis_client.hgetall(key)
            decoded_data = {key.decode(): value.decode() for key, value in data.items()}
            all_data.append(decoded_data)

            with open('database/json_files/redis_data.json',
                      'w') as file:
                json.dump({'data': all_data}, file, indent=4)



        with open('database/json_files/redis_data.json',
                  'r') as file:
            data_from_redis = json.load(file)

        # \nСтрана: {country}\nГород: {city}
        for items in data_from_redis['data']:
            hotel_name = items['name']
            hotel_image = items['image']
            check_in_date = items["check_in_date"]
            check_out_date = items["check_out_date"]
            total_price = items["price_all"]
            price_per_night = items["price_per_day"]
            caption = (f"\nОтель : {hotel_name}\nСтоимость за ночь : "
                       f"{price_per_night}\nСтоимость за все дни : {total_price}\nДата заезда : {check_in_date}\nДата выезда : {check_out_date}")
            bot.send_photo(message.chat.id, photo=hotel_image, caption=caption)
            print(hotel_name, hotel_image, check_in_date, check_out_date, price_per_night, total_price)

    else:
        # Если данных в Redis нет, обращаемся к базе данных SQLite
        get_history_from_sqlite(message, user_id, user_name)

        user_data_keys_after_sqlite = redis_client.keys(f'users:{user_name}--{user_id}:*')
        if not user_data_keys_after_sqlite:
            add_data_to_redis(user_id, user_name)
    redis_client.close()


def get_history_from_sqlite(message: Message, user_id, user_name) -> None:
    print(user_id)
    print(user_name)
    db.connect()

    user = UserModel.get(UserModel.telegram_id == user_id)

    # Получение истории поиска для найденного пользователя
    search_history = UserSearchHistory.select().where(UserSearchHistory.telegram_id == user)

    # Вывод данных
    for entry in search_history:
        country = entry.city_id.country
        city = entry.city_id.name
        hotel = entry.hotel_id.name
        image = entry.hotel_id.image
        price_per_night = entry.hotel_id.price_per_night
        total_price = entry.total_price
        check_in_date = entry.hotel_id.check_in_date
        check_out_date = entry.hotel_id.check_out_date
        caption = (f"\nСтрана : {country}\nГород : {city}\nОтель : {hotel}\nСтоимость за ночь : "
                   f"{price_per_night}\nСтоимость за все дни : {total_price}\nДата заезда : {check_in_date}\nДата выезда : {check_out_date}")
        bot.send_photo(message.chat.id, photo=image, caption=caption)

    db.close()


def add_data_to_redis(user_id, user_name):
    db.connect()
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST'),
        port=os.getenv('REDIS_PORT'),
        password=os.getenv('REDIS_PASSWORD'),
    )

    user = UserModel.get(UserModel.telegram_id == user_id)

    # Получение истории поиска для найденного пользователя
    search_history = UserSearchHistory.select().where(UserSearchHistory.telegram_id == user)

    for entry in search_history:
        city = entry.city_id.name
        country = entry.city_id.country
        searching_date = datetime.date.today()
        user_key = f'users:{user_name}--{user_id}'
        city_key = f'{user_key}:{country}:{city}:{searching_date}'

        hotel_id = entry.hotel_id.id
        hotel_key = f'{city_key}:hotel_{hotel_id}'
        hotel_data = {
            'id': hotel_id,
            'name': entry.hotel_id.name,
            'image': entry.hotel_id.image,
            'check_in_date': entry.hotel_id.check_in_date,
            'check_out_date': entry.hotel_id.check_out_date,
            'price_per_day': entry.hotel_id.price_per_night,
            'price_all': entry.total_price,
        }
        redis_client.hmset(hotel_key, hotel_data)

    redis_client.close()
    db.close()


def clear_redis():
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST'),
        port=os.getenv('REDIS_PORT'),
        password=os.getenv('REDIS_PASSWORD'),
    )
    redis_client.flushdb()
    redis_client.close()


# Планируем выполнение функции каждые 5 минут
scheduler.add_job(clear_redis, 'interval', minutes=5)
