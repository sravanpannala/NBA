import numpy as np
import pandas as pd
import json
import os
import argparse

home_DIR = "C:/Users/pansr/Documents/NBA/"
csv_export_DIR = "C:/Users/pansr/Documents/repos/csv/"

pbp_DIR = home_DIR + "pbpdata/"
data_DIR = home_DIR + "data/"

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

    args = parser.parse_args()

    season_start = args.season1
    season_end = args.season2

def main():
    parse_function()

    seasons = np.arange(season_start, season_end, 1).astype(str)
    # Update pbp Data
    print("Update PBP Data")
    update_pbp(seasons)

    # Update Boxscores
    print("Update Boxscores")
    update_boxscores(seasons)

    # Update Shot Dashboard
    print("Shot Dashboard")
    update_shot_dash(seasons)
    update_shot_dash_all(seasons)

    # Update Shot Details
    print("Shot Details PBP")
    update_shotdetails_pbp(seasons)
    update_shotdetails_nba(seasons)

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