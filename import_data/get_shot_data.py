
from itertools import product, chain
import time

import pandas as pd
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_fixed, Retrying

from nba_api.stats.endpoints import playerdashptshots, leaguedashplayerptshot, shotchartdetail
from pbpstats.client import Client
from pbpstats.resources.enhanced_pbp import FieldGoal

from update_data import data_DIR, pbp_DIR, player_dict

shot_DIR = data_DIR + "shots/"
shotloc_DIR = data_DIR + "ShotLocationData/"
pbp_loc_DIR = data_DIR + "pbpdata/"

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
        with pd.option_context("future.no_silent_downcasting", True):                    
            dfa1 = [df2.fillna(0).infer_objects(copy=False) for df2 in dfa if not df2.empty]
        df = pd.concat(dfa1)
        df.to_parquet(shot_DIR + f"{league}_Shots_{season}_All.parquet")


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
