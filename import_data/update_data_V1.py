import numpy as np
import pandas as pd
import json
import os, sys
import argparse

home_DIR = "C:/Users/pansr/Documents/NBA/"
csv_export_DIR = "C:/Users/pansr/Documents/repos/csv/"

pbp_DIR = home_DIR + "pbpdata/"
data_DIR = home_DIR + "data/"

sys.setrecursionlimit(10000)
pd.options.mode.chained_assignment =  None

os.environ["R_HOME"] = "C:\\Program Files\\R\\R-4.3.2\\"

with open(data_DIR + "NBA.json") as f:
    data = json.load(f)
pID_dict = {v: int(k) for k, v in data.items()}
player_dict = {int(k): v for k, v in data.items()}

from get_pbp_data import *
from get_boxscores import *
from get_shot_data import *
from get_advanced import *


def parse_function():
    global season_start
    global season_end
    global bool_pbp
    global bool_box
    global bool_idv
    global bool_shot
    global bool_adv

    parser = argparse.ArgumentParser(
        description="Update NBA Data",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--season1",
        "-s1",
        default=2023,
        type=int,
        help="Enter season to start",
    )
    parser.add_argument(
        "--season2",
        "-s2",
        default=2024,
        type=int,
        help="Enter season to start",
    )
    parser.add_argument(
        "--pbp",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Update PBP data",
    )
    parser.add_argument(
        "--box",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Update BoxScores data",
    )
    parser.add_argument(
        "--idv",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Update Individual Game BoxScores data",
    )
    parser.add_argument(
        "--shot",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Update Shot data",
    )
    parser.add_argument(
        "--adv",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Update Adv data",
    )

    args = parser.parse_args()

    season_start = args.season1
    season_end = args.season2
    bool_pbp  = args.pbp
    bool_box  = args.box
    bool_idv  = args.idv
    bool_shot = args.shot
    bool_adv  = args.adv

def main():
    parse_function()

    seasons = np.arange(season_start, season_end, 1).astype(str)
    # Update pbp Data
    if bool_pbp:
        print("Update PBP Data")
        update_pbp(seasons)

    # Update Boxscores
    if bool_box:
        print("Update Boxscores")
        update_box_base_t(seasons)
        update_box_base_p(seasons)
        update_box_p_cum(seasons)
        if bool_idv:
            for season in seasons:
                print(season)
                for boxscore in boxscores:
                    print("BoxScore " + boxscore["name"])
                    update_boxscores_idv(season, boxscore["fun"], boxscore["name"])

    if bool_shot:
        # Update Shot Dashboard
        print("Shot Dashboard")
        update_shot_dash(seasons)
        update_shot_dash_all(seasons)
        # Update Shot Details
        print("Shot Details PBP")
        update_shotdetails_pbp(seasons)
        update_shotdetails_nba(seasons)

    if bool_adv:
        # Update Injury Data
        print("Update Injury Data")
        update_injury_data(seasons)
        # Update DARKO
        print("Update DARKO")
        update_DARKO()
        # Update bbref advanced stats
        print("Update bbref")
        update_bbref(seasons)

if __name__ == "__main__":
    main()