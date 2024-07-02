import requests
from bs4 import BeautifulSoup
import time
import polars as pl

headers = {
    'User-Agent': 'My User Agent 1.0',
    'From': 'alexshulmin@gmail.com'
}


def log_info(into_str):
    with open("log.txt", 'a', encoding="utf-8") as file:
        file.write(into_str + "\n")


def to_float(s):
    return float(s.replace(',', '.'))


def collect_spicy(contents):
    spice = 0
    for svg in contents:
        if len(svg.contents) != 1:
            spice += 1
    return spice


def collect_difficulty(contents):
    diff = 0
    for svg in contents:
        if svg.get('class')[0] == "properties_iconActive__yDry0":
            diff += 1
    return diff


def is_breakfast(contents):
    for content in contents:
        if content['href'] == "/tags/zavtrak":
            return 1
    return 0


def parse_recipe(rec_id):
    global curr_id, dead
    source = f"https://food.ru/recipes/{rec_id}"
    try:
        response = requests.get(source, headers=headers, timeout=10)
    except Exception:
        dead = True
        return
    if response.status_code != 200:
        log_info(f"There is no recipe {rec_id}, skipping...")
        return
    curr_id += 1
    ids.append(curr_id)
    urls.append(source)
    soup = BeautifulSoup(response.content, "html.parser")

    name.append(soup.find('h1', class_='title_main__ok7t1').contents[0])
    cooking_time.append(
        soup.find('div', class_='properties_value__kAeD9 properties_valueWithIcon__WDXDm duration').contents[-1])

    serving_type.append(soup.find('h3', class_='ingredientsCalculator_subTitle__Pg0B_').contents[0])
    servings.append(soup.find('input', class_='input yield default yield')['value'])
    calories.append(to_float(soup.find('abbr', class_='calories').get('title').split()[0]))
    protein.append(to_float(soup.find('abbr', class_='protein').get('title').split()[0]))
    fat.append(to_float(soup.find('abbr', class_='fat').get('title').split()[0]))
    carbs.append(to_float(soup.find('abbr', class_='carbohydrates').get('title').split()[0]))
    diff_contents, spicy_contents = soup.find_all('div', class_='properties_level___bLQQ')
    difficulty.append(collect_difficulty(diff_contents))
    spicy.append(collect_spicy(spicy_contents))
    ingredients = soup.find_all('span', class_='name')
    ingredients_lists.append([str(ingredient.contents[0]) for ingredient in ingredients])
    [all_ingredients.append(str(ingredient.contents[0])) for ingredient in ingredients]
    curr_types = soup.find_all('span', class_='type')
    curr_types = [span.contents[0] for span in curr_types]
    types.append(curr_types)
    raw_weights = soup.find_all('span', class_='value')
    curr_weights = []
    raw_iter = 0
    for it in range(len(curr_types)):
        if curr_types[it] != 'г':
            curr_weights.append(0)
        else:
            curr_weights.append(float(raw_weights[raw_iter].contents[0]))
            raw_iter += 1
    weights.append(curr_weights)
    pic_urls.append(soup.find('div', class_='image_outer__M09PO image_widescreen__I7uNl').
                    contents[1].get('href').replace("640", "2544").replace("480", "1908"))
    breakfast_contents = soup.find_all('a', class_='tag_tag__2fJAC')
    breakfast.append(is_breakfast(breakfast_contents))


all_ingredients = []
ids = []
urls = []
name = []
cooking_time = []
serving_type = []
servings = []
calories = []
protein = []
fat = []
carbs = []
difficulty = []
spicy = []
ingredients_lists = []
weights = []
types = []
pic_urls = []
breakfast = []
curr_id = 0
dead = False
recipe_id = 189999
while recipe_id < 220000:
    recipe_id += 1
    if dead:
        recipe_id -= 1
        print("Going to sleep...")
        dead = False
        sleep_time = 10
        for i in range(sleep_time, sleep_time * 11, sleep_time):
            time.sleep(sleep_time)
            print(f"{i} seconds passed...")
        print(f"Waking up... Work again! Current recipe: {recipe_id}")
    try:
        parse_recipe(recipe_id)
    except Exception as e:
        log_info(f"Skipping recipe {recipe_id} due to error: {e}")
        continue

all_ingredients = sorted(set(all_ingredients))
ingredients_ids = [i + 1 for i in range(len(all_ingredients))]
pl.DataFrame(
    {"ID": ids, "Name": name, "Breakfast": breakfast, "Cooking time": cooking_time, "Serving type": serving_type,
     "Servings": servings, "Calories": calories, "Protein": protein, "Fat": fat, "Carbs": carbs,
     "Difficulty": difficulty, "Spicy": spicy, "Ingredients": ingredients_lists, "Weights": weights,
     "Types": types, "URL": urls, "Picture URL": pic_urls}, strict=False).to_pandas().to_csv('recipes.csv', index=False)
pl.DataFrame({"ID": ingredients_ids, "Ingredients": list(all_ingredients)},
             strict=False).to_pandas().to_csv('ingredients.csv', index=False)

all_ingredients = pl.read_csv("ingredients.csv").get_column("Ingredients").to_list()
recipe_ingredients = pl.read_csv("recipes.csv").get_column("Ingredients").to_list()
recipe_ingredients = [ingr.replace('[', '').replace(']', '').replace('\n', '').split("' ") for ingr in
                      recipe_ingredients]
recipe_ingredients = [[ingr.replace("'", '') for ingr in ingrs] for ingrs in recipe_ingredients]
recipe_ingredients = [[all_ingredients.index(ingr) + 1 for ingr in ingrs] for ingrs in recipe_ingredients]
all_weights = pl.read_csv("recipes.csv").get_column("Weights").to_list()
all_weights = [weight.replace('[', '').replace(']', '').split() for weight in all_weights]
all_weights = [[float(weight) for weight in weights] for weights in all_weights]
ids = []
recipe_ids = []
ingredient_ids = []
weights = []
curr_id = 1
for recipe_id in range(len(recipe_ingredients)):
    for ingr_id in range(len(recipe_ingredients[recipe_id])):
        ids.append(curr_id)
        curr_id += 1
        recipe_ids.append(recipe_id + 1)
        ingredient_ids.append(recipe_ingredients[recipe_id][ingr_id])
        weights.append(all_weights[recipe_id][ingr_id])

pl.read_csv("recipes.csv").with_columns(
    pl.Series(recipe_ingredients).alias("Ingredients")).to_pandas().to_csv('recipes.csv', index=False)
pl.DataFrame({"ID": ids, "Recipe ID": recipe_ids, "Ingredient ID": ingredient_ids, "Weight": weights},
             strict=False).to_pandas().to_csv('weights.csv', index=False)

recipe_time = pl.read_csv("recipes.csv").get_column("Cooking time").to_list()
time_in_minutes = []

for time in recipe_time:
    split_time = time.split()
    hours = 0
    minutes = 0
    if time.find('час') != -1 and time.find('минут') != -1:
        hours = int(split_time[0])
        minutes = int(split_time[2])
    elif time.find('час') != -1:
        hours = int(split_time[0])
    elif time.find('минут') != -1:
        minutes = int(split_time[0])
    time_in_minutes.append(hours * 60 + minutes)

pl.read_csv("recipes.csv").insert_column(3, pl.Series('Cooking time in minutes', time_in_minutes)).to_pandas().to_csv(
    'recipes.csv', index=False)
