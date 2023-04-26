import pymongo
import requests
from dotenv import load_dotenv
import os
import difflib
import json
import re

load_dotenv()

# Connects bot to MongoDB database
cluster = pymongo.MongoClient(os.getenv("MongoClient"))
db = cluster.user_messages
collection = db.manga_list

# Points towards Mangadex API for HTTP requests
base_url = "https://api.mangadex.org"

# Cache used for read command using -r
outdated_mangas = []


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

    # Reattempt request 5 times if status code of response is not 200. After 5 attempts, skips the request
    statusCode = 0
    attempts = 0
    while statusCode != 200:
        attempts += 1
        if attempts == 6:
            return "N/A", "N/A", "N/A"
        r = requests.get(
            f"{base_url}/manga",
            params
        )
        statusCode = r.status_code

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
def manga_latest_chapter(search: str, is_correct_id: bool):

    # Uses is_correct_id to avoid having to do an extra GET request to Mangadex. False only if user cmd
    if not is_correct_id:
        _, search = manga_search(search)
        # Checks if nothing was returned
        if search == "N/A":
            return "N/A", "N/A", "N/A"

    # Reattempt request 5 times if status code of response is not 200. After 5 attempts, skips the request
    statusCode = 0
    attempts = 0
    while statusCode != 200:
        attempts += 1
        if attempts == 6:
            return "N/A", "SKIP", "N/A"

        r = requests.get(
            f"{base_url}/chapter",
            params={"translatedLanguage[]": "en",
                    "order[chapter]": "desc",
                    "manga": search,
                    "limit": 1}
        )
        statusCode = r.status_code

    data = r.json()["data"]

    latest_chId = [chapter["id"] for chapter in data][0]
    latest_chNum = [chapter["attributes"]["chapter"] for chapter in data][0]
    latest_chTtl = [chapter["attributes"]["title"] for chapter in data][0]
    return latest_chId, latest_chNum, latest_chTtl


# Inserts into database the latest read chapter of manga of user
def manga_read_chapter(title, read_chapter):

    # If user inputs "-l", use latest chapter of manga
    if read_chapter == "-l":
        title, manga_id = manga_search(title)

        # Checks if nothing was returned
        if title == "N/A":
            return "N/A", "N/A"

        _, read_chapter, _ = manga_latest_chapter(manga_id, True)
        collection.update_one({"manga_id": manga_id, "manga_title": title},
                              {"$set": {"read_chapter": read_chapter}},
                              upsert=True)
    elif read_chapter == "-r":
        if len(outdated_mangas) == 0:
            return "RUNUPDATE", "RUNUPDATE"
        else:
            if title == "all":
                for manga in outdated_mangas:
                    _, read_chapter, _ = manga_latest_chapter(manga[0], True)
                    collection.update_one({"manga_id": manga[0], "manga_title": manga[1]},
                                          {"$set": {"read_chapter": read_chapter}},
                                          upsert=True)
                return "ALL", "ALL"
            elif title.isnumeric():
                print(title)
                print(title.isnumeric())
                print("!hutao {numeric} -r")
                index = int(title) - 1
                _, read_chapter, _ = manga_latest_chapter(outdated_mangas[index][0], True)
                title = outdated_mangas[index][1]
                collection.update_one({"manga_id": outdated_mangas[index][0], "manga_title": outdated_mangas[index][1]},
                                      {"$set": {"read_chapter": read_chapter}},
                                      upsert=True)
    # User input for read_chapter is a number, check if valid chapter number
    else:
        # Check if user chapter number is above the latest chapter
        _, latest_chNum, _ = manga_latest_chapter(manga_id, True)
        if float(read_chapter) > float(latest_chNum):
            return "N/A", _

    return title, read_chapter

# Deletes manga from database
def manga_delete_manga(title):
    title, manga_id = manga_search(title)

    # Checks if nothing was returned
    if title == "N/A":
        return "N/A"

    check_existence = collection.count_documents({"manga_id": manga_id, "manga_title": title})
    if check_existence == 1:
        collection.delete_many({"read_chapter":"SKIP"})
    else:
        return "DNE"

    return title


# Checks if user's mangas have any new chapters, and returns a list of updated mangas
def manga_check_update():
    current_db = list(collection.find({}))

    outdated_mangas.clear()

    for current_manga in current_db:
        _, latest_chNum, _ = manga_latest_chapter(current_manga["manga_id"], True)
        if latest_chNum == "SKIP":
            continue
        if float(current_manga["read_chapter"]) != float(latest_chNum):
            manga = [current_manga["manga_id"], current_manga["manga_title"]]
            outdated_mangas.append(manga)

    return outdated_mangas
