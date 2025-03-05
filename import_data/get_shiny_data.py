import json
import requests
import time
import numpy as np
import pandas as pd
from tqdm import tqdm
import zstandard as zstd
import dill

from update_data import data_DIR, teams_dict, player_dict

box_DIR = data_DIR + "box/"
pbp_DIR = data_DIR + "pbpdata/"
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

def export_player_distribution(seasons):
    dfa = []
    for season in seasons:
        year = int(season)
    # for year in tqdm(range(2004,2025)):
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

def export_team_distribution(seasons):
    dfa = []
    for season in seasons:
        year = int(season)
    # for year in tqdm(range(2004,2025)):
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
    for year in range(1996,2025):
        season = str(year)
        try:
            df1 = pd.read_parquet(box_DIR + "NBA_Box_P_" + "Base_"  + season + ".parquet", columns = cols1)
            dfa.append(df1)
        except:
            pass
        try:
            df2 = pd.read_parquet(box_DIR + "NBA_Box_P_" + "Base_"  + season + "_PS.parquet", columns = cols1)
            dfa.append(df2)
        except:
            pass
        
    dfa1 = [df2 for df2 in dfa if not df2.empty]
    df = pd.concat(dfa1)
    df = df.rename(columns=str.title)
    df = df.rename(columns={"Player_Name":"Player",'Player_Id':'Player ID'})
    df = df.reset_index(drop=True)
    df['Player'] = (
        df['Player']
        .str.normalize('NFKD')
        .str.encode('ascii', errors='ignore')
        .str.decode('utf-8')
    )
    df['Reb_Ast'] = df['Reb'] + df['Ast']  
    df["Game_Date"] = pd.to_datetime(df["Game_Date"], format="%Y-%m-%d")
    df1 = df.copy()
    df1["Pts_cat"] = 0
    idx = df1.index[((df1["Pts"] >= 10) & (df1["Pts"] < 20))].tolist()
    df1.loc[idx,"Pts_cat"] = 1
    idx = df1.index[((df1["Pts"] >= 20) & (df1["Pts"] < 30))].tolist()
    df1.loc[idx,"Pts_cat"] = 2
    idx = df1.index[((df1["Pts"] >= 30) & (df1["Pts"] < 40))].tolist()
    df1.loc[idx,"Pts_cat"] = 3
    idx = df1.index[(df1["Pts"] >= 40)].tolist()
    df1.loc[idx,"Pts_cat"] = 4

    df1["Ast_cat"] = 0
    idx = df1.index[((df1["Ast"] > 0) & (df1["Ast"] < 5))].tolist()
    df1.loc[idx,"Ast_cat"] = 1
    idx = df1.index[((df1["Ast"] >= 5) & (df1["Ast"] < 10))].tolist()
    df1.loc[idx,"Ast_cat"] = 2
    idx = df1.index[((df1["Ast"] >= 10) & (df1["Ast"] < 15))].tolist()
    df1.loc[idx,"Ast_cat"] = 3
    idx = df1.index[(df1["Ast"] >= 15)].tolist()
    df1.loc[idx,"Ast_cat"] = 4

    df1["Reb_cat"] = 0
    idx = df1.index[((df1["Reb"] > 0) & (df1["Reb"] < 5))].tolist()
    df1.loc[idx,"Reb_cat"] = 1
    idx = df1.index[((df1["Reb"] >= 5) & (df1["Reb"] < 10))].tolist()
    df1.loc[idx,"Reb_cat"] = 2
    idx = df1.index[((df1["Reb"] >= 10) & (df1["Reb"] < 15))].tolist()
    df1.loc[idx,"Reb_cat"] = 3
    idx = df1.index[(df1["Reb"] >= 15)].tolist()
    df1.loc[idx,"Reb_cat"] = 4

    df1["Reb_Ast_cat"] = 0
    idx = df1.index[((df1["Reb_Ast"] >= 5) & (df1["Reb_Ast"] < 10))].tolist()
    df1.loc[idx,"Reb_Ast_cat"] = 1
    idx = df1.index[((df1["Reb_Ast"] >= 10) & (df1["Reb_Ast"] < 15))].tolist()
    df1.loc[idx,"Reb_Ast_cat"] = 2
    idx = df1.index[((df1["Reb_Ast"] >= 15) & (df1["Reb_Ast"] < 20))].tolist()
    df1.loc[idx,"Reb_Ast_cat"] = 3
    idx = df1.index[(df1["Reb_Ast"] >= 20)].tolist()
    df1.loc[idx,"Reb_Ast_cat"] = 4

    df1["Stl_cat"] = 0
    idx = df1.index[((df1["Stl"] > 0) & (df1["Stl"] < 3))].tolist()
    df1.loc[idx,"Stl_cat"] = 1
    idx = df1.index[((df1["Stl"] >= 3) & (df1["Stl"] < 5))].tolist()
    df1.loc[idx,"Stl_cat"] = 2
    idx = df1.index[((df1["Stl"] >= 5) & (df1["Stl"] < 7))].tolist()
    df1.loc[idx,"Stl_cat"] = 3
    idx = df1.index[(df1["Stl"] >= 7)].tolist()
    df1.loc[idx,"Stl_cat"] = 4

    df1["Blk_cat"] = 0
    idx = df1.index[((df1["Blk"] > 0) & (df1["Blk"] < 3))].tolist()
    df1.loc[idx,"Blk_cat"] = 1
    idx = df1.index[((df1["Blk"] >= 3) & (df1["Blk"] < 5))].tolist()
    df1.loc[idx,"Blk_cat"] = 2
    idx = df1.index[((df1["Blk"] >= 5) & (df1["Blk"] < 7))].tolist()
    df1.loc[idx,"Blk_cat"] = 3
    idx = df1.index[(df1["Blk"] >= 7)].tolist()
    df1.loc[idx,"Blk_cat"] = 4

    df1["Tov_cat"] = 0
    idx = df1.index[((df1["Tov"] > 0) & (df1["Tov"] < 3))].tolist()
    df1.loc[idx,"Tov_cat"] = 1
    idx = df1.index[((df1["Tov"] >= 3) & (df1["Tov"] < 5))].tolist()
    df1.loc[idx,"Tov_cat"] = 2
    idx = df1.index[((df1["Tov"] >= 5) & (df1["Tov"] < 7))].tolist()
    df1.loc[idx,"Tov_cat"] = 3
    idx = df1.index[(df1["Tov"] >= 7)].tolist()
    df1.loc[idx,"Tov_cat"] = 4

    df1["Fg3M_cat"] = 0
    idx = df1.index[((df1["Fg3M"] > 0) & (df1["Fg3M"] < 4))].tolist()
    df1.loc[idx,"Fg3M_cat"] = 1
    idx = df1.index[((df1["Fg3M"] >= 4) & (df1["Fg3M"] < 7))].tolist()
    df1.loc[idx,"Fg3M_cat"] = 2
    idx = df1.index[((df1["Fg3M"] >= 7) & (df1["Fg3M"] < 10))].tolist()
    df1.loc[idx,"Fg3M_cat"] = 3
    idx = df1.index[(df1["Fg3M"] >= 10)].tolist()
    df1.loc[idx,"Fg3M_cat"] = 4

    df1["Ftm_cat"] = 0
    idx = df1.index[((df1["Ftm"] > 0) & (df1["Ftm"] < 5))].tolist()
    df1.loc[idx,"Ftm_cat"] = 1
    idx = df1.index[((df1["Ftm"] >= 5) & (df1["Ftm"] < 10))].tolist()
    df1.loc[idx,"Ftm_cat"] = 2
    idx = df1.index[((df1["Ftm"] >= 10) & (df1["Ftm"] < 15))].tolist()
    df1.loc[idx,"Ftm_cat"] = 3
    idx = df1.index[(df1["Ftm"] >= 15)].tolist()
    df1.loc[idx,"Ftm_cat"] = 4

    df1["Pts_cat"] = df1["Pts_cat"].astype("category")
    df1["Ast_cat"] = df1["Ast_cat"].astype("category")
    df1["Reb_cat"] = df1["Reb_cat"].astype("category")
    df1["Reb_Ast_cat"] = df1["Reb_Ast_cat"].astype("category")
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
    Reb_Ast_cat = ["0 to 4", "5 to 9", "10 to 14", "15 to 19", "20+"]
    df1["Reb_Ast_cat"] = df1["Reb_Ast_cat"].cat.rename_categories(Reb_Ast_cat)
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
    for year in range(2024,2025):
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
            time.sleep(2)
            dfa.append(df_players1)
    df_players = pd.concat(dfa)
    df_players = pd.merge(df_players,df_teams,left_on="team", right_on="id")
    df_players = df_players.rename(columns={"id_x":"pid","id_y":"tid","team_y":"team"})
    df_players = df_players.drop(columns=["team_x"]) 
    df_players.to_parquet(shiny_DIR + "lineup_data.parquet")
    df_players.to_parquet(shiny_export_DIR1 + "lineup_data.parquet")

def export_stat_query():
    dfa = []
    for year in range(1946,2025):
        df1 = pd.read_parquet(box_DIR + "NBA_Box_P_" + "Base" + "_" + str(year) + ".parquet")
        df1[df1["WL"] == 0]["WL"] = "L"
        df1["season"] = year+1
        with pd.option_context("future.no_silent_downcasting", True):
            df1 = df1.fillna(0).infer_objects(copy=False)
        dfa.append(df1)
    df = pd.concat(dfa)
    df.loc[df[df["WL"] == 0].index,"WL"] = "L"
    df["TS_PCT"] = round(df["PTS"]*0.5/((df["FGA"]+0.44*df["FTA"])),3)
    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"], format="%Y-%m-%d")
    df.to_parquet(box_DIR + "NBA_Box_P_" + "Base" + "_" + "All" + ".parquet")
    df.to_parquet(shiny_DIR + "NBA_Box_P_" + "Base" + "_" + "All" + ".parquet")
    # dfa = []
    # for year in range(1946,2025):
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
    for year in [2024]:
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
            dfii["TS_PCT"] = round(dfii["PTS"]*0.5/((dfii["FGA"]+0.44*dfii["FTA"])),3)
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
    

def export_Games_Missed():
    year = 2024
    season_str = str(year) + "-" + str(year+1)[-2:]
    df0 = pd.read_parquet(box_DIR + f"NBA_BOX_P_Trad_{year}.parquet")
    df0.columns = map(str.lower,df0.columns)
    df0 = df0[['gameid', 'personid', 'comment']]
    df0.columns = ['game_id', 'player_id', 'comment']
    with zstd.open(pbp_DIR +f"NBA_PBPdata_{year}"+".pkl.zst","rb") as f:
        games_list = dill.load(f)
    len(games_list)
    dfa = []
    for game in games_list:
        df1 = pd.DataFrame(game.boxscore.player_items)
        df1["game_id"] = game.game_id
        dfa.append(df1)
    df2 = pd.concat(dfa)
    cols = ['game_id','team_id', 'team_abbreviation', 'player_id','name', 'status', 'totsec']
    df3 = df2[cols]
    df3["game_id"] = df3["game_id"].astype(int)
    df3 = df3.rename(columns={"name":"Name"}).reset_index(drop=True)
    dfm1 = df3.query("totsec == 0").reset_index(drop=True)
    dfm1 = pd.merge(dfm1,df0,how="left")
    dfm1 = dfm1[~dfm1["comment"].isin(["DNP - Coach's Decision","DND - Coach's Decision"])]
    dfm1 = dfm1.reset_index(drop=True)
    dflb0 = pd.read_csv(aio_DIR + "NBA_LEBRON_FULL.csv")
    cols2 = ["player_id","player_name","Age","G","Mins","MPG","LEBRON","LEBRON_WinsAdded","multiLEBRON","multiLEBRON_WAR_Projection"]
    dflb = dflb0.query("Year == 2025")
    dflb = dflb[cols2]
    dflb = dflb.dropna()
    dflb["Min"] = dflb["MPG"]
    dflb["LBWAR_PG"] = dflb["multiLEBRON_WAR_Projection"]/82
    # dflb["LBWAR_PG"] = dflb["LEBRON_WinsAdded"]/dflb["G"]
    dflb.iloc[:,3:-1] = round(dflb.iloc[:,3:-1],4)
    dflb["LBWAR_PG"] = dflb["LBWAR_PG"].round(5)
    dflm = dflb[["player_id","LBWAR_PG","Min"]]
    dflb2 = dflb0.query("Year == 2024")
    dflb2 = dflb2[cols2]
    dflb2["Min"] = dflb2["MPG"]
    dflb2["LBWAR_PG"] = dflb2["multiLEBRON_WAR_Projection"]/82
    # dflb2["LBWAR_PG"] = dflb2["LEBRON_WinsAdded"]/dflb2["G"]
    dflb2.iloc[:,3:-1] = round(dflb2.iloc[:,3:-1],4)
    dflb2["LBWAR_PG"] = dflb2["LBWAR_PG"].round(5)
    dflm2 = dflb2[["player_id","LBWAR_PG","Min"]]
    dfm2 = pd.merge(dfm1,dflm,on="player_id",how="left")
    dfm3 = dfm1[dfm2["LBWAR_PG"].isna()]
    dfm4 = pd.merge(dfm1,dflm,on="player_id")
    dfm5 = pd.merge(dfm3,dflm2,on="player_id")
    dfm = pd.concat([dfm4,dfm5])
    dfm = dfm[~dfm.duplicated(keep="last")].reset_index(drop=True)
    dfmgt = dfm.groupby("team_abbreviation")
    keys = list(dfmgt.groups)
    dfb = []
    for key in keys:
        dfmt1 =  dfmgt.get_group(key)
        dfmt2 = dfmt1.groupby(["Name"])[["Name","LBWAR_PG","Min"]].agg({"Name":["count"],"Min":["sum"],"LBWAR_PG":["sum"]})
        dfmt2.columns = ["Games","Min","WAR"]
        dfmt2 = dfmt2.sort_values("WAR",ascending=False).reset_index()
        dfmt2["Min"] = dfmt2["Min"].round()
        dfmt2["WAR"] = dfmt2["WAR"].round(3)
        dfmt2["Team"] = key
        dfmt2.index +=1
        dfb.append(dfmt2)
    dfmt = pd.concat(dfb)
    dfmt.insert(0,"Team",dfmt.pop("Team"))
    df10 = pd.read_parquet(box_DIR + f"NBA_BOX_T_Base_{year}.parquet")
    df10= df10[["GAME_ID","TEAM_ID","GAME_DATE","MATCHUP","WL","PLUS_MINUS"]]
    df10 = df10.rename(columns={"GAME_ID":"game_id","TEAM_ID":"team_id"})
    df10["game_id"] = df10["game_id"].astype(int)
    dfmg =  (
        dfm
        .groupby(["game_id","team_id"])[["player_id","LBWAR_PG","Min"]]
        .agg({"player_id":["count"],"Min":["sum"],"LBWAR_PG":["sum"]})
    )
    dfmg.columns = ["Games_Missed","Minutes_Missed","LEBRON_WAR_Missed"]
    dfmg = dfmg.reset_index()
    # merge team boxscores to get game details like date and matchup
    dfmf = pd.merge(df10,dfmg,on=["game_id","team_id"])
    dfmf["Team"] = dfmf["team_id"].map(teams_dict)
    dfmf = dfmf.drop(columns=["team_id","team_id"])
    dfmf.insert(1,"Team",dfmf.pop("Team"))
    df_x = dfmf.groupby("Team").agg({"Games_Missed":["sum"],"Minutes_Missed":["sum"],"LEBRON_WAR_Missed":["sum"]})
    df_x.columns = ["Games_Missed","Minutes_Missed","LEBRON_WAR_Missed"]
    df_x = (df_x
            .reset_index()
            .sort_values("LEBRON_WAR_Missed",ascending=False)
            .reset_index(drop=True)
        )
    df_x["LEBRON_WAR_Missed"] = df_x["LEBRON_WAR_Missed"].round(2)
    df_x["Minutes_Missed"] = df_x["Minutes_Missed"].astype(int)
    df_teams = pd.read_csv(data_DIR + "NBA_teams_colors_logos.csv")
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
    df_z.to_parquet(shiny_export_DIR1 + "NBA_games_minutes_war_missed.parquet")
    dfmt.to_parquet(shiny_DIR + "NBA_games_minutes_war_missed_table.parquet")
    dfmt.to_parquet(shiny_export_DIR1 + "NBA_games_minutes_war_missed_table.parquet")
    

def update_shiny_data(seasons):
    # print("Player Distributions")
    # export_player_distribution(seasons)
    # print("Team Distributions")
    # export_team_distribution(seasons)
    # print("Scorigami")
    # get_scorigami_data()
    
    # print("Stat Query")
    # export_stat_query()
    print("Games Missed")
    export_Games_Missed()
    # print("Lineups")
    # try:
    #     export_lineups()
    # except Exception as error:
    #     print(error)
    
