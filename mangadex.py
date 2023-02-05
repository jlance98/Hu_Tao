import pymongo
import requests
from dotenv import load_dotenv
import os
import difflib
import json
import re
import shlex

load_dotenv()

# Connects bot to MongoDB database
cluster = pymongo.MongoClient(os.getenv("MongoClient"))
db = cluster.user_messages
collection = db.manga_list

# Points towards Mangadex API for HTTP requests
base_url = "https://api.mangadex.org"


# Finds manga with title closest to user input and returns its title, manga ID, and Mangadex link
def manga_search(manga_title: str):

    r = requests.get(
        f"{base_url}/manga",
        params={"title": manga_title}
    )
    data = r.json()["data"]

    # Checks if request returns nothing
    if len(data) == 0:
        return "No manga could be found with that title."

    # Puts all possible titles into a list
    titles = [manga["attributes"]["title"] for manga in data]
    titles_list = []
    for title in titles:
        titles_list.append(list(title.values())[0])

    # Puts all possible manga IDs into a list
    ids_list = [manga["id"] for manga in r.json()["data"]]

    # Finds the closest matching title to user input, and use that to find index for ID
    closest_title = difflib.get_close_matches(manga_title, titles_list)[0]
    index = titles_list.index(closest_title)
    closest_id = ids_list[index]

    return closest_title, closest_id


# Gets and returns information of manga's latest english chapter
def manga_latest_chapter(search: str):

    # Checks if user search input is a Mangadex ID
    id_regex = "[a-zA-z0-9]{8}-[a-zA-z0-9]{4}-[a-zA-z0-9]{4}-[a-zA-z0-9]{4}-[a-zA-z0-9]{12}"
    id_format = re.search(id_regex, search)
    if not id_format:
        _, search = manga_search(search)

    r = requests.get(
        f"{base_url}/manga/{search}/feed",
        params={"translatedLanguage[]": "en",
                "order[createdAt]": "desc",
                "limit": 1}
    )

    data = r.json()["data"]

    latest_chId = [chapter["id"] for chapter in r.json()["data"]][0]
    latest_chNum = [chapter["attributes"]["chapter"] for chapter in r.json()["data"]][0]
    latest_chTtl = [chapter["attributes"]["title"] for chapter in r.json()["data"]][0]

    return latest_chId, latest_chNum, latest_chTtl


# Inserts into database the latest read chapter of manga of user
def manga_read_chapter(user_input: str):
    params = shlex.split(user_input)
    title = params[0]
    read_chapter = params[1]
    title, manga_id = manga_search(title)

    # Check if user chapter number is above the latest chapter
    _, latest_chNum, latest_title = manga_latest_chapter(title)
    if float(read_chapter) > float(latest_chNum):
        return "N/A", _

    collection.update_one({"manga_id": manga_id},
                          {"$set": {"read_chapter": read_chapter}},
                          upsert=True)

    return title, latest_title, read_chapter


# Checks if user's mangas have any new chapters, and returns a list of updated mangas
def manga_check_update():
    current_db = collection.find({})
    outdated_mangas = []
    for current_manga in current_db:

        # Checks if read_chapter is the latest chapter
        _, latest_chNum, _ = manga_latest_chapter(current_manga["manga_id"])
        if float(current_manga["read_chapter"]) != float(latest_chNum):
            outdated_mangas.append(current_manga["manga_id"])

    print(outdated_mangas)

    return outdated_mangas

