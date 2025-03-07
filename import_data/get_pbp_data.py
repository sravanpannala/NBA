
from itertools import product, chain
from tqdm import tqdm
import zstandard as zstd
from zstandard import ZstdCompressor
import dill
import pandas as pd
from time import perf_counter

from pbpstats.client import Client
from pbpstats.resources.enhanced_pbp import FieldGoal


from update_data import data_DIR, pbp_DIR, player_dict

pbp_loc_DIR = data_DIR + "pbpdata/"
shotloc_DIR = data_DIR + "ShotLocationData/"

def update_pbp(seasons):
    season_types = ["Regular Season"]
    leagues = ["nba"]
    for season_yr, league, season_type in product(seasons, leagues, season_types):
        print(f"{season_yr},{league},{season_type}")
        if int(season_yr) > 2015:
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
        print(pbp_DIR + data_provider)
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
            "dir": pbp_DIR  + data_provider,
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

# Import Shot Details PBP
shot_variables = [
    "game_id",
    "clock",
    "player1_id",
    "team_id",
    "distance",
    "locX",
    "locY",
    "shot_value",
    "shot_type",
    "is_and1",
    "is_assisted",
    "is_blocked",
    "is_corner_3",
    "is_heave",
    "is_made",
    "is_putback",
    "player2_id",
    "period",
    "score_margin",
    "seconds_remaining",
    "seconds_since_previous_event",
]


def set_dtypes(df):
    for col in df.columns:
        if "is_" in col:
            df[col] = df[col].astype(bool)
        elif "_id" in col:
            df[col] = df[col].astype(int)
    if df["clock"].dtype == "O":
        mask = ~df["clock"].str.contains(r"\.")
        df.loc[mask, "clock"] = df.loc[mask, "clock"].apply(lambda x: x + ".0")
        df["clock"] = pd.to_datetime(df["clock"], format="%M:%S.%f").dt.time
    return df


def get_loc_data(games_list, player_dict):
    possessions = [game.possessions.items for game in games_list]
    possession_events = list(
        chain(*[possession.events for possession in list(chain(*possessions))])
    )
    pos_store = []
    for possession_event in possession_events:
        if isinstance(possession_event, FieldGoal):
            poss = {}
            for var in shot_variables:
                try:
                    poss[var] = getattr(possession_event, var)
                except:
                    poss[var] = 0
            pos_store.append(poss)
    df = pd.DataFrame(pos_store)
    df = df.rename(columns={"player1_id": "player_id", "player2_id": "player_ast_id"})
    df["player_name"] = df["player_id"].map(player_dict)
    df["player_ast_name"] = df["player_ast_id"].map(player_dict)
    return df


# pbp function to get all games list for a season
def pbp_season(
    league="NBA",
    season_yr="2024",
    season_type="Regular Season",
    data_provider="data_nba",
):
    settings = {
        "Games": {"source": "file", "data_provider": data_provider},
        "dir": pbp_DIR + data_provider,
    }
    client = Client(settings)
    season = client.Season(league, season_yr, season_type)
    games_id = []
    for final_game in season.games.final_games:
        games_id.append(final_game["game_id"])
    print("Number of games: ", len(games_id))
    return games_id


# function to get all games pbp data for a season
def pbp_games(games_id, data_provider="data_nba"):
    settings = {
        "Boxscore": {"source": "file", "data_provider": data_provider},
        "Possessions": {"source": "file", "data_provider": data_provider},
        "dir": pbp_DIR + data_provider,
    }
    print(pbp_DIR + data_provider)
    client = Client(settings)
    games_list = []
    bad_games_list = []
    for gameid in tqdm(games_id):
        try:
            games_list.append(client.Game(gameid))
        except:
            bad_games_list.append(gameid)
            continue
    print("Number of bad games: ", len(bad_games_list))

    return games_list


def update_shotdetails_pbp(seasons):
    league = "NBA"
    season_type = "Regular Season"
    for season in seasons:
        if int(season) > 2021:
            data_provider = "data_nba"
        else:
            data_provider = "stats_nba"
        games_id = pbp_season(
            league=league,
            season_yr=season,
            season_type=season_type,
            data_provider=data_provider,
        )
        games_list = pbp_games(games_id, data_provider=data_provider)
        print("Compressing PBP Data")
        filename = pbp_loc_DIR + league + "_PBPdata_" + season + ".pkl.zst"
        print(filename)
        t1 = perf_counter()
        with zstd.open(filename, "wb") as f:
            dill.dump(games_list, f)
        t2 = perf_counter()
        print(round(t2-t1))
        data = get_loc_data(games_list, player_dict)
        data = set_dtypes(data)
        data.to_parquet(shotloc_DIR + f"{league}_Shot_Loc_" + season + ".parquet")