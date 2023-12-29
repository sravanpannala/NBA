import time

import numpy as np
import pandas as pd
from nba_api.stats.endpoints import (
    boxscoreadvancedv3,
    boxscorefourfactorsv3,
    boxscorehustlev2,
    boxscoremiscv3,
    boxscoreplayertrackv3,
    boxscorescoringv3,
    leaguegamelog,
    leaguedashplayerstats,
)
from tenacity import retry, stop_after_attempt, wait_fixed
from tqdm import tqdm

from update_data import data_DIR

box_DIR = data_DIR + "box/"

# Update BoxScores
def get_gameids(season, name):
    df = pd.read_parquet(
        box_DIR + "NBA_Box_T_" + "Base" + "_" + season + ".parquet"
    )
    game_ids1 = df["GAME_ID"].tolist()
    game_ids1 = np.unique(game_ids1)
    try:
        dfr1 = pd.read_parquet(
            box_DIR + "NBA_Box_T_" + name + "_" + season + ".parquet"
        )
        dfr2 = pd.read_parquet(
            box_DIR + "NBA_Box_P_" + name + "_" + season + ".parquet"
        )
        game_ids3 = dfr1["gameId"].tolist()
        game_ids2 = np.unique(game_ids3)
        game_ids2 = ["00" + str(s) for s in game_ids2]
        game_ids = list(set(game_ids1).difference(game_ids2))
    except Exception as error:
        print(error)
        game_ids = game_ids1
        dfr1 = pd.DataFrame()
        dfr2 = pd.DataFrame()
    return game_ids, dfr1, dfr2


@retry(stop=stop_after_attempt(5), wait=wait_fixed(0.6))
def get_game_box(game_id, fun):
    try:
        t1 = time.perf_counter()
        stats = fun(game_id=game_id)
        df = stats.get_data_frames()
        t2 = time.perf_counter() - t1
        tsleep = 0.6
        if (t2)<0.6:
            time.sleep(tsleep)
    except Exception as error:
        print(error)
        df = pd.DataFrame()
        pass
    return df


def get_games_box(game_ids, fun):
    df_ap1, df_ap2 = [], []
    for game_id in tqdm(game_ids):
        try:
            df0 = get_game_box(game_id, fun)
            df1 = df0[1]
            df2 = df0[0]
        except Exception as error:
            print(error)
            df1 = pd.DataFrame()
            df2 = pd.DataFrame()
        df_ap1.append(df1)
        df_ap2.append(df2)
    return df_ap1, df_ap2


def update_boxscores_idv(season, fun, name):
    game_ids, dfr1, dfr2 = get_gameids(season, name)
    try:
        df_ap1, df_ap2 = get_games_box(game_ids, fun)
        df1 = pd.concat(df_ap1)
        df2 = pd.concat(df_ap2)
        df3 = pd.concat([dfr1, df1])
        df3["gameId"] = df3["gameId"].astype(int)
        df3 = df3.sort_values(by=["gameId"]).reset_index(drop=True)
        df3.to_parquet(
            box_DIR + "NBA_Box_T_" + name + "_" + season + ".parquet"
        )
        df4 = pd.concat([dfr2, df2])
        df4["gameId"] = df4["gameId"].astype(int)
        df4 = df4.sort_values(by=["gameId"]).reset_index(drop=True)
        df4.to_parquet(box_DIR+ "NBA_Box_P_"+ name + "_"+ season+ ".parquet")
    except Exception as error:
        print(error)
        pass

def update_box_base_t(seasons):
    for season in tqdm(seasons):
        try:
            stats = leaguegamelog.LeagueGameLog(
                player_or_team_abbreviation="T",
                season=season,
                season_type_all_star="Regular Season",
            )
            df = stats.get_data_frames()[0]
            df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"], format="%Y-%m-%d")
            df.to_parquet(box_DIR + "NBA_Box_T_" + "Base" + "_" + season + ".parquet")
            time.sleep(0.6)
            stats = leaguegamelog.LeagueGameLog(
                player_or_team_abbreviation="T",
                season=season,
                season_type_all_star="Playoffs",
            )
            df = stats.get_data_frames()[0]
            df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"], format="%Y-%m-%d")
            df.to_parquet(box_DIR + "NBA_Box_T_" + "Base" + "_" + season + "_PS.parquet")
            time.sleep(0.6)
        except Exception as error:
            continue

def update_box_base_p(seasons):
    for season in tqdm(seasons):
        try:
            stats = leaguegamelog.LeagueGameLog(
                player_or_team_abbreviation="P",
                season=season,
                season_type_all_star="Regular Season",
            )
            df = stats.get_data_frames()[0]
            df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"], format="%Y-%m-%d")
            df.to_parquet(box_DIR + "NBA_Box_P_" + "Base" + "_" + season + ".parquet")
            time.sleep(0.6)
            stats = leaguegamelog.LeagueGameLog(
                player_or_team_abbreviation="P",
                season=season,
                season_type_all_star="Playoffs",
            )
            df = stats.get_data_frames()[0]
            df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"], format="%Y-%m-%d")
            df.to_parquet(box_DIR + "NBA_Box_P_" + "Base" + "_" + season + "_PS.parquet")
        except Exception as error:
            continue

def get_box_p_cum(seasons, measure="Base", n=32):
    if measure == "Advanced":
        per_mode = "Per100Possessions"
    else:
        per_mode = "PerGame"
    for season in tqdm(seasons):
        try:
            season_str = season + "-" + str(int(season) + 1)[-2:]
            stats = leaguedashplayerstats.LeagueDashPlayerStats(
                measure_type_detailed_defense=measure,
                per_mode_detailed=per_mode,
                season=season_str,
            )
            df1 = stats.get_data_frames()[0]
            df = df1.iloc[:, :n]
            if measure == "Advanced":
                measure1 = "Adv"
            else:
                 measure1 = measure
            df.to_parquet(box_DIR + "NBA_Box_P_Cum_" + measure1 + "_" + season + ".parquet")
            time.sleep(0.6)
        except Exception as error:
            continue

def update_box_p_cum(seasons):
    print("Base")
    get_box_p_cum(seasons, measure="Base", n=32)
    print("Advanced")
    get_box_p_cum(seasons, measure="Advanced", n=43)
    print("Misc")
    get_box_p_cum(seasons, measure="Misc", n=23)
    print("Scoring")
    get_box_p_cum(seasons, measure="Scoring", n=29)

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
        "name": "Misc",
        "fun": boxscoremiscv3.BoxScoreMiscV3,
    },
    {"name": "Scoring", "fun": boxscorescoringv3.BoxScoreScoringV3},
    {
        "name": "Track",
        "fun": boxscoreplayertrackv3.BoxScorePlayerTrackV3,
    },
    {
        "name": "Hustle",
        "fun": boxscorehustlev2.BoxScoreHustleV2,
    },
]