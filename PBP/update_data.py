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
season_yr = "2023"
season_type = "Regular Season"
#Choose league here
leagues = ['nba','gleague','wnba']
leagues = ['nba','gleague']
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
        "Boxscore": {"source": "web", "data_provider": "data_nba"},
        "Possessions": {"source": "web", "data_provider": "data_nba"},
        "dir": "C:/Users/pansr/Documents/Sra_Coding/NBA/pbpdata"
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
    print('Number of bad games: ',len(bad_games_list))