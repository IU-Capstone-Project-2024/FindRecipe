import telebot
import os
from dotenv import load_dotenv
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()
TOKEN = os.getenv('TOKEN')

bot = telebot.TeleBot(TOKEN, parse_mode=None)
FASTAPI_URL = os.getenv('FASTAPI')


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hello, how are you doing?")


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


@bot.message_handler(commands=['menu'])
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
