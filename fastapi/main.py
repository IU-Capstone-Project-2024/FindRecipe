import fastapi
from pydantic import BaseModel
from typing import List, Dict

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
    return {
        "list_of_products": {
            "prod1": "100g",
            "prod2": "2 items"
        },
        "menu": [[
            {"name": "test_name1",
             "link_to_recipe": "link_recipe",
             "link_to_image": "link_image",
             "time": 30,
             "calories": 450.8,
             "pfc": [8.5, 6.7, 2.9]
             },
            {"name": "test_name2",
             "link_to_recipe": "link_recipe",
             "link_to_image": "link_image",
             "time": 23,
             "calories": 1200.8,
             "pfc": [4.5, 3.7, 2.9]
             },
            {"name": "test_name3",
             "link_to_recipe": "link_recipe",
             "link_to_image": "link_image",
             "time": 17,
             "calories": 200.3,
             "pfc": [4.5, 6.7, 1.9]
             }
        ] for _ in range(7)]}
