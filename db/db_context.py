from dotenv import load_dotenv, find_dotenv
from os import getenv
from pymongo import MongoClient

load_dotenv(find_dotenv('.env'))

client = MongoClient(getenv("MONGODB_CONNECTION_URI"))
db = client[getenv("DB_NAME")]


class DbContext:

    def __enter__(self):
        return db

    def __exit__(self, exc_type, exc_value, traceback):
        pass
