import pymongo
import bot
import responses
import requests
from dotenv import load_dotenv
import os

load_dotenv()

# Connects bot to MongoDB database
dbclient = pymongo.MongoClient(os.getenv("MongoClient"))
db = dbclient.user_messages

# Points towards Mangadex API for HTTP requests
base_url = "https://api.mangadex.org"


def search_manga(message, manga_title: str):
    r = requests.get(
        f"{base_url}/manga",
        params={"title": manga_title}
    )
    manga_ids = [manga["id"] for manga in r.json()["data"]]
    return manga_ids

def read_manga
