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


# Calculates the similarity as a ratio between two strings
def similar(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()


# Finds manga with title closest to user input and returns its title, manga ID, and Mangadex link
def manga_search(search_input: str):
    # Checks if user search input is a Mangadex ID or not; determines GET parameters
    id_regex = "[a-zA-z0-9]{8}-[a-zA-z0-9]{4}-[a-zA-z0-9]{4}-[a-zA-z0-9]{4}-[a-zA-z0-9]{12}"
    id_format = re.search(id_regex, search_input)

    if id_format:
        params = {"ids[]": [search_input]}
    else:
        params = {"title": search_input}

    r = requests.get(
        f"{base_url}/manga",
        params
    )
    data = r.json()["data"]

    # Checks if nothing was returned
    if len(data) == 0:
        return "N/A", "N/A"

    # Puts all possible titles into a list
    titles = [manga["attributes"]["title"] for manga in data]
    titles_list = []
    for title in titles:
        titles_list.append(list(title.values())[0])

    # Puts all possible manga IDs into a list
    ids_list = [manga["id"] for manga in r.json()["data"]]

    # If only one title is returned, use that
    if len(titles_list) == 1:
        closest_title = titles_list[0]

    # Finds the closest matching title to user input
    else:
        closest_title = ""
        best_match_ratio = -1
        for title in titles_list:
            if similar(search_input, title) > best_match_ratio:
                closest_title = title
                best_match_ratio = similar(search_input, title)

    # Uses the closest title as index to find the closest id
    index = titles_list.index(closest_title)
    closest_id = ids_list[index]

    return closest_title, closest_id


# Gets and returns information of manga's latest english chapter
def manga_latest_chapter(search: str):
    _, search = manga_search(search)

    # Checks if nothing was returned
    if search == "N/A":
        return "N/A", "N/A", "N/A"

    r = requests.get(
        f"{base_url}/chapter",
        params={"translatedLanguage[]": "en",
                "order[chapter]": "desc",
                "manga": search,
                "limit": 1}
    )
    data = r.json()["data"]

    latest_chId = [chapter["id"] for chapter in data][0]
    latest_chNum = [chapter["attributes"]["chapter"] for chapter in data][0]
    latest_chTtl = [chapter["attributes"]["title"] for chapter in data][0]
    return latest_chId, latest_chNum, latest_chTtl


# Inserts into database the latest read chapter of manga of user
def manga_read_chapter(title, read_chapter):
    title, manga_id = manga_search(title)

    # Checks if nothing was returned
    if title == "N/A":
        return "N/A", "N/A"

    # If user inputs "-l", use latest chapter of manga
    if read_chapter == "-l":
        _, read_chapter, _ = manga_latest_chapter(manga_id)
    else:
        # Check if user chapter number is above the latest chapter
        _, latest_chNum, _ = manga_latest_chapter(manga_id)
        if float(read_chapter) > float(latest_chNum):
            return "N/A", _

    collection.update_one({"manga_id": manga_id, "manga_title": title},
                          {"$set": {"read_chapter": read_chapter}},
                          upsert=True)

    return title, read_chapter


# Checks if user's mangas have any new chapters, and returns a list of updated mangas
def manga_check_update():
    current_db = list(collection.find({}))
    outdated_mangas = []

    for current_manga in current_db:
        _, latest_chNum, _ = manga_latest_chapter(current_manga["manga_id"])
        if float(current_manga["read_chapter"]) != float(latest_chNum):
            manga = [current_manga["manga_id"], current_manga["manga_title"]]
            outdated_mangas.append(manga)

    return outdated_mangas
