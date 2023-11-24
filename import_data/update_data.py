# Update pbp data
import numpy as np
import pandas as pd
from tqdm import tqdm
from itertools import product
import time 
import os, sys
sys.path.append(os.path.dirname(os.path.abspath("__file__")))
from nbafuns import *
from pbpstats.client import Client
from nba_api.stats.endpoints import leaguegamelog, boxscoreadvancedv3, boxscorefourfactorsv3
from nba_api.stats.endpoints import boxscorescoringv3,boxscoreplayertrackv3,boxscoremiscv3,boxscorehustlev2
from pbpstats.resources.enhanced_pbp import FieldGoal

data_DIR_box = "C:/Users/pansr/Documents/NBA/Leaderboards/boxscores/"
data_DIR_shot = "C:/Users/pansr/Documents/NBA/Shot_charts/ShotLocationData/"

# Update PBP Data
data_provider = "data_nba"
pbp_DIR = "C:/Users/pansr/Documents/NBA/pbpdata/"+data_provider

seasons = ["2019","2020","2021","2022","2023"]
season_types = ["Regular Season","Playoffs"]
leagues = ["nba","wnba"]
seasons = ["2023"]
season_types = ["Regular Season"]
leagues = ["nba"]
for season_yr,league,season_type in product(seasons,leagues,season_types):
    print(f"{season_yr},{league},{season_type}")
    settings = {
        "Games": {"source": "web", "data_provider": data_provider},
        "dir": pbp_DIR,
    }
    client = Client(settings)
    season = client.Season(league, season_yr, season_type)
    games_id = []
    k = 0
    for final_game in season.games.final_games:
        k += 1
        games_id.append(final_game['game_id'])

    print('Number of games: ',len(games_id))
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
    print('Number of bad games: ',len(bad_games_list))
    print('Number of missing games: ',len(games_list_online))
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
def get_gameids(season,name):
    stats = leaguegamelog.LeagueGameLog(player_or_team_abbreviation="T",season=season,season_type_all_star="Regular Season")
    df = stats.get_data_frames()[0]
    game_ids1 = df["GAME_ID"].tolist()
    game_ids1  = np.unique(game_ids1)
    try:
        dfr = pd.read_csv(data_DIR_box+"NBA_BoxScores_"+name+"_"+season+".csv")
        dfr = dfr.drop(dfr.columns[0],axis=1)
        game_ids3 = dfr["gameId"].astype(str).tolist()
        game_ids2 = ["00" +s for s in game_ids3]
        game_ids2  = np.unique(game_ids2)
        game_ids = list(set(game_ids1).difference(game_ids2))
    except:
        game_ids = game_ids1
        dfr = pd.DataFrame()
    return game_ids,dfr

def get_game_box(game_ids,fun):
    df_ap = []
    for game_id in tqdm(game_ids):
        for ii in range(5):
            time.sleep(0.6)
            try:
                stats = fun(game_id=game_id)
                df1 = stats.get_data_frames()[1]
                df_ap.append(df1)
                break
            except:
                print(game_id)
                # time.sleep(0.6)
                continue
    return df_ap

def get_boxscores(seasons,fun,name):
    for season in seasons:  
        game_ids,dfr = get_gameids(season,name)
        try:
            df_ap = get_game_box(game_ids,fun)
            df1 = pd.concat(df_ap)
            df = pd.concat([dfr,df1])
            df["gameId"] = df["gameId"].astype(int)
            df = df.sort_values(by=["gameId"]).reset_index(drop=True)
            df.to_csv(data_DIR_box+"NBA_BoxScores_"+name+"_"+season+".csv")
        except:
            continue

season_start = 2023
season_end = 2023
seasons = np.arange(season_start,season_end+1,1).astype(str)


fun = boxscoreadvancedv3.BoxScoreAdvancedV3
name = "Adv"
print("BoxScore " + name)
get_boxscores(seasons,fun,name)

fun = boxscorehustlev2.BoxScoreHustleV2
name = "Hustle"
print("BoxScore " + name)
get_boxscores(seasons,fun,name)

fun = boxscoremiscv3.BoxScoreMiscV3
name = "Misc"
print("BoxScore " + name)
get_boxscores(seasons,fun,name)

fun = boxscoreplayertrackv3.BoxScorePlayerTrackV3
name = "Track"
print("BoxScore " + name)
get_boxscores(seasons,fun,name)

fun = boxscorescoringv3.BoxScoreScoringV3
name = "Scoring"
print("BoxScore " + name)
get_boxscores(seasons,fun,name)

# Import Shot Details PBP
def get_loc_data(games_list,player_dict,team_dict):
    game_id, period, clock, seconds_remaining,poss_length = [],[],[],[],[]
    score_margin = []
    team_id, player1_id, player2_id= [],[],[]
    locX, locY, distance, shot_value, shot_type = [],[],[],[],[]
    is_made, is_putback, is_assisted, is_heave, is_and1  = [],[],[],[],[]
    is_second_chance_event = []
    pos_store = []
    for game in tqdm(games_list):
        for possession in game.possessions.items:
            for possession_event in possession.events:
                if isinstance(possession_event, FieldGoal):
                    try: 
                        game_id.append(possession_event.game_id)
                        period.append(possession_event.period)
                        clock.append(possession_event.clock)
                        seconds_remaining.append(possession_event.seconds_remaining)
                        poss_length.append(possession_event.seconds_since_previous_event)
                        score_margin.append(possession_event.score_margin)
                        team_id.append(possession_event.team_id)
                        player1_id.append(possession_event.player1_id)
                        locX.append(possession_event.locX)
                        locY.append(possession_event.locY)
                        distance.append(possession_event.distance)
                        shot_value.append(possession_event.shot_value)
                        shot_type.append(possession_event.shot_type)
                        is_made.append(possession_event.is_made)
                        is_and1.append(possession_event.is_and1)
                        is_second_chance_event.append(possession_event.is_second_chance_event)
                        is_heave.append(possession_event.is_heave)
                        is_assisted.append(possession_event.is_assisted)
                        if possession_event.is_assisted:
                            player2_id.append(possession_event.player2_id)
                        else:
                            player2_id.append(0)
                        is_putback.append(possession_event.is_putback)
                    except:
                        is_putback.append(False)
    player1_name = np.array([player_dict.get(x,np.nan) for x in player1_id])  
    player2_name = np.array([player_dict.get(x,np.nan) for x in player2_id])  
    team_name = [team['Team'] for team, tID in product(team_dict,team_id) if team['TeamID'] ==tID]
    data = pd.DataFrame({'game_id':game_id,'period':period,'clock':clock,
                        'seconds_remaining':seconds_remaining,'poss_length':poss_length,'score_margin':score_margin,
                        'team_id':team_id,'team_name':team_name,'player_id':player1_id,
                        'player_name':player1_name,'locX': locX,'locY':locY, 'distance':distance,
                        'shot_value':shot_value,'shot_type':shot_type,
                        'is_made':is_made,'is_and1':is_and1,'is_heave':is_heave,'is_putback':is_putback,
                        'is_assisted':is_assisted,'player_ast_id':player2_id,'player_ast_name':player2_name
                        })
    return data

print("Shot Details")
data_provider = "data_nba"
league = "NBA"
season_type = "Regular Season"
seasons = np.arange(2023,2024,1).astype(str)
for season in seasons:
    games_id = pbp_season(league=league,season_yr=season,season_type=season_type,data_provider=data_provider)
    games_list = pbp_games(games_id,data_provider=data_provider)
    player_dict = get_players_pbp(league=league)
    team_dict = teams.get_teams()
    team_dict = get_teams(league = league)
    data = get_loc_data(games_list,player_dict,team_dict)
    data.to_csv(data_DIR_shot+f"{league}_Shot_Loc_"+season+".csv",index=False)