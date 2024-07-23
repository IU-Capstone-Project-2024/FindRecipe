import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import telebot
import os
from dotenv import load_dotenv
import requests
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from io import BytesIO
import urllib
from PIL import Image
import re
import ast

load_dotenv()
TOKEN = os.getenv('TOKEN')

bot = telebot.TeleBot(TOKEN)
FASTAPI_URL = os.getenv('FASTAPI')
product_status = dict()
products = dict()
MIN_DIMENSION = 320
#### Aliye

user_data = dict()


def set_initial_preferences(message):
    user_preferences = {
        "bad_products": [],
        "calories": 2000,
        "pfc": [],
        "time": 300,
        "diff": 5,
        "spicy": 5,
        "num_products": 25
    }

    chat_id = message.chat.id
    user_preferences_json = json.dumps(user_preferences, ensure_ascii=False)
    # raise Exception(user_preferences_json)

    user_request = requests.post(f"{FASTAPI_URL}/preferences",
                                 json={"data": user_preferences_json, 'chat_id': str(chat_id)})
    user_request.raise_for_status()


@bot.message_handler(commands=['start', 'help'])
def start(message):
    text_message = ('''Привет! Я помогу тебе составить рацион на неделю, исходя из твоих предпочтений.\nВот, что можно сделать:\n\
        - создать новое меню\n\
        - редактировать существующее меню\n\
        - посмотреть черный список\n\
        - редактировать черный список\n\
    Все эти функции доступны в виде кнопок''')

    set_initial_preferences(message)

    main_page(message, text_message)


def main_page(message, text):
    markup = types.ReplyKeyboardMarkup()
    txt = 'Начать составление'
    itembtn_generate = types.KeyboardButton(txt)
    markup.row(itembtn_generate)
    photo = open('options.JPG', 'rb')
    bot.send_photo(chat_id=message.chat.id, photo=photo, caption=text, parse_mode='html', reply_markup=markup)
    # bot.send_message(message.chat.id, text, parse_mode='html', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in ['Начать составление'])
def start_generating(message):
    global user_data
    user_data = dict()
    choose_param(message)


def choose_param(message, option=None):
    pref_request = requests.get(f"{FASTAPI_URL}/preferences", params={'chat_id': message.chat.id})
    while 'not found' in json.loads(pref_request.content.decode('ascii')):
        set_initial_preferences(message)
        pref_request = requests.get(f"{FASTAPI_URL}/preferences", params={'chat_id': message.chat.id})
    data = json.loads(json.loads(pref_request.content.decode('ascii')))
    txt = f"""
Выбери параметр, чтобы изменить его
⚖️ калорийность - {data["calories"]}
⏰ время готовки - {data["time"]}
🌶 острота - {data["spicy"]}
📊 сложноть - {data["diff"]}
🛒 количество продуктов - {data["num_products"]}
"""
    markup = InlineKeyboardMarkup()
    calories = InlineKeyboardButton('⚖️ калорийность', callback_data='calories')
    time = InlineKeyboardButton('⏰ время готовки', callback_data='time')
    products = InlineKeyboardButton('🛒 количество продуктов', callback_data='products')
    spicy = InlineKeyboardButton('🌶 острота', callback_data='spicy')
    complexity = InlineKeyboardButton('📊 сложноть', callback_data='complexity')
    blacklist = InlineKeyboardButton('❌ черный список', callback_data='blacklist')
    generate = InlineKeyboardButton('🍽 составить меню', callback_data='generate')
    markup.add(generate)
    markup.row(calories, time)
    markup.row(spicy, complexity)
    markup.add(products)

    markup.add(blacklist)
    photo = open('options.JPG', 'rb')
    if option:
        media = types.InputMediaPhoto(photo, caption=txt)
        bot.edit_message_media(media=media, chat_id=message.chat.id, message_id=message.message_id,
                               reply_markup=markup)
    else:
        bot.send_photo(message.chat.id, photo=photo, caption=txt, parse_mode='html', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "products")
def modify_products(call: types.CallbackQuery):
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
    bot.send_message(chat_id=call.message.chat.id,
                     text='Введите количество продуктов на неделю (10-35)')
    bot.register_next_step_handler(call.message, process_products_input)


def modify_products_2(message):
    bot.delete_message(chat_id=message.chat.id, message_id=message.id)
    bot.send_message(chat_id=message.chat.id,
                     text='Введите количество продуктов на неделю (10-35)')
    bot.register_next_step_handler(message, process_products_input)


def process_products_input(message):
    products = message.text

    try:
        if not 10 <= int(products) <= 35:
            modify_products_2(message)
            return
    except Exception:
        modify_products_2(message)
        return

    chat_id = message.chat.id

    pref_request = requests.get(f"{FASTAPI_URL}/preferences", params={'chat_id': chat_id})
    pref_request.raise_for_status()

    user_preferences = json.loads(json.loads(pref_request.content))
    user_preferences['num_products'] = products
    user_preferences_json = json.dumps(user_preferences)

    user_request = requests.post(f"{FASTAPI_URL}/preferences",
                                 json={'chat_id': str(chat_id), 'data': user_preferences_json})
    user_request.raise_for_status()
    choose_param(message)


@bot.callback_query_handler(func=lambda call: call.data == "calories")
def modify_calories(call: types.CallbackQuery):
    bot.delete_message(chat_id=call.message.chat.id,
                       message_id=call.message.id)
    bot.send_message(chat_id=call.message.chat.id,
                     text='Введи калорийность в ккал. (1300-2500)')
    bot.register_next_step_handler(call.message,
                                   process_calories_input)


def modify_calories_2(message):
    bot.delete_message(chat_id=message.chat.id,
                       message_id=message.id)
    bot.send_message(chat_id=message.chat.id,
                     text='Введи калорийность в ккал. (1300-2500)')
    bot.register_next_step_handler(message,
                                   process_calories_input)


def process_calories_input(message):
    calories = message.text
    try:
        if not 1300 <= int(calories) <= 2500:
            modify_calories_2(message)
            return
    except Exception:
        modify_calories_2(message)
        return

    chat_id = message.chat.id

    pref_request = requests.get(f"{FASTAPI_URL}/preferences", params={'chat_id': chat_id})
    pref_request.raise_for_status()

    user_preferences = json.loads(json.loads(pref_request.content))
    user_preferences['calories'] = calories
    user_preferences_json = json.dumps(user_preferences)

    user_request = requests.post(f"{FASTAPI_URL}/preferences",
                                 json={"data": user_preferences_json, 'chat_id': str(chat_id)})

    user_request.raise_for_status()

    choose_param(message)


@bot.callback_query_handler(func=lambda call: call.data == "time")
def modify_time(call: types.CallbackQuery):
    bot.delete_message(chat_id=call.message.chat.id,
                       message_id=call.message.id)
    bot.send_message(chat_id=call.message.chat.id,
                     text='Введи время готовки в минутах. (10-300 минут. Ввод просто число)')
    bot.register_next_step_handler(call.message, process_time_input)


def modify_time_2(message):
    bot.delete_message(chat_id=message.chat.id,
                       message_id=message.id)
    bot.send_message(chat_id=message.chat.id,
                     text='Введи время готовки в минутах. (10-300 минут. Ввод просто число)')
    bot.register_next_step_handler(message, process_time_input)


def process_time_input(message):
    time = message.text
    try:
        if not 10 <= int(time) <= 300:
            modify_time_2(message)
            return
    except Exception:
        modify_time_2(message)
        return

    chat_id = message.chat.id

    pref_request = requests.get(f"{FASTAPI_URL}/preferences", params={'chat_id': chat_id})
    pref_request.raise_for_status()

    user_preferences = json.loads(json.loads(pref_request.content))
    user_preferences['time'] = time
    user_preferences_json = json.dumps(user_preferences)

    user_request = requests.post(f"{FASTAPI_URL}/preferences",
                                 json={"data": user_preferences_json, 'chat_id': str(chat_id)})
    user_request.raise_for_status()

    choose_param(message)


@bot.callback_query_handler(func=lambda call: call.data == "spicy")
def modify_spicy(call: types.CallbackQuery):
    bot.delete_message(chat_id=call.message.chat.id,
                       message_id=call.message.id)
    bot.send_message(chat_id=call.message.chat.id,
                     text='Введи число - степень максимальной остроты от 1 до 5')
    bot.register_next_step_handler(call.message, process_spicy_input)


def modify_spicy_2(message):
    bot.delete_message(chat_id=message.chat.id,
                       message_id=message.id)
    bot.send_message(chat_id=message.chat.id,
                     text='Введи число - степень максимальной остроты от 1 до 5')
    bot.register_next_step_handler(message, process_spicy_input)


def process_spicy_input(message):
    spicy = message.text
    try:
        if not 1 <= int(spicy) <= 5:
            modify_spicy_2(message)
            return
    except Exception:
        modify_spicy_2(message)
        return

    chat_id = message.chat.id

    pref_request = requests.get(f"{FASTAPI_URL}/preferences", params={'chat_id': chat_id})
    pref_request.raise_for_status()

    user_preferences = json.loads(json.loads(pref_request.content))
    user_preferences['spicy'] = spicy
    user_preferences_json = json.dumps(user_preferences)

    user_request = requests.post(f"{FASTAPI_URL}/preferences",
                                 json={"data": user_preferences_json, 'chat_id': str(chat_id)})
    user_request.raise_for_status()

    choose_param(message)


@bot.callback_query_handler(func=lambda call: call.data == "complexity")
def modify_complexity(call: types.CallbackQuery):
    bot.delete_message(chat_id=call.message.chat.id,
                       message_id=call.message.id)
    bot.send_message(chat_id=call.message.chat.id,
                     text='Введи число - сложность блюда от 1 до 5')
    bot.register_next_step_handler(call.message, process_complexity_input)


def modify_complexity_2(message):
    bot.delete_message(chat_id=message.chat.id,
                       message_id=message.id)
    bot.send_message(chat_id=message.chat.id,
                     text='Введи число - сложность блюда от 1 до 5')
    bot.register_next_step_handler(message, process_complexity_input)


def process_complexity_input(message):
    complexity = message.text
    try:
        if not 1 <= int(complexity) <= 5:
            modify_complexity_2(message)
            return
    except Exception:
        modify_complexity_2(message)
        return

    chat_id = message.chat.id

    pref_request = requests.get(f"{FASTAPI_URL}/preferences", params={'chat_id': chat_id})
    pref_request.raise_for_status()

    user_preferences = json.loads(json.loads(pref_request.content))
    user_preferences['diff'] = complexity
    user_preferences_json = json.dumps(user_preferences)

    user_request = requests.post(f"{FASTAPI_URL}/preferences",
                                 json={"data": user_preferences_json, 'chat_id': str(chat_id)})
    user_request.raise_for_status()

    choose_param(message)


@bot.callback_query_handler(func=lambda call: call.data == "blacklist")
def modify_blacklist(call: types.CallbackQuery):
    send_product_list(call)


### Sofia

blacklist = []


def return_edit(message):
    txt = 'Выбери параметр, чтобы изменить его'
    markup = types.InlineKeyboardMarkup()
    calories = types.InlineKeyboardButton('калорийность', callback_data='calories')
    time = types.InlineKeyboardButton('время готовки', callback_data='time')
    products = types.InlineKeyboardButton('количество продуктов', callback_data='products')
    spicy = types.InlineKeyboardButton('острота', callback_data='spicy')
    complexity = types.InlineKeyboardButton('сложность', callback_data='complexity')
    blacklist = types.InlineKeyboardButton('черный список', callback_data='blacklist')
    generate = types.InlineKeyboardButton('составить меню', callback_data='generate')

    # Organizing buttons into rows and individual placements
    markup.add(generate)
    markup.row(calories, time)
    markup.row(spicy, complexity)
    markup.add(products)
    markup.add(blacklist)

    # Editing the original message instead of sending a new one
    bot.edit_message_text(chat_id=message.chat.id,
                          message_id=message.message_id,
                          text=txt,
                          reply_markup=markup,
                          parse_mode='html')


@bot.callback_query_handler(func=lambda call: call.data == "chs_")
def modify_products(call: types.CallbackQuery):
    choose_param(call.message, option=1)


@bot.callback_query_handler(func=lambda call: call.data == "back")
def modify_times(call: types.CallbackQuery):
    choose_param(call.message, option=1)


def update_status(product, call):
    global product_status
    product_status[call.from_user.id][product] = not product_status[call.from_user.id][product]


def create_status(prods, call):
    global product_status
    product_status[call.from_user.id] = {product: False for product in prods}


def read_list(list_str):
    list_str = list_str.strip("[]")
    pattern = r"'([^']*)'"
    return re.findall(pattern, list_str)


def send_product_list(call: CallbackQuery, page=0):
    try:
        response = requests.get(f"{FASTAPI_URL}/chs", params={"chat_id": str(call.from_user.id)})
        if response.text[1] != "[":
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("Назад", callback_data="chs_"))
            photo = open('chs.jpg', 'rb')
            media = types.InputMediaPhoto(photo, caption='Черный список пуст')
            bot.edit_message_media(media=media, chat_id=call.message.chat.id, message_id=call.message.message_id,
                                   reply_markup=markup)
            return
        else:
            global products
            products[call.from_user.id] = read_list(response.text)
            global product_status
            product_status[call.from_user.id] = {product: False for product in products[call.from_user.id]}
            markup = create_product_markup(page, products[call.from_user.id], call)
            photo = open('chs.jpg', 'rb')
            media = types.InputMediaPhoto(photo, caption='Выберите продукты, чтобы удалить из списка:')
            bot.edit_message_media(media=media, chat_id=call.message.chat.id, message_id=call.message.message_id,
                                   reply_markup=markup)
    except Exception as e:
        bot.reply_to(call.message, f"Error: {str(e)}")


def add_shopping_list(call: CallbackQuery, message, page=0):
    global products
    create_status(products[call.from_user.id], call)
    markup = create_shopping_markup(page, products[call.from_user.id], call)
    photo = open('chs.jpg', 'rb')
    media = types.InputMediaPhoto(photo, caption="Выберите продукты, чтобы добавить в чс:")
    bot.edit_message_media(media=media, chat_id=call.message.chat.id, message_id=call.message.message_id,
                           reply_markup=markup)


def create_product_markup(page, products, call):
    global product_status
    buttons_per_page = min(max(5, (len(products) + 2) // 3), 10)
    markup = InlineKeyboardMarkup()
    start = page * buttons_per_page
    end = start + buttons_per_page
    for product in products[start:end]:
        emoji = " ✅" if product_status[call.from_user.id][product] else " 🔴"
        markup.add(InlineKeyboardButton(product + emoji, callback_data=f"product_{product}"))

    if len(products) > buttons_per_page:
        pagination_buttons = []
        if page > 0:
            pagination_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"page_{page - 1}"))
        if end < len(products):
            pagination_buttons.append(InlineKeyboardButton("➡️", callback_data=f"page_{page + 1}"))
        markup.add(*pagination_buttons)

    markup.add(InlineKeyboardButton("Завершить редактирование черного списка", callback_data="confirm"))

    return markup


def create_shopping_markup(page, products, call):
    global product_status
    buttons_per_page = min(max(5, (len(products) + 2) // 3), 8)
    markup = InlineKeyboardMarkup()
    start = page * buttons_per_page
    end = start + buttons_per_page
    counter = start
    for product in products[start:end]:
        emoji = " 🔴" if product_status[call.from_user.id][product] else ""
        markup.add(InlineKeyboardButton(product + emoji, callback_data=f"sh_{counter}"))
        counter += 1

    if len(products) > buttons_per_page:
        pagination_buttons = []
        if page > 0:
            pagination_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"shpage_{page - 1}"))
        if end < len(products):
            pagination_buttons.append(InlineKeyboardButton("➡️", callback_data=f"shpage_{page + 1}"))
        markup.add(*pagination_buttons)

    markup.add(InlineKeyboardButton("Добавить продукты в черный список", callback_data="shconfirm"))

    return markup


@bot.callback_query_handler(func=lambda call: call.data.startswith("page_"))
def page_handler(call: CallbackQuery):
    global products
    page = int(call.data.split("_")[1])
    markup = create_product_markup(page, products[call.from_user.id], call)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("shpage_"))
def page_handler(call: CallbackQuery):
    global products
    page = int(call.data.split("_")[1])
    markup = create_shopping_markup(page, products[call.from_user.id], call)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm"))
def confirm_handler(call: CallbackQuery):
    global product_status
    selected_products = [product for product, status in product_status[call.from_user.id].items() if status]
    if selected_products:
        selected_products = [product for product, status in product_status[call.from_user.id].items() if status]
        not_selected_products = [product for product, status in product_status[call.from_user.id].items() if status]
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Вернуться к редактированию меню", callback_data="back"))
        response = requests.get(f"{FASTAPI_URL}/chs", params={"chat_id": str(call.from_user.id)})
        if response.text[1] == "[":
            cur_list = read_list(response.text)
            set1 = set(cur_list)
            set2 = set(selected_products)
            selected_products = list(set1.symmetric_difference(set2))
        try:
            requests.post(f"{FASTAPI_URL}/chs",
                          json={'chat_id': str(call.from_user.id), "data": str(selected_products)})
        except:
            # bot.reply_to(call.message.id, "err")
            print("err")
        photo = open('chs.jpg', 'rb')
        media = types.InputMediaPhoto(photo, caption=f"Удалено из черного списка:\n" + "\n".join(not_selected_products))
        bot.edit_message_media(media=media, chat_id=call.message.chat.id, message_id=call.message.message_id,
                               reply_markup=markup)
    else:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Вернуться к редактированию меню", callback_data="back"))
        photo = open('chs.jpg', 'rb')
        media = types.InputMediaPhoto(photo, caption="Черный список не обновлен.")
        bot.edit_message_media(media=media, chat_id=call.message.chat.id, message_id=call.message.message_id,
                               reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("shconfirm"))
def shconfirm_handler(call: CallbackQuery):
    global product_status
    selected_products = [product for product, status in product_status[call.from_user.id].items() if status]
    if selected_products:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Вернуться к меню", callback_data="back"))
        response = requests.get(f"{FASTAPI_URL}/chs", params={"chat_id": str(call.from_user.id)})
        if response.text[1] == "[":
            cur_list = read_list(response.text)
            set1 = set(cur_list)
            set2 = set(selected_products)
            selected_products = list(set1.symmetric_difference(set2))
        try:
            response = requests.post(f"{FASTAPI_URL}/chs",
                                     json={'chat_id': str(call.from_user.id), "data": str(selected_products)})
        except:
            print("err")
        photo = open('chs.jpg', 'rb')
        media = types.InputMediaPhoto(photo, caption=f"Добавлено в черный список:\n" + "\n".join(selected_products))
        bot.edit_message_media(media=media, chat_id=call.message.chat.id, message_id=call.message.message_id,
                               reply_markup=markup)

    else:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Вернуться к редактированию меню", callback_data="next_-1"))
        photo = open('chs.jpg', 'rb')
        media = types.InputMediaPhoto(photo, caption="Черный список не обновлен.")
        bot.edit_message_media(media=media, chat_id=call.message.chat.id, message_id=call.message.message_id,
                               reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("product"))
def handle_product(call: CallbackQuery):
    global products
    product = call.data.split("_", 1)[1]

    update_status(product, call)
    buttons_per_page = min(max(5, (len(products[call.from_user.id]) + 2) // 3), 10)
    page = next((i for i, p in enumerate(products[call.from_user.id]) if product in p))
    if page is None:
        page = 0
    else:
        page = page // buttons_per_page
    print(page)
    markup = create_product_markup(page, products[call.from_user.id], call)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("sh_"))
def handle_sh_product(call: CallbackQuery):
    global products
    product_ind = int(call.data.split("_", 1)[1])
    product = products[call.from_user.id][product_ind]
    update_status(product, call)
    buttons_per_page = min(max(5, (len(products[call.from_user.id]) + 2) // 3), 8)
    page = product_ind // buttons_per_page
    markup = create_shopping_markup(page, products[call.from_user.id], call)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)


### Ilsiia

def get_user_data(message):
    chat_id = message.chat.id

    pref_request = requests.get(f"{FASTAPI_URL}/preferences", params={'chat_id': chat_id})
    pref_request.raise_for_status()
    # raise Exception([pref_request.content])
    user_preferences = json.loads(json.loads(pref_request.content))
    user_preferences['bad_products'] = ['Картошка']
    return user_preferences


def format_menu_day(menu, day_index):
    day_menu = menu[day_index]
    day_text = ""
    pictures = list()
    for i in range(0, 3):
        recipe = day_menu[i]
        if i == 0:
            day_text += f"🍳Завтрак:\n"
        elif i == 1:
            day_text += f"🍲Обед:\n"
        elif i == 2:
            day_text += f"🍝Ужин:\n"
        day_text += (
            f"  [{recipe['name']}]({recipe['link_to_recipe']})\n"
            f"  Время готовки: {recipe['time']} минут\n"
            f"  Калории: {round(float(recipe['calories']))}\n"
            f"  БЖУ: {round(float(recipe['pfc'][0]))}/{round(float(recipe['pfc'][1]))}/{round(float(recipe['pfc'][2]))}\n\n"
        )
        pictures.append(recipe['link_to_image'])
    return [day_text, pictures]


def format_shop_list(shopping_list):
    if isinstance(shopping_list, str):
        return shopping_list
    shopping_list_text = "Список покупок:\n"
    for product, quantity in shopping_list.items():
        shopping_list_text += f"◌ *{product}:*  {quantity}\n"
    return shopping_list_text


def create_navigation_buttons(current_day, mess_id):
    days = ['📝 Список покупок', '🥦 Понедельник', '🍎 Вторник', '🥕 Среда', '🥝 Четверг', '🥑 Пятница', '🍅 Суббота',
            '🍊 Воскресенье']
    markup = InlineKeyboardMarkup()

    if current_day == -1:
        next_day = InlineKeyboardButton(days[1], callback_data=f"next_{current_day}_{mess_id}")
        markup.add(next_day)
        blacklist = InlineKeyboardButton("❌ Добавить в черный список", callback_data=f"list_{current_day}")
        markup.add(blacklist)
    elif current_day == 6:
        prev_day = InlineKeyboardButton(days[current_day], callback_data=f"prev_{current_day}")
        markup.add(prev_day)
        change_breakfast = InlineKeyboardButton("🥞 Заменить завтрак",
                                                callback_data=f"change-breakfast_{current_day}")
        change_lunch = InlineKeyboardButton("🥘 Заменить обед", callback_data=f"change-lunch_{current_day}")
        change_dinner = InlineKeyboardButton("🥙 Заменить ужин", callback_data=f"change-dinner_{current_day}")
        change_day = InlineKeyboardButton("🍱 Заменить день", callback_data=f"change-day_{current_day}")

        markup.add(change_breakfast)
        markup.add(change_lunch)
        markup.add(change_dinner)
        markup.add(change_day)
    else:
        prev_day = InlineKeyboardButton(days[current_day], callback_data=f"prev_{current_day}")
        next_day = InlineKeyboardButton(days[current_day + 2], callback_data=f"next_{current_day}")
        markup.add(prev_day, next_day)
        change_breakfast = InlineKeyboardButton("🥞 Заменить завтрак",
                                                callback_data=f"change-breakfast_{current_day}")
        change_lunch = InlineKeyboardButton("🥘 Заменить обед", callback_data=f"change-lunch_{current_day}")
        change_dinner = InlineKeyboardButton("🥙 Заменить ужин", callback_data=f"change-dinner_{current_day}")
        change_day = InlineKeyboardButton("🍱 Заменить день", callback_data=f"change-day_{current_day}")

        markup.add(change_breakfast)
        markup.add(change_lunch)
        markup.add(change_dinner)
        markup.add(change_day)
    main_menu = InlineKeyboardButton("🏁 Главное меню", callback_data=f"main_menu_{current_day}")
    markup.add(main_menu)

    return markup


@bot.callback_query_handler(func=lambda call: call.data == "generate")
def get_menu(call: types.CallbackQuery):
    try:
        payload = get_user_data(call.message)
        response = requests.post(f"{FASTAPI_URL}/create", json=payload)
        response.raise_for_status()
        data = response.json()
        shopping_list = data['list_of_products']
        global products
        products[call.from_user.id] = [product for product, status in shopping_list.items()]
        current_day = -1  # if day is -1, then we show shopping list
        shopping_list_text = format_shop_list(shopping_list)
        menu = data['menu']

        chat_id = str(call.message.chat.id)
        mess_id = str(call.message.message_id)
        dt = {
            "menu": menu,
            "shopping_list": shopping_list_text
        }
        dt = json.dumps(dt)

        user_payload = {
            "chat_id": chat_id,
            "mess_id": mess_id,
            "data": dt
        }

        user_response = requests.post(f"{FASTAPI_URL}/user", json=user_payload)
        user_response.raise_for_status()

        markup = create_navigation_buttons(current_day, mess_id)
        photo = open('list.JPG', 'rb')
        media = types.InputMediaPhoto(photo, caption=shopping_list_text, parse_mode='Markdown')
        bot.edit_message_media(media=media, chat_id=call.message.chat.id, message_id=call.message.message_id,
                               reply_markup=markup)

    except requests.exceptions.RequestException as e:
        bot.reply_to(call.message, f"Failed to retrieve menu: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith(('prev_', 'next_', 'list_', 'main_menu', 'change-')))
def navigate_menu(call: types.CallbackQuery):
    payload = get_user_data(call.message)
    try:
        if 'main_menu' in call.data:
            choose_param(call.message, option=1)
            return

        chat_id = str(call.message.chat.id)
        mess_id = int(str(call.message.message_id))

        user_response = requests.get(f"{FASTAPI_URL}/user", params={"chat_id": chat_id, "mess_id": mess_id})
        user_response.raise_for_status()
        data = json.loads(json.loads(user_response.content))
        current_day = int(call.data.split('_')[1])
        menu = data['menu']
        shopping_list = data['shopping_list']
        if 'prev' in call.data and current_day > -1:
            current_day -= 1
        elif 'next' in call.data and current_day < len(menu) - 1:
            current_day += 1
        elif 'list' in call.data:
            add_shopping_list(call, call.message)
            return
        elif 'change-' in call.data:
            payload = get_user_data(call.message)
            if 'change-breakfast_' in call.data:
                payload["replace"] = [current_day * 3]
            elif 'change-lunch_' in call.data:
                payload["replace"] = [current_day * 3 + 1]
            elif 'change-dinner_' in call.data:
                payload["replace"] = [current_day * 3 + 2]
            elif 'change-day_' in call.data:
                payload["replace"] = [current_day * 3 + i for i in range(0, 3)]

            payload["menu"] = {"shopping_list": shopping_list, "menu": menu}
            recreated = requests.post(f"{FASTAPI_URL}/recreate", json=payload)
            recreated.raise_for_status()

            data = recreated.json()
            shopping_list = data['list_of_products']
            menu = data['menu']

            dt = {
                "menu": menu,
                "shopping_list": shopping_list
            }
            dt = json.dumps(dt)

            user_payload = {
                "chat_id": str(chat_id),
                "mess_id": str(mess_id),
                "data": dt
            }

            user_response = requests.post(f"{FASTAPI_URL}/user", json=user_payload)
            user_response.raise_for_status()

        pictures = None
        if current_day == -1:
            text = format_shop_list(shopping_list)
        else:
            response = format_menu_day(menu, current_day)
            text = response[0]
            pictures = response[1]

        markup = create_navigation_buttons(current_day, mess_id)

        if pictures:
            collage(pictures)

            photo = open('collage.jpg', 'rb')
            image = Image.open('collage.jpg')
            media = types.InputMediaPhoto(photo, caption=text, parse_mode='Markdown')

            bot.edit_message_media(media=media, chat_id=call.message.chat.id, message_id=call.message.message_id,
                                   reply_markup=markup)
        else:
            photo = open('list.JPG', 'rb')
            media = types.InputMediaPhoto(photo, caption=text, parse_mode='Markdown')
            bot.edit_message_media(media=media, chat_id=call.message.chat.id, message_id=call.message.message_id,
                                   reply_markup=markup)

    except requests.exceptions.RequestException as e:
        bot.reply_to(call.message, f"Failed to retrieve menu: {e}.")


def download_image(url, save_as):
    try:
        file_path = save_as
        urllib.request.urlretrieve(url, file_path)
        print(f"Image successfully downloaded and saved to {file_path}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download image: {e}")


def resize_to_height(image, new_height):
    width, height = image.size
    new_width = new_height * width / height
    img = image.resize((int(new_width), new_height), Image.LANCZOS)
    return img


def resize_to_width(image, new_width):
    width, height = image.size
    new_height = new_width * height / width
    img = image.resize((new_width, int(new_height)), Image.LANCZOS)
    return img


def count(sizes, value):
    count = 0
    for i in range(0, 3):
        if sizes[i][0] == value:
            count += 1
    return count


def size_picture(width, height):
    if width > height:
        return 0
    elif height > width or height == width:
        return 1


def collage(pictures):
    download_image(pictures[0], 'image1.jpg')
    download_image(pictures[1], 'image2.jpg')
    download_image(pictures[2], 'image3.jpg')

    image1 = Image.open('image1.jpg')
    image2 = Image.open('image2.jpg')
    image3 = Image.open('image3.jpg')

    width1, height1 = image1.size
    width2, height2 = image2.size
    width3, height3 = image3.size

    sizes = [(size_picture(width1, height1), image1), (size_picture(width2, height2), image2),
             (size_picture(width3, height3), image3)]
    sizes.sort(key=lambda x: x[0])

    if count(sizes, 0) == 3:
        total_width = min(width1, width2, width3)
        if total_width < width1:
            image1 = resize_to_width(image1, total_width)
        if total_width < width2:
            image2 = resize_to_width(image2, total_width)
        if total_width < width3:
            image3 = resize_to_width(image3, total_width)

        height1 = image1.size[1]
        height2 = image2.size[1]
        height3 = image3.size[1]

        total_height = height1 + height2 + height3

        collage = Image.new("RGB", (total_width, total_height), "white")

        collage.paste(image1, (0, 0))
        collage.paste(image2, (0, height1))
        collage.paste(image3, (0, height1 + height2))
        collage.save("collage.jpg")

    elif count(sizes, 1) == 3:
        total_height = min(height1, height2, height3)
        if height1 > total_height:
            image1 = resize_to_height(image1, total_height)
        if height2 > total_height:
            image2 = resize_to_height(image2, total_height)
        if height3 > total_height:
            image3 = resize_to_height(image3, total_height)

        width1 = image1.size[0]
        width2 = image2.size[0]
        width3 = image3.size[0]

        total_width = width1 + width2 + width3

        collage = Image.new("RGB", (total_width, total_height), "white")

        collage.paste(image1, (0, 0))
        collage.paste(image2, (width1, 0))
        collage.paste(image3, (width1 + width2, 0))
        collage.save("collage.jpg")

    elif count(sizes, 1) == 2:
        ver_height = min(sizes[1][1].size[1], sizes[2][1].size[1])
        if sizes[1][1].size[1] > ver_height:
            image1 = resize_to_height(sizes[1][1], ver_height)
        else:
            image1 = sizes[1][1]

        if sizes[2][1].size[1] > ver_height:
            image2 = resize_to_height(sizes[2][1], ver_height)
        else:
            image2 = sizes[2][1]

        total_width = (image1.size[0] + image2.size[0])

        if sizes[0][1].size[0] != total_width:
            image3 = resize_to_width(sizes[0][1], total_width)
        else:
            image3 = sizes[0][1]

        total_height = image1.size[1] + image3.size[1]

        collage = Image.new("RGB", (total_width, total_height), "white")

        collage.paste(image1, (0, 0))
        collage.paste(image2, (image1.size[0], 0))
        collage.paste(image3, (0, image1.size[1]))

        collage.save("collage.jpg")

    elif count(sizes, 0) == 2:
        ver_width = min(sizes[0][1].size[0], sizes[1][1].size[0])

        if sizes[0][1].size[0] > ver_width:
            image1 = resize_to_width(sizes[0][1], ver_width)
        else:
            image1 = sizes[0][1]
        if sizes[1][1].size[0] > ver_width:
            image2 = resize_to_width(sizes[1][1], ver_width)
        else:
            image2 = sizes[1][1]

        total_height = image1.size[1] + image2.size[1]

        if sizes[2][1].size[1] != total_height:
            image3 = resize_to_height(sizes[2][1], total_height)
        else:
            image3 = sizes[2][1]

        total_width = image1.size[0] + image3.size[0]

        collage = Image.new("RGB", (total_width, total_height), "white")

        collage.paste(image1, (0, 0))
        collage.paste(image2, (0, image1.size[1]))
        collage.paste(image3, (image1.size[0], 0))
        collage.save("collage.jpg")

    collage = Image.open("collage.jpg")

    if collage.size[0] > 1024:
        collage = resize_to_width(collage, 1024)
    if collage.size[1] > 1024:
        collage = resize_to_height(collage, 1024)

    collage.save("collage.jpg")

    return 0


bot.infinity_polling()
