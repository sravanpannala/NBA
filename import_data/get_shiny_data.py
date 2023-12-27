import numpy as np
import pandas as pd

from update_data_V1 import data_DIR

box_DIR = data_DIR + "box/"
shiny_DIR = data_DIR + "shiny/"
track_DIR = data_DIR + "tracking/"

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
    # for season in seasons:
    #     year = int(season)
    for year in range(2013,2024):
        season = int(year)
        df1 = pd.read_parquet(box_DIR + "NBA_Box_P_" + "Base_"  + season + ".parquet", columns = cols1)
        df1["GAME_ID"] = df1["GAME_ID"].astype(int)
        df2 = pd.read_parquet(box_DIR + "NBA_Box_P_" + "Adv_"  + season + ".parquet", columns = cols2)
        dfm1 = pd.merge(df1,df2,left_on=['PLAYER_ID','TEAM_ID','GAME_ID'], right_on=['personId', 'teamId','gameId'])
        df3 = pd.read_parquet(track_DIR + "NBA_PBP_" + "Tracking_"  + season + ".parquet", columns = cols3)
        dfm = pd.merge(dfm1,df3,left_on=['PLAYER_ID','TEAM_ID','GAME_ID'], right_on=['player_id', 'team_id','game_id'])
        dfm = dfm.drop(columns=['player_id', 'team_id','game_id'])
        dfm["Season"] = year +1
        dfg = dfm.groupby("PLAYER_ID")
        keys = list(dfg.groups)
        dfb = []
        for key in keys:
            dfgg = dfg.get_group(key)
            dfgg = dfgg.reset_index(drop=True).reset_index()
            dfgg = dfgg.rename(columns={"index":"Games Played"})
            dfgg["Games Played"] +=1
            dfa.append(dfgg)
    df = pd.concat(dfa)

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
    cols = df1.columns
    df1 = df1.drop( columns = cols[cols.str.contains("Estimated")])
    df1 = df1.fillna(0)
    df1 = df1[df1["Pace"] > 60]
    df1 = df1.reset_index(drop=True)
    df1.columns
    df1.to_parquet(shiny_DIR + "NBA_Player_Distribution.parquet")
    # df2 = pd.read_parquet(shiny_DIR + "NBA_Player_Distribution.parquet")
    # df3 = pd.concat([df2,df1])
    # df4 = df3[~df3.duplicated(keep="last")].reset_index(drop=True)
    # df4.to_parquet(shiny_DIR + "NBA_Player_Distribution.parquet")

def update_shiny_data(seasons):
    export_player_distribution(seasons)