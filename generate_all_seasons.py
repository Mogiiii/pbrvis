import asyncio
import time
import pymongo
import sys
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

BASE_NOTEBOOK_PATH = "base.ipynb"
START_STRING = "##########"
END_STRING = "%%%%%%%%%%"

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

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


def create_season_file(season):
    s = season_borders[season]
    start = s["from"]
    end = s["to"]
    with open(BASE_NOTEBOOK_PATH, "r") as base:

        nb = base.read()
        nb = nb.replace(START_STRING, datetime_to_formatted_string(start))
        nb = nb.replace(END_STRING, datetime_to_formatted_string(end))
    with open(f"./seasons/Season {season}.ipynb", "w") as outfile:
        outfile.write(nb)


def run_notebook_for_season(season):
    path_to_nb = "./seasons/Season " + str(season) + ".ipynb"
    with open(path_to_nb, "r") as f:
        nb = nbformat.read(f, as_version=4)
        ep = ExecutePreprocessor()
        ep.preprocess(nb)
    with open(path_to_nb, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)


def main():
    if len(sys.argv) == 2:
        start_time = time.perf_counter()
        s = int(sys.argv[1])
        create_season_file(s)
        run_notebook_for_season(s)
        print(f"finished in {str(time.perf_counter() - start_time)}")
    else:
        start_time = time.perf_counter()
        for i in range(len(season_borders)):
            loop_start_time = time.perf_counter()
            print(f"Creating season {i}")
            create_season_file(i)
            run_notebook_for_season(i)
            loop_end_time = time.perf_counter()
            print(f"Season {i} finished in {str(loop_end_time - loop_start_time)}")
        print(f"All seasons complete in {time.perf_counter() - start_time}")


if __name__ == "__main__":
    main()
