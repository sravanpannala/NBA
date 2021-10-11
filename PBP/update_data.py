import pandas as pd
from tqdm import tqdm
from pbpstats.client import Client

settings = {
    "Games": {"source": "web", "data_provider": "data_nba"},
     "dir": "G:/My Drive/Sra_coding/NBA/pbpdata",
}
client = Client(settings)
# ID of all games for 2020-21 Season
season_yr = "2021"
season_type = "Regular Season"
leagues = ['nba','gleague']
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
        "dir": "G:/My Drive/Sra_coding/NBA/pbpdata"
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
    print(len(bad_games_list))