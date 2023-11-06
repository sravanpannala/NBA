# Update pbp data
import pandas as pd
from tqdm import tqdm
from pbpstats.client import Client

settings = {
    "Games": {"source": "web", "data_provider": "data_nba"},
     "dir": "C:/Users/pansr/Documents/Sra_Coding/NBA/pbpdata",
}
client = Client(settings)
# Choose season here
season_yr = "2019"
season_type = "Regular Season"
#Choose league here
# leagues = ['gleague']
# leagues = ['wnba']
leagues = ['nba']
for league in leagues:
    print(league)
    season = client.Season(league, season_yr, season_type)
    games_id = []
    k = 0
    for final_game in season.games.final_games:
        k += 1
        games_id.append(final_game['game_id'])

    print('Number of games: ',len(games_id))
    settings = {
        "Boxscore": {"source": "file", "data_provider": "data_nba"},
        "Possessions": {"source": "file", "data_provider": "data_nba"},
        "dir": "C:/Users/pansr/Documents/Sra_Coding/NBA/pbpdata"
    }
    client = Client(settings)
    games_list_online = []
    error_list = []
    bad_games_list = []
    for gameid in tqdm(games_id):
        try:
            client.Game(gameid)
        except Exception as error:
            if "does not exist" in error.args[0] or :
                games_list_online.append(gameid)
            elif "pstsg" in error.args[0]:
                games_list_online.append(gameid)
                error_list.append(error.args[0])
            else:
                bad_games_list.append(gameid)
                error_list.append(error.args[0])
            continue
    print('Number of bad games: ',len(bad_games_list))
    print('Number of missing games: ',len(games_list_online))
    print(error_list)
    # print(games_list_online)
    settings = {
        "Boxscore": {"source": "web", "data_provider": "data_nba"},
        "Possessions": {"source": "web", "data_provider": "data_nba"},
        "dir": "C:/Users/pansr/Documents/Sra_Coding/NBA/pbpdata"
    }
    client = Client(settings)
    bad_games_list = []
    error_list = []
    for gameid in tqdm(games_list_online):
        try:
            client.Game(gameid)
        except Exception as error:
            print(error)
            error_list.append(error.args[0])
            continue
    # print(error_list)
