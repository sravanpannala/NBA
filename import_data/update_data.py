# Update pbp data
import os, sys
from itertools import product, chain
import time
import datetime as dt

sys.setrecursionlimit(10000)

import numpy as np
import pandas as pd
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_fixed, Retrying
from thefuzz import fuzz, process
import zstandard as zstd
import dill
from bs4 import BeautifulSoup
import requests
import json

from nba_api.stats.endpoints import leaguegamelog, boxscoreadvancedv3
from nba_api.stats.endpoints import boxscorefourfactorsv3, boxscorescoringv3
from nba_api.stats.endpoints import boxscoreplayertrackv3, boxscoremiscv3
from nba_api.stats.endpoints import boxscorehustlev2, shotchartdetail
from nba_api.stats.endpoints import playerdashptshots, leaguedashplayerstats
from nba_api.stats.endpoints import leaguedashplayerptshot

from pbpstats.client import Client
from pbpstats.resources.enhanced_pbp import FieldGoal

os.environ["R_HOME"] = "C:\\Program Files\\R\\R-4.3.2\\"
from rpy2.robjects.packages import importr
import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri

pd.options.mode.chained_assignment =  None

home_DIR = "C:/Users/pansr/Documents/NBA/"
data_DIR_box = home_DIR + "data/boxscores_team/"
data_DIR_shot = home_DIR + "data/ShotLocationData/"
export_DIR = home_DIR + "data/"

csv_export_DIR = "C:/Users/pansr/Documents/repos/csv/"

# Update PBP Data
data_provider = "data_nba"
pbp_DIR = home_DIR + "pbpdata/" + data_provider


with open(export_DIR + "NBA.json") as f:
    data = json.load(f)
pID_dict = {v: int(k) for k, v in data.items()}
player_dict = {int(k): v for k, v in data.items()}


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
        for final_game in season.games.final_games:
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


@retry(stop=stop_after_attempt(5), wait=wait_fixed(0.6))
def get_game_box(game_id, fun):
    try:
        stats = fun(game_id=game_id)
        df = stats.get_data_frames()[1]
    except Exception as error:
        print(error)
    return df


def get_games_box(game_ids, fun):
    df_ap = []
    for game_id in tqdm(game_ids):
        df = get_game_box(game_id, fun)
        df_ap.append(df)
    return df_ap


def get_boxscores(seasons, fun, name):
    for season in seasons:
        print(season)
        game_ids, dfr = get_gameids(season, name)
        try:
            df_ap = get_games_box(game_ids, fun)
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


def update_player_boxscores(seasons, measure="Base", n=32):
    if measure == "Advanced":
        per_mode = "Per100Possessions"
    else:
        per_mode = "PerGame"
    for season in seasons:
        season_str = season + "-" + str(int(season) + 1)[-2:]
        stats = leaguedashplayerstats.LeagueDashPlayerStats(
            measure_type_detailed_defense=measure,
            per_mode_detailed=per_mode,
            season=season_str,
        )
        df1 = stats.get_data_frames()[0]
        df = df1.iloc[:, :n]
        df.to_parquet(
            export_DIR
            + "boxscores_player/"
            + f"NBA_Player_BoxScores_{measure}_"
            + season
            + ".parquet"
        )


def update_individual_boxscores(seasons):
    for season in seasons:
        print(season)
        stats = leaguegamelog.LeagueGameLog(
            player_or_team_abbreviation="P",
            season=season,
            season_type_all_star="Regular Season",
        )
        df = stats.get_data_frames()[0]
        df.to_parquet(
            export_DIR
            + "boxscores_player/"
            + "NBA_Player_BoxScores_"
            + "Indv"
            + "_"
            + season
            + ".parquet"
        )


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
                export_DIR + "shots/" + f"{league}_Shots_{season}_{d}.parquet"
            )


def update_shot_dash_all(seasons):
    league, league_id = "NBA", "00"
    general_range = ["Catch and Shoot", "Pull Ups", "Less than 10 ft", "Other"]
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
            for i in Retrying(stop=stop_after_attempt(5), wait=wait_fixed(0.6)):
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
                    break
                except Exception as error:
                    print(error)
                    continue
        dfa1 = [df2 for df2 in dfa if not df2.empty]
        df = pd.concat(dfa1)
        df.to_parquet(export_DIR + "shots/" + f"{league}_Shots_{season}_All.parquet")


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
    if df["clock"].dtype == 'O':
        mask = ~df["clock"].str.contains('\.')
        df.loc[mask,"clock"] = df.loc[mask,"clock"].apply(lambda x: x + ".0")
        df["clock"] = pd.to_datetime(df["clock"],format="%M:%S.%f").dt.time
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
        "dir": pbp_DIR ,
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
        "dir": pbp_DIR ,
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
    data_provider = "data_nba"
    league = "NBA"
    season_type = "Regular Season"
    for season in seasons:
        games_id = pbp_season(
            league=league,
            season_yr=season,
            season_type=season_type,
            data_provider=data_provider,
        )
        games_list = pbp_games(games_id, data_provider=data_provider)
        print("Compressing PBP Data")
        filename = export_DIR + "pbpdata/" + league + "_PBPdata_" + season + ".pkl.zst"
        print(filename)
        with zstd.open(filename, "wb") as f:
            dill.dump(games_list, f)
        data = get_loc_data(games_list, player_dict)
        data = set_dtypes(data)
        data.to_parquet(data_DIR_shot + f"{league}_Shot_Loc_" + season + ".parquet")


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
        shots.to_parquet(export_DIR + "ShotLocationData/" + f"NBA_Shot_Details_{season}.parquet")
        time.sleep(0.6)


def get_missing_pId(player, player_dict):
    pId = process.extract(player, player_dict, scorer=fuzz.partial_ratio, limit=1)[0][2]
    return pId


def update_injury_data():
    header = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }

    try:
        df0 = pd.read_parquet(
            export_DIR + "injuries/" + "NBA_prosptran_injuries_2023.parquet"
        )
        start_date = (df0["Date"].iloc[-1] + dt.timedelta(days=-1)).strftime("%Y-%m-%d")
    except:
        df0 = pd.DataFrame()
        start_date = "2023-07-01"

    print(start_date)
    url = f"https://www.prosportstransactions.com/basketball/Search/SearchResults.php?Player=&Team=&BeginDate={start_date}&EndDate=&ILChkBx=yes&InjuriesChkBx=yes&PersonalChkBx=yes&Submit=Search"

    response = requests.get(url)
    print(response)  # Response [200] means it went through
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
        one_a_tag = soup.findAll("a")[i]
        link = one_a_tag["href"]
        download_url = "https://www.prosportstransactions.com/basketball/Search/" + link
        dfs = pd.read_html(download_url, storage_options=header)
        df = dfs[0]
        df.drop([0], inplace=True)
        df[2] = df[2].str[2:]  # "Acquired" column
        df[3] = df[3].str[2:]  # "Relinquished" column
        df.columns = ["Date", "Team", "Acquired", "Relinquished", "Notes"]
        time.sleep(0.5)
        dfa.append(df)

    df1 = pd.concat(dfa)
    df = df1.copy()
    acq = df["Acquired"]
    rel = df["Relinquished"]
    df["Acquired"] = np.where(acq.str.contains("/"), acq.str.split("/ ").str[1], acq)
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
    df["playerID"] = df["Player"].map(pID_dict)
    df1 = df.copy()
    df1["playerID"][df["playerID"].isna()] = df["Player"][df["playerID"].isna()].apply(
        lambda x: get_missing_pId(x, player_dict)
    )
    df1["playerID"] = df1["playerID"].astype(int)
    df1["Date"] = pd.to_datetime(df1["Date"], format="%Y-%m-%d")
    df1.insert(2, "playerID", df1.pop("playerID"))
    df2 = pd.concat([df0, df1]).reset_index(drop=True)
    df3 = df2[~df2.duplicated(keep="last")].reset_index(drop=True)
    df3.to_csv(
        export_DIR + "injuries/" + "NBA_prosptran_injuries_2023.csv", index=False
    )
    df3.to_parquet(export_DIR + "injuries/" + "NBA_prosptran_injuries_2023.parquet")
    df3.to_csv(csv_export_DIR + "NBA_prosptran_injuries_2023.csv", index=False)


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
    df1.to_csv(export_DIR + "all_in_one_metrics/" + "NBA_DARKO_Current.csv")
    df1.to_parquet(export_DIR + "all_in_one_metrics/" + "NBA_DARKO_Current.parquet")
    df2 = dfa[1]
    df2 = df2.rename(columns={"nba_id": "idPlayerNBA", "player_name": "namePlayer"})
    df2.to_csv(export_DIR + "all_in_one_metrics/" + "NBA_DARKO_History.csv")
    df2.to_parquet(export_DIR + "all_in_one_metrics/" + "NBA_DARKO_History.parquet")
    df3 = dfa[2]
    df3 = df3.rename(columns={"nba_id": "idPlayerNBA", "player_name": "namePlayer"})
    df3.to_csv(export_DIR + "all_in_one_metrics/" + "NBA_DARKO_BoxScore_Talent.csv")
    df3.to_parquet(
        export_DIR + "all_in_one_metrics/" + "NBA_DARKO_BoxScore_Talent.parquet"
    )
    df4 = dfa[3]
    df4 = df4.rename(columns={"nba_id": "idPlayerNBA", "player_name": "namePlayer"})
    df4.to_csv(export_DIR + "all_in_one_metrics/" + "NBA_DARKO_Time_Decay_RAPM.csv")
    df4.to_parquet(
        export_DIR + "all_in_one_metrics/" + "NBA_DARKO_Time_Decay_RAPM.parquet"
    )
    df5 = dfa[4]
    df5 = df5.rename(columns={"nba_id": "idPlayerNBA", "player_name": "namePlayer"})
    df5.to_csv(
        export_DIR + "all_in_one_metrics/" + "NBA_DARKO_Time_Decay_RAPM_Pace.csv"
    )
    df5.to_parquet(
        export_DIR + "all_in_one_metrics/" + "NBA_DARKO_Time_Decay_RAPM_Pace.parquet"
    )


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
            return_message=True,
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
        bpm.to_csv(export_DIR + "bbref/" + f"NBA_bbref_Player_Adv_{season}.csv")
        bpm.to_parquet(export_DIR + "bbref/" + f"NBA_bbref_Player_Adv_{season}.parquet")
        time.sleep(5)


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

season_start = 2023
season_end = 2024
seasons = np.arange(season_start, season_end, 1).astype(str)

# Update pbp Data
update_pbp(seasons)

# Update Boxscores
print("Update Standard Boxscores")
update_standard_boxscores(seasons)

# Update Team Boxscores
for boxscore in boxscores:
    print("BoxScore " + boxscore["name"])
    get_boxscores(seasons, boxscore["fun"], boxscore["name"])

# Update Individual Player Boxscores
print("Update Player Boxscores")
update_individual_boxscores(seasons)
update_player_boxscores(seasons, measure="Base", n=32)
update_player_boxscores(seasons, measure="Advanced", n=43)
update_player_boxscores(seasons, measure="Misc", n=23)
update_player_boxscores(seasons, measure="Scoring", n=29)

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
update_injury_data()

# Update DARKO
print("Update DARKO")
update_DARKO()

# Update bbref advanced stats
print("Update bbref")
update_bbref(seasons)
