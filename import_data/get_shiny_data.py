import numpy as np
import pandas as pd

from update_data_V1 import data_DIR

box_DIR = data_DIR + "box/"
shiny_DIR = data_DIR + "shiny/"

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

def export_player_distribution(seasons):
    dfa = []
    for season in seasons:
        year = int(season)
        df1 = pd.read_parquet(box_DIR + "NBA_Box_P_" + "Base_"  + season + ".parquet", columns = cols1)
        df1["GAME_ID"] = df1["GAME_ID"].astype(int)
        df2 = pd.read_parquet(box_DIR + "NBA_Box_P_" + "Adv_"  + season + ".parquet", columns = cols2)
        dfm = pd.merge(df1,df2,left_on=['PLAYER_ID','TEAM_ID','GAME_ID'], right_on=['personId', 'teamId','gameId'])
        dfm["Season"] = year +1
        dfg = dfm.groupby("PLAYER_ID")
        keys = list(dfg.groups)
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
    df1.columns = df1.columns.str.replace("_Pct","Pct")
    df1.columns = df1.columns.str.replace("Pct","_Pct")
    df1.columns = df1.columns.str.replace("_"," ")
    df1 = df1.rename(columns={
            "FGa":"FGA","FGm":"FGM","FTa":"FTA","FTm":"FTM","Pf":"PF", "Wl":"WL","Oreb":"OReb","Dreb":"DReb","Pie":"PIE","AsttoTov":"Ast/Tov",
            "Usage": "USG","Possessions":"Poss"
        }
    )
    df1 = df1.drop(columns=['Gameid', 'Teamid', 'Personid','Position', 'Paceper40'])
    cols = df1.columns
    df1 = df1.drop( columns = cols[cols.str.contains("Estimated")])
    df1 = df1.fillna(0)
    df1 = df1[df1["Pace"] > 60]
    df1 = df1.reset_index(drop=True)
    # df2 = pd.read_parquet(shiny_DIR + "NBA_Player_Distribution.parquet")
    # df3 = pd.concat([df2,df1])
    # df4 = df3[~df3.duplicated(keep="last")].reset_index(drop=True)
    df4 = df1
    df4.to_parquet(shiny_DIR + "NBA_Player_Distribution.parquet")

def update_shiny_data(seasons):
    export_player_distribution(seasons)