# NBA Analytics Projects by Sravan
## Setup
1. Install [NBA API](https://github.com/swar/nba_api)
2. Install [PBP Stats API](https://github.com/dblackrun/pbpstats)
3. Other python packages required can be installed from the Pipfile
## Project List 

1. [Wingspan and Defense Correlation](Wingspan_Defense/)
    - Using NBA API
    - Get wingspan, height and standing reach from draft data 
    - Get rim protection data 
    - Find and plot correlations
2. [3PT Shooting and FT Shooting Correlation](Shooting/)
    - Using NBA API
    - Get different type of 3 PT shooting data
    - Find and plot correlations between them and FT shooting
3. [Frustration Fouls and Coast to Coast](Frustration_Coast/)
    - Using PBP Stats API
    - Frustration fouls
    - Euro fouls for player and team
    - Coast to coast buckets and assists
    - Assists after offensive rebounds 
4. [Save Player and League Data](Save_Player_League_Data/)
    - Using NBA API
    - Save player data
    - Save league data
    - Write functions to import these data for use in other projects
5. [Plot Shot Charts](Shot_Charts/)
    - Get location data using PBP Stats API
    - Plot location heat maps for NBA
    - Plot location heat maps for WNBA (probably need to merge both files)
    - Plot shot hex map using NBA API and plotly
6. [3PT shooting for various attributes](Shooting/)
    - Number of dribbles
    - Shotclock
    - Touch time
7. [Tweeting Bots](TweetBots/)
    - Uses [Tweepy API](https://www.tweepy.org/)
    - Gets Shotdata from NBA API
    - Plots shotchart
    - Tweets out data and shotchart when you run this [file](TweetBots/tweet_grizz_3pt.py)
    - Added [.bat file](TweetBots/grizz.bat) to enable automatic scheduling using Windows Task Scheduler
    - You need to apply for [developer access](https://developer.twitter.com) and get your own authentication tokens to enable tweeting
    


