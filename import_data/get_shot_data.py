
from itertools import product, chain
import time

import pandas as pd
from tqdm import tqdm
import zstandard as zstd
import dill
from tenacity import retry, stop_after_attempt, wait_fixed, Retrying

from nba_api.stats.endpoints import playerdashptshots, leaguedashplayerptshot, shotchartdetail
from pbpstats.client import Client
from pbpstats.resources.enhanced_pbp import FieldGoal

from update_data import data_DIR, pbp_DIR, player_dict

shot_DIR = data_DIR + "shots/"
shotloc_DIR = data_DIR + "ShotLocationData/"

def update_shot_dash(seasons):
    league, league_id = "NBA", "00"
    dash_types = [
        "overall",
        "shot_type",
        "shot_clock",
        "dribble",
        "closest_def",
        "closest_def_10",
        "touch_time",
    ]
    for season in seasons:
        print(season)
        season_str = season + "-" + str(int(season) + 1)[-2:]
        stats = playerdashptshots.PlayerDashPtShots(
            league_id=league_id, team_id=0, player_id=0, season=season_str
        ).get_data_frames()
        for i, d in enumerate(dash_types):
            df = stats[i].drop(
                columns=[
                    "SORT_ORDER",
                    "FGA_FREQUENCY",
                    "FG2A_FREQUENCY",
                    "FG3A_FREQUENCY",
                ]
            )
            df.to_parquet(
                shot_DIR + f"{league}_Shots_{season}_{d}.parquet"
            )
        time.sleep(0.6)


def update_shot_dash_all(seasons):
    league, league_id = "NBA", "00"
    general_range = ['Catch and Shoot', 'Pullups', 'Less Than 10 ft']
    shot_clock = [
        "24-22",
        "22-18 Very Early",
        "18-15 Early",
        "15-7 Average",
        "7-4 Late",
        "4-0 Very Late",
    ]
    dribbles = ["0 Dribbles", "1 Dribble", "2 Dribbles", "3-6 Dribbles", "7+ Dribbles"]
    closest_def = [
        "0-2 Feet - Very Tight",
        "2-4 Feet - Tight",
        "4-6 Feet - Open",
        "6+ Feet - Wide Open",
    ]
    touch_time = ["Touch < 2 Seconds", "Touch 2-6 Seconds", "Touch 6+ Seconds"]
    for season in seasons:
        season_str = season + "-" + str(int(season) + 1)[-2:]
        n = 0
        for a, b, c in product(general_range, closest_def, touch_time):
            n += 1
        dfa = []
        for a, b, c in tqdm(product(general_range, closest_def, touch_time), total=n):
            # for i in Retrying(stop=stop_after_attempt(2), wait=wait_fixed(0.6)):
                try:
                    stats = leaguedashplayerptshot.LeagueDashPlayerPtShot(
                        league_id=league_id,
                        season=season_str,
                        general_range_nullable=a,
                        close_def_dist_range_nullable=b,
                        touch_time_range_nullable=c,
                        # dribble_range_nullable =  d,
                    ).get_data_frames()
                    df1 = stats[0]
                    df1["general_range"] = a
                    df1["closest_def"] = b
                    df1["touch_time"] = c
                    dfa.append(df1)
                    time.sleep(0.6)
                    # break
                except Exception as error:
                    print(error)
                    # continue
        dfa1 = [df2.fillna(0) for df2 in dfa if not df2.empty]
        df = pd.concat(dfa1)
        df.to_parquet(shot_DIR + f"{league}_Shots_{season}_All.parquet")

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
        mask = ~df["clock"].str.contains("\.")
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
    season_yr="2023",
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
        filename = pbp_DIR + league + "_PBPdata_" + season + ".pkl.zst"
        print(filename)
        with zstd.open(filename, "wb") as f:
            dill.dump(games_list, f)
        data = get_loc_data(games_list, player_dict)
        data = set_dtypes(data)
        data.to_parquet(shotloc_DIR + f"{league}_Shot_Loc_" + season + ".parquet")


def update_shotdetails_nba(seasons):
    for season in seasons:
        season_str = season + "-" + str(int(season) + 1)[-2:]
        player_shotchart = shotchartdetail.ShotChartDetail(
            league_id="00",
            team_id=0,
            player_id=0,
            context_measure_simple="FGA",
            season_nullable=season_str,
        )
        shots = player_shotchart.get_data_frames()[0]
        shots["LOC_X"] = -shots["LOC_X"]
        shots.to_parquet(
            shotloc_DIR + f"NBA_Shot_Details_{season}.parquet"
        )
        time.sleep(0.6)
