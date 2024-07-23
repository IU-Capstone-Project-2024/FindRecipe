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

ORDER = list(map(lambda x: x.strip(), open("order_of_products.txt").readlines()))


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


class ChatData(BaseModel):
    data: str
    chat_id: str


class MessData(BaseModel):
    mess_id: str
    data: str
    chat_id: str


class FilterCreateMenu(BaseModel):
    bad_products: List[str] = list()
    calories: float = 2000
    pfc: List[float] = list()
    time: int = 120
    diff: int = 5
    spicy: int = 2
    num_products: int = 15


class FilterRecreateMenu(BaseModel):
    menu: dict
    bad_products: List[str] = list()
    calories: float = 2000
    pfc: List[float] = list()
    time: int = 120
    diff: int = 5
    spicy: int = 2
    num_products: int = 15
    replace: List[int] = list()


def string_to_list_int(s):  # "[2 4   5 3434]" -> [2, 4, 5, 3434]
    return list(map(int, s[1:len(s) - 1].split()))


def string_to_list_float(s):
    return list(map(float, s[1:len(s) - 1].split(", ")))


def string_to_list_string(s):
    s = s.replace("\n", "")
    return s[2:len(s) - 2].split("', '")


@app.post("/create", response_model=Menu)
def get_menu(filters: FilterCreateMenu = FilterCreateMenu()):
    def get_list_of_products(recipes: list):
        list_of_products = {}
        for recipe in recipes:
            ings = find_names_of_products(string_to_list_int(recipe["Ingredients"]))
            weights = string_to_list_float(recipe["Weights"])
            for i in range(len(weights)):
                weights[i] /= recipe["Servings"]
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

    def get_list_by_keys(item, keys):
        a = []
        for key in keys:
            a.append(item[key])
        return a

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
        "Cooking time in minutes": {"$lte": filters.time},
        "Difficulty": {"$lte": filters.diff},
        "Spicy": {"$lte": filters.spicy}
    }
    recipes = list(db['recipes'].find(filter_for_query))
    if filters.bad_products:
        recipes = list(filter(
            lambda x: not any(
                [(i in filters.bad_products) for i in find_names_of_products(string_to_list_int(x["Ingredients"]))]),
            recipes))

    for recipe in recipes:
        recipe["recipeCalories"] = sum(string_to_list_float(recipe["Weights"])) / 100 * recipe["Calories"] / recipe[
            "Servings"]

    z = 0.25 * filters.calories
    o = 0.4 * filters.calories
    u = 0.35 * filters.calories

    breakfast = list(filter(lambda x: x["Breakfast"] == 1 and get_list_by_keys(x,
                                                                               ["Dessert", "Pastry", "Salad",
                                                                                "Snack"]).count(1) > 0, recipes))
    lunch = list(filter(lambda x: x["Breakfast"] == 0 and get_list_by_keys(x,
                                                                           ["Lunch", "Dinner", "Soup",
                                                                            "Second course"]).count(1) > 0, recipes))
    dinner = list(filter(lambda x: x["Breakfast"] == 0 and get_list_by_keys(x,
                                                                            ["Dessert", "Pastry", "Salad",
                                                                             "Snack"]).count(1) > 0, recipes))

    recipes_z = sorted(breakfast, key=lambda x: abs(z - x["recipeCalories"]))
    recipes_o = sorted(lunch, key=lambda x: abs(o - x["recipeCalories"]))

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
                "name": str(menu[ind][i]["Name"]),
                "link_to_recipe": menu[ind][i]["URL"],
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

    return recreate_and_get_menu(FilterRecreateMenu(
        menu=response, bad_products=filters.bad_products,
        calories=filters.calories, pfc=filters.pfc, time=filters.time,
        diff=filters.diff, num_products=filters.num_products
    ))


@app.post("/recreate", response_model=Menu)
def recreate_and_get_menu(filters: FilterRecreateMenu):
    menu = filters.menu["menu"]

    def get_list_by_keys(item, keys):
        a = []
        for key in keys:
            a.append(item[key])
        return a

    def get_list_of_products(recipes: list):
        list_of_products = {}
        for recipe in recipes:
            if recipe is not None:
                ings = find_names_of_products(string_to_list_int(recipe["Ingredients"]))
                weights = string_to_list_float(recipe["Weights"])
                for i in range(len(weights)):
                    weights[i] /= recipe["Servings"]
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
    for i in menu:
        for recipe in i:
            list_bad_recipes_id.append(recipe["id"])

    if filters.replace:
        for num in filters.replace:
            i, j = num // 3, num % 3
            menu[i][j] = None

    ids = []
    for i in menu:
        for recipe in i:
            if recipe:
                ids.append(recipe["id"])
    recipes = list(db['recipes'].find({"ID": {"$in": ids}}))

    for i in recipes:
        for j in menu:
            for k in range(len(j)):
                if j[k] and "id" in j[k] and j[k]["id"] == i["ID"]:
                    j[k] = i
                    break

    list_of_products = list(get_list_of_products(recipes).items())  # [("Name", [weight, count]), (...), (...)]

    list_of_products.sort(key=lambda x: x[1][1] * 100000 + x[1][0], reverse=True)
    if not filters.bad_products:
        filters.bad_products = []
    list_of_products = [i[0] for i in list_of_products[:filters.num_products]]
    for counter in range(5, -1, -1):
        for i in menu:
            for recipe in range(len(i)):
                cn = counter
                if i[recipe]:
                    for prod in find_names_of_products(string_to_list_int(i[recipe]["Ingredients"])):
                        if prod not in list_of_products:
                            cn -= 1
                if cn < 0:
                    i[recipe] = None
        tmp_array = []
        for i in menu:
            for recipe in i:
                tmp_array += [recipe]
        list_of_products = list(get_list_of_products(tmp_array).items())
        list_of_products.sort(key=lambda x: x[1][1] * 100000 + x[1][0], reverse=True)
        if len(list_of_products) <= filters.num_products:
            list_of_products = [i[0] for i in list_of_products[:filters.num_products]]
            break
        list_of_products = [i[0] for i in list_of_products[:filters.num_products]]
    cn = 0
    while len(list_of_products) < filters.num_products:
        if ORDER[cn] not in filters.bad_products + list_of_products:
            list_of_products += [ORDER[cn]]
        cn += 1

    response = {
        "list_of_products": None,
        "menu": None
    }

    filter_for_query = {
        "ID": {"$nin": list_bad_recipes_id},
        "Cooking time in minutes": {"$lte": filters.time},
        "Difficulty": {"$lte": filters.diff},
        "Spicy": {"$lte": filters.spicy}
    }
    recipes = list(db['recipes'].find(filter_for_query))

    for recipe in recipes:
        recipe["recipeCalories"] = sum(string_to_list_float(recipe["Weights"])) / 100 * recipe["Calories"] / recipe[
            "Servings"]
        cn = 0
        for prod in find_names_of_products(string_to_list_int(recipe["Ingredients"])):
            if prod in list_of_products:
                cn += 1
        recipe["pr_pop"] = cn / len(list_of_products)

    for recips in menu:
        for recipe in recips:
            if recipe:
                recipe["recipeCalories"] = sum(string_to_list_float(recipe["Weights"])) / 100 * recipe["Calories"] / recipe[
                    "Servings"]

    z = 0.25 * filters.calories
    o = 0.4 * filters.calories
    u = 0.35 * filters.calories

    breakfast_main = list(filter(lambda x: x["Breakfast"] == 1 and get_list_by_keys(x,
    ["Dessert", "Pastry", "Salad", "Snack"]).count(1) > 0, recipes))
    breakfast_main.sort(key=lambda x: (1 - x["pr_pop"]) * 1000000 + abs(z - x["recipeCalories"]))
    breakfast_main = breakfast_main[:1]
    lunch_main = list(filter(lambda x: x["Breakfast"] == 0 and get_list_by_keys(x,
    ["Lunch", "Dinner", "Soup", "Second course"]).count(1) > 0, recipes))
    lunch_main.sort(key=lambda x: (1 - x["pr_pop"]) * 1000000 + abs(o - x["recipeCalories"]))
    lunch_main = lunch_main[:1]
    dinner_main = list(filter(lambda x: x["Breakfast"] == 0 and get_list_by_keys(x,
    ["Dessert", "Pastry", "Salad", "Snack"]).count(1) > 0, recipes))
    dinner_main.sort(key=lambda x: (1 - x["pr_pop"]) * 1000000 + abs(u - x["recipeCalories"]))
    dinner_main = dinner_main[:1]

    recipes = list(filter(
        lambda x: all([(i in list_of_products) for i in find_names_of_products(string_to_list_int(x["Ingredients"]))]),
        recipes))

    breakfast = list(filter(lambda x: x["Breakfast"] == 1 and get_list_by_keys(x,
    ["Dessert", "Pastry", "Salad", "Snack"]).count(1) > 0, recipes))
    lunch = list(filter(lambda x: x["Breakfast"] == 0 and get_list_by_keys(x,
    ["Lunch", "Dinner", "Soup", "Second course"]).count(1) > 0, recipes))
    dinner = list(filter(lambda x: x["Breakfast"] == 0 and get_list_by_keys(x,
    ["Dessert", "Pastry", "Salad", "Snack"]).count(1) > 0, recipes))

    recipes_z = sorted(breakfast, key=lambda x: abs(z - x["recipeCalories"]))
    recipes_o = sorted(lunch, key=lambda x: abs(o - x["recipeCalories"]))

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

    recipes_delta50 = list(filter(lambda x: abs(z - x["recipeCalories"]) <= 50, recipes_z))
    pool = None
    if len(recipes_delta50) >= cn_z:
        pool = random.sample(recipes_delta50, cn_z)
    else:
        recipes_z += breakfast_main
        cn_z = min(cn_z, len(recipes_z))
        pool = random.sample(recipes_z[:cn_z], cn_z)
    for i in range(7):
        if not menu[i][0] and cn_z >= 1:
            menu[i][0] = pool[cn_z - 1]
            cn_z -= 1

    recipes_delta50 = list(filter(lambda x: abs(o - x["recipeCalories"]) <= 50, recipes_o))
    if len(recipes_delta50) >= cn_o:
        pool = random.sample(recipes_delta50, cn_o)
    else:
        recipes_o += lunch_main
        cn_o = min(cn_o, len(recipes_o))
        pool = random.sample(recipes_o[:cn_o], cn_o)
    for i in range(7):
        if not menu[i][1] and cn_o >= 1:
            menu[i][1] = pool[cn_o - 1]
            recipes_o.remove(pool[cn_o - 1])
            cn_o -= 1

    recipes_u = sorted(recipes_o + dinner, key=lambda x: abs(u - x["recipeCalories"]))

    recipes_delta50 = list(filter(lambda x: abs(u - x["recipeCalories"]) <= 50, recipes_u))
    if len(recipes_delta50) >= cn_u:
        pool = random.sample(recipes_delta50, cn_u)
    else:
        recipes_u += dinner_main
        cn_u = min(cn_u, len(recipes_u))
        pool = random.sample(recipes_u[:cn_u], cn_u)
    for i in range(7):
        if not menu[i][2] and cn_u >= 1:
            menu[i][2] = pool[cn_u - 1]
            cn_u -= 1

    a = [[0] * 3 for i in range(7)]
    for i in range(7):
        for j in range(3):
            if menu[i][j]:
                a[i][j] = 1

    a_start = a
    flag_bad_menu = False
    if not menu[0][0]:
        for i in range(6, 0, -1):
            if menu[i][0]:
                menu[0][0], menu[i][0] = menu[i][0], menu[0][0]
                break
        else:
            flag_bad_menu = True

    if not menu[0][1]:
        for i in range(6, 0, -1):
            if menu[i][1]:
                menu[0][1], menu[i][1] = menu[i][1], menu[0][1]
                break
        else:
            flag_bad_menu = True

    if not menu[0][2]:
        for i in range(6, 0, -1):
            if menu[i][2]:
                menu[0][2], menu[i][2] = menu[i][2], menu[0][2]
                break
        else:
            flag_bad_menu = True

    if flag_bad_menu:
        # break
        a = [[0] * 3 for i in range(7)]
        for i in range(7):
            for j in range(3):
                if menu[i][j]:
                    a[i][j] = 1
        raise Exception(a, a_start)

    for i in range(1, 7):
        for j in range(3):
            if not menu[i][j]:
                menu[i][j] = menu[i-1][j]

    for ind in range(7):
        for i in range(3):
            if len(menu[ind][i]) != 7:
                menu[ind][i] = {
                    "id": menu[ind][i]["ID"],
                    "name": str(menu[ind][i]["Name"]),
                    "link_to_recipe": menu[ind][i]["URL"],
                    "link_to_image": menu[ind][i]["Picture URL"],
                    "time": menu[ind][i]["Cooking time in minutes"],
                    "calories": menu[ind][i]["recipeCalories"],
                    "pfc": [menu[ind][i]["Protein"], menu[ind][i]["Fat"], menu[ind][i]["Carbs"]]
                }
    response["menu"] = menu

    ids = []
    for i in menu:
        for j in i:
            ids.append(j["id"])

    list_of_products = get_list_of_products(list(db['recipes'].find({"ID": {"$in": ids}})))

    for i in list_of_products:
        list_of_products[i] = str(int(list_of_products[i][0])) + " грамм"

    response["list_of_products"] = list_of_products
    return response


@app.get("/user", response_model=str)
def get_user(chat_id: str, mess_id: str):
    try:
        client = MongoClient(
            f'mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin')
        document = client['findrecipe']['user'].find_one({"chat_id": chat_id, "mess_id": mess_id})
        if document:
            return document['data']
        else:
            return "Chat ID not found"
    except Exception as e:
        raise "FAILED"


@app.post("/user", response_model=str)
def send_user(data: MessData):
    try:
        client = MongoClient(
            f'mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin')
        db = client['findrecipe']
        result = db['user'].update_one(
            {"chat_id": data.chat_id, "mess_id": data.mess_id},
            {"$set": {"data": data.data}},
            upsert=True
        )
        if result.matched_count > 0 or result.upserted_id is not None:
            return "OK"
        else:
            return "Update failed"
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
def send_chs(data: ChatData):
    try:
        client = MongoClient(
            f'mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin')
        db = client['findrecipe']
        result = db['chs'].update_one(
            {"chat_id": data.chat_id},
            {"$set": {"data": data.data}},
            upsert=True
        )
        if result.matched_count > 0 or result.upserted_id is not None:
            return "OK"
        else:
            return "Update failed"
    except Exception as e:
        raise "FAILED"


@app.get("/preferences", response_model=str)
def get_preferences(chat_id: str):
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
def send_preferences(data: ChatData):
    try:
        client = MongoClient(
            f'mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin')
        db = client['findrecipe']
        result = db['preferences'].update_one(
            {"chat_id": data.chat_id},
            {"$set": {"data": data.data}},
            upsert=True
        )
        if result.matched_count > 0 or result.upserted_id is not None:
            return "OK"
        else:
            return "Update failed"
    except Exception as e:
        raise "FAILED"
