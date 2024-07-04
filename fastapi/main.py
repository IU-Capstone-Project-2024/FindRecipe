import fastapi
from pydantic import BaseModel
from typing import List, Dict
from pymongo import MongoClient
import random

MONGO_HOST = 'mongo_db'
MONGO_PORT = 27017
MONGO_DB = "findrecipe"
MONGO_USER = "root"
MONGO_PASS = "password"

app = fastapi.FastAPI()


class Recipe(BaseModel):
    name: str
    link_to_recipe: str
    link_to_image: str
    time: int
    calories: float
    pfc: List[float]


class Menu(BaseModel):
    list_of_products: Dict[str, str]
    menu: List[List[Recipe]]


def string_to_list_int(s):  # "[2 4   5 3434]" -> [2, 4, 5, 3434]
    return list(map(int, s[1:len(s) - 1].split()))


def string_to_list_float(s):
    return list(map(float, s[1:len(s) - 1].split(", ")))


def string_to_list_string(s):
    s = s.replace("\n", "")
    return s[2:len(s) - 2].split("', '")


@app.post("/create", response_model=Menu)
def get_menu(bad_products: List[str] = None, calories: float = 2000,
             pfc: List[float] = None, time: int = 120, replace: List[List[bool]] = None,
             diff: int = 5, spicy: int = 2, num_products: int = 25):
    def find_names_of_products(products_ids: List[int]):
        return list(i['Ingredients'] for i in db['ingredients'].find({"ID": {"$in": products_ids}}))

    def find_ids_of_products(products_names: List[str]):
        return list(i['ID'] for i in db['ingredients'].find({"Ingredients": {"$in": products_names}}))

    client = MongoClient(f'mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin')
    db = client['findrecipe']

    response = {
        "list_of_products": None,
        "menu": None
    }

    filter_for_query = {
        "Cooking time in minutes": {"$lte": time},
        "Difficulty": {"$lte": diff},
        "Spicy": {"$lte": spicy}
    }

    recipes = list(db['recipes'].find(filter_for_query))
    recipes = list(filter(
        lambda x: not any([(i in bad_products) for i in find_names_of_products(string_to_list_int(x["Ingredients"]))]),
        recipes))

    for recipe in recipes:
        recipe["recipeCalories"] = sum(string_to_list_float(recipe["Weights"])) / 100 * recipe["Calories"] / recipe["Servings"]

    z = 0.25 * calories
    o = 0.4 * calories
    u = 0.35 * calories

    recipes_z = sorted(list(filter(lambda x: x["Breakfast"] == 1, recipes)), key=lambda x: abs(z - x["recipeCalories"]))
    recipes_o = sorted(list(filter(lambda x: x["Breakfast"] == 0, recipes)), key=lambda x: abs(o - x["recipeCalories"]))

    menu = [[None, None, None] for _ in range(7)]

    recipes_delta50 = list(filter(lambda x: abs(z - x["recipeCalories"]) <= 50, recipes_z))
    if len(recipes_delta50) >= 7:
        pool = random.sample(recipes_delta50, 7)
        for recipe in range(len(pool)):
            menu[recipe][0] = pool[recipe]
    else:
        pool = random.sample(recipes_z[:7], 7)
        for recipe in range(len(pool)):
            menu[recipe][0] = pool[recipe]

    recipes_delta50 = list(filter(lambda x: abs(o - x["recipeCalories"]) <= 50, recipes_o))
    if len(recipes_delta50) >= 7:
        pool = random.sample(recipes_delta50, 7)
        for recipe in range(len(pool)):
            menu[recipe][1] = pool[recipe]
            recipes_o.remove(pool[recipe])
    else:
        pool = random.sample(recipes_o[:7], 7)
        for recipe in range(len(pool)):
            menu[recipe][1] = pool[recipe]
            recipes_o.remove(pool[recipe])

    recipes_u = sorted(recipes_o, key=lambda x: abs(u - x["recipeCalories"]))

    recipes_delta50 = list(filter(lambda x: abs(u - x["recipeCalories"]) <= 50, recipes_u))
    if len(recipes_delta50) >= 7:
        pool = random.sample(recipes_delta50, 7)
        for recipe in range(len(pool)):
            menu[recipe][2] = pool[recipe]
    else:
        pool = random.sample(recipes_u[:7], 7)
        for recipe in range(len(pool)):
            menu[recipe][2] = pool[recipe]

    list_of_products = {}
    for ind in range(7):
        for i in range(3):
            recipe_for_bot = {
                # "name": str(find_names_of_products(string_to_list_int(i["Ingredients"]))) ,
                # "name": str(menu[ind][i]) + "\n\n" + str(find_names_of_products(string_to_list_int(menu[ind][i]["Ingredients"]))),
                "name": menu[ind][i]["Name"] + "\n" + str(menu[ind][i]["recipeCalories"]),
                # "name": menu[ind][i]["Name"],
                "link_to_recipe": menu[ind][i]["URL"],
                "link_to_image": menu[ind][i]["Picture URL"],
                "time": menu[ind][i]["Cooking time in minutes"],
                "calories": menu[ind][i]["Calories"],
                "pfc": [menu[ind][i]["Protein"], menu[ind][i]["Fat"], menu[ind][i]["Carbs"]]
            }
            recipe = menu[ind][i]
            menu[ind][i] = recipe_for_bot

            lp = find_names_of_products(string_to_list_int(recipe["Ingredients"]))
            for prod in range(len(lp)):
                list_of_products[lp[prod]] = list_of_products.get(lp[prod], list()) + [
                    string_to_list_float(recipe["Weights"])[prod]]
    response["menu"] = menu
    for i in list_of_products:
        list_of_products[i] = str((sum(list_of_products[i]), len(list_of_products[i])))
    response["list_of_products"] = list_of_products

    return response


@app.get("/user", response_model=str)
def get_user(chat_id: str, mess_id: str):
    client = MongoClient(f'mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin')
    return client['findrecipe']["users"].find_one({"chat_id": chat_id, "mess_id": mess_id})["data"]


@app.post("/user", response_model=str)
def send_user(chat_id: str, mess_id: str, data: str):
    try:
        client = MongoClient(
            f'mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin')
        db = client['findrecipe']
        db['users'].insert_one({"chat_id": chat_id, "mess_id": mess_id, "data": data})
        return "OK"
    except Exception:
        return "FAILED"


@app.get("/chs", response_model=str)
def get_chs(chat_id: str):
    client = MongoClient(f'mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin')
    return client['findrecipe']["chs"].find_one({"chat_id": chat_id})["data"]


@app.post("/chs", response_model=str)
def send_chs(chat_id: str, data: str):
    try:
        client = MongoClient(
            f'mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin')
        db = client['findrecipe']
        db['chs'].insert_one({"chat_id": chat_id, "data": data})
        return "OK"
    except Exception:
        return "FAILED"

# {'_id': ObjectId('66852e3e82d561d774654c7d'), 'ID': 191, 'Name':
# 'Быстрые маринованные вешенки', 'Breakfast': 0, 'Cooking time in minutes': 160,
# 'Cooking time': '2 часа 40 минут', 'Serving type': 'Порции', 'Servings': 3,
# 'Calories': 37.62, 'Protein': 0.66, 'Fat': 2.38, 'Carbs': 3.59, 'Difficulty': 2,
# 'Spicy': 2, 'Ingredients': '[ 62  54 408 390 337 314 488 205 485 180]',
# 'Types': "['г', 'г', 'г', 'г', 'г', 'г', 'г', 'г', 'г', 'по желанию']",
# 'Weights': '[1000.0, 350.0, 30.0, 30.0, 25.0, 34.0, 10.0, 1.0, 3.0, 0]',
# 'URL': 'https://food.ru/recipes/190204'