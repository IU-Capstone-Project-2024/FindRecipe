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

# load_dotenv()
# TOKEN = os.getenv('TOKEN')
#
# bot = telebot.TeleBot(TOKEN, parse_mode=None)
# FASTAPI_URL = os.getenv('FASTAPI')
load_dotenv()
API_TOKEN = '6399232568:AAGD9zt2uvhb0HkTcrrYTPWRr9WkQreY2RY'
os.environ['TELEGRAM_API_TOKEN'] = API_TOKEN

bot = telebot.TeleBot(API_TOKEN, parse_mode=None)
FASTAPI_URL = "http://localhost:8000"
global product_status
global products
img = Image.new('RGB', (1, 1), color='white')
img.save('white_pixel.jpg')

#### Aliye

user_data = dict()


@bot.message_handler(commands=['start', 'help'])
def start(message):
    text_message = ('''Привет! Я помогу тебе составить рацион на неделю, исходя из твоих предпочтений.\nВот, что можно сделать:\n\
        - создать новое меню\n\
        - редактировать существующее меню\n\
        - посмотреть черный список\n\
        - редактировать черный список\n\
    Все эти функции доступны в виде кнопок''')

    main_page(message, text_message)


def main_page(message, text):
    markup = types.ReplyKeyboardMarkup()
    txt = 'Начать составление'
    itembtn_generate = types.KeyboardButton(txt)
    markup.row(itembtn_generate)
    photo = open('intro.jpeg', 'rb')
    bot.send_photo(chat_id=message.chat.id, photo=photo, caption=text, parse_mode='html', reply_markup=markup)
    # bot.send_message(message.chat.id, text, parse_mode='html', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in ['Начать составление'])
def start_generating(message):
    global user_data
    user_data = dict()
    choose_param(message)


def choose_param(message, option=None):
    txt = 'Выбери параметр, чтобы изменить его'
    markup = InlineKeyboardMarkup()
    calories = InlineKeyboardButton('калорийность', callback_data='calories')
    time = InlineKeyboardButton('время готовки', callback_data='time')
    products = InlineKeyboardButton('количество продуктов', callback_data='products')
    spicy = InlineKeyboardButton('острота', callback_data='spicy')
    complexity = InlineKeyboardButton('сложноть', callback_data='complexity')
    blacklist = InlineKeyboardButton('черный список', callback_data='blacklist')
    generate = InlineKeyboardButton('составить меню', callback_data='generate')
    markup.add(generate)
    markup.row(calories, time)
    markup.row(spicy, complexity)
    markup.add(products)

    markup.add(blacklist)
    photo = open('intro.jpeg', 'rb')
    if option:
        media = types.InputMediaPhoto(photo, caption=txt)
        bot.edit_message_media(media=media, chat_id=message.chat.id, message_id=message.message_id,
                              reply_markup=markup)
    else:
        bot.send_photo(message.chat.id, photo=photo, caption=txt, parse_mode='html', reply_markup=markup)


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
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                          text='Введи время готовки в минутах')
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

    send_product_list(call, call.message)

@bot.callback_query_handler(func=lambda call: call.data == "generate")
def generate(call: types.CallbackQuery):
    get_menu(call)
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
    return_edit(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "back")
def modify_time(call: types.CallbackQuery):
    return_edit(call.message)
def update_status(product):
    global product_status
    product_status[product] = not product_status[product]

def create_status(products):
    global product_status
    product_status = {product: False for product in products}


def send_product_list(call: CallbackQuery, message, page=0):
    global products
    try:
        # response = requests.post(f"{FASTAPI_URL}/chs", params=data)
        response = requests.get(f"{FASTAPI_URL}/chs", params={"chat_id": str(message.chat.id)})

        if response.text[1] != "[":
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("Назад", callback_data="chs_"))
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                  text='Черный список пуст', reply_markup=markup)
            return
        else:
            pr_l = response.text
            pattern = re.compile(r"[\w\s]+", re.U)
            pr_l = pattern.findall(pr_l)
            products = [word.strip() for word in pr_l if word.strip()]
            create_status(products)
            markup = create_product_markup(page, products)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                  text="Выберите продукты, чтобы удалить из списка:", reply_markup=markup)
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

def add_shopping_list(call: CallbackQuery, message, page=0):
    global products
    print(products)
    create_status(products)
    markup = create_shopping_markup(page, products)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                  text="Выберите продукты, чтобы добавить в чс:", reply_markup=markup)
def create_product_markup(page, products):
    buttons_per_page = min(max(5, (len(products) + 2) // 3), 10)
    markup = InlineKeyboardMarkup()
    start = page * buttons_per_page
    end = start + buttons_per_page
    for product in products[start:end]:
        emoji = " ✅" if product_status[product] else " 🔴"
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

def create_shopping_markup(page, products):
    buttons_per_page = min(max(5, (len(products) + 2) // 3), 8)
    markup = InlineKeyboardMarkup()
    start = page * buttons_per_page
    end = start + buttons_per_page
    counter = start
    for product in products[start:end]:

        emoji = " 🔴" if product_status[product] else ""
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
    page = int(call.data.split("_")[1])
    markup = create_product_markup(page, products)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("shpage_"))
def page_handler(call: CallbackQuery):
    page = int(call.data.split("_")[1])
    markup = create_shopping_markup(page, products)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm"))
def confirm_handler(call: CallbackQuery):
    selected_products = [product for product, status in product_status.items() if status]
    if selected_products:
        selected_products = [product for product, status in product_status.items() if not status]
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Вернуться к редактированию меню", callback_data="back"))
        data = {
            "chat_id": str(call.message.chat.id),
            "data": str(selected_products)
        }
        try:
            requests.post(f"{FASTAPI_URL}/chs", params=data)
        except:
            print("err")
        bot.edit_message_text(
            f"Текущий черный список:\n" + "\n".join(selected_products),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    else:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Вернуться к редактированию меню", callback_data="back"))
        bot.edit_message_text(
            "Черный список не обновлен.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("shconfirm"))
def shconfirm_handler(call: CallbackQuery):
    selected_products = [product for product, status in product_status.items() if status]
    if selected_products:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Вернуться к меню", callback_data="next_-1"))
        data = {
            "chat_id": str(call.message.chat.id),
            "data": str(selected_products)
        }
        try:
            requests.post(f"{FASTAPI_URL}/chs", params=data)
        except:
            print("err")
        bot.edit_message_text(
            f"Текущий черный список:\n" + "\n".join(selected_products),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    else:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Вернуться к редактированию меню", callback_data="next_-1"))
        bot.edit_message_text(
            "Черный список не обновлен.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
@bot.callback_query_handler(func=lambda call: call.data.startswith("product"))
def handle_product(call: CallbackQuery):
    product = call.data.split("_", 1)[1]

    update_status(product)
    buttons_per_page = min(max(5, (len(products) + 2) // 3), 10)
    page = next((i for i, p in enumerate(products) if product in p))
    if page is None:
        page = 0
    else:
        page = page // buttons_per_page
    print(page)
    markup = create_shopping_markup(page, products)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("sh_"))
def handle_sh_product(call: CallbackQuery):
    product_ind = int(call.data.split("_", 1)[1])
    product = products[product_ind]
    update_status(product)
    buttons_per_page = min(max(5, (len(products) + 2) // 3), 8)
    page = product_ind // buttons_per_page
    markup = create_shopping_markup(page, products)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)

### Ilsiia

def get_user_data(message):
    payload = {
        "bad_products": [
            "string"
        ],
        "calories": 1500,
        "pfc": [
            0
        ],
        "time": 120,
        "diff": 5,
        "spicy": 5,
        "num_products": 15
    }
    return payload


def format_menu_day(menu, day_index):
    day_menu = menu[day_index]
    day_text = f"День {day_index + 1}:\n"
    pictures = list()
    for recipe in day_menu:
        day_text += (
            f"- {recipe['name']}\n"
            f"  Время готовки: {recipe['time']} минут\n"
            f"  Калории: {recipe['calories']}\n"
            f"  Белки/Жиры/Углеводы: {recipe['pfc'][0]}/{recipe['pfc'][1]}/{recipe['pfc'][2]}\n"
            f"  Ссылка на рецепт: {recipe['link_to_recipe']}\n"
        )
        pictures.append(recipe['link_to_image'])
    return [day_text, pictures]


def format_shop_list(shopping_list):
    shopping_list_text = "Shopping List:\n"
    for product, quantity in shopping_list.items():
        shopping_list_text += f"- {product}: {quantity}\n"
    return shopping_list_text


def create_navigation_buttons(current_day, mess_id):
    days = ['Список покупок', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    markup = InlineKeyboardMarkup()

    if current_day == -1:
        next_day = InlineKeyboardButton(days[1], callback_data=f"next_{current_day}_{mess_id}")
        markup.add(next_day)
        blacklist = InlineKeyboardButton("Добавить в черный список", callback_data=f"list_{current_day}_{mess_id}")
        markup.add(blacklist)
    elif current_day == 6:
        prev_day = InlineKeyboardButton(days[current_day], callback_data=f"prev_{current_day}_{mess_id}")
        markup.add(prev_day)
        change_breakfast = InlineKeyboardButton("Заменить завтрак",
                                                callback_data=f"change_breakfast_{current_day}_{mess_id}")
        change_lunch = InlineKeyboardButton("Заменить обед", callback_data=f"change_lunch_{current_day}_{mess_id}")
        change_dinner = InlineKeyboardButton("Заменить ужин", callback_data=f"change_dinner_{current_day}_{mess_id}")
        change_day = InlineKeyboardButton("Заменить день", callback_data=f"change_day_{current_day}_{mess_id}")

        markup.add(change_breakfast)
        markup.add(change_lunch)
        markup.add(change_dinner)
        markup.add(change_day)
    else:
        prev_day = InlineKeyboardButton(days[current_day], callback_data=f"prev_{current_day}_{mess_id}")
        next_day = InlineKeyboardButton(days[current_day + 2], callback_data=f"next_{current_day}_{mess_id}")
        markup.add(prev_day, next_day)
        change_breakfast = InlineKeyboardButton("Заменить завтрак",
                                                callback_data=f"change_breakfast_{current_day}_{mess_id}")
        change_lunch = InlineKeyboardButton("Заменить обед", callback_data=f"change_lunch_{current_day}_{mess_id}")
        change_dinner = InlineKeyboardButton("Заменить ужин", callback_data=f"change_dinner_{current_day}_{mess_id}")
        change_day = InlineKeyboardButton("Заменить день", callback_data=f"change_day_{current_day}_{mess_id}")

        markup.add(change_breakfast)
        markup.add(change_lunch)
        markup.add(change_dinner)
        markup.add(change_day)
    main_menu = InlineKeyboardButton("Главное меню", callback_data=f"main_menu_{current_day}_{mess_id}")
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
        current_day = -1  # if day is -1, then we show shopping list
        shopping_list_text = format_shop_list(shopping_list)
        menu = data['menu']
        global products
        products = [product for product, status in shopping_list.items()]
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

        user_response = requests.post(f"{FASTAPI_URL}/user", params=user_payload)
        user_response.raise_for_status()

        markup = create_navigation_buttons(current_day, mess_id)
        photo = open('list.JPG', 'rb')
        media = types.InputMediaPhoto(photo, caption=shopping_list_text)
        bot.edit_message_media(media=media, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

    except requests.exceptions.RequestException as e:
        bot.reply_to(call.message, f"Failed to retrieve menu: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith(('prev_', 'next_', 'main_menu')))
def navigate_menu(call: types.CallbackQuery):
    payload = get_user_data(call.message)
    try:
        if 'main_menu' in call.data:
            choose_param(call.message, option=1)
            return

        chat_id = str(call.message.chat.id)
        mess_id = int(call.data.split('_')[2])

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

        if current_day == -1:
            text = format_shop_list(shopping_list)
        else:
            response = format_menu_day(menu, current_day)
            text = response[0]
            pictures = response[1]

        markup = create_navigation_buttons(current_day, mess_id)

        if pictures:
            download_image(pictures[0], 'image.jpg')
            download_image(pictures[1], 'image1.jpg')
            download_image(pictures[2], 'image2.jpg')

            image1 = Image.open('image.jpg')
            image2 = Image.open('image1.jpg')
            image3 = Image.open('image2.jpg')

            width1, height1 = image1.size
            width2, height2 = image2.size
            width3, height3 = image3.size


            total_width = width1 + width2 + width3
            total_height = max(height1, height2, height3)
            if height1 < total_height:
                image1 = resize_to_height(image1, total_height)
            if height2 < total_height:
                image2 = resize_to_height(image2, total_height)
            if height3 < total_height:
                image3 = resize_to_height(image3, total_height)

            collage = Image.new("RGB", (total_width, total_height), "white")

            collage.paste(image1, (0, 0))
            collage.paste(image2, (width1, 0))
            collage.paste(image3, (width1 + width2, 0))

            collage.save("collage.jpg")

            photo = open('collage.jpg', 'rb')
            media = types.InputMediaPhoto(photo, caption=text)
            bot.edit_message_media(media=media, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
        else:
            photo = open('list.JPG', 'rb')
            media = types.InputMediaPhoto(photo, caption=text)
            bot.edit_message_media(media=media, chat_id=call.message.chat.id, message_id=call.message.message_id, \
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

def resize_to_height(image, target_height):
    width, height = image.size
    new_width = int((target_height / height) * width)
    resized_image = image.resize((new_width, target_height), Image.Resampling.LANCZOS)
    return resized_image

@bot.callback_query_handler(func=lambda call: call.data.startswith('list_'))
def ch_list(call):
    add_shopping_list(call, call.message)
bot.infinity_polling()
