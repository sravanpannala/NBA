# default packages for system, data and time
import os, sys, pathlib
import pandas as pd
import numpy as np
import scipy
import time
from time import perf_counter
import datetime as dt
from datetime import datetime

# scraping
import requests
from bs4 import BeautifulSoup

# other convenience packages
import json
from IPython.display import clear_output
from IPython.core.display import HTML
from collections import Counter
import operator
from functools import reduce
from itertools import product, chain
from tqdm import tqdm
from thefuzz import fuzz, process
import icecream as ic

# save/load data
import dill
import zstandard as zstd

# matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Arc
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
#seaborn
import seaborn as sns
# plotly
import plotly.graph_objects as go
import plotly.express as px
# plotnine
from plotnine import ggplot, aes, ggsave, themes, theme, labs
from plotnine import geom_point, geom_line, geom_hline, geom_vline
from plotnine import geom_bar, geom_smooth, geom_abline, geom_col
from plotnine import geom_boxplot, geom_violin, geom_density
from plotnine import geom_jitter, geom_dotplot, geom_segment, geom_tile
from plotnine import geom_text, annotate
from plotnine import geom_histogram, stat_bin, stat_density, geom_rect
from plotnine import element_rect, element_blank, element_text, element_line
from plotnine import coord_flip, lims, guides, coord_cartesian, facet_wrap
from plotnine import ylim, scale_y_continuous, scale_y_reverse, scale_x_reverse
from plotnine import xlim, scale_x_continuous, scale_x_discrete, scale_x_date
from plotnine import scale_color_manual, scale_color_discrete, scale_color_identity
from plotnine import scale_color_gradientn, scale_color_cmap, scale_color_brewer
from plotnine import scale_fill_manual, scale_fill_gradient
from plotnine import theme_xkcd, theme_classic, theme_538, watermark
from plotnine import arrow
from plotnine import after_stat, position_jitter, position_jitterdodge
from plotnine.geoms.geom import geom
from plotnine.doctools import document
from mizani.formatters import percent_format
# great tables
from great_tables import GT, md, html
# save images from dataframe
# import imgkit
# from html2image import Html2Image
# hti = Html2Image()

# nba api
import nba_api
from nba_api.stats.static import teams as nba_teams
from nba_api.stats.endpoints import leaguegamelog, leaguedashteamstats
# pbpstats
from pbpstats.client import Client
from pbpstats.resources.enhanced_pbp import Foul, Turnover, FieldGoal, Rebound
# numba
from numba import jit, njit
from numba.core.errors import NumbaDeprecationWarning, NumbaPendingDeprecationWarning
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=NumbaDeprecationWarning)
warnings.simplefilter(action='ignore', category=NumbaPendingDeprecationWarning)

pd.options.mode.chained_assignment =  None

sns.set_theme(style="whitegrid")

# plotnine themes
theme_idv = theme_xkcd(base_size=16,scale=0,length=2,randomness=0,stroke_size=3)
theme_idv += theme(
    text=element_text(family=["Comic Sans MS","xkcd"]),
    plot_title=element_text(face="bold", size=20),
    plot_caption=element_text(size=10,ha='left'),
)

pnba = labs(
    caption="bsky:@sradjoker.cc | x:@SravanNBA | source: nba.com/stats",
)
ppbp = labs(
    caption="bsky:@sradjoker.cc | x:@SravanNBA | source: pbpstats",
)

os.environ["R_HOME"] = "C:\\Program Files\\R\\R-4.4.2\\"
pbp_DIR = "C:/Users/pansr/Documents/NBA/pbpdata/"


# function to get player info as dictionary using pbpstats database
def get_players_pbp(league="NBA"):
    PATH = pathlib.Path(__file__)
    DATA_PATH = PATH.joinpath("../data").resolve()
    with open(DATA_PATH.joinpath("{0}.json".format(league))) as f:
        data = json.load(f)
    player_dict = {int(k): v for k, v in data.items()}
    idx_bad = []
    # idx_bad = [2168,2345,2610,2794,202435,202443,202603,203606,203624,1627310,1610612745,873,1301,1371,1672,1778,1941,203152,204005,1610612746,1658,2152,1610612737,1610612741,1610612744,1610612747,1610612749,1610612750,1610612756,1610612762,1243,1256,1320,1335,1787,2719,201690,201690,202101,202105,203535,204085,1610612751,1610612752,1610612755]
    for idx in idx_bad:
        player_dict[idx] = np.nan
    return player_dict

def get_pID_pbp(league="NBA"):
    PATH = pathlib.Path(__file__)
    DATA_PATH = PATH.joinpath("../data").resolve()
    with open(DATA_PATH.joinpath("{0}.json".format(league))) as f:
        data = json.load(f)
    pID_dict = {v: int(k) for k, v in data.items()}
    return pID_dict

# get player ID for player name
def get_pID(player, league="NBA"):
    PATH = pathlib.Path(__file__)
    DATA_PATH = PATH.joinpath("../data").resolve()
    with open(DATA_PATH.joinpath("{0}.json".format(league))) as f:
        data = json.load(f)
    pID_dict = {v: int(k) for k, v in data.items()}
    pID = pID_dict.get(player, np.nan)
    return pID

def get_ss(year):
    season_str = str(year) + "-" + str(year+1)[-2:]
    return season_str

# function to get player info as dictionary using NBA database
def get_players(league="NBA", from_year=2020, to_year=2020):
    PATH = pathlib.Path(__file__)
    DATA_PATH = PATH.joinpath("../data").resolve()
    data = pd.read_csv(DATA_PATH.joinpath("{0}_players_database.csv".format(league)))
    player_data = data[(data["From"] <= from_year) & (data["To"] >= to_year)]
    player_data = player_data.reset_index(drop=True)
    player_dict = player_data.to_dict(orient="records")
    return player_dict

def get_missing_pId(player, player_dict):
    pId = process.extract(player, player_dict, scorer=fuzz.partial_ratio, limit=1)[0][2]
    return pId

def get_box(PT="P",measure="Base",cum=False,seasons=[2024]):
    PATH = pathlib.Path(__file__)
    DATA_PATH = PATH.joinpath("../data/box").resolve()
    join = ""
    if cum:
        join = "Cum_"
    dfa = []
    for season in seasons:
        loc = f"NBA_Box_{PT}_"+join+f"{measure}_{season}.parquet"
        df1 = pd.read_parquet(DATA_PATH.joinpath(loc))
        df1.columns = map(str.lower,df1.columns)
        df1["season"] = season +1
        dfa.append(df1)
    df2 = pd.concat(dfa)
    return df2

# function to get team info as dictionary using NBA database
def get_teams(league="NBA"):
    PATH = pathlib.Path(__file__)
    DATA_PATH = PATH.joinpath("../data").resolve()
    team_data = pd.read_csv(DATA_PATH.joinpath("{0}_teams_database.csv".format(league)))
    team_list = team_data["TeamID"].tolist()
    team_dict1 = team_data.to_dict(orient="records")
    team_dict = {team["TeamID"]: team["Team"] for team in team_dict1}
    return team_dict, team_list

# Function to dd team info to dataframes
def add_tinfo(df,on="team_name"):
    PATH = pathlib.Path(__file__)
    DATA_PATH = PATH.joinpath("../data").resolve()
    dft = pd.read_csv(DATA_PATH.joinpath("NBA_teams_colors_logos.csv"))
    df1 = pd.merge(df,dft,on=on)
    return df1


# pbp function to get all games list for a season
def pbp_season(
    league="NBA",
    season_yr="2023",
    season_type="Regular Season",
    data_provider="data_nba",
):
    settings = {
        "Games": {"source": "file", "data_provider": data_provider},
        "dir": pbp_DIR + data_provider,
    }
    client = Client(settings)
    season = client.Season(league, season_yr, season_type)
    games_id = []
    for final_game in season.games.final_games:
        games_id.append(final_game["game_id"])
    print("Number of games: ", len(games_id))
    return games_id


# function to get all games pbp data for a season
def pbp_games(games_id, data_provider="data_nba"):
    settings = {
        "Boxscore": {"source": "file", "data_provider": data_provider},
        "Possessions": {"source": "file", "data_provider": data_provider},
        "dir": pbp_DIR + data_provider,
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
    print("Number of bad games: ", len(bad_games_list))

    return games_list


# function to rank pbp data like fouls, assists etc
def rank_data_pbp(IDs, player_dict, team_dict, sort="Player", var="Fouls"):
    ID, items = np.unique(IDs, return_counts=True)
    if sort == "Player":
        ppl = np.array([player_dict.get(x, np.nan) for x in ID])
    elif sort == "Team":
        ppl = [
            team["full_name"] for team, tID in zip(team_dict, ID) if team["id"] == tID
        ]
    df = pd.DataFrame({sort: ppl, "pID": ID,var: items})
    df1 = df.sort_values(by=[var], ascending=False)
    df1 = df1.reset_index(drop=True)
    df1["#"] = df1.index + 1
    df2 = df1[["#", "pID", sort, var]]
    # df3 = df2.iloc[:10]

    return df2


# Amazing function by Bradley Fay for plotting the nba court
# source: https://github.com/bradleyfay/py-Goldsberry/blob/master/docs/Visualizing%20NBA%20Shots%20with%20py-Goldsberry.ipynb
def draw_court(ax=None, color="black", lw=2, outer_lines=True, z=3):
    # If an axes object isn't provided to plot onto, just get current one
    if ax is None:
        ax = plt.gca()

    # Create the various parts of an NBA basketball court

    # Create the basketball hoop
    # Diameter of a hoop is 18" so it has a radius of 9", which is a value
    # 7.5 in our coordinate system
    hoop = Circle((0, 0), radius=7.5, linewidth=lw, color=color, fill=False, zorder=z)

    # Create backboard
    backboard = Rectangle((-30, -7.5), 60, -1, linewidth=lw, color=color, zorder=z)

    # The paint
    # Create the outer box 0f the paint, width=16ft, height=19ft
    outer_box = Rectangle(
        (-80, -47.5), 160, 190, linewidth=lw, color=color, fill=False, zorder=z
    )
    # Create the inner box of the paint, widt=12ft, height=19ft
    inner_box = Rectangle(
        (-60, -47.5), 120, 190, linewidth=lw, color=color, fill=False, zorder=z
    )

    # Create free throw top arc
    top_free_throw = Arc(
        (0, 142.5),
        120,
        120,
        theta1=0,
        theta2=180,
        linewidth=lw,
        color=color,
        fill=False,
        zorder=z,
    )
    # Create free throw bottom arc
    bottom_free_throw = Arc(
        (0, 142.5),
        120,
        120,
        theta1=180,
        theta2=0,
        linewidth=lw,
        color=color,
        linestyle="dashed",
        zorder=z,
    )
    # Restricted Zone, it is an arc with 4ft radius from center of the hoop
    restricted = Arc(
        (0, 0), 80, 80, theta1=0, theta2=180, linewidth=lw, color=color, zorder=z
    )

    # Three point line
    # Create the side 3pt lines, they are 14ft long before they begin to arc
    corner_three_a = Rectangle(
        (-220, -47.5), 0, 138, linewidth=lw, color=color, zorder=z
    )
    corner_three_b = Rectangle(
        (220, -47.5), 0, 138, linewidth=lw, color=color, zorder=z
    )
    # 3pt arc - center of arc will be the hoop, arc is 23'9" away from hoop
    # I just played around with the theta values until they lined up with the
    # threes
    three_arc = Arc(
        (0, 0),
        475,
        475,
        theta1=22.13,
        theta2=157.87,
        linewidth=lw,
        color=color,
        zorder=z,
    )

    # Center Court
    center_outer_arc = Arc(
        (0, 422), 120, 120, theta1=180, theta2=0, linewidth=lw, color=color, zorder=z
    )
    center_inner_arc = Arc(
        (0, 422), 40, 40, theta1=180, theta2=0, linewidth=lw, color=color, zorder=z
    )

    # List of the court elements to be plotted onto the axes
    court_elements = [
        hoop,
        backboard,
        outer_box,
        inner_box,
        top_free_throw,
        bottom_free_throw,
        restricted,
        corner_three_a,
        corner_three_b,
        three_arc,
        center_outer_arc,
        center_inner_arc,
    ]
    if outer_lines:
        # Draw the half court line, baseline and side out bound lines
        outer_lines = Rectangle(
            (-249, -48), 498, 470, linewidth=lw, color=color, fill=None
        )
        court_elements.append(outer_lines)

    # Add the court elements onto the axes
    for element in court_elements:
        ax.add_patch(element)

    return ax

# creating bins for hex shot chart
def create_bins(
    data_frame,
    bin_number_x=30,
    bin_number_y=300 / (500.0 / 30.0),
    league_average=None,
    width=500,
    height=300,
    norm_x=250,
    norm_y=48,
):
    """
    Method which creates bins the dataset into squared grid. This is used so that plot looks nicer than the raw
    locations plot. Along with binning the data, the percentages per zones and for each bin are calculated here
    and added to the copy of data_frame object so they can be used for plotting later.

    :return: Returns the copied  data_frame pandas DataFrame object with additional info about the shots.
    """
    # Binned x and y coordinates
    x_bins, y_bins = [], []
    # Copying the dataset to add more data
    copied_df = data_frame.copy()
    # Keys are basically x_bin and y_bin
    keys = []
    # Counter of shots and shots made per locations
    location_counts, location_made = Counter(), Counter()
    # be found

    # Size of elements in bin, they should be the same
    bin_size_x = float(width) / float(bin_number_x)
    bin_size_y = float(height) / float(bin_number_y)
    # List for locations of shots
    locations_annotated = []
    # Counter of shots and shots made per zone
    zones_counts, zones_made = Counter(), Counter()

    # Maximum size of an element in one bin
    max_size = int((int(bin_size_x) - 1) * (int(bin_size_y) - 1))

    # Keys that are in restricted area will be stored here, this will be used for finding maximum number of shots
    restricted_area_keys = []

    # Dictionary which will determine the color of marker in bin
    percentage_color_dict = {}

    for i in range(len(data_frame)):
        # Row from data frame
        row = data_frame.iloc[i]

        x_shot_orig, y_shot_orig = row.LOC_X, row.LOC_Y

        # Normalize
        x_shot = x_shot_orig + norm_x  # to put minimum to zero
        y_shot = y_shot_orig + norm_y  # to put minimum to zero

        # bin_index = (x_shot / w) * bin_size
        curr_x_bin = 0 if x_shot == 0 else int((x_shot / float(width)) * bin_number_x)
        curr_y_bin = 0 if y_shot == 0 else int((y_shot / float(height)) * bin_number_y)

        # Key for dicts
        key = (curr_x_bin, curr_y_bin)

        if row.SHOT_ZONE_BASIC == "Restricted Area":
            restricted_area_keys.append(key)

        # Counting number of shots made and shots shot
        keys.append(key)
        location_counts[key] += 1
        location_made[key] += row.SHOT_MADE_FLAG

        basic_shot_zone, shot_zone_area = row.SHOT_ZONE_BASIC, row.SHOT_ZONE_AREA
        zone_dist = row.SHOT_ZONE_RANGE

        area_code = shot_zone_area.split("(")[1].split(")")[0]
        if "3" in basic_shot_zone:
            locations_annotated.append("3" + area_code)
        elif "Paint" in basic_shot_zone:
            locations_annotated.append("P" + area_code + zone_dist[0])
        elif "Mid" in basic_shot_zone:
            locations_annotated.append("M" + area_code + zone_dist[0])
        else:
            locations_annotated.append("R" + area_code)

        # Creating key for zones
        zone_key = (basic_shot_zone, shot_zone_area, zone_dist)

        # Counting the occurences based on both bin_key and zone_key, because of that we have dict in dict
        if key in percentage_color_dict:
            if zone_key in percentage_color_dict[key]:
                percentage_color_dict[key][zone_key] = (
                    percentage_color_dict[key][zone_key] + 1
                )
            else:
                percentage_color_dict[key][zone_key] = 1
        else:
            percentage_color_dict[key] = {}
            percentage_color_dict[key][zone_key] = 1

        zones_counts[zone_key] += 1

        if row.SHOT_MADE_FLAG:
            zones_made[zone_key] += 1

    shot_locations_percentage = []  # percentage in given bin
    shot_locations_counts = []
    raw_counts = []
    # List which contains comparison for each shot with league average in that zone
    shot_comparison = []
    # List which contains comparison of player's shooting in zone vs league average
    per_zone_comparison = []
    per_zone_percentage = []

    # Finding the maximal number of shots from data
    non_ra = []
    for key in location_counts:
        if key not in restricted_area_keys:
            if location_counts[key] not in non_ra:
                non_ra.append(location_counts[key])

    sorted_non_ra = sorted(non_ra)
    max_out_of_restricted = float(sorted_non_ra[-1])

    for j in range(len(data_frame)):
        key = keys[j]
        x_bin, y_bin = key[0], key[1]
        shot_percent = float(location_made[key]) / location_counts[key]
        # shot_percent = np.clip(shot_percent, 0.3, 0.7)
        shot_locations_percentage.append(shot_percent * 100)
        if league_average is not None:
            # Getting info about zone
            # We are getting that info from
            per_zone_counter_from_percentage_color_dict = percentage_color_dict[key]
            zone_key = max(
                per_zone_counter_from_percentage_color_dict.items(),
                key=operator.itemgetter(1),
            )[0]

            shot_zone_basic = zone_key[0]
            shot_zone_area = zone_key[1]
            distance = zone_key[2]

            # Calculating the percentage in current zone
            zone_percent = (
                0.0
                if zone_key not in zones_made
                else float(zones_made[zone_key]) / float(zones_counts[zone_key])
            )

            # Retrieving league average percentage for current zone
            avg_percentage = league_average.loc[
                (league_average.SHOT_ZONE_BASIC == shot_zone_basic)
                & (league_average.SHOT_ZONE_AREA == shot_zone_area)
                & (league_average.SHOT_ZONE_RANGE == distance)
            ].FG_PCT.iloc[0]
            # Comparison of league average and each shot
            shot_comparison.append(
                np.clip((shot_percent - avg_percentage) * 100, -10, 10)
            )
            # Comparison of zone and league average
            per_zone_comparison.append(
                np.clip((zone_percent - avg_percentage) * 100, -10, 10)
            )
            # Percentage of shot in current zone, kinda inaccurate info, good for some other type of plot
            per_zone_percentage.append(zone_percent * 100)

        # Calculating value to which the markers will be scaled later on
        # The data in restricted is scaled to maximum out of restricted area, because players usually have a lot
        # more shots in restricted area
        value_to_scale = (
            max_out_of_restricted
            if location_counts[key] > max_out_of_restricted
            else location_counts[key]
        )
        # Storing the data into a list
        shot_locations_counts.append(
            (float(value_to_scale) / max_out_of_restricted) * max_size
        )

        # Count of shots per bin
        raw_counts.append(location_counts[key])

        # Middle of current and next bin is where we will place the marker in real coordinates
        unbinned_x = (
            (x_bin * float(width)) / bin_number_x
            + ((x_bin + 1) * float(width)) / bin_number_x
        ) / 2 - norm_x
        unbinned_y = (
            (y_bin * float(height)) / bin_number_y
            + ((y_bin + 1) * float(height)) / bin_number_y
        ) / 2 - norm_y

        # Adding binned locations
        x_bins.append(unbinned_x)
        y_bins.append(unbinned_y)

    # Binned locations
    copied_df["BIN_LOC_X"] = x_bins
    copied_df["BIN_LOC_Y"] = y_bins
    # Percentage comparison with league averages
    if league_average is not None:
        # Comparison of each shot with league average for that zone
        copied_df["PCT_LEAGUE_AVG_COMPARISON"] = shot_comparison
        # Comparison of each zone with league average for that zone
        copied_df["PCT_LEAGUE_COMPARISON_ZONE"] = per_zone_comparison
        # Percentage of whole zone (not in comparison with league average)
        copied_df["LOC_ZONE_PERCENTAGE"] = per_zone_percentage
    # Percentage of shots for that location
    copied_df["LOC_PERCENTAGE"] = shot_locations_percentage

    # Scaled count of shots and count of shots per bin
    copied_df["LOC_COUNTS"] = shot_locations_counts
    copied_df["LOC_RAW_COUNTS"] = raw_counts

    return copied_df

# Drawing NBA court using plotly
def draw_plotly_court(fig, lw=3, lcolor="Orange", fig_width=600, margins=10):
    # From: https://community.plot.ly/t/arc-shape-with-path/7205/5
    def ellipse_arc(
        x_center=0.0,
        y_center=0.0,
        a=10.5,
        b=10.5,
        start_angle=0.0,
        end_angle=2 * np.pi,
        N=200,
        closed=False,
    ):
        t = np.linspace(start_angle, end_angle, N)
        x = x_center + a * np.cos(t)
        y = y_center + b * np.sin(t)
        path = f"M {x[0]}, {y[0]}"
        for k in range(1, len(t)):
            path += f"L{x[k]}, {y[k]}"
        if closed:
            path += " Z"
        return path

    fig_height = fig_width * (470 + 2 * margins) / (500 + 2 * margins)
    fig.update_layout(width=fig_width, height=fig_height)

    # Set axes ranges
    fig.update_xaxes(range=[-250 - margins, 250 + margins])
    fig.update_yaxes(range=[-52.5 - margins, 417.5 + margins])

    threept_break_y = 89.47765084
    three_line_col = "#777777"
    main_line_col = "#777777"

    fig.update_layout(
        # Line Horizontal
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="white",
        plot_bgcolor="white",
        yaxis=dict(
            scaleanchor="x",
            scaleratio=1,
            showgrid=False,
            zeroline=False,
            showline=False,
            ticks="",
            showticklabels=False,
            fixedrange=True,
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=False,
            ticks="",
            showticklabels=False,
            fixedrange=True,
        ),
        shapes=[
            dict(
                type="rect",
                x0=-250,
                y0=-52.5,
                x1=250,
                y1=417.5,
                line=dict(color=lcolor, width=lw),
                # fillcolor='#333333',
                layer="above",
            ),
            dict(
                type="rect",
                x0=-80,
                y0=-52.5,
                x1=80,
                y1=137.5,
                line=dict(color=lcolor, width=lw),
                # fillcolor='#333333',
                layer="above",
            ),
            dict(
                type="rect",
                x0=-60,
                y0=-52.5,
                x1=60,
                y1=137.5,
                line=dict(color=lcolor, width=lw),
                # fillcolor='#333333',
                layer="above",
            ),
            dict(
                type="circle",
                x0=-60,
                y0=77.5,
                x1=60,
                y1=197.5,
                xref="x",
                yref="y",
                line=dict(color=lcolor, width=lw),
                # fillcolor='#dddddd',
                layer="above",
            ),
            dict(
                type="line",
                x0=-60,
                y0=137.5,
                x1=60,
                y1=137.5,
                line=dict(color=lcolor, width=lw),
                layer="above",
            ),
            dict(
                type="rect",
                x0=-2,
                y0=-7.25,
                x1=2,
                y1=-12.5,
                line=dict(color="#ec7607", width=lw),
                fillcolor="#ec7607",
            ),
            dict(
                type="circle",
                x0=-7.5,
                y0=-7.5,
                x1=7.5,
                y1=7.5,
                xref="x",
                yref="y",
                line=dict(color="#ec7607", width=lw),
            ),
            dict(
                type="line",
                x0=-30,
                y0=-12.5,
                x1=30,
                y1=-12.5,
                line=dict(color="#ec7607", width=lw),
            ),
            dict(
                type="path",
                path=ellipse_arc(a=40, b=40, start_angle=0, end_angle=np.pi),
                line=dict(color=lcolor, width=lw),
                layer="above",
            ),
            dict(
                type="path",
                path=ellipse_arc(
                    a=237.5,
                    b=237.5,
                    start_angle=0.386283101,
                    end_angle=np.pi - 0.386283101,
                ),
                line=dict(color=lcolor, width=lw),
                layer="above",
            ),
            dict(
                type="line",
                x0=-220,
                y0=-52.5,
                x1=-220,
                y1=threept_break_y,
                line=dict(color=lcolor, width=lw),
                layer="above",
            ),
            dict(
                type="line",
                x0=-220,
                y0=-52.5,
                x1=-220,
                y1=threept_break_y,
                line=dict(color=lcolor, width=lw),
                layer="above",
            ),
            dict(
                type="line",
                x0=220,
                y0=-52.5,
                x1=220,
                y1=threept_break_y,
                line=dict(color=lcolor, width=lw),
                layer="above",
            ),
            dict(
                type="path",
                path=ellipse_arc(
                    y_center=417.5, a=60, b=60, start_angle=-0, end_angle=-np.pi
                ),
                line=dict(color=lcolor, width=lw),
                layer="above",
            ),
        ],
    )
    return True


# add annotations/text to plotly hex maps
def layout_update_plotly(fig, player_name, season, league, season_type, bgcolor):
    fig.update_layout(
        plot_bgcolor=bgcolor,
        paper_bgcolor=bgcolor,
        title=dict(
            text="Shot Hex Map: {0}".format(player_name),
            y=0.975,
            x=0.06,
            xanchor="auto",
            yanchor="middle",
        ),
        font=dict(family="Arial, Tahoma, Helvetica", size=15, color="Orange"),
        annotations=[
            go.layout.Annotation(
                x=200,
                y=-65,
                showarrow=False,
                text="@SravanNBA",
                font=dict(family="Arial, Tahoma, Helvetica", size=15, color="White"),
            ),
            go.layout.Annotation(
                x=-225,
                y=400,
                showarrow=False,
                text=season + " " + league,
                xanchor="left",
                font=dict(family="Arial, Tahoma, Helvetica", size=15, color="White"),
            ),
            go.layout.Annotation(
                x=-225,
                y=380,
                showarrow=False,
                text=season_type,
                xanchor="left",
                font=dict(family="Arial, Tahoma, Helvetica", size=15, color="White"),
            ),
        ],
    )
    return True

# Download Player image and export figure scale for plotly
def import_image(league, player_id):
    if league == "NBA":
        url_image = "https://cdn.nba.com/headshots/nba/latest/260x190/{0}.png".format(
            player_id
        )
        sizex = 104 * 1.2
        sizey = 76 * 1.2
    elif league == "WNBA":
        url_image = "https://ak-static.cms.nba.com/wp-content/uploads/headshots/wnba/{0}.png".format(
            player_id
        )
        sizex = 100
        sizey = 100
    # PATH = pathlib.Path(__file__)
    # DATA_PATH = PATH.joinpath("../player_imgs").resolve()
    # target_dir = DATA_PATH
    # img_path = str(DATA_PATH.joinpath('{0}.png'.format(player_id)))
    # if f"{player_id}.png" not in os.listdir(target_dir):
    #     url = url_image
    #     response = requests.get(url)
    #     with open((img_path), 'wb') as f:
    #         f.write(response.content)
    # return str(img_path), sizex, sizey
    return url_image, sizex, sizey

@document
class geom_image(geom):
    """
    Plot Images with plotnine
    Based on geom_point 
    Instead of points, plots images at those points

    Args:
        geom : ggplot geom
    """    
    DEFAULT_AES = {"size": 0.1}#, "color": None, "fill": "#333333",
                   #"linetype": "solid", "size": 0.5 }
    DEFAULT_PARAMS = {"stat": "identity", "position": "identity",
                      "na_rm": False} # no idea if I need this
    REQUIRED_AES = {"x", "y","image"} # just need an image column

    def draw_panel(self, data, panel_params, coord, ax, **params):
        """
        assume only one image per panel,
        """
        data = coord.transform(data, panel_params)
        self.draw_unit(data, panel_params, coord, ax, **params)
    
    @staticmethod
    def draw_group(data, panel_params, coord, ax, **params):
        data = coord.transform(data, panel_params)
        units = "shape"
        for _, udata in data.groupby(units, dropna=False):
            udata.reset_index(inplace=True, drop=True)
            geom_image.draw_unit(udata, panel_params, coord, ax, **params)
    
    @staticmethod
    def draw_unit(data, panel_params, coord, ax, **params):
        for i in range(len(data)):
            img = data["image"].iloc[i]
            zoom = data["size"].iloc[i]
            ab = AnnotationBbox(
                OffsetImage(plt.imread(img), zoom=zoom),
                (data["x"].iloc[i], data["y"].iloc[i]),
                frameon=False,
            )
            ax.add_artist(ab)


def path_to_image_html(path,width=60):
    str1 = '<img src="'
    str2 = path
    str3 = f'" width="' + f'{width}' + '" >'
    return str1 + str2 + str3

# Bluesky
# PATH = pathlib.Path(__file__)
# DATA_PATH = PATH.joinpath("../").resolve()
# with open(DATA_PATH.joinpath("secret-bsky.json")) as f:
#      login_bsky = json.load(f)

# def bsky_client():
#     from atproto import Client

#     bsky = Client()
#     bsky.login(login_bsky["bsky_user"], login_bsky["bsky_pass"])
#     return bsky

# def bsky_image(bsky,img_path="",text="",alt_tex=""):
#     with open(img_path, 'rb') as f:
#         img_data = f.read()
#     bsky.send_image(text=text, image=img_data, image_alt=alt_tex)

t3 = perf_counter()

# Obsolete Code
# theme_sra = themes.theme_538(base_size=9, base_family="Tahoma")
# theme_sra += theme(
#     plot_background = element_rect(fill = 'ghostwhite', color = "ghostwhite"),
#     plot_title=element_text(face="bold", size=16),
#     strip_text=element_text(face="bold", size=10),
#     plot_caption=element_text(size=10),
#     plot_subtitle=element_text(size=12),
#     axis_text_x=element_text(size=8),
#     axis_text_y=element_text(size=8),
#     axis_title_x=element_text(size=12),
#     axis_title_y=element_text(size=12),
# )

# Function to plot table with Top 10 ranked
# def plot_table_rank_plotly(
#     df1,
#     var,
#     sort="Player",
#     n=10,
#     title=" ",
#     title_shift=0.05,
#     title_font=15,
#     footer=" ",
#     source="nba.com/stats",
#     col_width=15,
# ):
#     df = df1.iloc[:n]
#     fig = go.Figure(
#         data=[
#             go.Table(
#                 columnwidth=[5, 40, col_width],
#                 header=dict(
#                     values=list("<b>" + df.columns + "<b>"),
#                     fill_color="blue",
#                     align=["center", "left", "center"],
#                     font=dict(color="snow", size=12),
#                     line_color="grey",
#                 ),
#                 cells=dict(
#                     values=[df["#"], df[sort], df[var]],
#                     fill_color="lavender",
#                     align=["center", "left", "center"],
#                     height=23,
#                     line_color="grey",  # lightgrey",
#                     # font=dict(family="Cambria", size=12)
#                 ),
#                 # height=25
#             ),
#         ]
#     )
#     # fig.update_layout(title_text=title)
#     fig.update_layout(
#         title=dict(
#             text="<b>" + title + "<b>",
#             y=0.98,
#             x=title_shift,
#             font=dict(size=title_font),
#         )
#     )
#     tab_width = 250 + col_width
#     tab_height = 305
#     fig.add_annotation(
#         x=0.0,
#         y=0.0,
#         text="@SravanNBA",
#         showarrow=False,
#         xshift=1,
#         yshift=1,
#         font=dict(size=10),
#     )
#     fig.add_annotation(
#         x=1.0,
#         y=0.0,
#         text=f"Source: {source}",
#         showarrow=False,
#         xshift=1,
#         yshift=1,
#         font=dict(size=10),
#     )
#     if len(footer) > 1:
#         fig.add_annotation(
#             x=0.0,
#             y=0.0,
#             text=footer,
#             showarrow=False,
#             xshift=0,
#             yshift=15,
#             font=dict(size=10),
#         )
#         tab_height = 318
#     fig.update_layout(
#         width=tab_width, height=tab_height, margin=dict(t=25, b=1, l=1, r=1)
#     )
#     # fig.update_layout(autosize=True)
#     fig.show()
#     return fig


# Plot Table using matplotlib
# def render_mpl_table(
#     data,
#     col_width=3.0,
#     row_height=0.625,
#     font_size=14,
#     header_color="#40466e",
#     row_colors=["#f1f1f2", "w"],
#     edge_color="w",
#     bbox=[0, 0, 1, 1],
#     header_columns=0,
#     ax=None,
#     **kwargs,
# ):
#     if ax is None:
#         size = (np.array(data.shape[::-1]) + np.array([0, 1])) * np.array(
#             [col_width, row_height]
#         )
#         fig, ax = plt.subplots(figsize=size)
#         ax.axis("off")
#     mpl_table = ax.table(
#         cellText=data.values,
#         bbox=bbox,
#         cellLoc="center",
#         colLabels=data.columns,
#         **kwargs,
#     )
#     mpl_table.auto_set_font_size(False)
#     mpl_table.set_fontsize(font_size)

#     for k, cell in mpl_table._cells.items():
#         cell.set_edgecolor(edge_color)
#         if k[0] == 0 or k[1] < header_columns:
#             cell.set_text_props(weight="bold", color="w")
#             cell.set_facecolor(header_color)
#         else:
#             cell.set_facecolor(row_colors[k[0] % len(row_colors)])
#     fig.set_facecolor("#fc8662")
#     return ax.get_figure(), ax

# Obsolete code from other places

# Get Fonts
# import matplotlib.font_manager
# fpaths = matplotlib.font_manager.findSystemFonts()

# for i in fpaths:
#     f = matplotlib.font_manager.get_font(i)
#     print(f.family_name)

## Code to figure out errors in player ID mapping
# Player_Name = []
# a = Assist_pID
# wrong_id = []
# Assist_pID1, Assists = np.unique(a, return_counts=True)
# for pID in Assist_pID1:
#     abc = False
#     for player in player_dict:
#         if player['pID'] == pID:
#             abc= True
#             Player_Name.append(player['Name'])
#     if not abc:
#         wrong_id.append(pID)
# print(len(Assist_pID1))
# print(len(Player_Name))
# print(len(wrong_id))

## Code to map pID to players using old format
# Player_Name = []
# a = Assist_pID
# Assist_pID1, Assists = np.unique(a, return_counts=True)
# for pID in Assist_pID1:
#     Player_Name.append([player['Name'] for player in player_dict if player['pID'] == pID])
# for i in range(len(Player_Name)):
#     if not Player_Name[i]:
#         Player_Name[i] =['abc']
# Player_Name = list(itertools.chain(*Player_Name))
