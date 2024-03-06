import json
from pprint import pprint
import redis
import requests
from telebot.types import Message, CallbackQuery
import datetime
import peewee as pw
from states.searching_states import LowPriceStates
from utils.misc.models import UserModel, City, Hotel, UserSearchHistory, db

from loader import bot
import os

"""
# Команда /low
# После ввода команды у пользователя запрашивается:
# 1. Услуга/товар, по которым будет проводиться 
поиск (самые дешёвые отели).
# 2. Количество единиц категории (товаров/услуг), 
которое необходимо вывести (не
# больше программно определённого максимума).
# """

states_dict = {}


@bot.callback_query_handler(func=lambda call: call.data == 'low_price')
def handle_lowprice_query(call: CallbackQuery):
    user_id = call.from_user.id
    user_name = call.from_user.username
    time = datetime.time()
    print(user_id)
    print(user_name)
    print(time)
    handle_lowprice_city(call.message, user_id, user_name)


def handle_lowprice_city(message: Message, user_id, user_name) -> None:
    """Получение города от пользователя"""
    bot.set_state(user_id, LowPriceStates.city, message.chat.id)
    bot.send_message(user_id, f'Привет, {user_name} в '
                              f'каком городе будем искать самые дешовые отели?')


@bot.message_handler(state=LowPriceStates.city)
def get_count(message: Message) -> None:
    if message.text.isalpha():
        bot.send_message(message.chat.id,
                         'Теперь введите количество отелей которые хотите увидеть.')
        bot.set_state(message.from_user.id, LowPriceStates.hotels, message.chat.id)

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['city'] = message.text
            states_dict['city'] = data['city']
            print(data['city'])
    else:
        bot.send_message(message.from_user.id, 'Город можно вводить только буквами.')
    url = "https://hotels4.p.rapidapi.com/locations/v3/search"

    querystring = {"q": f"{data['city']}",
                   "locale": "en_US",
                   "langid": "1033",
                   "siteid": "300000001"}

    headers = {
        "X-RapidAPI-Key": os.getenv("RAPID_API_KEY"),
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    if response.status_code == requests.codes.ok:
        # print(f'Response status {response.status_code}ок')
        data = response.json()
        with open('database/json_files/locations_search.json', 'w') as file:
            json.dump(data, file, indent=4)

        with open('database/json_files/locations_search.json', 'r') as file:
            data = json.load(file)

    else:
        print('Ошибка при выполнении запроса')

    gaia_id = data['sr'][0]['gaiaId']
    country = data['sr'][0]["regionNames"]["secondaryDisplayName"]
    print(country)
    states_dict['country'] = country
    states_dict['gaiaId'] = gaia_id


@bot.message_handler(state=LowPriceStates.hotels)
def get_check_in_date(message: Message) -> None:
    bot.send_message(message.from_user.id,
                     'Теперь введите желаемую дату заезда.(в формате число-месяц-год, 15-09-23)')
    bot.set_state(message.from_user.id, LowPriceStates.check_in_date, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['hotel_count'] = int(message.text)
        states_dict['hotel_count'] = data['hotel_count']
        print(data['hotel_count'])

    with open('database/json_files/city_and_hotels_count.json', 'w') as file:
        json.dump(states_dict, file, indent=4)


@bot.message_handler(state=LowPriceStates.check_in_date)
def get_check_out_date(message: Message) -> None:
    bot.send_message(message.from_user.id,
                     'Теперь введите желаемую дату выезда.(в формате число-месяц-год, 20-09-23)')
    bot.set_state(message.from_user.id, LowPriceStates.check_out_date, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['check_in_date'] = message.text
        states_dict['check_in_date'] = data['check_in_date']
        print('Строка 113: ', states_dict['check_in_date'])


@bot.message_handler(state=LowPriceStates.check_out_date)
def temporary_name(message: Message) -> None:
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['check_out_date'] = message.text
        states_dict['check_out_date'] = data['check_out_date']
        print('Строка 121: ', states_dict['check_out_date'])
    with open('database/json_files/city_and_hotels_count.json', 'w') as file:
        json.dump(states_dict, file, indent=4)
        print('Строка 124: ', states_dict)
    with open('database/json_files/city_and_hotels_count.json', 'r') as file:
        data = json.load(file)


    check_in_date = data["check_in_date"]
    day_in, month_in, year_in = check_in_date.split('-')
    day_in = int(day_in)
    month_in = int(month_in)
    year_in = int(year_in)

    check_out_date = data["check_out_date"]
    day_out, month_out, year_out = check_out_date.split('-')
    day_out = int(day_out)
    month_out = int(month_out)
    year_out = int(year_out)

    data["check_in_date"] = {'day': day_in, 'month': month_in, 'year': year_in}
    data["check_out_date"] = {'day': day_out, 'month': month_out, 'year': year_out}
    with open('database/json_files/city_and_hotels_count.json', 'w') as file:
        json.dump(data, file, indent=4)
    with open('database/json_files/city_and_hotels_count.json', 'r') as file:
        data = json.load(file)
    city = data['city']
    country = data['country']
    gaia_id = data['gaiaId']
    hotel_count = data["hotel_count"]
    day_in = data["check_in_date"]["day"]
    month_in = data["check_in_date"]["month"]
    year_in = data["check_in_date"]["year"]
    day_out = data["check_out_date"]["day"]
    month_out = data["check_out_date"]["month"]
    year_out = data["check_out_date"]["year"]
    print(type(hotel_count), hotel_count,
          type(day_in), day_in,
          type(month_in), month_in,
          type(year_in), year_in,
          type(day_out), day_out,
          type(month_out), month_out,
          type(year_out), year_out)
    property_search(message, gaia_id, country, city,
                    hotel_count, day_in, month_in, year_in, day_out, month_out, year_out)


def property_search(message: Message, gaia_id=str, country=str,
                    city=str, hotel_count=int,
                    day_in=int, month_in=int, year_in=int, day_out=int, month_out=int, year_out=int):
    username = message.from_user.username
    user_id = message.from_user.id
    url = "https://hotels4.p.rapidapi.com/properties/v2/list"
    payload = {
        "currency": "USD",
        "eapid": 1,
        "locale": "ru_RU",
        "siteId": 300000001,
        "destination": {"regionId": f'{gaia_id}'},
        "checkInDate": {
            "day": day_in,
            "month": month_in,
            "year": year_in
        },
        "checkOutDate": {
            "day": day_out,
            "month": month_out,
            "year": year_out
        },
        "rooms": [
            {
                "adults": 2,
                "children": [{"age": 5}, {"age": 7}]
            }
        ],
        "resultsStartingIndex": 0,
        "resultsSize": hotel_count,
        "sort": "PRICE_LOW_TO_HIGH",
        "filters": {"price": {
            "max": 100000,
            "min": 1
        }}
    }
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": os.getenv("RAPID_API_KEY"),
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }

    response = requests.request("POST", url, json=payload, headers=headers)
    print('Строка 211: ', response.status_code)

    data = response.json()
    print(data)
    check_in_date = states_dict['check_in_date']
    check_out_date = states_dict['check_out_date']
    with open('database/json_files/properties_list.json', 'w') as file:
        json.dump(data, file, indent=4)

    all_property_dicts = {'user_name': f"{username}", 'user_id': f"{user_id}", 'country': f"{country}",
                          'city': f"{city}",
                          'city_id': f"{gaia_id}",
                          'data': []}

    for i in range(hotel_count):
        with open('database/json_files/properties_list.json', 'r') as file:
            data = json.load(file)
        property_id = data['data']['propertySearch']['properties'][i]['id']
        property_name = data['data']['propertySearch']['properties'][i]['name']
        property_image = data['data']['propertySearch']['properties'][i]['propertyImage']['image']['url']
        price_per_day = \
            data['data']['propertySearch']['properties'][i]['price']['displayMessages'][0]['lineItems'][0]['price'][
                'formatted']
        property_all_price = \
            data['data']['propertySearch']['properties'][i]['price']['displayMessages'][1]['lineItems'][0]['value']
        property_dict = {'id': property_id, 'name': property_name,
                         'image': property_image, 'check_in_date': check_in_date,
                         'check_out_date': check_out_date,
                         'price_per_day': price_per_day, 'price_all': property_all_price}

        all_property_dicts['data'].append(property_dict)

    with open("database/json_files/search_five_hotels.json", 'w') as file:
        json.dump(all_property_dicts, file, indent=4, separators=(',', ':'))

    with open('database/json_files/search_five_hotels.json', 'r') as file:
        data = json.load(file)

    # Перебрать отели в данных
    for hotel in data["data"]:
        # Получить изображение отеля
        photo_url = hotel['image']
        # Получить название и цену отеля
        caption = (f"\nСтрана: {data['country']}\nГород: {data['city']}\nОтель: {hotel['name']}\nЦена за ночь: "
                   f"{hotel['price_per_day']}\nЦена за все дни: {hotel['price_all']}")
        bot.send_photo(message.chat.id, photo_url, caption)
    add_to_redis_and_sqlite(message, username, country, city, db)


def add_to_redis_and_sqlite(message: Message, username, country, city, db):
    with open('database/json_files/search_five_hotels.json', 'r') as file:
        data = json.load(file)

    # Создание таблиц, если они не существуют
    db_path = 'database/peewee/search_history.db'
    try:
        db.connect()
        if not os.path.exists(db_path):
            # Создание базы данных, если она не существует
            db = pw.SqliteDatabase(db_path)

            db.create_tables([UserModel, City, Hotel, UserSearchHistory])
        else:
            db = pw.SqliteDatabase(db_path)

    except Exception as e:
        print(f"Error while creating database: {e}")
    finally:
        db.close()

    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST'),
        port=os.getenv('REDIS_PORT'),
        password=os.getenv('REDIS_PASSWORD'),
    )

    user_id = message.from_user.id
    searching_date = datetime.date.today()
    user_key = f'users:{username}--{user_id}'
    city_key = f'{user_key}:{country}:{city}:{searching_date}'

    for i, hotel in enumerate(data["data"], start=1):
        hotel_key = f'{city_key}:hotel_{i}'
        hotel_data = {
            'id': hotel['id'],
            'name': hotel['name'],
            'image': hotel['image'],
            'check_in_date': hotel['check_in_date'],
            'check_out_date': hotel['check_out_date'],
            'price_per_day': hotel['price_per_day'],
            'price_all': hotel['price_all'],
            'country': country,
            'city': city
        }
        redis_client.hmset(hotel_key, hotel_data)
        hotel_data_redis = redis_client.hgetall(hotel_key)
        pprint(hotel_data_redis)

    redis_client.close()

    # Получение или создание пользователя
    user, _ = UserModel.get_or_create(
        telegram_id=user_id,
        defaults={'user_name': username,
                  'searching_date': searching_date}
    )

    # Получение или создание города
    city, _ = City.get_or_create(
        city_id=data['city_id'],  # Проверьте, как определена переменная city_id
        defaults={
            'country': country,
            'name': city}
    )

    # Сохранение данных по отелям
    for hotel_data in data['data']:
        hotel, _ = Hotel.get_or_create(
            hotel_id=hotel_data['id'],
            defaults={
                'name': hotel_data['name'],
                'image': hotel_data['image'],
                'check_in_date': hotel_data['check_in_date'],
                'check_out_date': hotel_data['check_out_date'],
                'price_per_night': float(hotel_data['price_per_day'].replace('$', '').replace(',', '')),
                'price_all': float(hotel_data['price_all'].split()[0].replace('$', '').replace(',', ''))
            }
        )

        UserSearchHistory.create(
            telegram_id=user,
            city_id=city,
            hotel_id=hotel,
            total_price=hotel_data['price_all'],
            searching_date=searching_date
        )

    # Закрытие соединения с базой данных
    db.close()
