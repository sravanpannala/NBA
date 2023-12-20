# Scripts to Import and Update Data

## Save Player and League Data
- Using nba API and pbpstats API
- Functions exist to import this data for use in other projects
- [Player Info nba API](./get_player_database.ipynb)
- [Player Dictionaries pbpstats API](./get_player_dictionaries.ipynb)
- [Teams Info](./get_nba_teams.ipynb)
- [League Rosters](./get_nba_rosters.ipynb)

## Note: 
Run the above scripts first to generate database needed for running scripts below

## Shot Location Data
- [Using nba API](./get_shot_data.ipynb)
- [Using pbpstats API](./get_shot_data_PBP.ipynb)

## Import Possessions for RAPM
- Import possessions only which count as official possessions
- Get players on offense and defense for those possessions
- Get points scored during that possession
- [Notebook](./get_rapm_possessions.ipynb)

## Shooting Data
- [Shot Dashboards](./get_shot_dashboards.ipynb)
- [Synergy Play types](./get_synergy_playtypes.ipynb)

## Advanced Stats
- Scrapes basketball ref for BPM and DARKO google sheet for DPM
- [Notebook](./get_DARKO.ipynb)

## Injury Data
- Scrapes NBA injury data
- [Notebook](./get_injury_data.ipynb)