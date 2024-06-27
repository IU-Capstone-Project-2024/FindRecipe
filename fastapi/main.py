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


@app.post("/create", response_model=Menu)
def get_recipe(bad_products: List[str] = None, calories: float = 2000,
               pfc: List[float] = None, time: int = 120, replace: List[List[bool]] = None,
               diff: int = 5, spicy: int = 0, num_products: int = 25):
    client = MongoClient(f'mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin')
    db = client['findrecipe']

    response = {
        "list_of_products": None,
        "menu": None
    }

    menu = list()
    for _ in range(7):
        menu.append(list())
        cn = 0
        for i in random.choices(list(db['recipes'].find()), k=3):
            cn += 1
            recipe_for_bot = {
                "name": i["Name"],
                "link_to_recipe": i["URL"],
                "link_to_image": i["Picture URL"],
                "time": int(i["Cooking time"].split()[0]),
                "calories": i["Calories"],
                "pfc": [i["Protein"], i["Fat"], i["Carbs"]]
            }
            menu[-1].append(recipe_for_bot)
            if cn == 3:
                break
    response["menu"] = menu
    response["list_of_products"] = {
        "prod1": "100g",
        "prod2": "2 items"
    }

    return response
