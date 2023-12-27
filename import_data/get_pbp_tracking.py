import requests
import pandas as pd
import numpy as np
import time
from io import StringIO

from update_data_V1 import data_DIR

track_DIR = data_DIR + "tracking/"

token_headers = {"Content-Type": "application/json"}
payload = {"username": "tracking_read_only", "password": "0YfUDRfUYb2Tr8dS"}
token_request = requests.post("https://tracking.pbpstats.com/auth", headers=token_headers, json=payload)
access_token = token_request.json()["access_token"]
headers = {"Authorization": f"JWT {access_token}"}


def update_pbp_tracking(seasons):
    for season in seasons:
        season_str = season + "-" + str(int(season)+1)[-2:]
        params = {"Season": season_str, "SeasonType": "RegularSeason", "Type": "game_logs"}
        tracking_csv = requests.get("https://tracking.pbpstats.com/get-tracking-csv", params=params, headers=headers)
        txt = StringIO(tracking_csv.text)
        df = pd.read_csv(txt)
        df.to_csv(track_DIR + f"NBA_PBP_Tracking_{season}.csv")
        df.to_parquet(track_DIR + f"NBA_PBP_Tracking_{season}.parquet")
        time.sleep(1)



