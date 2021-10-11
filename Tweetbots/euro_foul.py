import tweepy
import json
import os, sys
import matplotlib.pyplot as plt
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath("__file__"))))
sys.path.append((os.path.dirname(os.path.abspath("__file__"))))
from nbafuns import *
import pandas as pd
import numpy as np
from collections import Counter
from functools import reduce
import itertools
from nba_api.stats.static import teams
from pbpstats.client import Client
from tqdm import tqdm

from pbpstats.client import Client

settings = {
    "Games": {"source": "web", "data_provider": "data_nba"},
     "dir": "G:/My Drive/Sra_coding/NBA/pbpdata",
}
client = Client(settings)
# ID of all games for 2020-21 Season
league = "nba"
season_yr = "2021"
season_type = "Regular Season"
season = client.Season(league, season_yr, season_type)
games_id = []

for final_game in season.games.final_games:
    games_id.append(final_game['game_id'])
print('Number of games: ',len(games_id))

settings = {
    "Boxscore": {"source": "file", "data_provider": "data_nba"},
    "Possessions": {"source": "file", "data_provider": "data_nba"},
    "dir": "G:/My Drive/Sra_coding/NBA/pbpdata"
}
client = Client(settings)
games_list = []
bad_games_list = []
for gameid in tqdm(games_id):
    try:
        games_list.append(client.Game(gameid))
    except:
        # print(gameid)
        bad_games_list.append(gameid)
        continue
print("Number of Bad Games: ",len(bad_games_list))

year = int(season_yr)
player_dict = get_players(league = 'NBA', from_year = year, to_year = year)
team_dict = teams.get_teams() # Creating Team Dictionary

from pbpstats.resources.enhanced_pbp import Foul
from pbpstats.resources.enhanced_pbp import Turnover
from pbpstats.resources.enhanced_pbp import FieldGoal
pos_store = []
TO_Miss_pID = []
Foul_pID = []
Foul_tID = []
for game in games_list:
    for possession in game.possessions.items:
        for possession_event in possession.events:
            if isinstance(possession_event, Foul) and (isinstance(possession_event.previous_event, Turnover) or  (isinstance(possession_event.previous_event, FieldGoal) and not possession_event.previous_event.is_made)) and possession_event.seconds_since_previous_event <= 5:
                pos_store.append(possession)
                TO_Miss_pID.append(possession_event.previous_event.player1_id)
                # print ("Turnover/Missed Shot Player: {0}".format(possession_event.previous_event.player1_id))
                Foul_pID.append(possession_event.player1_id)
                Foul_tID.append(possession_event.team_id)
                # print ("Foul Player: {0}".format(possession_event.player1_id))


Team_Name = [] 
a = Foul_tID
Foul_tID1, Fouls = np.unique(a, return_counts=True)  
for tID in Foul_tID1:  
    Team_Name.append([team['full_name'] for team in team_dict if team['id'] == tID])
Team_Name = list(itertools.chain(*Team_Name))

data_euro = pd.DataFrame({'Foul_tID':Foul_tID1,'Team':Team_Name,'Fouls':Fouls})
data_euro['rank'] = data_euro['Fouls'].rank(ascending=False) 
data_euro = data_euro.sort_values(by=['rank'])
data_euro_plot = data_euro.drop(columns=['Foul_tID', 'rank'])
data_euro_plot = data_euro_plot.head(10)

fig,ax = render_mpl_table(data_euro_plot, header_columns=0, col_width=3.0)
ax.set_title(f"Euro Fouls: 2020-21 NBA Season",fontsize=18)
fig.savefig("G:/My Drive/Sra_coding/NBA/Tweetbots/Euro_Foul.png")

f = open('.G:/My Drive/Sra_coding/NBA/Tweetbots/twitter_keys.json')
twitter_auth_keys = json.load(f)

auth = tweepy.OAuthHandler(
            twitter_auth_keys['consumer_key'],
            twitter_auth_keys['consumer_secret']
            )
auth.set_access_token(
            twitter_auth_keys['access_token'],
            twitter_auth_keys['access_token_secret']
            )
api = tweepy.API(auth)


tweet = "Euro Fouls leaderboard for the 2021-22 NBA Season\n #basketballobservations"
media = api.media_upload("G:/My Drive/Sra_coding/NBA/Tweetbots/Euro_Foul.png")
post_result = api.update_status(status=tweet, media_ids=[media.media_id])
