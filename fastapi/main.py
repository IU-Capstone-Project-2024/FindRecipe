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
    return list(map(float, s[1:len(s) - 1].split()))


def string_to_list_string(s):
    s = s.replace("\n", "")
    return s[2:len(s) - 2].split("' '")


@app.post("/create", response_model=Menu)
def get_recipe(bad_products: List[str] = None, calories: float = 2000,
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
        "Cooking time in minutes": {"$gte": time},
        "Difficulty": {"$lte": diff},
        "Spicy": {"$gte": spicy}
    }

    recipes = list(db['recipes'].find(filter_for_query))
    recipes = list(filter(
        lambda x: not any([(i in bad_products) for i in find_names_of_products(string_to_list_int(x["Ingredients"]))]),
        recipes))
    list_of_products = {}
    menu = list()
    for _ in range(7):
        menu.append(list())
        cn = 0
        for i in random.sample(recipes, 3):
            cn += 1
            recipe_for_bot = {
                # "name": str(find_names_of_products(string_to_list_int(i["Ingredients"]))) ,
                "name": str(i) + str(find_names_of_products(string_to_list_int(i["Ingredients"]))),
                # "name": i["Name"],
                "link_to_recipe": i["URL"],
                "link_to_image": i["Picture URL"],
                "time": i["Cooking time in minutes"],
                "calories": i["Calories"],
                "pfc": [i["Protein"], i["Fat"], i["Carbs"]]
            }
            menu[-1].append(recipe_for_bot)

            lp = find_names_of_products(string_to_list_int(i["Ingredients"]))
            for prod in range(len(lp)):
                list_of_products[lp[prod]] = list_of_products.get(lp[prod], list()) + [
                    string_to_list_float(i["Weights"])[prod]]
            if cn == 3:
                break
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
