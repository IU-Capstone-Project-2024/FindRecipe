import telebot
from telebot import types
# import generate_menu
import sonyas

bot = telebot.TeleBot('7482635787:AAHYpkSBBkca9_NdcxaSsyaBM9Op0Ht23XI')

user_data = dict()

@bot.message_handler(commands=['start', 'help'])
def start(message):
    text_message = ('''Привет! Я помогу тебе составить рацион на неделю, исходя из твоих предпочтений.\nВот, что можно сделать:\n\
        - создать новое меню\n\
        - редактировать существующее меню\n\
        - посмотреть черный список\n\
        - редактировать черный список\n\
    Все эти функции доступны в виде кнопок''')

    # bot.send_message(message.chat.id, text_message)
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

#
# @bot.callback_query_handler(func=lambda call: True)
# def callback_handler(callback):
#
#     match  callback.data:
#         case 'products':
#             modify_products(callback.message)
#
#         case 'calories':
#             modify_calories(callback.message)
#
#         case 'time':
#             modify_time(callback.message)
#
#         case 'spicy':
#             modify_spicy(callback.message)
#
#         case 'complexity':
#             modify_complexity(callback.message)
#
#         case 'blacklist':
#             modify_blacklist(callback.message)
#
#         case 'generate':
#             generate(callback.message)
#



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
    sonyas.send_product_list(call.message)

def generate(message):
    pass
# @bot.message_handler(func=lambda message: message.text == ['Начать составление'])
# def start_generating(message):
#     generate(bot, message)





if __name__ == '__main__':
    bot.infinity_polling()
