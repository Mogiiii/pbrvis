import asyncio
import time
import pymongo
import sys
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import threading

BASE_NOTEBOOK_PATH = "base.ipynb"
START_STRING = "##########"
END_STRING = "%%%%%%%%%%"
SEASON_STRING = "%SEASON%"
CSV_PATH_STRING = "%CSVPATH%"
THREAD_COUNT = 8

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # avoid warning

db = pymongo.MongoClient()["tpp3"]
season_borders = db["pokeyen_bet_rankings"].aggregate(pipeline=[
    {"$group": {
        "_id": {"$ifNull": ["$season", 0]},
        "from": {"$min": "$timestamp"},
        "to": {"$max": "$timestamp"}
    }},
    {"$sort": {"_id": pymongo.ASCENDING}},
])  # ty felk
season_borders = list(season_borders)


def datetime_to_formatted_string(datetime):
    return str(datetime).replace(" ", "T")[:-3]


def create_single_season_file(season):
    s = season_borders[season]
    start = s["from"]
    end = s["to"]
    with open(BASE_NOTEBOOK_PATH, "r") as base:
        nb = base.read()
        nb = nb.replace(START_STRING, datetime_to_formatted_string(start))
        nb = nb.replace(END_STRING, datetime_to_formatted_string(end))
        nb = nb.replace(SEASON_STRING, str(season))
        nb = nb.replace(CSV_PATH_STRING, "../user_ids_to_names.csv")
    with open(f"./seasons/Season {season}.ipynb", "w") as outfile:
        outfile.write(nb)


def create_all_season_files():
    with open(BASE_NOTEBOOK_PATH, "r") as base:
        base_nb = base.read()
        for i in range(len(season_borders)):
            s = season_borders[i]
            start = s["from"]
            end = s["to"]
            nb = base_nb.replace(START_STRING, datetime_to_formatted_string(start))
            nb = nb.replace(END_STRING, datetime_to_formatted_string(end))
            nb = nb.replace(SEASON_STRING, str(i))
            nb = nb.replace(CSV_PATH_STRING, "../user_ids_to_names.csv")

            with open(f"./seasons/Season {i}.ipynb", "w") as outfile:
                outfile.write(nb)


def run_notebook_for_season(season):
    start_time = time.perf_counter()
    path_to_nb = "./seasons/Season " + str(season) + ".ipynb"
    print(f"Beginning season {season}")
    with open(path_to_nb, "r") as f:
        nb = nbformat.read(f, as_version=4)
        ep = ExecutePreprocessor()
        ep.preprocess(nb)
    with open(path_to_nb, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)
    print(f"Season {season} finished in {time.perf_counter() - start_time}")


def run_all_seasons():
    threads = [threading.Thread(name=f"Season_{i}", target=run_notebook_for_season, args=[i])
               for i in range(len(season_borders))]
    unstarted_threads = threads.copy()
    allowed_threads = THREAD_COUNT + len(threading.enumerate())
    while len(unstarted_threads) > 0:
        if len(threading.enumerate()) < allowed_threads:
            t = unstarted_threads.pop()
            t.start()
        else:
            time.sleep(1)
    for thread in threads:
        thread.join()


def main():
    if len(sys.argv) == 2:
        s = int(sys.argv[1])
        create_single_season_file(s)
        run_notebook_for_season(s)
    else:
        print("Creating season files...")
        create_all_season_files()
        print("Running notebook for all seasons...")
        start_time = time.perf_counter()
        run_all_seasons()
        print(f"All seasons complete in {time.perf_counter() - start_time}")


if __name__ == "__main__":
    main()
