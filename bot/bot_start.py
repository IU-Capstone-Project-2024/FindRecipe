import telebot
from telebot import types
from config import bot
import bot_preferences

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
    main_page(message, text_message)


def main_page(message, text):
    markup = types.ReplyKeyboardMarkup()
    txt = 'Начать составление'
    itembtn_generate = types.KeyboardButton(txt)
    markup.row(itembtn_generate)

    bot.send_message(message.chat.id, text, parse_mode='html', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in ['Начать составление'])
def start_generating(message):
    global user_data
    user_data = dict()
    bot_preferences.choose_param(message)



if __name__ == '__main__':
    bot.infinity_polling()
