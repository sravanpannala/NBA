import tweepy
import json
import pandas as pd
import itertools

from nba_api.stats.endpoints.leaguedashteamshotlocations import LeagueDashTeamShotLocations
from nba_api.stats.endpoints.leaguedashplayerptshot import LeagueDashPlayerPtShot
from nba_api.stats.endpoints.shotchartdetail import ShotChartDetail
import os, sys
sys.path.append((os.path.dirname(os.path.abspath("__file__"))))
print(sys.path)
from nbafuns import *
league = 'NBA'
team_name = 'Memphis Grizzlies'
team_id = 1610612763
season = '2021-22'
season_type = 'Pre Season'

team_data = LeagueDashTeamShotLocations(per_mode_detailed='Totals', 
                                        distance_range = "By Zone", rank ='Y',
                                        season=season, season_type_all_star=season_type)

tstats = team_data.get_dict()
theaders = tstats['resultSets']['headers']
col_skip = theaders[0]['columnsToSkip']
col_span = theaders[0]['columnSpan']
shot_types = theaders[0]['columnNames']
shot_columns = theaders[1]['columnNames']#[col_skip:]
s_key = shot_columns[:col_span+col_skip]
df_list = list()
for i in range(len(shot_types)):
    df = pd.DataFrame(columns=s_key)
    for j in range(30):
        shot_values = tstats['resultSets']['rowSet'][j][col_skip:]
        s_val0 = tstats['resultSets']['rowSet'][j][:col_skip]
        s_val1 = shot_values[i*col_span:(i+1)*col_span]
        s_val = list(itertools.chain(*[s_val0,s_val1]))
        df.loc[j]=s_val
    df_list.append(df)

c3_l = df_list[3]
c3_r = df_list[4]
abv3 = df_list[5]

abv3['Tot'] = c3_l['FGM']+c3_r['FGM']+abv3['FGM']

c3_l['rank'] = c3_l['FGM'].rank(ascending=False) 
c3_l_rank = int(c3_l[c3_l['TEAM_NAME'] == team_name]['rank'])
# print(c3_l_rank)
c3_r['rank'] = c3_r['FGM'].rank(ascending=False) 
c3_r_rank = int(c3_r[c3_r['TEAM_NAME'] == team_name]['rank'])
# print(c3_r_rank)
abv3['rank'] = abv3['FGM'].rank(ascending=False) 
abv3_rank = int(abv3[abv3['TEAM_NAME'] == team_name]['rank'])
# print(abv3_rank)
abv3['tot_rank'] = abv3['Tot'].rank(ascending=False) 
tot_rank = int(abv3[abv3['TEAM_NAME'] == team_name]['tot_rank'])
# print(tot_rank)
team_shotchart = ShotChartDetail(team_id=team_id, player_id=0, context_measure_simple='FG3A', 
                                season_nullable=season, season_type_all_star=season_type)

shots_df = team_shotchart.get_data_frames()[0]
shots_df.LOC_X = -shots_df.LOC_X
league_avg = team_shotchart.get_data_frames()[1]
binned_df = create_bins(data_frame=shots_df, league_average=league_avg)
data_frame = binned_df
dropped_dups = data_frame.drop_duplicates(subset=['BIN_LOC_X', 'BIN_LOC_Y'], keep='first')
dropped_dups = dropped_dups.loc[dropped_dups.BIN_LOC_Y < 417.5]
dropped_dups = dropped_dups.loc[dropped_dups.LOC_RAW_COUNTS > 1]

bball_gray = '#312f30'
bball_white = '#dddee0'
bball_orange = '#f87c24'
bball_light_orange = '#fbaf7b'
bball_black = '#000010'
dark_grey = '#282828'

colorscale = 'Plasma'

fig = go.Figure()

draw_plotly_court(fig,lw=1,margins=13,lcolor=bball_orange)
fig.add_trace(go.Scatter(
    x=dropped_dups.BIN_LOC_X, y=dropped_dups.BIN_LOC_Y, mode='markers', name='markers',
    text = dropped_dups.LOC_ZONE_PERCENTAGE	,
    marker=dict(
        size=dropped_dups.LOC_COUNTS, sizemode='area', sizeref=1.5, 
        sizemin=2.5,
        color=dropped_dups.PCT_LEAGUE_COMPARISON_ZONE, colorscale=colorscale,
        colorbar=dict(
            thickness=15,
            x=0.85,
            y=0.87,
            yanchor='middle',
            len=0.2,
            title=dict(
                text="<B>Accuracy</B>",
                font=dict(
                    size=11,
                    color='White'
                ),
            ),
            tickvals=[-10, 0, 10],
            ticktext=['Worse','Average','Better'],
            tickfont=dict(
                size=11,
                color='White'
            )
        ),
        cmin=-10, cmax=10,
        line=dict(width=0.5, color='White'), symbol='hexagon',
    ),
    hovertemplate ='<i>FG%</i>: %{text:.0f}<extra></extra>',
))
layout_update_plotly(fig,team_name,season, league,season_type, bball_black)
fig.write_image("Hex Map {0} {1}.png".format(team_name,season),scale=5)
# fig.show()

f = open('./tweetbots/twitter_keys.json')
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


tweet = "Memphis Grizzlies {} 3PT Makes Ranks:\nLeft Corner 3: {}\n\
Right Corner 3: {}\nAbove the Break 3: {}\nTotal 3s: {}\n".format(season_type,c3_l_rank,c3_r_rank,abv3_rank,tot_rank)
media = api.media_upload("./Hex Map Memphis Grizzlies {}.png".format(season))
post_result = api.update_status(status=tweet, media_ids=[media.media_id])