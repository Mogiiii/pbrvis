import datetime
import math
from sqlite3 import Date
import requests
from pymongo import mongo_client
import threading
import time
from tppapi import Tppapi

api = "https://twitchplayspokemon.tv/api/"
tppapi = Tppapi()
db_client = mongo_client.MongoClient(host="localhost", port=27017)
match_db = db_client.tpp3.matches
rankings_db = db_client.tpp3.pokeyen_bet_rankings

def calc_skip(latest, local):
    return int((latest - local) / 100) * 100

def update_matches():
    latest_id = tppapi.get_latest_match()["id"]
    try:
        latest_local_id = match_db.find_one(sort=[("_id", -1)])["_id"] # should find the latest match
    except TypeError:
        latest_local_id = 0
    latest_local_id = latest_local_id + 1 # start at the next id since we already have the current one
    while latest_local_id < latest_id:
        # skip if this exists locally already
        if match_db.find_one({"_id": latest_local_id}):
            print(f"match already exists: {latest_local_id}")
            latest_local_id += 1
            continue
        print(f"Updating match {latest_local_id}")
        match = tppapi.get_match(latest_local_id)
        if match:
            match["_id"] = latest_local_id
            match.pop("id", None)
            match_db.insert_one(match)
        else:
            print(f"Match not found: {latest_local_id}")
        latest_local_id += 1
    print("Finished updating matches")

def update_pokeyen_rankings():
    latest_id = tppapi.get_latest_pokeyen_rankings()["id"]
    try:
        latest_local_id = int(rankings_db.find_one(sort=[("_id", -1)])["_id"]) # should find the latest match
    except TypeError:
        latest_local_id = 0
    latest_local_id = latest_local_id + 1 # start at the next id since we already have the current one
    ranking_info = tppapi.get_pokeyen_ranking_info(skip=calc_skip(latest_id, latest_local_id))
    while latest_local_id < latest_id:
        # skip if this exists locally already
        if rankings_db.find_one({"_id": latest_local_id}):
            print(f"ranking already exists: {latest_local_id}")
            latest_local_id += 1
            continue
        print(f"Updating ranking {latest_local_id}")
        try:
            ranking_object = [x for x in ranking_info if x["id"] == latest_local_id][0].copy()
        except IndexError:
            ranking_info = tppapi.get_pokeyen_ranking_info(skip=calc_skip(latest_id, latest_local_id))
            ranking_object = [x for x in ranking_info if x["id"] == latest_local_id][0].copy()
        ranking = tppapi.get_pokeyen_ranking(latest_local_id)
        if ranking:
            ranking_object["_id"] = latest_local_id
            ranking_object.pop("id", None)
            ranking_object["timestamp"] = datetime.datetime.strptime(ranking_object["timestamp"], '%Y-%m-%d %H:%M:%S.%f')
            ranking_object["ranking"] = ranking
            rankings_db.insert_one(ranking_object)
        else:
            print(f"Ranking not found: {latest_local_id}")
        latest_local_id += 1
    print("Finished updating rankings")


if __name__ == "__main__":
    # update in seprate threads
    start_time = time.perf_counter()
    t1 = threading.Thread(target=update_matches)
    t2 = threading.Thread(target=update_pokeyen_rankings)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    print(f"Finished in {datetime.timedelta(time.perf_counter() - start_time)}")