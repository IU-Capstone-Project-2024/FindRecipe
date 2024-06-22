import telebot
import os
from dotenv import load_dotenv
import requests
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()
TOKEN = os.getenv('TOKEN')

bot = telebot.TeleBot(TOKEN, parse_mode=None)
FASTAPI_URL = os.getenv('FASTAPI')

#### Алие

user_data = dict()


@bot.message_handler(commands=['start', 'help'])
def start(message):
    text_message = ('''Привет! Я помогу тебе составить рацион на неделю, исходя из твоих предпочтений.\nВот, что можно сделать:\n\
        - создать новое меню\n\
        - редактировать существующее меню\n\
        - посмотреть черный список\n\
        - редактировать черный список\n\
    Все эти функции доступны в виде кнопок''')

    main_page(bot, message, text_message)


def main_page(bot, message, text):
    markup = types.ReplyKeyboardMarkup()
    txt = 'Начать составление'
    itembtn_generate = types.KeyboardButton(txt)
    markup.row(itembtn_generate)

    bot.send_message(message.chat.id, text, parse_mode='html', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in ['Начать составление'])
def start_generating(message):
    global user_data
    user_data = dict()
    choose_param(message)


def choose_param(message):
    txt = 'Выбери параметр, чтобы изменить его'
    markup = types.InlineKeyboardMarkup()
    calories = types.InlineKeyboardButton('калорийность', callback_data='calories')
    time = types.InlineKeyboardButton('время готовки', callback_data='time')
    products = types.InlineKeyboardButton('количество продуктов', callback_data='products')
    spicy = types.InlineKeyboardButton('острота', callback_data='spicy')
    complexity = types.InlineKeyboardButton('сложноть', callback_data='complexity')
    blacklist = types.InlineKeyboardButton('черный список', callback_data='blacklist')
    generate = types.InlineKeyboardButton('составить меню', callback_data='generate')
    markup.add(generate)
    markup.row(calories, time)
    markup.row(spicy, complexity)
    markup.add(products)

    markup.add(blacklist)
    bot.send_message(message.chat.id, txt, parse_mode='html', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "products")
def modify_products(call: types.CallbackQuery):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                          text='Enter a number - list of products')
    bot.register_next_step_handler(call.message, process_products_input)


def process_products_input(message):
    products = message.text
    user_data['products'] = products
    choose_param(message)


@bot.callback_query_handler(func=lambda call: call.data == "calories")
def modify_calories(call: types.CallbackQuery):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='Введи калорийность в ккал')
    bot.register_next_step_handler(call.message, process_calories_input)


def process_calories_input(message):
    calories = message.text
    user_data['calories'] = calories
    choose_param(message)


@bot.callback_query_handler(func=lambda call: call.data == "time")
def modify_time(call: types.CallbackQuery):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='Введи время готовки в минутах')
    bot.register_next_step_handler(call.message, process_time_input)


def process_time_input(message):
    time = message.text
    user_data['time'] = time
    choose_param(message)


@bot.callback_query_handler(func=lambda call: call.data == "spicy")
def modify_spicy(call: types.CallbackQuery):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                          text='Введи число - степень остроты от 1 до 5')
    bot.register_next_step_handler(call.message, process_time_input)


def process_spicy_input(message):
    spicy = message.text
    user_data['spicy'] = spicy
    choose_param(message)


@bot.callback_query_handler(func=lambda call: call.data == "complexity")
def modify_complexity(call: types.CallbackQuery):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                          text='Введи число - сложность блюда от 1 до 5')
    bot.register_next_step_handler(call.message, process_time_input)


def process_complexity_input(message):
    complexity = message.text
    user_data['complexity'] = complexity
    choose_param(message)


@bot.callback_query_handler(func=lambda call: call.data == "blacklist")
def modify_blacklist(call: types.CallbackQuery):
    #sonyas.send_product_list(call.message)
    pass


@bot.callback_query_handler(func=lambda call: call.data == "generate")
def generate(call: types.CallbackQuery):
    get_menu(call.message)


### Ilsiia

def get_user_data(message):
    payload = {
        "bad_products": [],
        "calories": 2000,
        "pfc": [],
        "time": 120,
        "replace": [],
        "diff": 5,
        "spicy": 0,
        "num_products": 25
    }
    return payload


def format_menu_day(menu, day_index):
    day_menu = menu[day_index]
    day_text = f"День {day_index + 1}:\n"
    for recipe in day_menu:
        day_text += (
            f"- {recipe['name']}\n"
            f"  Время готовки: {recipe['time']} минут\n"
            f"  Калории: {recipe['calories']}\n"
            f"  Белки/Жиры/Углеводы: {recipe['pfc'][0]}/{recipe['pfc'][1]}/{recipe['pfc'][2]}\n"
            f"  Ссылка на рецепт: {recipe['link_to_recipe']}\n"
        )
    return day_text


def format_shop_list(shopping_list):
    shopping_list_text = "Shopping List:\n"
    for product, quantity in shopping_list.items():
        shopping_list_text += f"- {product}: {quantity}\n"
    return shopping_list_text


def create_navigation_buttons(current_day):
    days = ['Список покупок', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    markup = InlineKeyboardMarkup()
    if current_day == -1:
        next_day = InlineKeyboardButton(days[1], callback_data=f"next_{current_day}")
        markup.add(next_day)
        blacklist = InlineKeyboardButton("Добавить в черный список", callback_data=f"next_{current_day}")
        markup.add(blacklist)
    elif current_day == 6:
        prev_day = InlineKeyboardButton(days[current_day], callback_data=f"prev_{current_day}")
        markup.add(prev_day)
        change_breakfast = InlineKeyboardButton("Заменить завтрак", callback_data=f"change_breakfast_{current_day}")
        change_lunch = InlineKeyboardButton("Заменить обед", callback_data=f"change_lunch_{current_day}")
        change_dinner = InlineKeyboardButton("Заменить ужин", callback_data=f"change_dinner_{current_day}")
        change_day = InlineKeyboardButton("Заменить день", callback_data=f"change_day_{current_day}")

        markup.add(change_breakfast)
        markup.add(change_lunch)
        markup.add(change_dinner)
        markup.add(change_day)
    else:
        prev_day = InlineKeyboardButton(days[current_day], callback_data=f"prev_{current_day}")
        next_day = InlineKeyboardButton(days[current_day+2], callback_data=f"next_{current_day}")
        markup.add(prev_day, next_day)
        change_breakfast = InlineKeyboardButton("Заменить завтрак", callback_data=f"change_breakfast_{current_day}")
        change_lunch = InlineKeyboardButton("Заменить обед", callback_data=f"change_lunch_{current_day}")
        change_dinner = InlineKeyboardButton("Заменить ужин", callback_data=f"change_dinner_{current_day}")
        change_day = InlineKeyboardButton("Заменить день", callback_data=f"change_day_{current_day}")

        markup.add(change_breakfast)
        markup.add(change_lunch)
        markup.add(change_dinner)
        markup.add(change_day)


    return markup


def get_menu(message):
    payload = get_user_data(message)
    try:
        response = requests.post(FASTAPI_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        shopping_list = data['list_of_products']
        current_day = -1  # if day is -1, then we show shopping list
        shopping_list_text = format_shop_list(shopping_list)
        markup = create_navigation_buttons(current_day)
        bot.send_message(message.chat.id, shopping_list_text, reply_markup=markup)

    except requests.exceptions.RequestException as e:
        bot.reply_to(message, f"Failed to retrieve menu: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith(('prev_', 'next_')))
def navigate_menu(call):
    payload = get_user_data(call)
    try:
        response = requests.post(FASTAPI_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        menu = data['menu']
        shopping_list = data['list_of_products']
        current_day = int(call.data.split('_')[1])

        if 'prev' in call.data and current_day > -1:
            current_day -= 1
        elif 'next' in call.data and current_day < len(menu) - 1:
            current_day += 1

        if current_day == -1:
            text = format_shop_list(shopping_list)
        else:
            text = format_menu_day(menu, current_day)

        markup = create_navigation_buttons(current_day)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text,
                              reply_markup=markup)

    except requests.exceptions.RequestException as e:
        bot.reply_to(call.message, f"Failed to retrieve menu: {e}")


bot.infinity_polling()
