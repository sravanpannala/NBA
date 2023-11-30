from sklearn.linear_model import RidgeCV
# import os, sys
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath("__file__"))))
# from nbafuns import *
import pandas as pd
import scipy
import numpy as np
from nba_api.stats.endpoints import leaguegamelog
import subprocess

data_DIR = "C:\\Users\\pansr\\Documents\\NBA\\data\\"

box_DIR = "C:\\Users\\pansr\\Documents\\NBA\\team_ratings\\boxscores\\"

export_DIR = "C:\\Users\\pansr\\Documents\\repos\\csv\\"

team_data = pd.read_csv(data_DIR + "NBA_teams_database.csv") 
teams_list = team_data["TeamID"].tolist()
team_dict1 = team_data.to_dict(orient="records")
teams_dict = {team["TeamID"]:team["Team"] for team in team_dict1}

def get_ratings(season=2023):
    df1 = pd.read_csv(box_DIR + f"NBA_BoxScores_Adv_{season}.csv")
    cols = ["gameId","teamName","teamId","offensiveRating","defensiveRating","netRating","possessions"]
    df2 = df1[cols]
    df2.iloc[:,2:]=df2.iloc[:,2:].astype(str)
    df3 = df2.groupby("gameId")[cols[1:]].agg(", ".join).reset_index()
    df4 = df3.copy()
    df4[["team1","team2"]] = df3["teamName"].str.split(",",expand=True)
    df4[["tId1","tId2"]] = df3["teamId"].str.split(",",expand=True)
    df4[["ORtg1","ORtg2"]] = df3["offensiveRating"].str.split(",",expand=True)
    df4[["DRtg1","DRtg2"]] = df3["defensiveRating"].str.split(",",expand=True)
    df4[["NRtg1","NRtg2"]] = df3["netRating"].str.split(",",expand=True)
    df4[["poss1","poss2"]] = df3["possessions"].str.split(",",expand=True)
    df4 = df4.drop(columns=cols[1:])
    df5 = df3.copy()
    df5[["team2","team1"]] = df3["teamName"].str.split(",",expand=True)
    df5[["tId2","tId1"]] = df3["teamId"].str.split(",",expand=True)
    df5[["ORtg2","ORtg1"]] = df3["offensiveRating"].str.split(",",expand=True)
    df5[["DRtg2","DRtg1"]] = df3["defensiveRating"].str.split(",",expand=True)
    df5[["NRtg2","NRtg1"]] = df3["netRating"].str.split(",",expand=True)
    df5[["poss2","poss1"]] = df3["possessions"].str.split(",",expand=True)
    df5 = df5.drop(columns=cols[1:])
    df6 = pd.concat([df4,df5]).sort_values(by="gameId").reset_index(drop=True)
    df6.iloc[:,5:]=df6.iloc[:,5:].astype(float)
    df6.iloc[:,3:5]=df6.iloc[:,3:5].astype(int)
    data1 = df6.copy()
    stats = leaguegamelog.LeagueGameLog(player_or_team_abbreviation="T",season=season,season_type_all_star="Regular Season")
    df10 = stats.get_data_frames()[0]
    df10["HOME"] = df10['MATCHUP'].str.contains("@")
    df10["tId1"]= df10["TEAM_ID"]
    df10["gameId"]= df10["GAME_ID"]
    df11 = df10[["gameId","tId1","HOME"]].sort_values(by="gameId").reset_index(drop=True)
    df11[["gameId","tId1"]] = df11[["gameId","tId1"]].astype(int)
    data = pd.merge(data1,df11)
    return data

def process_results(data,results_adj,intercept):
    data["pts1"] = data["ORtg1"] * data["poss1"]
    data["pts2"] = data["DRtg1"] * data["poss1"]
    off_prior = data.groupby(["tId1"])[["poss1","pts1"]].agg("sum").reset_index()
    def_prior = data.groupby(["tId1"])[["poss1","pts2"]].agg("sum").reset_index()
    off_prior["OFF"] = off_prior["pts1"] / off_prior["poss1"] 
    off_prior = off_prior[["tId1","OFF"]]
    def_prior["DEF"] = def_prior["pts2"] / def_prior["poss1"] 
    def_prior = def_prior[["tId1","DEF"]]
    results_net = pd.merge(off_prior,def_prior,on=["tId1"])
    results_net["NET"] = results_net["OFF"] - results_net["DEF"] 
    results_net.rename(columns={"tId1":"tId"},inplace=True)
    results_net = results_net.astype(float).round(2)
    results_net["tId"] = results_net["tId"].astype(int)
    ortg_mean = data["pts1"].sum()/data["poss1"].sum()
    drtg_mean = data["pts2"].sum()/data["poss1"].sum()    
    results_adj["tId"] = results_adj["tId"].astype(int)
    results_comb = pd.merge(results_net,results_adj,on=["tId"])
    results_comb["aOFF"] = results_comb["aOFF"] + intercept
    results_comb["aDEF"] = results_comb["aDEF"] + intercept
    results_comb["oSOS"] = results_comb["aOFF"] -results_comb["OFF"]
    results_comb["dSOS"] = results_comb["DEF"] -results_comb["aDEF"]
    results_comb["SOS"] = results_comb["oSOS"] + results_comb["dSOS"]
    results_comb.iloc[:,1:] = results_comb.iloc[:,1:].round(1)
    # results = results_comb[["Team","OFF","oSOS","aOFF","DEF","dSOS","aDEF","NET","SOS","aNET"]]
    results = results_comb[["Team","OFF","DEF","NET","aOFF","aDEF","aNET"]]
    results = results.sort_values(by="aNET",ascending=0).reset_index(drop=True)
    return results,ortg_mean,drtg_mean

def map_teams(row_in, teams,scale):
    t1 = row_in[0]
    t2 = row_in[1]

    rowOut = np.zeros([len(teams) * 3])
    rowOut[teams.index(t1)] = scale
    rowOut[teams.index(t2) + len(teams)] = scale

    return rowOut

def convert_to_matricies(possessions, name, teams,scale = 1):
    # extract only the columns we need
    # Convert the columns of player ids into a numpy matrix
    stints_x_base = possessions[['tId1', 'tId2']].to_numpy()
    # Apply our mapping function to the numpy matrix
    stint_X_rows = np.apply_along_axis(map_teams, 1, stints_x_base, teams,scale=scale)
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
    model = clf.fit(train_x, train_y,)

    # convert our list of players into a mx1 matrix
    team_arr = np.transpose(np.array(teams_list).reshape(1, len(teams_list)))

    # extract our coefficients into the offensive and defensive parts
    coef_offensive_array = model.coef_[0:len(teams_list)][np.newaxis].T
    coef_defensive_array = model.coef_[len(teams_list):2*len(teams_list)][np.newaxis].T
    # concatenate the offensive and defensive values with the playey ids into a mx3 matrix
    team_id_with_coef = np.concatenate([team_arr, coef_offensive_array, coef_defensive_array], axis=1)
    # build a dataframe from our matrix
    teams_coef = pd.DataFrame(team_id_with_coef)
    intercept = model.intercept_
    teams_coef.columns = ["tId","aOFF","aDEF"]
    teams_coef["aNET"] = teams_coef["aOFF"] - teams_coef["aDEF"]
    teams_coef["aOFF"] = teams_coef["aOFF"] 
    teams_coef["aDEF"] = teams_coef["aDEF"] 
    teams_coef['Team']=teams_coef['tId'].map(teams_dict)
    results = teams_coef[["tId","Team","aOFF","aDEF","aNET"]]
    results = results.sort_values(by=['aNET'],ascending=False).reset_index(drop=True)
    return results,model,intercept

data = get_ratings(2023)
train_x, train_y = convert_to_matricies(data, "ORtg1", teams_list,scale=1/2)
n = 1.5
lambdas_net = [.01*n, .05*n, 0.1*n]
results_adj,model,intercept = calculate_netrtg(train_x, train_y, lambdas_net, teams_list)
results,ortg_mean,drtg_mean = process_results(data,results_adj,intercept)
results["OFF_R"] = results["OFF"].rank(ascending=False).astype(int)
results["DEF_R"] = results["DEF"].rank(ascending=True).astype(int)
results["NET_R"] = results["NET"].rank(ascending=False).astype(int)
results["aOFF_R"] = results["aOFF"].rank(ascending=False).astype(int)
results["aDEF_R"] = results["aDEF"].rank(ascending=True).astype(int)
results["aNET_R"] = results["aNET"].rank(ascending=False).astype(int)

results.to_csv(export_DIR + "NBA_Adj_Ratings_2023_2024.csv",index=False)

subprocess.run(["git", "add", "."],cwd=export_DIR)
subprocess.run(["git", "commit", "-m","update NBA Adj Ratings"],cwd=export_DIR)
subprocess.run(["git", "push"],cwd=export_DIR)