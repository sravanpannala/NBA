import json
import requests
import time
import numpy as np
import pandas as pd
from tqdm import tqdm

from update_data import data_DIR, teams_dict, player_dict

box_DIR = data_DIR + "box/"
shiny_DIR = data_DIR + "shiny/"
track_DIR = data_DIR + "tracking/"
injury_DIR = data_DIR + "injuries/"
aio_DIR = data_DIR + "all_in_one_metrics/"
shiny_export_DIR1 = "C:/Users/pansr/Documents/shinyNBA/data/"
shiny_export_DIR2 = "C:/Users/pansr/Documents/shinyNBA-export/"

cols1 = ['PLAYER_ID', 'PLAYER_NAME', 'TEAM_ID', 'TEAM_ABBREVIATION', 'GAME_ID', 'GAME_DATE','MIN', 'FGM',
       'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT', 'FTM', 'FTA', 'FT_PCT',
       'OREB', 'DREB', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS', 'PLUS_MINUS']
cols2 = ['gameId', 'teamId', 'personId',"position",'estimatedOffensiveRating', 'offensiveRating',
       'estimatedDefensiveRating', 'defensiveRating', 'estimatedNetRating',
       'netRating', 'assistPercentage', 'assistToTurnover', 'assistRatio',
       'offensiveReboundPercentage', 'defensiveReboundPercentage',
       'reboundPercentage', 'turnoverRatio', 'effectiveFieldGoalPercentage',
       'trueShootingPercentage', 'usagePercentage', 'estimatedUsagePercentage',
       'estimatedPace', 'pace', 'pacePer40', 'possessions', 'PIE']
cols3 = ['game_id', 'player_id', 'team_id',
       'off_poss', 'def_poss', 'drives', 'drive_fgm', 'drive_fga', 'drive_ftm',
       'drive_fta', 'drive_points', 'drive_passes', 'drive_assists',
       'drive_turnovers', 'drive_fouls', 'passes_made', 'passes_received',
       'ft_assists', 'secondary_assists', 'potential_assists',
       'adj_assists', 'assist_pts', 'def_rim_fgm',
       'def_rim_fga', 'touches', 'front_court_touches', 'time_of_poss',
       'seconds_per_touch', 'dribbles_per_touch', 'elbow_touches',
       'elbow_touch_fgm', 'elbow_touch_fga', 'elbow_touch_ftm',
       'elbow_touch_fta', 'elbow_touch_points', 'elbow_touch_passes',
       'elbow_touch_assists', 'elbow_touch_turnovers', 'elbow_touch_fouls',
       'paint_touches', 'paint_touch_fgm', 'paint_touch_fga',
       'paint_touch_ftm', 'paint_touch_fta', 'paint_touch_points',
       'paint_touch_passes', 'paint_touch_assists', 'paint_touch_turnovers',
       'paint_touch_fouls', 'post_touches', 'post_touch_fgm', 'post_touch_fga',
       'post_touch_ftm', 'post_touch_fta', 'post_touch_points',
       'post_touch_passes', 'post_touch_assists', 'post_touch_turnovers',
       'post_touch_fouls', 'oreb_contest', 'oreb_uncontest',
       'oreb_chances', 'oreb_chance_defer', 'dreb_contest',
       'dreb_uncontest', 'dreb_chances', 'dreb_chance_defer', 'feet', 'miles',
       'miles_off', 'miles_def', 'avg_speed', 'avg_speed_off',
       'avg_speed_def']

def export_player_distribution():
    dfa = []
    for season in [2023]:
        year = int(season)
    # for year in tqdm(range(2004,2024)):
        season = str(year)
        df1 = pd.read_parquet(box_DIR + "NBA_Box_P_" + "Base_"  + season + ".parquet", columns = cols1)
        df1["GAME_ID"] = df1["GAME_ID"].astype(int)
        df2 = pd.read_parquet(box_DIR + "NBA_Box_P_" + "Adv_"  + season + ".parquet", columns = cols2)
        dfm1 = pd.merge(df1,df2,left_on=['PLAYER_ID','TEAM_ID','GAME_ID'], right_on=['personId', 'teamId','gameId'], how="left")
        df3 = pd.read_parquet(track_DIR + "NBA_PBP_" + "Tracking_"  + season + ".parquet", columns = cols3)
        dfm = pd.merge(dfm1,df3,left_on=['PLAYER_ID','TEAM_ID','GAME_ID'], right_on=['player_id', 'team_id','game_id'], how="left")
        dfm = dfm.fillna(0)
        dfm = dfm.drop(columns=['player_id', 'team_id','game_id'])
        dfm["Season"] = year +1
        dfg = dfm.groupby("PLAYER_ID")
        keys = list(dfg.groups)
        for key in keys:
            dfgg = dfg.get_group(key)
            dfgg = dfgg.reset_index(drop=True).reset_index()
            dfgg = dfgg.rename(columns={"index":"Games Played"})
            dfgg["Games Played"] +=1
            dfa.append(dfgg)
    dfa1 = [df2 for df2 in dfa if not df2.empty]
    df = pd.concat(dfa1)
    df = df.reset_index(drop=True)
    df[df.columns[53:76]]  = df[df.columns[53:76]].astype(int)
    df[df.columns[79:118]] = df[df.columns[79:118]].astype(int)
    df1 = df.copy()
    df1 = df1.rename(columns=str.title)
    df1 = df1.rename(columns={"Player_Name":"Player"})
    df1["Player Season"] = df1["Season"].astype(str) + " " + df1["Player"]
    df1.columns = df1.columns.str.replace("Fg","FG")
    df1.columns = df1.columns.str.replace("Ft","FT")
    df1.columns = df1.columns.str.replace("Id","ID")
    df1.columns = df1.columns.str.replace("rating","Rtg")
    df1.columns = df1.columns.str.replace("ratio","_Ratio")
    df1.columns = df1.columns.str.replace("rebound","Reb")
    df1.columns = df1.columns.str.replace("Rebound","Reb")
    df1.columns = df1.columns.str.replace("shooting","Shooting")
    df1.columns = df1.columns.str.replace("percentage","Pct")
    df1.columns = df1.columns.str.replace("turnover","Tov")
    df1.columns = df1.columns.str.replace("Turnover","Tov")
    df1.columns = df1.columns.str.replace("Offensive","O")
    df1.columns = df1.columns.str.replace("Defensive","D")
    df1.columns = df1.columns.str.replace("Assist","Ast")
    df1.columns = df1.columns.str.replace("Effectivefieldgoal","eFG")
    df1.columns = df1.columns.str.replace("TrueShooting","TS")
    df1.columns = df1.columns.str.replace("Usage","USG")
    df1.columns = df1.columns.str.replace("_Pct","Pct")
    # df1.columns = df1.columns.str.replace("Pct","_Pct")
    df1.columns = df1.columns.str.replace("Pct","_%")
    df1.columns = df1.columns.str.replace("Dreb","DReb")
    df1.columns = df1.columns.str.replace("Oreb","OReb")
    df1.columns = df1.columns.str.replace("FGa","FGA")
    df1.columns = df1.columns.str.replace("FGm","FGM")
    df1.columns = df1.columns.str.replace("FTa","FTA")
    df1.columns = df1.columns.str.replace("FTm","FTM")
    df1.columns = df1.columns.str.replace("_"," ")
    df1 = df1.rename(columns={
            "Pf":"PF", "Wl":"WL","Pie":"PIE","AsttoTov":"Ast/Tov","Possessions":"Poss",
        }
    )
    df1 = df1.drop(columns=['Gameid', 'Teamid', 'Personid','Position', 'Paceper40'])
    df1["Extra Possessions"] = df1["OReb"] - (df1["FGA"]-df1["FGM"]) - df1["Tov"]
    df1["TSA"] = df1["FGA"] + 0.44*df1["FTA"]
    cols = df1.columns
    df1 = df1.drop( columns = cols[cols.str.contains("Estimated")])
    df1 = df1.fillna(0)
    df1 = df1[df1["Pace"] > 60]
    df1 = df1.sort_values(by=["Player","Game Date"]).reset_index(drop=True)
    # df1.to_parquet(shiny_DIR + "NBA_Player_Distribution.parquet")
    # df1.to_parquet(shiny_export_DIR1 + "NBA_Player_Distribution.parquet")
    # df1.to_parquet(shiny_export_DIR2 + "NBA-Distributions/" + "NBA_Player_Distribution.parquet")
    df2 = pd.read_parquet(shiny_DIR + "NBA_Player_Distribution.parquet")
    df3 = pd.concat([df2,df1])
    df4 = df3[~df3.duplicated(subset=["Player ID","Team ID","Game ID"],keep="last")].reset_index(drop=True)
    df4.to_parquet(shiny_DIR + "NBA_Player_Distribution.parquet")
    df4.to_parquet(shiny_export_DIR1 + "NBA_Player_Distribution.parquet")
    df4.to_parquet(shiny_export_DIR2 + "NBA-Distributions/" + "NBA_Player_Distribution.parquet")

cols1t = ['TEAM_ID', 'TEAM_ABBREVIATION', 'TEAM_NAME', 'GAME_ID', 'GAME_DATE','MIN', 'FGM',
       'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT', 'FTM', 'FTA', 'FT_PCT',
       'OREB', 'DREB', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS', 'PLUS_MINUS']
cols2t = ['gameId', 'teamId','estimatedOffensiveRating', 'offensiveRating',
       'estimatedDefensiveRating', 'defensiveRating', 'estimatedNetRating',
       'netRating', 'assistPercentage', 'assistToTurnover', 'assistRatio',
       'offensiveReboundPercentage', 'defensiveReboundPercentage',
       'reboundPercentage', 'turnoverRatio', 'effectiveFieldGoalPercentage',
       'trueShootingPercentage', 'usagePercentage', 'estimatedUsagePercentage',
       'estimatedPace', 'pace', 'pacePer40', 'possessions', 'PIE']
cols3t = ['game_id', 'player_id', 'team_id',
       'off_poss', 'def_poss', 'drives', 'drive_fgm', 'drive_fga', 'drive_ftm',
       'drive_fta', 'drive_points', 'drive_passes', 'drive_assists',
       'drive_turnovers', 'drive_fouls', 'passes_made', 'passes_received',
       'ft_assists', 'secondary_assists', 'potential_assists',
       'adj_assists', 'assist_pts', 'def_rim_fgm',
       'def_rim_fga', 'touches', 'front_court_touches', 'time_of_poss',
       'seconds_per_touch', 'dribbles_per_touch', 'elbow_touches',
       'elbow_touch_fgm', 'elbow_touch_fga', 'elbow_touch_ftm',
       'elbow_touch_fta', 'elbow_touch_points', 'elbow_touch_passes',
       'elbow_touch_assists', 'elbow_touch_turnovers', 'elbow_touch_fouls',
       'paint_touches', 'paint_touch_fgm', 'paint_touch_fga',
       'paint_touch_ftm', 'paint_touch_fta', 'paint_touch_points',
       'paint_touch_passes', 'paint_touch_assists', 'paint_touch_turnovers',
       'paint_touch_fouls', 'post_touches', 'post_touch_fgm', 'post_touch_fga',
       'post_touch_ftm', 'post_touch_fta', 'post_touch_points',
       'post_touch_passes', 'post_touch_assists', 'post_touch_turnovers',
       'post_touch_fouls', 'oreb_contest', 'oreb_uncontest',
       'oreb_chances', 'oreb_chance_defer', 'dreb_contest',
       'dreb_uncontest', 'dreb_chances', 'dreb_chance_defer', 'feet', 'miles',
       'miles_off', 'miles_def', 'avg_speed', 'avg_speed_off',
       'avg_speed_def']

def export_team_distribution():
    dfa = []
    for season in [2023]:
        year = int(season)
    # for year in tqdm(range(2004,2024)):
        season = str(year)
        df1 = pd.read_parquet(box_DIR + "NBA_Box_T_" + "Base_"  + season + ".parquet", columns=cols1t)
        df1["GAME_ID"] = df1["GAME_ID"].astype(int)
        df2 = pd.read_parquet(box_DIR + "NBA_Box_T_" + "Adv_"  + season + ".parquet", columns=cols2t)
        dfm1 = pd.merge(df1,df2,left_on=['TEAM_ID','GAME_ID'], right_on=['teamId','gameId'], how="left")
        df3 = pd.read_parquet(track_DIR + "NBA_PBP_" + "Tracking_"  + season + ".parquet", columns = cols3t)
        df3s = df3.groupby(["game_id","team_id"]).sum()
        df3s = df3s.drop(columns=['player_id','off_poss','def_poss','touches', 'front_court_touches', 'time_of_poss',
            'seconds_per_touch', 'dribbles_per_touch','feet', 'miles', 'miles_off', 'miles_def',
            'avg_speed', 'avg_speed_off', 'avg_speed_def'])
        df3s = df3s.reset_index()
        dfm = pd.merge(dfm1,df3s,left_on=['TEAM_ID','GAME_ID'], right_on=['team_id','game_id'], how="left")
        dfm = dfm.fillna(0)
        dfm = dfm.drop(columns=['team_id','game_id','gameId', 'teamId','MIN'])
        dfm["Season"] = year +1
        dfg = dfm.groupby("TEAM_ID")
        keys = list(dfg.groups)
        for key in keys:
            dfgg = dfg.get_group(key)
            dfgg = dfgg.reset_index(drop=True).reset_index()
            dfgg = dfgg.rename(columns={"index":"Games Played"})
            dfgg["Games Played"] +=1
            dfa.append(dfgg)
    dfa1 = [df2 for df2 in dfa if not df2.empty]
    df = pd.concat(dfa1)
    df = df.reset_index(drop=True)
    df[df.columns[47:]] = df[df.columns[47:]].astype(int)
    df1 = df.copy()
    df1 = df1.rename(columns=str.title)
    df1 = df1.rename(columns={"Team_Name":"Team"})
    df1["Team Season"] = df1["Season"].astype(str) + " " + df1["Team"]
    df1.columns = df1.columns.str.replace("Fg","FG")
    df1.columns = df1.columns.str.replace("Ft","FT")
    df1.columns = df1.columns.str.replace("Id","ID")
    df1.columns = df1.columns.str.replace("rating","Rtg")
    df1.columns = df1.columns.str.replace("ratio","_Ratio")
    df1.columns = df1.columns.str.replace("rebound","Reb")
    df1.columns = df1.columns.str.replace("Rebound","Reb")
    df1.columns = df1.columns.str.replace("shooting","Shooting")
    df1.columns = df1.columns.str.replace("percentage","Pct")
    df1.columns = df1.columns.str.replace("turnover","Tov")
    df1.columns = df1.columns.str.replace("Turnover","Tov")
    df1.columns = df1.columns.str.replace("Offensive","O")
    df1.columns = df1.columns.str.replace("Defensive","D")
    df1.columns = df1.columns.str.replace("Assist","Ast")
    df1.columns = df1.columns.str.replace("Effectivefieldgoal","eFG")
    df1.columns = df1.columns.str.replace("TrueShooting","TS")
    df1.columns = df1.columns.str.replace("Usage","USG")
    df1.columns = df1.columns.str.replace("_Pct","Pct")
    # df1.columns = df1.columns.str.replace("Pct","_Pct")
    df1.columns = df1.columns.str.replace("Pct","_%")
    df1.columns = df1.columns.str.replace("Dreb","DReb")
    df1.columns = df1.columns.str.replace("Oreb","OReb")
    df1.columns = df1.columns.str.replace("FGa","FGA")
    df1.columns = df1.columns.str.replace("FGm","FGM")
    df1.columns = df1.columns.str.replace("FTa","FTA")
    df1.columns = df1.columns.str.replace("FTm","FTM")
    df1.columns = df1.columns.str.replace("_"," ")
    df1 = df1.rename(columns={
            "Pf":"PF", "Wl":"WL","Pie":"PIE","AsttoTov":"Ast/Tov","Possessions":"Poss",
        }
    )
    df1 = df1.drop(columns=['Paceper40'])
    df1["Extra Possessions"] = df1["OReb"] - (df1["FGA"]-df1["FGM"]) - df1["Tov"]
    df1["TSA"] = df1["FGA"] + 0.44*df1["FTA"]
    cols = df1.columns
    df1 = df1.drop( columns = cols[cols.str.contains("Estimated")])
    df1 = df1.fillna(0)
    df1 = df1[df1["Pace"] > 60]
    df1["Team"] = df1["Team ID"].map(teams_dict)
    df1 = df1.sort_values(by=["Team","Game Date"]).reset_index(drop=True)
    # df1.to_parquet(shiny_DIR + "NBA_Team_Distribution.parquet")
    # df1.to_parquet(shiny_export_DIR1 + "NBA_Team_Distribution.parquet")
    # df1.to_parquet(shiny_export_DIR2 + "NBA-Distributions/" + "NBA_Team_Distribution.parquet")
    df2 = pd.read_parquet(shiny_DIR + "NBA_Team_Distribution.parquet")
    df3 = pd.concat([df2,df1])
    df4 = df3[~df3.duplicated(subset=["Team ID","Game ID"],keep="last")].reset_index(drop=True)
    df4.to_parquet(shiny_DIR + "NBA_Team_Distribution.parquet")
    df4.to_parquet(shiny_export_DIR1 + "NBA_Team_Distribution.parquet")

def get_scorigami_data():
    dfa = []
    for year in range(1996,2024):
        season = str(year)
        df1 = pd.read_parquet(box_DIR + "NBA_Box_P_" + "Base_"  + season + ".parquet", columns = cols1)
        df2 = pd.read_parquet(box_DIR + "NBA_Box_P_" + "Base_"  + season + "_PS.parquet", columns = cols1)
        dfa.append(df1)
        dfa.append(df2)
    dfa1 = [df2 for df2 in dfa if not df2.empty]
    df = pd.concat(dfa1)
    df = df.rename(columns=str.title)
    df = df.rename(columns={"Player_Name":"Player",'Player_Id':'Player ID'})
    df = df.reset_index(drop=True)

    df1 = df.copy()
    df1["Pts_cat"] = 0
    idx = df1.index[((df1["Pts"] >= 10) & (df1["Pts"] < 20))].tolist()
    df1["Pts_cat"].loc[idx] = 1
    idx = df1.index[((df1["Pts"] >= 20) & (df1["Pts"] < 30))].tolist()
    df1["Pts_cat"].loc[idx] = 2
    idx = df1.index[((df1["Pts"] >= 30) & (df1["Pts"] < 40))].tolist()
    df1["Pts_cat"].loc[idx] = 3
    idx = df1.index[(df1["Pts"] >= 40)].tolist()
    df1["Pts_cat"].loc[idx] = 4

    df1["Ast_cat"] = 0
    idx = df1.index[((df1["Ast"] > 0) & (df1["Ast"] < 5))].tolist()
    df1["Ast_cat"].loc[idx] = 1
    idx = df1.index[((df1["Ast"] >= 5) & (df1["Ast"] < 10))].tolist()
    df1["Ast_cat"].loc[idx] = 2
    idx = df1.index[((df1["Ast"] >= 10) & (df1["Ast"] < 15))].tolist()
    df1["Ast_cat"].loc[idx] = 3
    idx = df1.index[(df1["Ast"] >= 15)].tolist()
    df1["Ast_cat"].loc[idx] = 4

    df1["Reb_cat"] = 0
    idx = df1.index[((df1["Reb"] > 0) & (df1["Reb"] < 5))].tolist()
    df1["Reb_cat"].loc[idx] = 1
    idx = df1.index[((df1["Reb"] >= 5) & (df1["Reb"] < 10))].tolist()
    df1["Reb_cat"].loc[idx] = 2
    idx = df1.index[((df1["Reb"] >= 10) & (df1["Reb"] < 15))].tolist()
    df1["Reb_cat"].loc[idx] = 3
    idx = df1.index[(df1["Reb"] >= 15)].tolist()
    df1["Reb_cat"].loc[idx] = 4

    df1["Stl_cat"] = 0
    idx = df1.index[((df1["Stl"] > 0) & (df1["Stl"] < 3))].tolist()
    df1["Stl_cat"].loc[idx] = 1
    idx = df1.index[((df1["Stl"] >= 3) & (df1["Stl"] < 5))].tolist()
    df1["Stl_cat"].loc[idx] = 2
    idx = df1.index[((df1["Stl"] >= 5) & (df1["Stl"] < 7))].tolist()
    df1["Stl_cat"].loc[idx] = 3
    idx = df1.index[(df1["Stl"] >= 7)].tolist()
    df1["Stl_cat"].loc[idx] = 4

    df1["Blk_cat"] = 0
    idx = df1.index[((df1["Blk"] > 0) & (df1["Blk"] < 3))].tolist()
    df1["Blk_cat"].loc[idx] = 1
    idx = df1.index[((df1["Blk"] >= 3) & (df1["Blk"] < 5))].tolist()
    df1["Blk_cat"].loc[idx] = 2
    idx = df1.index[((df1["Blk"] >= 5) & (df1["Blk"] < 7))].tolist()
    df1["Blk_cat"].loc[idx] = 3
    idx = df1.index[(df1["Blk"] >= 7)].tolist()
    df1["Blk_cat"].loc[idx] = 4

    df1["Tov_cat"] = 0
    idx = df1.index[((df1["Tov"] > 0) & (df1["Tov"] < 3))].tolist()
    df1["Tov_cat"].loc[idx] = 1
    idx = df1.index[((df1["Tov"] >= 3) & (df1["Tov"] < 5))].tolist()
    df1["Tov_cat"].loc[idx] = 2
    idx = df1.index[((df1["Tov"] >= 5) & (df1["Tov"] < 7))].tolist()
    df1["Tov_cat"].loc[idx] = 3
    idx = df1.index[(df1["Tov"] >= 7)].tolist()
    df1["Tov_cat"].loc[idx] = 4

    df1["Fg3M_cat"] = 0
    idx = df1.index[((df1["Fg3M"] > 0) & (df1["Fg3M"] < 4))].tolist()
    df1["Fg3M_cat"].loc[idx] = 1
    idx = df1.index[((df1["Fg3M"] >= 4) & (df1["Fg3M"] < 7))].tolist()
    df1["Fg3M_cat"].loc[idx] = 2
    idx = df1.index[((df1["Fg3M"] >= 7) & (df1["Fg3M"] < 10))].tolist()
    df1["Fg3M_cat"].loc[idx] = 3
    idx = df1.index[(df1["Fg3M"] >= 10)].tolist()
    df1["Fg3M_cat"].loc[idx] = 4

    df1["Ftm_cat"] = 0
    idx = df1.index[((df1["Ftm"] > 0) & (df1["Ftm"] < 5))].tolist()
    df1["Ftm_cat"].loc[idx] = 1
    idx = df1.index[((df1["Ftm"] >= 5) & (df1["Ftm"] < 10))].tolist()
    df1["Ftm_cat"].loc[idx] = 2
    idx = df1.index[((df1["Ftm"] >= 10) & (df1["Ftm"] < 15))].tolist()
    df1["Ftm_cat"].loc[idx] = 3
    idx = df1.index[(df1["Ftm"] >= 15)].tolist()
    df1["Ftm_cat"].loc[idx] = 4

    df1["Pts_cat"] = df1["Pts_cat"].astype("category")
    df1["Ast_cat"] = df1["Ast_cat"].astype("category")
    df1["Reb_cat"] = df1["Reb_cat"].astype("category")
    df1["Stl_cat"] = df1["Stl_cat"].astype("category")
    df1["Blk_cat"] = df1["Blk_cat"].astype("category")
    df1["Tov_cat"] = df1["Tov_cat"].astype("category")
    df1["Fg3M_cat"] = df1["Fg3M_cat"].astype("category")
    df1["Ftm_cat"] = df1["Ftm_cat"].astype("category")

    Pts_cat = ["0 to 9", "10 to 19", "20 to 29", "30 to 39", "40+"]
    df1["Pts_cat"] = df1["Pts_cat"].cat.rename_categories(Pts_cat)
    Ast_cat = ["0", "1 to 4", "5 to 9", "10 to 14", "15+"]
    df1["Ast_cat"] = df1["Ast_cat"].cat.rename_categories(Ast_cat)
    Reb_cat = ["0", "1 to 4", "5 to 9", "10 to 14", "15+"]
    df1["Reb_cat"] = df1["Reb_cat"].cat.rename_categories(Reb_cat)
    Stl_cat = ["0", "1 to 2", "3 to 4", "5 to 6", "7+"]
    df1["Stl_cat"] = df1["Stl_cat"].cat.rename_categories(Stl_cat)
    Blk_cat = ["0", "1 to 2", "3 to 4", "5 to 6", "7+"]
    df1["Blk_cat"] = df1["Blk_cat"].cat.rename_categories(Blk_cat)
    Tov_cat = ["0", "1 to 2", "3 to 4", "5 to 6", "7+"]
    df1["Tov_cat"] = df1["Tov_cat"].cat.rename_categories(Tov_cat)
    Fg3M_cat = ["0", "1 to 3", "3 to 6", "7 to 9", "10+"]
    df1["Fg3M_cat"] = df1["Fg3M_cat"].cat.rename_categories(Fg3M_cat)
    Ftm_cat = ["0", "1 to 4", "5 to 9", "10 to 14", "15+"]
    df1["Ftm_cat"] = df1["Ftm_cat"].cat.rename_categories(Ftm_cat)
    df1 = df1.sort_values(by="Player").reset_index(drop=True)
    df1.to_parquet(shiny_DIR + "NBA_Player_Scorigami.parquet")

def export_lineups():
    teams_response = requests.get("https://api.pbpstats.com/get-teams/nba")
    teams = teams_response.json()
    teams_dict = teams["teams"]
    df_teams = pd.DataFrame(teams_dict)
    df_teams = df_teams.rename(columns={"text":"team"})
    teams_list = df_teams["id"].to_list()
    dfa = []
    for year in range(2023,2024):
        season = str(year) + '-' + str(year+1)[-2:]
        for team in tqdm(teams_list):
            url = "https://api.pbpstats.com/get-team-players-for-season?S"
            params = {
                "Season": season, # To get for multiple seasons, separate seasons by comma
                "SeasonType": "Regular Season",
                "TeamId": team,
            }
            response = requests.get(url, params=params)
            response_json = response.json()
            players = response_json["players"]
            df_players1 = pd.DataFrame.from_dict(players,orient="index",columns=["player"]).reset_index()
            df_players1 = df_players1.rename(columns={"index":"id"})
            df_players1["team"] = team
            df_players1["season"] = season
            time.sleep(0.1)
            dfa.append(df_players1)
    df_players = pd.concat(dfa)
    df_players = pd.merge(df_players,df_teams,left_on="team", right_on="id")
    df_players = df_players.rename(columns={"id_x":"pid","id_y":"tid","team_y":"team"})
    df_players = df_players.drop(columns=["team_x"]) 
    df_players.to_parquet(shiny_DIR + "lineup_data.parquet")
    df_players.to_parquet(shiny_export_DIR1 + "lineup_data.parquet")

def export_stat_query():
    dfa = []
    for year in range(1946,2024):
        df1 = pd.read_parquet(box_DIR + "NBA_Box_P_" + "Base" + "_" + str(year) + ".parquet")
        df1[df1["WL"] == 0]["WL"] = "L"
        df1["season"] = year+1
        df1 = df1.fillna(0)
        dfa.append(df1)
    df = pd.concat(dfa)
    df.loc[df[df["WL"] == 0].index,"WL"] = "L"
    df.to_parquet(box_DIR + "NBA_Box_P_" + "Base" + "_" + "All" + ".parquet")
    df.to_parquet(shiny_DIR + "NBA_Box_P_" + "Base" + "_" + "All" + ".parquet")
    # dfa = []
    # for year in range(1946,2024):
    #     df1 = pd.read_parquet(box_DIR + "NBA_Box_P_Lead_" + "Base" + "_" + str(year) + ".parquet")
    #     df1["season"] = year+1
    #     df1 = df1.fillna(0)
    #     dfa.append(df1)
    # dfa1 = [df2 for df2 in dfa if not df2.empty]
    # df = pd.concat(dfa1)
    # df.to_parquet(box_DIR + "NBA_Box_P_Lead_" + "Base" + "_" + "All" + ".parquet")
    # df.to_parquet(shiny_DIR + "NBA_Box_P_Lead_" + "Base" + "_" + "All" + ".parquet")
    # df.to_parquet(shiny_export_DIR1 + "NBA_Box_P_Lead_" + "Base" + "_" + "All" + ".parquet")
    cols_i = ['GP', 'W', 'L', 'MIN', 'FGM', 'FGA', 'FG_PCT', 
        'FG3M', 'FG3A', 'FG3_PCT', 'FTM', 'FTA', 'FT_PCT','OREB', 'DREB', 'REB', 
        'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS','PLUS_MINUS']
    dfa = []
    for year in [2023]:
        df1 = pd.read_parquet(box_DIR + "NBA_Box_P_" + "Base" + "_" + str(year) + ".parquet")
        df1 = df1.fillna(0)
        df1[df1["WL"] == 0]["WL"] = "L"
        df1g = df1.groupby(["PLAYER_ID","PLAYER_NAME","TEAM_ID","TEAM_NAME"])
        keys = list(df1g.groups)
        dfb = []
        for key in keys:
            dfi = df1g.get_group(key)
            dfi["GP"] = 1
            dfi["W"] = np.where(dfi["WL"] == "W",1,0)
            dfi["L"] = np.where(dfi["WL"] == "L",1,0)
            dfi1 = dfi[cols_i]
            dfii = pd.DataFrame(dfi1.sum()).T
            dfii.iloc[:,3:] = dfii.iloc[:,3:]/dfii["GP"][0]
            dfii.iloc[:,3:] = dfii.iloc[:,3:].round(2)
            dfii["FG_PCT"] = round(dfii["FGM"]/dfii["FGA"],3)
            dfii["FG3_PCT"] = round(dfii["FG3M"]/dfii["FG3A"],3)
            dfii["FT_PCT"] = round(dfii["FTM"]/dfii["FTA"],3)
            dfii[["PLAYER_ID", "PLAYER_NAME", "TEAM_ID", "TEAM_NAME"]] = list(key)
            dfb.append(dfii)
        dfb = pd.concat(dfb)
        dfb["season"] = year + 1
        dfa.append(dfb)
    dfa = pd.concat(dfa)
    df1 = dfa.replace([np.inf, -np.inf], np.nan)
    df1 = df1.fillna(0).reset_index(drop=True)
    df2 = pd.read_parquet(shiny_DIR + "NBA_Box_P_Cum_Base_All.parquet")
    df3 = pd.concat([df2,df1])
    df4 = df3[~df3.duplicated(subset=["PLAYER_ID","TEAM_ID","season"],keep="last")].reset_index(drop=True)
    df4.to_parquet(shiny_DIR + "NBA_Box_P_Cum_Base_All.parquet")
    df4.to_parquet(shiny_export_DIR1 + "NBA_Box_P_Cum_Base_All.parquet")
    

def is_injured(dfinj, pId_missed, game_date):
    missed_games = np.array([False] * len(pId_missed))
    for i,pId in enumerate(pId_missed):
        df_p = dfinj.query(f'playerID == {pId}').reset_index(drop=True)
        if len(df_p) > 0:
            df_p["Comp"] = df_p["Date"] <= game_date
            idxi = df_p[df_p["Comp"]].index
            if len(idxi) > 0:
                idx = idxi[-1]
                missed_game = df_p["Out"].loc[idx]
                missed_games[i] = missed_game
    gp = missed_games*pId_missed
    pId_m = gp[gp !=0 ]
    # pId_m = list(pId_m)
    return pId_m

def export_Games_Missed():
    year = 2023
    season_str = str(year) + "-" + str(year+1)[-2:]
    df0 = pd.read_parquet(box_DIR + f"NBA_BOX_T_Base_{year}.parquet")
    df0= df0[["GAME_ID","TEAM_ID","GAME_DATE","MATCHUP","WL","PLUS_MINUS"]]
    df0["GAME_ID"] = df0["GAME_ID"].astype(int)
    # load player indvidual game boxscores
    df1 = pd.read_parquet(box_DIR + "NBA_BOX_P_" + "Base" + "_" + str(year) + ".parquet")
    df1["GAME_DATE"] = pd.to_datetime(df1["GAME_DATE"], format="%Y-%m-%d")
    dfinj = pd.read_parquet(injury_DIR + f'NBA_prosptran_injuries_{year}.parquet')
    player_list = df1["PLAYER_ID"].unique()
    dfr = df1[["TEAM_ID","PLAYER_ID"]]
    dfrt = dfr.groupby("TEAM_ID")
    df2 = df1.groupby(["GAME_ID","TEAM_ID"])
    # loop through all groups and get injured players 
    keys = list(df2.groups)
    dfma = []
    for key in tqdm(keys):
        p_played =  df2["PLAYER_ID"].get_group(key).to_numpy()
        p_roster = dfrt["PLAYER_ID"].get_group(key[1]).to_numpy()
        pId_missed = np.setdiff1d(p_roster,p_played)
        game_date = df2["GAME_DATE"].get_group(key).iloc[0]
        players_missed = is_injured(dfinj,pId_missed,game_date)
        dfm1 = pd.DataFrame({"PLAYER_ID":players_missed})
        dfm1["TEAM_ID"] = key[1]
        dfm1["GAME_ID"] = key[0]
        dfm1["GAME_DATE"] = game_date
        dfma.append(dfm1)
    dfm1 = pd.concat(dfma)
    dfm1["PLAYER_ID"] = dfm1["PLAYER_ID"].astype(int)
    dfm1["PLAYER_NAME"] = dfm1["PLAYER_ID"].map(player_dict)
    dfm1["TEAM_NAME"] = dfm1["TEAM_ID"].map(teams_dict)
    dflb = pd.read_csv(aio_DIR + f"NBA_LEBRON_{year}.csv")
    dflb = dflb.rename(columns={"LEBRON WAR":"LEBRON_WAR"})
    dflb = dflb[["PLAYER_ID","LEBRON_WAR"]]
    dfgp = pd.read_parquet(box_DIR + f"NBA_BOX_P_Cum_Base_{year}.parquet")
    dfgp = dfgp[["PLAYER_ID","GP","MIN"]]
    dflm = pd.merge(dflb,dfgp,on="PLAYER_ID")
    dflm["LBWAR_PG"] = round(dflm["LEBRON_WAR"]/dflm["GP"],4)
    dflm = dflm[["PLAYER_ID","LBWAR_PG","MIN"]]
    dfm = pd.merge(dfm1,dflm,on="PLAYER_ID")
    dfmg =  (
        dfm
        .groupby(["GAME_ID","TEAM_ID"])[["PLAYER_ID","LBWAR_PG","MIN"]]
        .agg({"PLAYER_ID":["count"],"MIN":["sum"],"LBWAR_PG":["sum"]})
    )
    dfmg.columns = ["Games_Missed","Minutes_Missed","LEBRON_WAR_Missed"]
    dfmg = dfmg.reset_index()
    dfmg["GAME_ID"] = dfmg["GAME_ID"].astype(int)
    # merge team boxscores to get game details like date and matchup
    dfmf = pd.merge(df0,dfmg,on=["GAME_ID","TEAM_ID"])
    dfmf["Team"] = dfmf["TEAM_ID"].map(teams_dict)
    dfmf = dfmf.drop(columns=["GAME_ID","TEAM_ID"])
    dfmf.insert(1,"Team",dfmf.pop("Team"))
    df_x = dfmf.groupby("Team").agg({"Games_Missed":["sum"],"Minutes_Missed":["sum"],"LEBRON_WAR_Missed":["sum"]})
    df_x.columns = ["Games_Missed","Minutes_Missed","LEBRON_WAR_Missed"]
    df_x = (df_x
            .reset_index()
            .sort_values("LEBRON_WAR_Missed",ascending=False)
            .reset_index(drop=True)
        )
    df_x["LEBRON_WAR_Missed"] = df_x["LEBRON_WAR_Missed"].round(2)
    df_teams = pd.read_csv(data_DIR + "NBA_teams_colors_logos.csv")
    df_teams["Team"] = df_teams["nameTeam"]
    df_teams = df_teams[["Team","colorsTeam"]]
    df_y = pd.merge(df_x, df_teams, on="Team")
    df_avg = df_y.iloc[:,1:-1].mean()
    df_avg = pd.DataFrame(df_avg).T
    df_avg["Games_Missed"] = df_avg["Games_Missed"].round(0)
    df_avg["Minutes_Missed"] = df_avg["Minutes_Missed"].round(1)
    df_avg["LEBRON_WAR_Missed"] = df_avg["LEBRON_WAR_Missed"].round(2)
    df_avg["Team"] = "League Average"
    df_avg["colorsTeam"]  = "#000000"
    df_z = pd.concat([df_y,df_avg]).sort_values("LEBRON_WAR_Missed",ascending=False).reset_index(drop=True)
    teams = df_z["Team"].to_list()
    teams.reverse()
    df_z["Team"] = pd.Categorical(df_z['Team'], categories=teams)
    df_z.to_parquet(shiny_DIR + "NBA_games_minutes_war_missed.parquet")
    df_z.to_parquet(shiny_export_DIR2 + "NBA-Games-Missed/" + "NBA_games_minutes_war_missed.parquet")


def update_shiny_data(seasons):
    export_player_distribution()
    export_team_distribution()
    get_scorigami_data()
    export_lineups()
    export_stat_query()
    export_Games_Missed()