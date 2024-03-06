import os
from dotenv import load_dotenv, find_dotenv

if not find_dotenv():
    exit('Переменные окружения не загружены т.к отсутствует файл .env.template')
else:
    load_dotenv()

dotenv_path = os.path.join(os.path.dirname(__file__), '.env.template')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

BOT_TOKEN = os.getenv('BOT_TOKEN')
RAPID_API_KEY = os.getenv('RAPID_API_KEY')
DEFAULT_COMMANDS = (
    ('start', "Запустить бота"),
    ('help', "Вывести справку"),
    # ('lowprice', "Отели по низким ценам"),
    # ('highprice', "Отели по высоким ценам"),
    # ('custom_price', 'Кастомные цены'),
)
