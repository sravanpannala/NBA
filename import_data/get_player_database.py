import time
import json
import requests
import numpy as np
import pandas as pd
from nba_api.stats.endpoints import commonallplayers, playerindex

from update_data import data_DIR

roster_DIR = data_DIR + "rosters/"

def update_player_database():
    season = "2024"
    season_str = season + "-" + str(int(season)+1)[-2:]
    league_id = "00"
    league = "NBA"
    stats = commonallplayers.CommonAllPlayers(league_id=league_id, season=season, is_only_current_season=["0"])
    df = stats.get_data_frames()[0]
    df["PERSON_ID"] = df["PERSON_ID"].astype(int)
    df["FROM_YEAR"] = df["FROM_YEAR"].astype(int)
    df["TO_YEAR"] = df["TO_YEAR"].astype(int)
    df = df.rename(
        columns={
            "PERSON_ID": "pID",
            "DISPLAY_FIRST_LAST": "Name",
            "FROM_YEAR": "From",
            "TO_YEAR": "To",
        }
    )
    data = df[["pID", "Name", "From", "To"]]
    data.to_csv(data_DIR + f"{league}_players_database.csv", index=False)

    stats = playerindex.PlayerIndex(league_id = "00", season =season_str)
    df = stats.get_data_frames()[0]
    df = df.query("ROSTER_STATUS == 1").reset_index(drop=True)
    df.to_parquet(roster_DIR + "NBA_Team_Rosters" + "_" + season + ".parquet")

    players_response = requests.get(
        "https://api.pbpstats.com/get-all-players-for-league/nba"
    )
    players = players_response.json()
    players = players["players"]
    with open(data_DIR + "NBA.json", "w") as outfile:
        json.dump(players, outfile, indent=2)

