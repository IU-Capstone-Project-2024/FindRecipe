import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import json
from config import bot

# Replace 'YOUR_BOT_TOKEN' with your actual bot token obtained from BotFather
# bot = telebot.TeleBot('7482635787:AAHYpkSBBkca9_NdcxaSsyaBM9Op0Ht23XI')

blacklist = []

def read_products(filename):
    file = open(filename)
    data = json.load(file)
    products = [product[0] for product in data['list_of_products'].items()]
    return products
def add_blacklist(products, filename):
    file = open(filename)
    data = json.load(file)
    file.close()
    if 'blacklist' not in data:
        data['blacklist'] = {}
    for elem in products:
        data['blacklist'][elem] = None
    with open(filename, 'w') as file:
        json.dump(data, file)


products = read_products("test.json")
buttons_per_page = min(max(5, (len(products) + 2) // 3), 10)

product_status = {product: False for product in products}


def send_product_list(message, page=0):
    markup = create_product_markup(page)
    bot.send_message(message.chat.id, "Выберите продукты, чтобы добавить в черный список:", reply_markup=markup)


def create_product_markup(page):
    markup = InlineKeyboardMarkup()
    start = page * buttons_per_page
    end = start + buttons_per_page

    for product in products[start:end]:
        emoji = " 🔴" if product_status[product] else ""
        markup.add(InlineKeyboardButton(product + emoji, callback_data=f"product_{product}"))

    if len(products) > buttons_per_page:
        pagination_buttons = []
        if page > 0:
            pagination_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"page_{page - 1}"))
        if end < len(products):
            pagination_buttons.append(InlineKeyboardButton("➡️", callback_data=f"page_{page + 1}"))
        markup.add(*pagination_buttons)

    markup.add(InlineKeyboardButton("Добавить продукты в черный список", callback_data="confirm"))

    return markup

@bot.callback_query_handler(func=lambda call: call.data.startswith("page_"))
def page_handler(call: CallbackQuery):
    page = int(call.data.split("_")[1])
    markup = create_product_markup(page)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm"))
def confirm_handler(call: CallbackQuery):
    selected_products = [product for product, status in product_status.items() if status]
    if selected_products:
        bot.edit_message_text(
            f"Добавлены в черный список:\n" + "\n".join(selected_products),
            call.message.chat.id,
            call.message.message_id
        )
        add_blacklist(selected_products, "test.json")
    else:
        bot.edit_message_text(
            "Черный список не обновлен.",
            call.message.chat.id,
            call.message.message_id
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("product"))
def handle_product(call: CallbackQuery):
    product = call.data.split("_", 1)[1]
    product_status[product] = not product_status[product]

    page = next((i for i, p in enumerate(products) if product in p)) // buttons_per_page
    markup = create_product_markup(page)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)



