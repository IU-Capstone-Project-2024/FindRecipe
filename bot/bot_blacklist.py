import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json


bot = telebot.TeleBot('6399232568:AAGD9zt2uvhb0HkTcrrYTPWRr9WkQreY2RY')

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

@bot.message_handler(commands=['blacklist'])
def send_product_list(message, page=0):
    markup = create_product_markup(page)
    bot.send_message(message.chat.id, "Выберите продукты, чтобы удалить из списка:", reply_markup=markup)


def create_product_markup(page):
    markup = InlineKeyboardMarkup()
    start = page * buttons_per_page
    end = start + buttons_per_page

    for product in products[start:end]:
        emoji = " ✅" if product_status[product] else " 🔴"
        markup.add(InlineKeyboardButton(product + emoji, callback_data=product))

    if len(products) > buttons_per_page:
        pagination_buttons = []
        if page > 0:
            pagination_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"page_{page - 1}"))
        if end < len(products):
            pagination_buttons.append(InlineKeyboardButton("➡️", callback_data=f"page_{page + 1}"))
        markup.add(*pagination_buttons)

    markup.add(InlineKeyboardButton("Удалить из списка", callback_data="confirm"))

    return markup


@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data.startswith("page_"):
        page = int(call.data.split("_")[1])
        markup = create_product_markup(page)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)
    elif call.data.startswith("confirm"):
        selected_products = [product for product, status in product_status.items() if not status]
        if selected_products:
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("Вернуться в меню", callback_data="return")]
            ])
            bot.edit_message_text(
                text=f"Текущий черный список:\n" + "\n".join(selected_products),
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=markup
            )


            add_blacklist(selected_products, "test.json")
        else:
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("Вернуться в меню", callback_data="return")]
            ])
            bot.edit_message_text(
                text=f"Черный список не обновлен:\n" + "\n".join(selected_products),
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=markup
            )
    else:
        product = call.data
        product_status[product] = not product_status[product]

        page = next((i for i, p in enumerate(products) if product in p)) // buttons_per_page
        markup = create_product_markup(page)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)


bot.polling()
