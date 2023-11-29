# NBA Analytics Projects by Sravan
## Setup
- Most of the code in this repo is written in Python or iPython (jupyter) notebooks. You need python to run the code.
- You can install the packages required by this repo using [poetry](https://python-poetry.org/). 
- After installing poetry, just run
```
poetry install
```
- This command will install all the packages used to run the different codes in this repo.
- Some of the notebooks also contain R code along with python for creating pretty tables and charts. The R code in jupyter notebooks is handled by the `rpy2` package, which is installed automatically using poetry
- In addition to `rpy2`, running R code also requires a working [R](https://www.r-project.org/) install.
- The code in the [R](R/) folder also requires R.

## Project List 


1. [Play-by-Play Related Stuff](pbp_related/)
    - Uses pbpstats API 
   - Frustration fouls
   - Euro fouls for player and team
   - Coast-to-coast buckets and assists
   - Assists after offensive rebounds 
   - Chasedown blocks?
2. [Plot Shot Charts](Shot_Charts/)
   - Plot location heat maps for NBA and WNBA
   - Plot shot hex map using NBA API and plotly
3. [Team Ratings](team_ratings/)
   - NBA SoS Adjusted Ratings
   - Adjusted Efficiency Landscape
   - Four Factor Analysis
   - Simple Win Loss Model using Rolling Net Rating
   - Rolling Team Ratings 
4. [Leaderboards](Leaderboards/)
   - Create Player Leaderboards in various categories
   - Create Team Leaderboards
5. [R based Visualizations and Analysis](R/)
   - Bad calls analysis based on L2M reports
   - NBA Histograms: Weighted Player Age Distribution
   - NBA Ratings aggregated from different sources
   - NBA Efficiency Landscape
6. [Import and Update Data](import_data/)
   - Using NBA API and pbpstats API
   - Save player data
   - Save league data
   - Update possession data
   - Import shot location data using NBA API
   - Get shot data using PBP Stats API
   - Import possession data for RAPM
   - Functions exist to import this data for use in other projects
7. [Player Analysis](player_analysis/)
   1. [3PT Shooting and FT Shooting Correlation](player_analysis/Shooting/)
       - Using NBA API
       - Get different type of 3 PT shooting data
       - Find and plot correlations between them and FT shooting
   2. [Wingspan and Defense Correlation](player_analysis/Wingspan_Defense/)
       - Using NBA API
       - Get wingspan, height and standing reach from draft data 
       - Get rim protection data 
       - Find and plot correlations
8.  [Tweeting Bots](Tweetbots/) (Might not work because of new Twitter API)
    - Uses [Tweepy API](https://www.tweepy.org/)
    - Gets Shot data from NBA API
    - Plots shotchart
    - Tweets out data and shotchart when you run this [file](Tweetbots/tweet_grizz_3pt.py)
    - Added [.bat file](Tweetbots/tweet_grizz_3pt.bat) to enable automatic scheduling using Windows Task Scheduler
    - You need to apply for [developer access](https://developer.twitter.com) and get your own authentication tokens to enable tweeting
    


