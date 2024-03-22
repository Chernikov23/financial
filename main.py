import telebot
from telebot import types
import requests
from bs4 import BeautifulSoup
import matplotlib
from datetime import datetime, timedelta
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import json
import re
import google.generativeai as genai
import threading
from threading import Lock


user_data_lock = Lock()
TOKEN = '6757224636:AAF6w4kJhnT4qYALsUrMUdMGNTgCa5jtBNA'
bot = telebot.TeleBot(TOKEN)
GEMINI_API_KEY = 'AIzaSyA8CDVJzTbLK-uwfSxxhdkP7vdFS6dC57g'  # ключ API Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')
MAX_MESSAGE_LENGTH = 4096


startMes = 'Добро пожаловать к вашему надежному финансовому помощнику!\nЯ - ваш персональный финансовый ассистент, который поможет вам:\n🔹 Отслеживать расходы и доходы\n🔹 Планировать свой бюджет\n🔹 Ставить финансовые цели\nПрисоединяйтесь ко мне сегодня и начните контролировать свои финансы!\n Каждый час бот будет высылать актуальную информацию с курсами криптовалют. В любой момент вы можете отключить эту функцию'
url = "https://ru.investing.com/currencies/usd-rub"
doll = requests.get(url)
url1 = 'https://ru.investing.com/currencies/eur-rub'
eu = requests.get(url1)
url2 = 'https://ru.investing.com/currencies/gbp-rub'
fund = requests.get(url2)
url3 = 'https://ru.investing.com/currencies/cny-rub'
cny = requests.get(url3)




fiati = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False, row_width=2)
dol = types.KeyboardButton('Курс доллара')
e = types.KeyboardButton('Курс евро')
fs = types.KeyboardButton('Курс фунтов стерлинга')
cn = types.KeyboardButton('Курс юаней')
fiati.add(dol,e,fs,cn)




main = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False, row_width=2)
itembtn1 = types.KeyboardButton("Управление деньгами")
itembtn2 = types.KeyboardButton("Внести трату")
itembtn3 = types.KeyboardButton("Курсы криптовалют")
itembtn4 = types.KeyboardButton("Таблица трат")
main.add(itembtn1, itembtn2, itembtn3, itembtn4)

def load_user_data():
    with user_data_lock:
        try:
            with open('user_data.json', 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

def save_user_data(user_data):
    with user_data_lock:
        with open('user_data.json', 'w') as file:
            json.dump(user_data, file, ensure_ascii=False, indent=4)


user_data_file_path = 'user_data.json'

# Проверяем, существует ли файл user_data.json и является ли он валидным JSON
try:
    with open(user_data_file_path, 'r') as file:
        user_data = json.load(file)
    print("ВСЕ ОТЛИЧНО")
except FileNotFoundError:
    # Если файл не найден, создаем новый с пустым объектом
    user_data = {}
    with open(user_data_file_path, 'w') as file:
        json.dump(user_data, file)
except json.JSONDecodeError:
    # Если файл не является валидным JSON, выводим сообщение об ошибке
    print(f"Файл {user_data_file_path} поврежден или не является валидным JSON.")

def show_money_management_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
    itembn1 = types.KeyboardButton("Баланс")
    itembn2 = types.KeyboardButton("Установить бюджет")
    itembn3 = types.KeyboardButton("Рассчитать процент")  
    itembn4 = types.KeyboardButton("Как потратить?")
    markup.add(itembn1, itembn2, itembn3, itembn4)
    bot.send_message(message.chat.id, "Что бы ты хотел сделать?", reply_markup=markup)

def convert_comma_to_dot(string):
    """
    Функция преобразует десятичный разделитель из запятой в точку для корректного преобразования строки в число.
    """
    return string.replace(',', '.')

def safe_float_conversion(user_input):
    """
    Безопасное преобразование пользовательского ввода в число с плавающей точкой.
    """
    try:
        return float(convert_comma_to_dot(user_input))
    except ValueError:
        return None


@bot.message_handler(func=lambda message: message.text == "Рассчитать криптовалюту")
def ask_for_crypto_amount(message):
    msg = bot.send_message(message.chat.id, "Введите количество коинов:")
    bot.register_next_step_handler(msg, process_crypto_amount)

def process_crypto_amount(message):
    amount = safe_float_conversion(message.text)
    if (amount is not None) and (amount > 0):
        msg = bot.send_message(message.chat.id, "Введите стоимость одного коина:")
        # Передаем amount как дополнительный аргумент
        bot.register_next_step_handler(msg, calculate_crypto_value, amount)
    else:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректное число.")

def calculate_crypto_value(message, amount):
    coin_value = safe_float_conversion(message.text)
    if (coin_value is not None) and (coin_value > 0):
        total_value = amount * coin_value
        bot.send_message(message.chat.id, f"Итоговая стоимость: {total_value:.2f}", reply_markup=main)
    else:
        bot.send_message(message.chat.id, "Пожалуйста, введите стоимость одного коина.")



def print_user_data_periodically():
    # Загружаем данные пользователей внутри функции
    user_data = load_user_data()
    print("Текущее состояние user_data:", user_data)
    # Запланировать следующий вызов
    threading.Timer(6000, print_user_data_periodically).start()

# Запустить периодический вывод данных при старте бота
print_user_data_periodically()

# Start command
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = str(message.chat.id)
    user_data_local = load_user_data()
    if chat_id not in user_data_local:
        user_data_local[chat_id] = {
            'total_amount': 0.0, 
            'spent': 0.0, 
            'expenses': [], 
            'categories': {}, 
            'sendCourses': True,
            'crypto_amount': 0.0, 
            'principal': 0.0, 
            'interest_rate': 0.0, 
            'days': 0,
            'daily_budget': 0.0
        }
        save_user_data(user_data_local)
    bot.send_message(chat_id, startMes, reply_markup=main)




@bot.message_handler(commands=['numofusers'])
def num_of_users(message):
    try:
        with open('user_data.json', 'r') as file:
            user_data = json.load(file)
        num_users = len(user_data)
        bot.reply_to(message, f"Количество пользователей: {num_users}")
    except Exception as e:
        bot.reply_to(message, "Ошибка при подсчете пользователей: " + str(e))


# Handler for 'Manage Money'
@bot.message_handler(func=lambda message: message.text == 'Установить бюджет')
def ask_for_amount(message):
    msg = bot.send_message(message.chat.id, "Введите количество средств, которые планируете разбить")
    bot.register_next_step_handler(msg, process_amount_step)

def process_amount_step(message):
    chat_id = str(message.chat.id)
    amount = safe_float_conversion(message.text)
    if amount is not None and amount > 0:
        user_data_local = load_user_data()  
        user_data_local[chat_id]['total_amount'] = amount
        save_user_data(user_data_local)  
        msg = bot.send_message(chat_id, "Бюджет установлен. Введите количество дней, на которые вы хотите его распределить.")
        bot.register_next_step_handler(msg, process_days_step)
    else:
        bot.send_message(chat_id, "Пожалуйста, введите корректную сумму.")


def process_days_step(message):
    chat_id = str(message.chat.id)
    days = safe_float_conversion(message.text)
    user_data_local = load_user_data()
    if days is not None and days > 0:
        user_data_local[chat_id]['days'] = days
        daily_budget = user_data_local[chat_id]['total_amount'] / days
        user_data_local[chat_id]['daily_budget'] = daily_budget
        save_user_data(user_data_local)  
        bot.send_message(chat_id, f"Ваш дневной бюджет: {daily_budget:.2f}₽", reply_markup=main)
    else:
        bot.send_message(chat_id, "Введите корректное количество дней.")



@bot.message_handler(func=lambda message: message.text == 'Баланс')
def show_balance(message):
    chat_id = str(message.chat.id)
    user_data_local = load_user_data()
    if chat_id in user_data_local and 'total_amount' in user_data_local[chat_id]:
        total_amount = user_data_local[chat_id]['total_amount']
        spent = user_data_local[chat_id].get('spent', 0)
        remaining = total_amount - spent
        days_left = user_data_local[chat_id].get('days', 1)
        daily_budget = remaining / days_left if days_left > 0 else 0
        user_data_local[chat_id]['daily_budget'] = daily_budget
        save_user_data(user_data_local)
        bot.send_message(chat_id, f"Оставшийся баланс: {remaining:.2f}₽\nДневной бюджет: {daily_budget:.2f}₽\nДней: {days_left}", reply_markup=main)
    else:
        bot.send_message(chat_id, "Баланс не найден. Возможно, вы еще не начали использовать бюджет.", reply_markup=main)



@bot.message_handler(func=lambda message: message.text == 'Как потратить?')
def how_to_spend(message):
    chat_id = str(message.chat.id)
    user_data_local = load_user_data()  # Загружаем актуальные данные

    # Убедимся, что данные пользователя существуют и инициализированы
    if chat_id in user_data_local:
        user = user_data_local[chat_id]
        
        # Проверяем наличие ключа 'total_amount' и его значение
        if 'total_amount' in user and user['total_amount'] != 0:
            bot.send_message(chat_id, "Предупреждение! Аналитику проводит ИИ, могут быть неточности")
            if user['total_amount'] < 0:
                # Используйте user вместо user_data[chat_id] для доступа к данным текущего пользователя
                response = model.generate_content(f"Представь, что ты жесткий эксперт в финансах, что ты прям финансовый эксперт мира.Я живу в России. У меня долг {user['total_amount']}. Как посоветуешь разобраться с этим долгом?")
                response_text = response.text
                response_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', response_text)  # Замена текст на <b>текст</b>
                response_text = re.sub(r'\* (.*?)', r'🔹 \1', response_text)  # Замена * текст на 🔹 текст
                response_text = re.sub(r'\# (.*?)', r'▪️ \1', response_text)  # Замена # текст на ▪️ текст
                response_text = re.sub(r'\`\`\`(.*?)\`\`\`', r'<code>\1</code>', response_text, flags=re.DOTALL)
                for i in range(0, len(response_text), MAX_MESSAGE_LENGTH): # Если ответ слишком длинный, разбить его на несколько сообщений
                    bot.send_message(chat_id, response_text[i:i+MAX_MESSAGE_LENGTH], parse_mode='HTML', reply_markup=main)
            elif user['total_amount'] > 0:
                # Используйте user вместо user_data[chat_id] для доступа к данным текущего пользователя
                response = model.generate_content(f"Представь, что ты жесткий эксперт в финансах, что ты прям финансовый эксперт мира.Я живу в России. У меня есть {user['total_amount']} на {user['days']} дней, то есть {user['total_amount']/user['days']}. Как посоветуешь их распределить, чтобы еще что-то осталось в конце срока?")
                response_text = response.text
                response_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', response_text)  # Замена текст на <b>текст</b>
                response_text = re.sub(r'\* (.*?)', r'🔹 \1', response_text)  # Замена * текст на 🔹 текст
                response_text = re.sub(r'\# (.*?)', r'▪️ \1', response_text)  # Замена # текст на ▪️ текст
                response_text = re.sub(r'\`\`\`(.*?)\`\`\`', r'<code>\1</code>', response_text, flags=re.DOTALL)
                for i in range(0, len(response_text), MAX_MESSAGE_LENGTH): # Если ответ слишком длинный, разбить его на несколько сообщений
                    bot.send_message(chat_id, response_text[i:i+MAX_MESSAGE_LENGTH], parse_mode='HTML', reply_markup=main)
        else:
            bot.send_message(chat_id, "Ваш баланс пустой", reply_markup=main)
    else:
        bot.send_message(chat_id, "Данные пользователя не найдены. Возможно, вы еще не начали использовать бота.", reply_markup=main)


@bot.message_handler(func=lambda message: message.text == "Внести трату")
def initiate_expense_entry(message):
    msg = bot.send_message(message.chat.id, "Введите сумму расхода:")
    bot.register_next_step_handler(msg, process_expense_amount)


def show_categories(message):
    msg = bot.send_message(message.chat.id, "Введите категорию расхода (не более 15 символов):")
    bot.register_next_step_handler(msg, process_expense_category)


def process_expense_amount(message):
    chat_id = str(message.chat.id)
    amount = safe_float_conversion(message.text)
    if amount is not None:
        msg = bot.send_message(chat_id, "Введите категорию расхода:")
        bot.register_next_step_handler(msg, process_expense_category, amount)
    else:
        bot.send_message(chat_id, "Пожалуйста, введите корректное число. Сумма расхода должна быть положительной.")

def process_expense_category(message, amount):
    chat_id = str(message.chat.id)
    category = message.text.strip()
    
    user_data_local = load_user_data()  # Загружаем актуальные данные
    
    # Инициализируем данные пользователя, если они ещё не были инициализированы
    if chat_id not in user_data_local:
        user_data_local[chat_id] = {
            'total_amount': 0.0, 
            'spent': 0.0, 
            'categories': {},  # Правильно инициализируем как словарь
            'crypto_amount': 0.0, 
            'principal': 0.0, 
            'interest_rate': 0.0, 
            'days': 0,
            'daily_budget': 0.0
        }
    
    # Добавляем или обновляем категорию с расходом
    user_data_local[chat_id].setdefault('categories', {})[category] = user_data_local[chat_id].get('categories', {}).get(category, 0) + amount
    
    # Вычитаем сумму расхода из общего баланса
    user_data_local[chat_id]['total_amount'] -= amount
    
    # Пересчитываем дневной бюджет
    days_left = max(user_data_local[chat_id].get('days', 1), 1)
    new_daily_budget = max((user_data_local[chat_id]['total_amount'] / days_left), 0) if days_left > 0 else 0
    user_data_local[chat_id]['daily_budget'] = new_daily_budget

    save_user_data(user_data_local)  # Сохраняем обновленные данные пользователя
    
    bot.send_message(chat_id, f"Расход {amount}₽ на '{category}' добавлен. Ваш новый баланс: {user_data_local[chat_id]['total_amount']:.2f}₽\nДневной бюджет: {new_daily_budget:.2f}₽", reply_markup=main)



def generate_expense_chart_and_summary(chat_id):
    summary_text = "Расходы по категориям:\n"
    if 'expenses' in user_data[chat_id] and user_data[chat_id]['expenses']:
        categories = {}
        for expense in user_data[chat_id]['expenses']:
            categories[expense['category']] = categories.get(expense['category'], 0) + expense['amount']
        
        for category, amount in categories.items():
            summary_text += f"{category} - {amount:.2f}\n"
        
        fig, ax = plt.subplots()
        ax.pie(categories.values(), labels=categories.keys(), autopct='%1.1f%%', startangle=90)
        ax.axis('equal')  # Для круговой диаграммы
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)  # Очищаем память от фигуры
        return buf, summary_text
    else:
        return None, summary_text.rstrip()


def get_crypto_price(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    price_container = soup.find('div', class_='sc-f70bb44c-0 flfGQp flexStart alignBaseline')
    price = price_container.find('span', class_='sc-f70bb44c-0 jxpCgO base-text').text
    return price


@bot.message_handler(func=lambda message: message.text == "Таблица трат")
def display_expenses(message):
    chat_id = str(message.chat.id)
    user_data_local = load_user_data()  # Загружаем актуальные данные

    # Проверяем наличие категорий расходов вместо списка expenses
    if chat_id in user_data_local and 'categories' in user_data_local[chat_id] and user_data_local[chat_id]['categories']:
        # Готовим данные для круговой диаграммы
        categories = user_data_local[chat_id]['categories']
        labels = list(categories.keys())
        sizes = list(categories.values())

        # Создаем круговую диаграмму
        fig, ax = plt.subplots()
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

        # Сохраняем диаграмму в память
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)

        # Отправляем фото диаграммы пользователю
        bot.send_photo(chat_id, photo=buf)
        plt.close(fig)  # Закрываем фигуру, чтобы освободить память

    else:
        # Если данных о расходах нет, сообщаем об этом пользователю
        bot.send_message(chat_id, "Расходы пока не добавлены. Используйте 'Внести трату', чтобы начать учет расходов.", reply_markup=main)

@bot.message_handler(func=lambda message: message.text == "Курсы криптовалют")
def show_crypto_options(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
    cryptos = ["Bitcoin", "Ethereum", "Tether USDt", "Solana", "BNB", "XRP", "USDC", "Cardano", "Avalanche", "Dogecoin", "Chainlink", "Tron", "Polkadot", "Polygon", "Toncoin"]
    for crypto in cryptos:
        markup.add(types.KeyboardButton(crypto))
    bot.send_message(message.chat.id, "Выберите криптовалюту:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ["Bitcoin", "Ethereum", "Tether USDt", "Solana", "BNB", "XRP", "USDC", "Cardano", "Avalanche", "Dogecoin", "Chainlink", "Tron", "Polkadot", "Polygon", "Toncoin"])
def crypto_price(message):
    crypto_urls = {
        "Bitcoin": "https://coinmarketcap.com/currencies/bitcoin/",
        "Ethereum": "https://coinmarketcap.com/currencies/ethereum/",
        "Tether USDt": 'https://coinmarketcap.com/currencies/tether/',
        "Solana": "https://coinmarketcap.com/currencies/solana/",
        "BNB": "https://coinmarketcap.com/currencies/bnb/",
        "XRP": "https://coinmarketcap.com/currencies/xrp/",
        "USDC": "https://coinmarketcap.com/currencies/usd-coin/",
        "Cardano": "https://coinmarketcap.com/currencies/cardano/",
        "Avalanche": "https://coinmarketcap.com/currencies/avalanche/",
        "Dogecoin": "https://coinmarketcap.com/currencies/dogecoin/",
        "Chainlink": "https://coinmarketcap.com/currencies/chainlink/",
        "Tron": "https://coinmarketcap.com/currencies/tron/",
        "Polkadot": "https://coinmarketcap.com/currencies/polkadot-new/",
        "Polygon": "https://coinmarketcap.com/currencies/polygon/",
        "Toncoin": "https://coinmarketcap.com/currencies/toncoin/",
    }
    if message.text in crypto_urls:
        price = get_crypto_price(crypto_urls[message.text])
        bot.send_message(message.chat.id, f"1{message.text} = <b>{price}$</b>", reply_markup=main, parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, "Извините, информация по данной криптовалюте не найдена.")

@bot.message_handler(func=lambda message: message.text == "Рассчитать процент")
def ask_for_principal(message):
    msg = bot.send_message(message.chat.id, "Введите сумму кредита:")
    bot.register_next_step_handler(msg, process_principal_step)

def get_currency_rates():
    urls = {
        "Bitcoin": "https://coinmarketcap.com/currencies/bitcoin/",  
        "TonCoin": "https://coinmarketcap.com/currencies/toncoin/",
        "Ethereum": "https://coinmarketcap.com/currencies/ethereum/",
        "Tether USDt": 'https://coinmarketcap.com/currencies/tether/',
        "Solana": "https://coinmarketcap.com/currencies/solana/",
        "BNB": "https://coinmarketcap.com/currencies/bnb/",
        "Avalanche": "https://coinmarketcap.com/currencies/avalanche/",
        "Dogecoin": "https://coinmarketcap.com/currencies/dogecoin/",
        "Chainlink": "https://coinmarketcap.com/currencies/chainlink/",
        "Tron": "https://coinmarketcap.com/currencies/tron/",
    }
    rates = {}

    for currency, url in urls.items():
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Условные селекторы, измените их на актуальные для вашего случая
            if currency == "Dollar":
                price_container = soup.find('div', class_='text-5xl/9 font-bold md:text-[42px] md:leading-[60px] text-[#232526]')
            else:
                price_container = soup.find('div', class_='sc-f70bb44c-0 flfGQp flexStart alignBaseline')
            
            if price_container:
                price = price_container.find('span', class_='sc-f70bb44c-0 jxpCgO base-text').text
                rates[currency] = price
        else:
            rates[currency] = "Ошибка при запросе"

    # Формируем сообщение с курсами валют
    rates_message = "Курсы валют:\n" + "\n".join([f"<b>{currency}</b>: <u>{rate}</u>\n" for currency, rate in rates.items()])
    final = "Хотите ли вы получать уведомления о курсах валют?"
    return rates_message+final

def send_currency_rates():
    user_data = load_user_data()
    
    for chat_id in user_data:
        if user_data[chat_id].get('sendCourses', False):
            rates_message = get_currency_rates()
            markup = types.InlineKeyboardMarkup()
            yes_button = types.InlineKeyboardButton(text="Да", callback_data="continue_yes")
            no_button = types.InlineKeyboardButton(text="Нет", callback_data="continue_no")
            markup.add(yes_button, no_button)
            bot.send_message(chat_id, rates_message, reply_markup=markup, parse_mode='HTML')
    # Перезапускаем задачу через 3600 секунд (1 час)
    threading.Timer(3600, send_currency_rates).start()


@bot.callback_query_handler(func=lambda call: call.data.startswith('continue_'))
def handle_subscription_callback(call):
    chat_id = str(call.message.chat.id)
    user_data = load_user_data()
    if call.data == "continue_yes":
        bot.answer_callback_query(call.id, "Спасибо! Рассылка с курсами будет продолжаться")
        user_data[chat_id]['sendCourses'] = True
        save_user_data(user_data)
    elif call.data == "continue_no":
        if chat_id in user_data:
            user_data[chat_id]['sendCourses'] = False
            save_user_data(user_data)
        bot.answer_callback_query(call.id, "Вы отписались от рассылки курсов валют.")


def decrement_days():
    user_data = load_user_data()
    for user_id, data in user_data.items():
        if data['days'] > 0:
            data['days'] -= 1
            # Тут можно добавить пересчет дневного бюджета, если необходимо
            # Например:
            if data['days'] > 0:
                data['daily_budget'] = data['total_amount'] / data['days']
            else:
                data['daily_budget'] = 0
    save_user_data(user_data)
    # Запланировать следующее уменьшение через 24 часа
    threading.Timer(86400, decrement_days).start()

def ensure_user_data_initialized(chat_id):
    if str(chat_id) not in user_data:
        user_data[str(chat_id)] = {
            'total_amount': 0.0, 
            'spent': 0.0, 
            'expenses': [], 
            'categories': [], 
            'crypto_amount': 0.0, 
            'principal': 0.0, 
            'interest_rate': 0, 
            'days': 0,
            'daily_budget': 0.0,
            'years': 0
        }
        save_user_data()

def process_principal_step(message):
    principal = safe_float_conversion(message.text)
    if principal is not None and principal > 0:
        msg = bot.send_message(message.chat.id, "Введите годовой процент:")
        # Передаем principal как дополнительный аргумент
        bot.register_next_step_handler(msg, process_interest_rate_step, principal)
    else:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректную сумму.")

def process_interest_rate_step(message, principal):
    interest_rate = safe_float_conversion(message.text)
    if interest_rate is not None and interest_rate > 0:
        msg = bot.send_message(message.chat.id, "На сколько лет выдан кредит?")
        # Передаем principal и interest_rate как дополнительные аргументы
        bot.register_next_step_handler(msg, process_years_step, principal, interest_rate)
    else:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректный процент.")

def process_years_step(message, principal, interest_rate):
    years = safe_float_conversion(message.text)
    if years is not None and years > 0:
        total_amount = principal * (1 + interest_rate / 100) ** years
        bot.send_message(message.chat.id, f"Через {years} лет(года) вы должны будете вернуть: {total_amount:.2f}")
    else:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректное количество лет.")


@bot.message_handler(func=lambda message: message.text in ["Управление деньгами", "Внести трату", "Курсы валют", "Таблица трат"])
def handle_menu_options(message):
    if message.text == "Управление деньгами":
        show_money_management_menu(message)

def run_periodic_tasks():
    # Запуск функций в отдельных потоках
    threading.Thread(target=send_currency_rates).start()
    threading.Thread(target=decrement_days).start()

if __name__ == '__main__':
    # Запускаем периодические задачи в отдельном потоке
    run_periodic_tasks()
    bot.infinity_polling()