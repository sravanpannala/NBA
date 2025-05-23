import pandas as pd
import scipy
import json
import numpy as np
from sklearn.linear_model import RidgeCV
from nba_api.stats.endpoints import leaguegamelog
import subprocess

data_DIR = "C:/Users/pansr/Documents/NBA/data/"

box_DIR = data_DIR + "box/"
shot_DIR = data_DIR + "shots/"

export_DIR = "C:/Users/pansr/Documents/repos/csv/"

team_data = pd.read_csv(data_DIR + "NBA_teams_database.csv")
teams_list = team_data["TeamID"].tolist()
team_dict1 = team_data.to_dict(orient="records")
teams_dict = {team["TeamID"]: team["Team"] for team in team_dict1}

with open(data_DIR + "NBA.json") as f:
    data = json.load(f)
pID_dict = {v: int(k) for k, v in data.items()}
player_dict = {int(k): v for k, v in data.items()}

def get_ratings(season=2024,ngames=0):
    cols = [
        "gameId",
        "teamName",
        "teamId",
        "offensiveRating",
        "defensiveRating",
        "netRating",
        "possessions",
    ]
    df = pd.read_parquet(box_DIR + f"NBA_Box_T_Adv_{season}.parquet", columns=cols)
    cols = ["gameId", "team", "tId", "ORtg", "DRtg", "NRtg", "poss"]
    df.columns = cols
    df1 = df.groupby("gameId")
    df1_1 = df1.nth(0)
    df1_2 = df1.nth(1)
    df1_1.columns = ["gameId"] + [s + "1" for s in df1_1.columns if s != "gameId"]
    df1_2.columns = ["gameId"] + [s + "2" for s in df1_2.columns if s != "gameId"]
    df1_3 = pd.merge(df1_1, df1_2, on="gameId")
    df1_4 = df1.nth(1)
    df1_5 = df1.nth(0)
    df1_4.columns = ["gameId"] + [s + "1" for s in df1_4.columns if s != "gameId"]
    df1_5.columns = ["gameId"] + [s + "2" for s in df1_5.columns if s != "gameId"]
    df1_6 = pd.merge(df1_4, df1_5, on="gameId")
    df2 = pd.concat([df1_3, df1_6]).sort_values(by="gameId").reset_index(drop=True)
    data1 = df2.copy()
    df10 = pd.read_parquet(box_DIR + f"NBA_Box_T_Base_{season}.parquet")
    if ngames != 0:
            df10g = df10.groupby("TEAM_NAME")
            df10 = df10g.nth(np.arange(-ngames,0,1)).reset_index(drop=True)
    df10["HOME"] = ~df10["MATCHUP"].str.contains("@")
    df10["tId1"] = df10["TEAM_ID"]
    df10["gameId"] = df10["GAME_ID"]
    df11 = (
        df10[["gameId", "tId1", "HOME"]].sort_values(by="gameId").reset_index(drop=True)
    )
    df11[["gameId", "tId1"]] = df11[["gameId", "tId1"]].astype(int)
    data = pd.merge(data1, df11)
    return data


def process_results(data, results_adj, intercept):
    data["pts1"] = data["ORtg1"] * data["poss1"]
    data["pts2"] = data["DRtg1"] * data["poss1"]
    off_prior = data.groupby(["tId1"])[["poss1", "pts1"]].agg("sum").reset_index()
    def_prior = data.groupby(["tId1"])[["poss1", "pts2"]].agg("sum").reset_index()
    off_prior["OFF"] = off_prior["pts1"] / off_prior["poss1"]
    off_prior = off_prior[["tId1", "OFF"]]
    def_prior["DEF"] = def_prior["pts2"] / def_prior["poss1"]
    def_prior = def_prior[["tId1", "DEF"]]
    results_net = pd.merge(off_prior, def_prior, on=["tId1"])
    results_net["NET"] = results_net["OFF"] - results_net["DEF"]
    results_net.rename(columns={"tId1": "tId"}, inplace=True)
    results_net = results_net.astype(float).round(2)
    results_net["tId"] = results_net["tId"].astype(int)
    ortg_mean = data["pts1"].sum() / data["poss1"].sum()
    drtg_mean = data["pts2"].sum() / data["poss1"].sum()
    results_adj["tId"] = results_adj["tId"].astype(int)
    results_comb = pd.merge(results_net, results_adj, on=["tId"])
    results_comb["aOFF"] = results_comb["aOFF"] + intercept
    results_comb["aDEF"] = results_comb["aDEF"] + intercept
    results_comb["oSOS"] = results_comb["aOFF"] - results_comb["OFF"]
    results_comb["dSOS"] = results_comb["DEF"] - results_comb["aDEF"]
    results_comb["SOS"] = results_comb["oSOS"] + results_comb["dSOS"]
    results_comb.iloc[:, 1:] = results_comb.iloc[:, 1:].round(1)
    # results = results_comb[["Team","OFF","oSOS","aOFF","DEF","dSOS","aDEF","NET","SOS","aNET"]]
    results = results_comb[["Team", "OFF", "DEF", "NET", "aOFF", "aDEF", "aNET"]]
    results = results.sort_values(by="aNET", ascending=0).reset_index(drop=True)
    return results, ortg_mean, drtg_mean


def map_teams(row_in, teams, scale):
    t1 = row_in[0]
    t2 = row_in[1]

    rowOut = np.zeros([len(teams) * 3])
    rowOut[teams.index(t1)] = scale
    rowOut[teams.index(t2) + len(teams)] = scale

    return rowOut


def convert_to_matricies(possessions, name, teams, scale=1):
    # extract only the columns we need
    # Convert the columns of player ids into a numpy matrix
    stints_x_base = possessions[["tId1", "tId2"]].to_numpy()
    # Apply our mapping function to the numpy matrix
    stint_X_rows = np.apply_along_axis(map_teams, 1, stints_x_base, teams, scale=scale)
    # Convert the column of target values into a numpy matrix
    stint_Y_rows = possessions[name].to_numpy()

    # return matricies and possessions series
    return stint_X_rows, stint_Y_rows


# Convert lambda value to alpha needed for ridge CV
def lambda_to_alpha(lambda_value, samples):
    return (lambda_value * samples) / 2.0


# Convert RidgeCV alpha back into a lambda value
def alpha_to_lambda(alpha_value, samples):
    return (alpha_value * 2.0) / samples


def calculate_netrtg(train_x, train_y, lambdas, teams_list):
    alphas = [lambda_to_alpha(l, train_x.shape[0]) for l in lambdas]
    # create a 5 fold CV ridgeCV model. Our target data is not centered at 0, so we want to fit to an intercept.
    clf = RidgeCV(alphas=alphas, cv=5, fit_intercept=True)

    # fit our training data
    model = clf.fit(
        train_x,
        train_y,
    )

    # convert our list of players into a mx1 matrix
    team_arr = np.transpose(np.array(teams_list).reshape(1, len(teams_list)))

    # extract our coefficients into the offensive and defensive parts
    coef_offensive_array = model.coef_[0 : len(teams_list)][np.newaxis].T
    coef_defensive_array = model.coef_[len(teams_list) : 2 * len(teams_list)][
        np.newaxis
    ].T
    # concatenate the offensive and defensive values with the playey ids into a mx3 matrix
    team_id_with_coef = np.concatenate(
        [team_arr, coef_offensive_array, coef_defensive_array], axis=1
    )
    # build a dataframe from our matrix
    teams_coef = pd.DataFrame(team_id_with_coef)
    intercept = model.intercept_
    teams_coef.columns = ["tId", "aOFF", "aDEF"]
    teams_coef["aNET"] = teams_coef["aOFF"] - teams_coef["aDEF"]
    teams_coef["aOFF"] = teams_coef["aOFF"]
    teams_coef["aDEF"] = teams_coef["aDEF"]
    teams_coef["Team"] = teams_coef["tId"].map(teams_dict)
    results = teams_coef[["tId", "Team", "aOFF", "aDEF", "aNET"]]
    results = results.sort_values(by=["aNET"], ascending=False).reset_index(drop=True)
    return results, model, intercept


data = get_ratings(season=2024, ngames=10)
train_x, train_y = convert_to_matricies(data, "ORtg1", teams_list, scale=1 / 2)
n = 1.5
lambdas_net = [0.001 * n, 0.005 * n, 0.01 * n]
results_adj, model, intercept = calculate_netrtg(
    train_x, train_y, lambdas_net, teams_list
)
results, ortg_mean, drtg_mean = process_results(data, results_adj, intercept)
results["OFF_R"] = results["OFF"].rank(ascending=False).astype(int)
results["DEF_R"] = results["DEF"].rank(ascending=True).astype(int)
results["NET_R"] = results["NET"].rank(ascending=False).astype(int)
results["aOFF_R"] = results["aOFF"].rank(ascending=False).astype(int)
results["aDEF_R"] = results["aDEF"].rank(ascending=True).astype(int)
results["aNET_R"] = results["aNET"].rank(ascending=False).astype(int)

results.to_csv(export_DIR + "NBA_Adj_Ratings_2024_2025.csv", index=False)

season = "2024"
dft = pd.read_parquet(box_DIR + f"NBA_Box_P_Cum_Base_"+season+".parquet", columns = ["PLAYER_ID","TEAM_ID"])
df = pd.read_parquet(shot_DIR + f"NBA_Shots_{season}_All.parquet")

df = df[["PLAYER_ID","PLAYER_NAME","PLAYER_LAST_TEAM_ID","FGM","FGA","FG2M","FG2A","FG3M","FG3A", 'general_range', 'closest_def', 'touch_time']]
df = df.query("general_range != 'Other'")
df_avg = df.groupby(['general_range', 'closest_def', 'touch_time']).sum()
df_avg = df_avg.drop(columns= ["PLAYER_ID","PLAYER_NAME","PLAYER_LAST_TEAM_ID"])
df_avg["xFG2"] = df_avg["FG2M"]/df_avg["FG2A"]
df_avg["xFG3"] = df_avg["FG3M"]/df_avg["FG3A"]
df_avg = df_avg.drop(columns =["FGM","FGA","FG2M","FG2A","FG3M","FG3A"])
df_avg = df_avg.reset_index()

shots = pd.merge(df,df_avg,on=['general_range', 'closest_def', 'touch_time'])
shots["FG2_PCT"] = shots["FG2M"]/shots["FG2A"]
shots["FG3_PCT"] = shots["FG3M"]/shots["FG3A"]
shots = shots.replace([np.inf, -np.inf], np.nan)
shots = shots.fillna(0)
shots["PTS2"] =  (2*shots["FG2A"]*shots["FG2_PCT"]).round(2)
shots["PTS3"] =  (3*shots["FG3A"]*shots["FG3_PCT"]).round(2)
shots["PTS"] =  (2*shots["FG2A"]*shots["FG2_PCT"] + 3*shots["FG3A"]*shots["FG3_PCT"]).round(2)
shots["xPTS2"] = (2*shots["FG2A"]*shots["xFG2"]).round(2)
shots["xPTS3"] = (3*shots["FG3A"]*shots["xFG3"]).round(2)
shots["xPTS"] = (2*shots["FG2A"]*shots["xFG2"] + 3*shots["FG3A"]*shots["xFG3"]).round(2)

fg = (
    shots
    .groupby(['PLAYER_ID'])[['FG2M', 'FG2A', 'FG3M', 'FG3A', 'FGM', 'FGA', 'PTS2', 'PTS3', 'PTS', 'xPTS2', 'xPTS3', 'xPTS']]
    .sum()
)
fg.columns = ['FG2M', 'FG2A', 'FG3M', 'FG3A','FGM', 'FGA', 'PTS2', 'PTS3', 'PTS', 'xPTS2', 'xPTS3', 'xPTS']
fg['FG2_PCT'] = np.round(fg['FG2M']/fg['FG2A'], 3)
fg['FG3_PCT'] = np.round(fg['FG3M']/fg['FG3A'], 3)
fg['eFG'] = np.round(fg['PTS']/fg['FGA']/2, 3)
fg['xeFG'] = np.round(fg['xPTS']/fg['FGA']/2, 3)
fg['Shot_Making2'] = np.round((fg['PTS2'] - fg['xPTS2'])/fg['FG2A'], 3)
fg['Shot_Making3'] = np.round((fg['PTS3'] - fg['xPTS3'])/fg['FG3A'], 3)
fg['Shot_Making'] = np.round((fg['PTS'] - fg['xPTS'])/fg['FGA'], 3)
# fg = fg.drop(columns=['FGM', 'FGA'])
fg = fg.fillna(0)
# fg = pd.merge(dfd,fg,on=["PLAYER_ID"])
fg["Points_Added2"] = fg['PTS2'] - fg['xPTS2']
fg["Points_Added3"] = fg['PTS3'] - fg['xPTS3']
fg["Points_Added"] = fg['PTS'] - fg['xPTS']
fg["PTS"] = fg["PTS"].astype(int)
fg = fg.reset_index()
fg["Player"] = fg["PLAYER_ID"].map(player_dict)
fg.insert(1,"Player",fg.pop("Player"))
fg = pd.merge(fg,dft,on="PLAYER_ID")
fg["Team"] = fg["TEAM_ID"].map(teams_dict)
fg.insert(2,"Team",fg.pop("Team"))
fg[['Points_Added']] = fg[['Points_Added']].round(1)
fg[['Shot_Making']] = fg[['Shot_Making']].round(3)
fg1 = fg.drop(columns=["TEAM_ID",'FGM', 'FGA', 'FG2M', 'FG2A',
       'FG3M', 'FG3A',])
fg1 = fg1[['Player', 'Team', 'PLAYER_ID', 
            'PTS2', 'xPTS2', 'FG2_PCT', 'Shot_Making2', 'Points_Added2', 
            'PTS3', 'xPTS3', 'FG3_PCT', 'Shot_Making3', 'Points_Added3', 
            'PTS', 'xPTS', 'eFG', 'xeFG', 'Shot_Making', 'Points_Added'
       ]]
fg1[['xPTS2','Points_Added2','xPTS3','Points_Added3',]] = fg1[['xPTS2','Points_Added2','xPTS3','Points_Added3',]].round(2)
fg1[['xPTS','Points_Added',]] = fg1[['xPTS','Points_Added']].round(2)
fg1 = fg1.query("PTS >= 100").reset_index(drop=True)
fg1.to_csv(export_DIR + "NBA_Shot_Quality_2024_2025_V2.csv")


subprocess.run(["git", "add", "."], cwd=export_DIR)
subprocess.run(["git", "commit", "-m", "update adj rat, injury & SSQM"], cwd=export_DIR)
subprocess.run(["git", "push"], cwd=export_DIR)