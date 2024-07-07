import fastapi
from pydantic import BaseModel
from typing import List, Dict
from pymongo import MongoClient
import time as ttt
import random

MONGO_HOST = 'mongo_db'
MONGO_PORT = 27017
MONGO_DB = "findrecipe"
MONGO_USER = "root"
MONGO_PASS = "password"

app = fastapi.FastAPI()


class Recipe(BaseModel):
    id: int
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
             pfc: List[float] = None, time: int = 120,
             diff: int = 5, spicy: int = 2, num_products: int = 15):
    def get_list_of_products(recipes: list):
        list_of_products = {}
        for recipe in recipes:
            ings = find_names_of_products(string_to_list_int(recipe["Ingredients"]))
            weights = string_to_list_float(recipe["Weights"])
            for id in range(len(ings)):
                if ings[id] in list_of_products:
                    list_of_products[ings[id]][0] += weights[id]
                    list_of_products[ings[id]][1] += 1
                else:
                    list_of_products[ings[id]] = [weights[id], 1]
        return list_of_products

    def find_names_of_products(products_ids: List[int]):
        nonlocal ingredients
        ans = [None] * len(products_ids)
        for i, id in enumerate(products_ids):
            ans[i] = ingredients[id]
        return ans

    def find_ids_of_products(products_names: List[str]):
        return list(i['ID'] for i in db['ingredients'].find({"Ingredients": {"$in": products_names}}))

    client = MongoClient(f'mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin')
    db = client['findrecipe']
    ingredients = {}
    for i in list(db['ingredients'].find()):
        ingredients[i["ID"]] = i["Ingredients"]

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
        recipe["recipeCalories"] = sum(string_to_list_float(recipe["Weights"])) / 100 * recipe["Calories"] / recipe[
            "Servings"]

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
                "id": menu[ind][i]["ID"],
                # "name": str(find_names_of_products(string_to_list_int(i["Ingredients"]))) ,
                "name": str(menu[ind][i]) + str(
                    find_names_of_products(string_to_list_int(menu[ind][i]["Ingredients"]))),
                # "name": menu[ind][i]["Name"] + "\n" + str(menu[ind][i]["recipeCalories"]),
                # "name": menu[ind][i]["Name"],
                "link_to_recipe": menu[ind][i]["URL"],
                # "link_to_recipe": menu[ind][i]["Picture URL"],
                "link_to_image": menu[ind][i]["Picture URL"],
                "time": menu[ind][i]["Cooking time in minutes"],
                "calories": menu[ind][i]["Calories"],
                "pfc": [menu[ind][i]["Protein"], menu[ind][i]["Fat"], menu[ind][i]["Carbs"]]
            }
            menu[ind][i] = recipe_for_bot
    response["menu"] = menu

    ids = []
    for i in menu:
        for j in i:
            ids.append(j["id"])
    recipes = list(db['recipes'].find({"ID": {"$in": ids}}))
    list_of_products = get_list_of_products(recipes)

    for i in list_of_products:
        list_of_products[i] = str(list_of_products[i])

    response["list_of_products"] = list_of_products

    return recreate_and_get_menu(response, bad_products, calories, pfc, time, diff, spicy, num_products)


@app.post("/recreate", response_model=Menu)
def recreate_and_get_menu(menu: dict, bad_products: List[str] = None, calories: float = 2000,
                          pfc: List[float] = None, time: int = 120,
                          diff: int = 5, spicy: int = 2, num_products: int = 15, replace: List[int] = None):
    def get_list_of_products(recipes: list):
        list_of_products = {}
        for recipe in recipes:
            ings = find_names_of_products(string_to_list_int(recipe["Ingredients"]))
            weights = string_to_list_float(recipe["Weights"])
            for id in range(len(ings)):
                if ings[id] in list_of_products:
                    list_of_products[ings[id]][0] += weights[id]
                    list_of_products[ings[id]][1] += 1
                else:
                    list_of_products[ings[id]] = [weights[id], 1]
        return list_of_products

    def find_names_of_products(products_ids: List[int]):
        nonlocal ingredients
        ans = [None] * len(products_ids)
        for i, id in enumerate(products_ids):
            ans[i] = ingredients[id]
        return ans

    client = MongoClient(f'mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin')
    db = client['findrecipe']
    ingredients = {}
    for i in list(db['ingredients'].find()):
        ingredients[i["ID"]] = i["Ingredients"]

    list_bad_recipes_id = []
    for i in menu["menu"]:
        for recipe in i:
            list_bad_recipes_id.append(recipe["id"])

    if replace:
        for num in replace:
            i, j = num // 3, num % 3
            menu["menu"][i][j] = None

    ids = []
    for i in menu["menu"]:
        for recipe in i:
            if recipe:
                ids.append(recipe["id"])
    recipes = list(db['recipes'].find({"ID": {"$in": ids}}))
    list_of_products = list(get_list_of_products(recipes).items())  # [("Name", [weight, count]), (...), (...)]

    list_of_products.sort(key=lambda x: x[1][1] * 100000 + x[1][0], reverse=True)

    bad_products += [i[0] for i in list_of_products[num_products:]]
    list_of_products = [i[0] for i in list_of_products[:num_products]]

    for i in menu["menu"]:
        for recipe in range(len(i)):
            for prod in i[recipe]:
                if prod not in list_of_products:
                    i[recipe] = None
                    break

    response = {
        "list_of_products": None,
        "menu": None
    }

    filter_for_query = {
        "ID": {"$nin": list_bad_recipes_id},
        "Cooking time in minutes": {"$lte": time},
        "Difficulty": {"$lte": diff},
        "Spicy": {"$lte": spicy}
    }
    recipes = list(db['recipes'].find(filter_for_query))

    recipes = list(filter(
        lambda x: all([(i in list_of_products) for i, j in
                       zip(find_names_of_products(string_to_list_int(x["Ingredients"])),
                           string_to_list_float(x["Weights"]))]),
        recipes))

    for recipe in recipes:
        recipe["recipeCalories"] = sum(string_to_list_float(recipe["Weights"])) / 100 * recipe["Calories"] / recipe[
            "Servings"]

    z = 0.25 * calories
    o = 0.4 * calories
    u = 0.35 * calories

    recipes_z = sorted(list(filter(lambda x: x["Breakfast"] == 1, recipes)), key=lambda x: abs(z - x["recipeCalories"]))
    recipes_o = sorted(list(filter(lambda x: x["Breakfast"] == 0, recipes)), key=lambda x: abs(o - x["recipeCalories"]))
    # raise Exception(len(list_of_products), len(recipes),  len(recipes_o), len(recipes_z))

    menu = menu["menu"]
    cn_z = 0
    cn_o = 0
    cn_u = 0
    for i in range(7):
        if not menu[i][0]:
            cn_z += 1
        if not menu[i][1]:
            cn_o += 1
        if not menu[i][2]:
            cn_u += 1
    if len(recipes_z) < cn_z:
        recipes_z += recipes_o
    if len(recipes_o) < cn_o + cn_u:
        recipes_o += recipes_z

    recipes_delta50 = list(filter(lambda x: abs(z - x["recipeCalories"]) <= 50, recipes_z))
    pool = None
    if len(recipes_delta50) >= cn_z:
        pool = random.sample(recipes_delta50, cn_z)
    else:
        pool = random.sample(recipes_z[:cn_z], cn_z)
    for i in range(7):
        if not menu[i][0]:
            menu[i][0] = pool[cn_z - 1]
            cn_z -= 1

    recipes_delta50 = list(filter(lambda x: abs(o - x["recipeCalories"]) <= 50, recipes_o))
    if len(recipes_delta50) >= cn_o:
        pool = random.sample(recipes_delta50, cn_o)
    else:
        pool = random.sample(recipes_o[:cn_o], cn_o)
    for i in range(7):
        if not menu[i][1]:
            menu[i][1] = pool[cn_o - 1]
            recipes_o.remove(pool[cn_o - 1])
            cn_o -= 1

    recipes_u = sorted(recipes_o, key=lambda x: abs(u - x["recipeCalories"]))

    recipes_delta50 = list(filter(lambda x: abs(u - x["recipeCalories"]) <= 50, recipes_u))
    if len(recipes_delta50) >= cn_u:
        pool = random.sample(recipes_delta50, cn_u)
    else:
        pool = random.sample(recipes_u[:cn_u], cn_u)
    for i in range(7):
        if not menu[i][2]:
            menu[i][2] = pool[cn_u - 1]
            cn_u -= 1

    for ind in range(7):
        for i in range(3):
            if len(menu[ind][i]) != 7:
                recipe_for_bot = {
                    "id": menu[ind][i]["ID"],
                    # "name": menu[ind][i]["Name"] + '\n' + str(find_names_of_products(string_to_list_int(i["Ingredients"]))) ,
                    "name": str(menu[ind][i]["Name"]) + "\n" + str(
                        find_names_of_products(string_to_list_int(menu[ind][i]["Ingredients"]))),
                    # "name": menu[ind][i]["Name"] + "\n" + str(menu[ind][i]["recipeCalories"]),
                    # "name": menu[ind][i]["Name"],
                    "link_to_recipe": menu[ind][i]["URL"],
                    # "link_to_recipe": menu[ind][i]["Picture URL"],
                    "link_to_image": menu[ind][i]["Picture URL"],
                    "time": menu[ind][i]["Cooking time in minutes"],
                    "calories": menu[ind][i]["Calories"],
                    "pfc": [menu[ind][i]["Protein"], menu[ind][i]["Fat"], menu[ind][i]["Carbs"]]
                }
                menu[ind][i] = recipe_for_bot
    response["menu"] = menu

    ids = []
    for i in menu:
        for j in i:
            ids.append(j["id"])
    recipes = list(db['recipes'].find({"ID": {"$in": ids}}))
    list_of_products = get_list_of_products(recipes)

    for i in list_of_products:
        list_of_products[i] = str((list_of_products[i][0], list_of_products[i][1]))

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
    try:
        client = MongoClient(
            f'mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin')
        db = client['findrecipe']
        document = db['chs'].find_one({"chat_id": chat_id})
        if document:
            return document['data']
        else:
            return "Chat ID not found"
    except Exception as e:
        raise "FAILED"


@app.post("/chs", response_model=str)
def send_chs(chat_id: str, data: str):
    try:
        client = MongoClient(
            f'mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin')
        db = client['findrecipe']
        result = db['chs'].update_one(
            {"chat_id": chat_id},
            {"$set": {"data": data}},
            upsert=True
        )
        if result.matched_count > 0 or result.upserted_id is not None:
            return "OK"
        else:
            return "Update failed"
    except Exception as e:
        raise "FAILED"


@app.get("/preferences", response_model=str)
def get_chs(chat_id: str):
    try:
        client = MongoClient(
            f'mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin')
        db = client['findrecipe']
        document = db['preferences'].find_one({"chat_id": chat_id})
        if document:
            return document['data']
        else:
            return "Chat ID not found"
    except Exception as e:
        raise "FAILED"


@app.post("/preferences", response_model=str)
def send_chs(chat_id: str, data: str):
    try:
        client = MongoClient(
            f'mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin')
        db = client['findrecipe']
        result = db['preferences'].update_one(
            {"chat_id": chat_id},
            {"$set": {"data": data}},
            upsert=True
        )
        if result.matched_count > 0 or result.upserted_id is not None:
            return "OK"
        else:
            return "Update failed"
    except Exception as e:
        raise "FAILED"

# {'_id': ObjectId('66852e3e82d561d774654c7d'), 'ID': 191, 'Name':
# 'Быстрые маринованные вешенки', 'Breakfast': 0, 'Cooking time in minutes': 160,
# 'Cooking time': '2 часа 40 минут', 'Serving type': 'Порции', 'Servings': 3,
# 'Calories': 37.62, 'Protein': 0.66, 'Fat': 2.38, 'Carbs': 3.59, 'Difficulty': 2,
# 'Spicy': 2, 'Ingredients': '[ 62  54 408 390 337 314 488 205 485 180]',
# 'Types': "['г', 'г', 'г', 'г', 'г', 'г', 'г', 'г', 'г', 'по желанию']",
# 'Weights': '[1000.0, 350.0, 30.0, 30.0, 25.0, 34.0, 10.0, 1.0, 3.0, 0]',
# 'URL': 'https://food.ru/recipes/190204'
