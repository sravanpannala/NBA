
import time
import datetime as dt
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import requests
from thefuzz import fuzz, process
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_fixed, Retrying

from rpy2.robjects.packages import importr
import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri

from update_data_V1 import data_DIR, player_dict, pID_dict, csv_export_DIR

injury_DIR = data_DIR + "injuries/"
aio_DIR = data_DIR + "all_in_one_metrics/"
bbref_DIR = data_DIR + "bbref/"

def get_missing_pId(player, player_dict):
    pId = process.extract(player, player_dict, scorer=fuzz.partial_ratio, limit=1)[0][2]
    return pId


def update_injury_data(seasons):
    for season in seasons:
        year = int(season)
        header = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
        }
        start_date = f"{year}-07-01"
        end_date = f"{year+1}-06-30"
        try:
            # raise Exception
            df0 = pd.read_parquet(
                injury_DIR + f"NBA_prosptran_injuries_{year}.parquet"
            )
            start_date = (df0["Date"].iloc[-1] + dt.timedelta(days=-1)).strftime(
                "%Y-%m-%d"
            )
        except:
            df0 = pd.DataFrame()

        print(start_date)
        url = f"https://www.prosportstransactions.com/basketball/Search/SearchResults.php?Player=&Team=&BeginDate={start_date}&EndDate={end_date}&ILChkBx=yes&InjuriesChkBx=yes&PersonalChkBx=yes&Submit=Search"

        response = requests.get(url)
        # print(response) # Response [200] means it went through
        soup = BeautifulSoup(response.text, "html.parser")
        df_first_page = pd.read_html(url, storage_options=header)
        df_first_page = df_first_page[0]
        df_first_page.drop([0], inplace=True)
        df_first_page[2] = df_first_page[2].str[2:]  # "Acquired" column
        df_first_page[3] = df_first_page[3].str[2:]  # "Relinquished" column
        df_first_page.columns = ["Date", "Team", "Acquired", "Relinquished", "Notes"]
        dfa = []
        dfa.append(df_first_page)
        for i in tqdm(range(4, len(soup.findAll("a")) - 4)):  #'a' tags are for links
            for kk in Retrying(wait=wait_fixed(5)):
                try:
                    tic = time.perf_counter()
                    one_a_tag = soup.findAll("a")[i]
                    link = one_a_tag["href"]
                    download_url = (
                        "https://www.prosportstransactions.com/basketball/Search/"
                        + link
                    )
                    # print(download_url)
                    dfs = pd.read_html(download_url, storage_options=header)
                    df = dfs[0]
                    df.drop([0], inplace=True)
                    df[2] = df[2].str[2:]  # "Acquired" column
                    df[3] = df[3].str[2:]  # "Relinquished" column
                    df.columns = ["Date", "Team", "Acquired", "Relinquished", "Notes"]
                    toc = time.perf_counter()
                    if (toc - tic) > 10:
                        raise Exception("Website Timeout")
                    time.sleep(0.2)
                    dfa.append(df)
                    break
                except Exception as error:
                    print(download_url)
                    print(error)
                    continue

        df1 = pd.concat(dfa)
        df = df1.copy()
        acq = df["Acquired"]
        rel = df["Relinquished"]
        df["Acquired"] = np.where(
            acq.str.contains("/"), acq.str.split("/ ").str[1], acq
        )
        df["Relinquished"] = np.where(
            rel.str.contains("/"), rel.str.split("/ ").str[1], rel
        )

        # Remove instances where value is like "(some text)"
        df["Acquired"] = df.Acquired.str.replace(r"[\(\[].*?[\)\]]", "")
        df["Relinquished"] = df.Relinquished.str.replace(r"[\(\[].*?[\)\]]", "")
        df["In"] = ~df["Acquired"].isna()
        df["Out"] = ~df["Relinquished"].isna()
        df["Player"] = (df["Acquired"] * ~df["Acquired"].isna()).fillna("") + (
            df["Relinquished"] * ~df["Relinquished"].isna()
        ).fillna("")
        df = df[["Date", "Team", "Player", "In", "Out", "Notes"]]
        df = df[df["Player"].str.istitle()].reset_index(drop=True)
        df["Player"].loc[df["Player"].str.contains("Enes")] = "Enes Kanter"
        df["playerID"] = df["Player"].map(pID_dict)
        df1 = df.copy()
        df1["playerID"][df["playerID"].isna()] = df["Player"][
            df["playerID"].isna()
        ].apply(lambda x: get_missing_pId(x, player_dict))
        df1["playerID"] = df1["playerID"].astype(int)
        df1["Date"] = pd.to_datetime(df1["Date"], format="%Y-%m-%d")
        df1.insert(2, "playerID", df1.pop("playerID"))
        df2 = pd.concat([df0, df1]).reset_index(drop=True)
        df3 = df2[~df2.duplicated(keep="last")].reset_index(drop=True)
        df3.to_csv(csv_export_DIR + f"NBA_prosptran_injuries_{year}.csv", index=False)
        df3.to_parquet(
            injury_DIR + f"NBA_prosptran_injuries_{year}.parquet"
        )


def update_DARKO():
    sheet = "1mhwOLqPu2F9026EQiVxFPIN1t9RGafGpl-dokaIsm9c"
    sheet_ids = [1064086941, 142925152, 284274620, 923517192, 1503564342]
    dfa = []
    for sheet_id in sheet_ids:
        url = f"https://docs.google.com/spreadsheets/d/{sheet}/gviz/tq?tqx=out:csv&gid={sheet_id}"
        df = pd.read_csv(url)
        dfa.append(df)
        time.sleep(0.5)
    df1 = dfa[0]
    df1.columns = [
        "idPlayerNBA",
        "namePlayer",
        "position",
        "age",
        "dpm",
        "o_dpm",
        "d_dpm",
        "box_odpm",
        "box_ddpm",
        "on_off_odpm",
        "on_off_ddpm",
    ]
    df1.to_parquet(aio_DIR + "NBA_DARKO_Current.parquet")
    df2 = dfa[1]
    df2 = df2.rename(columns={"nba_id": "idPlayerNBA", "player_name": "namePlayer"})
    df2.to_parquet(aio_DIR + "NBA_DARKO_History.parquet")
    df3 = dfa[2]
    df3 = df3.rename(columns={"nba_id": "idPlayerNBA", "player_name": "namePlayer"})
    df3.to_parquet(
        aio_DIR + "NBA_DARKO_BoxScore_Talent.parquet"
    )
    df4 = dfa[3]
    df4 = df4.rename(columns={"nba_id": "idPlayerNBA", "player_name": "namePlayer"})
    df4.to_parquet(
        aio_DIR + "NBA_DARKO_Time_Decay_RAPM.parquet"
    )
    df5 = dfa[4]
    df5 = df5.rename(columns={"nba_id": "idPlayerNBA", "player_name": "namePlayer"})
    df5.to_parquet(aio_DIR + "NBA_DARKO_Time_Decay_RAPM_Pace.parquet")


def update_bbref(seasons):
    for season in seasons:
        season1 = str(int(season) + 1)
        nbastatR = importr("nbastatR")
        robjects.r(
            """
                Sys.setenv("VROOM_CONNECTION_SIZE" = 131072 * 2)
            """
        )
        r_df = nbastatR.bref_players_stats(
            seasons=season1,
            tables="advanced",
            include_all_nba=False,
            only_totals=False,
            nest_data=False,
            assign_to_environment=True,
            widen_data=True,
            join_data=True,
            return_message=False,
        )
        with (robjects.default_converter + pandas2ri.converter).context():
            bpm = robjects.conversion.get_conversion().rpy2py(r_df)
        vars = [
            "urlPlayerThumbnail",
            "urlPlayerHeadshot",
            "urlPlayerPhoto",
            "urlPlayerStats",
            "urlPlayerActionPhoto",
        ]
        bpm[vars] = bpm[vars].astype(str)
        # bpm.to_csv(bbref_DIR + f"NBA_bbref_P_Adv_{season}.csv")
        bpm.to_parquet(bbref_DIR + f"NBA_bbref_P_Adv_{season}.parquet")
        time.sleep(5)