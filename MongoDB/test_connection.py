from pymongo import MongoClient

MONGO_HOST = 'localhost'
MONGO_PORT = 27000
MONGO_DB = "findrecipe"
MONGO_USER = "root"
MONGO_PASS = "password"

# Create a MongoClient instance
client = MongoClient(f'mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin')

# Get a reference to the database
db = client['findrecipe']

# Get a reference to the collection

collection = db['ingredients']
cursor = collection.find({'ID': 2})
cn = len([i for i in cursor])
if cn == 1:
    print("\n\n\nOK\n\n\n")
else:
    print("\n\n\nDB HAS DUBLICATES IN ingredients\n\n\n")
    raise Exception("DB HAS DUBLICATES IN ingredients")


collection = db['recipes']
cursor = collection.find({'ID': 2})
cn = len([i for i in cursor])
if cn == 1:
    print("\n\n\nOK\n\n\n")
else:
    print("\n\n\nDB HAS DUBLICATES IN recipes\n\n\n")
    raise Exception("DB HAS DUBLICATES IN recipes")


collection = db['weights']
cursor = collection.find({'ID': 2})
cn = len([i for i in cursor])
if cn == 1:
    print("\n\n\nOK\n\n\n")
else:
    print("\n\n\nDB HAS DUBLICATES IN weights\n\n\n")
    raise Exception("DB HAS DUBLICATES IN weights")

