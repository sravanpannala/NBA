# Update pbp data
import numpy as np
import pandas as pd
from tqdm import tqdm
from itertools import product
import time
import os, sys

sys.path.append(os.path.dirname(os.path.abspath("__file__")))
# print(sys.path.append(os.path.dirname(os.path.abspath("__file__"))))
from nbafuns import *
from pbpstats.client import Client
from nba_api.stats.endpoints import (
    leaguegamelog,
    boxscoreadvancedv3,
    boxscorefourfactorsv3,
)
from nba_api.stats.endpoints import (
    boxscorescoringv3,
    boxscoreplayertrackv3,
    boxscoremiscv3,
    boxscorehustlev2,
)
from pbpstats.resources.enhanced_pbp import FieldGoal

data_DIR_box = "C:/Users/pansr/Documents/NBA/team_ratings/boxscores/"
data_DIR_shot = "C:/Users/pansr/Documents/NBA/Shot_charts/ShotLocationData/"

# Update PBP Data
data_provider = "data_nba"
pbp_DIR = "C:/Users/pansr/Documents/NBA/pbpdata/" + data_provider


def update_pbp(seasons):
    season_types = ["Regular Season"]
    leagues = ["nba"]
    for season_yr, league, season_type in product(seasons, leagues, season_types):
        print(f"{season_yr},{league},{season_type}")
        settings = {
            "Games": {"source": "web", "data_provider": data_provider},
            "dir": pbp_DIR,
        }
        client = Client(settings)
        season = client.Season(league, season_yr, season_type)
        games_id = []
        k = 0
        for final_game in season.games.final_games:
            k += 1
            games_id.append(final_game["game_id"])
        print("Number of games: ", len(games_id))
        settings = {
            "Boxscore": {"source": "file", "data_provider": data_provider},
            "Possessions": {"source": "file", "data_provider": data_provider},
            "dir": pbp_DIR,
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


# Update BoxScores
def get_gameids(season, name):
    df = pd.read_csv(
        data_DIR_box + "NBA_BoxScores_" + "Standard" + "_" + season + ".csv"
    )
    game_ids1 = df["GAME_ID"].tolist()
    game_ids1 = np.unique(game_ids1)
    try:
        dfr = pd.read_csv(
            data_DIR_box + "NBA_BoxScores_" + name + "_" + season + ".csv"
        )
        dfr = dfr.drop(dfr.columns[0], axis=1)
        game_ids3 = dfr["gameId"].tolist()
        game_ids2 = np.unique(game_ids3)
        game_ids = list(set(game_ids1).difference(game_ids2))
    except:
        game_ids = game_ids1
        dfr = pd.DataFrame()
    game_ids = ["00" + str(s) for s in game_ids]
    return game_ids, dfr


def get_game_box(game_ids, fun, it=5):
    df_ap = []
    for game_id in tqdm(game_ids):
        for ii in range(it):
            try:
                stats = fun(game_id=game_id)
                df1 = stats.get_data_frames()[1]
                df_ap.append(df1)
                break
            except:
                print(game_id)
                time.sleep(0.6)
                continue
    return df_ap


def get_boxscores(seasons, fun, name):
    for season in seasons:
        print(season)
        game_ids, dfr = get_gameids(season, name)
        try:
            df_ap = get_game_box(game_ids, fun)
            df1 = pd.concat(df_ap)
            df = pd.concat([dfr, df1])
            df["gameId"] = df["gameId"].astype(int)
            df = df.sort_values(by=["gameId"]).reset_index(drop=True)
            df.to_csv(data_DIR_box + "NBA_BoxScores_" + name + "_" + season + ".csv")
        except:
            continue


def update_standard_boxscores(seasons):
    for season in seasons:
        print(season)
        stats = leaguegamelog.LeagueGameLog(
            player_or_team_abbreviation="T",
            season=season,
            season_type_all_star="Regular Season",
        )
        df = stats.get_data_frames()[0]
        df.to_csv(data_DIR_box + "NBA_BoxScores_" + "Standard" + "_" + season + ".csv")


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


def get_loc_data(games_list, player_dict, team_dict):
    pos_store = []
    for game in tqdm(games_list):
        for possession in game.possessions.items:
            for possession_event in possession.events:
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


def update_shotdetails(seasons):
    data_provider = "data_nba"
    league = "NBA"
    season_type = "Regular Season"
    for season in seasons:
        print(season)
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
        player_dict = get_players_pbp(league=league)
        team_dict = teams.get_teams()
        team_dict = get_teams(league=league)
        data = get_loc_data(games_list, player_dict, team_dict)
        data.to_parquet(
            data_DIR_shot + f"{league}_Shot_Loc_" + season + ".parquet"
        )


season_start = 2023
season_end = 2023
seasons = np.arange(season_start, season_end + 1, 1).astype(str)

# Update pbp Data
update_pbp(seasons)

# Update Boxscores
print("Update Standard Boxscores")
update_standard_boxscores(seasons)

boxscores = [
    {
        "name": "Adv",
        "fun": boxscoreadvancedv3.BoxScoreAdvancedV3,
    },
    {
        "name": "4Factor",
        "fun": boxscorefourfactorsv3.BoxScoreFourFactorsV3,
    },
    {
        "name": "Hustle",
        "fun": boxscorehustlev2.BoxScoreHustleV2,
    },
    {
        "name": "Misc",
        "fun": boxscoremiscv3.BoxScoreMiscV3,
    },
    {
        "name": "Track",
        "fun": boxscoreplayertrackv3.BoxScorePlayerTrackV3,
    },
    {"name": "Scoring", "fun": boxscorescoringv3.BoxScoreScoringV3},
]

for boxscore in boxscores:
    print("BoxScore " + boxscore["name"])
    get_boxscores(seasons, boxscore["fun"], boxscore["name"])

# Update Shot Details
print("Shot Details")
update_shotdetails(seasons)
