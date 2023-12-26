
from itertools import product, chain
from tqdm import tqdm

from pbpstats.client import Client

from update_data_V1 import pbp_DIR




def update_pbp(seasons):
    season_types = ["Regular Season"]
    leagues = ["nba"]
    for season_yr, league, season_type in product(seasons, leagues, season_types):
        print(f"{season_yr},{league},{season_type}")
        if int(season_yr) > 2021:
            data_provider = "data_nba"
        else:
            data_provider = "stats_nba"
        settings = {
            "Games": {"source": "web", "data_provider": data_provider},
            "dir": pbp_DIR + data_provider,
        }
        client = Client(settings)
        season = client.Season(league, season_yr, season_type)
        games_id = []
        for final_game in season.games.final_games:
            games_id.append(final_game["game_id"])
        print("Number of games: ", len(games_id))
        settings = {
            "Boxscore": {"source": "file", "data_provider": data_provider},
            "Possessions": {"source": "file", "data_provider": data_provider},
            "dir": pbp_DIR + data_provider,
        }
        client = Client(settings)
        games_list_online = []
        error_list = []
        bad_games_list = []
        for gameid in tqdm(games_id):
            try:
                client.Game(gameid)
            except Exception as error:
                if "does not exist" in error.args[0]:
                    games_list_online.append(gameid)
                elif "pstsg" in error.args[0]:
                    games_list_online.append(gameid)
                    error_list.append(error.args[0])
                else:
                    bad_games_list.append(gameid)
                    error_list.append(error.args[0])
                continue
        print(error_list)
        print("Number of bad games: ", len(bad_games_list))
        print("Number of missing games: ", len(games_list_online))
        settings = {
            "Boxscore": {"source": "web", "data_provider": data_provider},
            "Possessions": {"source": "web", "data_provider": data_provider},
            "dir": pbp_DIR,
        }
        client = Client(settings)
        # error_list = []
        for gameid in tqdm(games_list_online):
            try:
                client.Game(gameid)
            except Exception as error:
                # print(error)
                # error_list.append(error.args[0])
                continue
        # print(error_list)