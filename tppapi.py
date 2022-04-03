import requests
import csv

class Tppapi:

    def __init__(self):
        self.api = "https://twitchplayspokemon.tv/api/"
        self.id_to_name_csv_path = "user_ids_to_names.csv"

    def get_data(self, endpoint):
        print(f"GET {self.api + endpoint}")
        return requests.get(self.api + endpoint).json()

    def get_user_from_id(self, id):
        return self.get_data(f"users/{id}")
    
    def get_username_from_id(self, id):
        try:
            with open(self.id_to_name_csv_path, "r") as f:
                reader = csv.reader(f)
                for row in reader:
                    if row[0] == str(id):
                        return row[1]
            # get it from the api and add to the csv
            user = self.get_user_from_id(id)
            with open(self.id_to_name_csv_path, "a") as f:
                writer = csv.writer(f)
                writer.writerow([id, user["name"]])
        except FileNotFoundError:
            user = self.get_user_from_id(id)
            with open(self.id_to_name_csv_path, "w") as f:
                writer = csv.writer(f)
                writer.writerow(["id", "name"])
                writer.writerow([id, user["name"]])
        return user["name"]

    def get_latest_match(self):
        return self.get_data("matches")[0]

    def get_match(self, match_id):
        match = self.get_data(f"matches/{match_id}")
        if "message" in match:
            return None
        else:
            return match

    def get_latest_pokeyen_rankings(self):
        return self.get_data("pokeyen_rankings")[0]

    def get_pokeyen_ranking(self, ranking_id):
        ranking = self.get_data(f"pokeyen_rankings/{ranking_id}")
        if "message" in ranking:
            return None
        else:
            return ranking

    def get_pokeyen_ranking_info(self, skip=0, limit=150):
        return self.get_data(f"pokeyen_rankings?skip={skip}&limit={limit}")