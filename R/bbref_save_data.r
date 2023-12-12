library(tidyverse)
library(rvest)
library(nbastatR)
library(scales)
library(fuzzyjoin)
library(gt)

Sys.setenv("VROOM_CONNECTION_SIZE" = 131072 * 2)

# Advanced Leaderboards

## Single Season

season <- 2024

df1 <- bref_players_stats(
  seasons = season,
  tables = "advanced",
  include_all_nba = FALSE,
  only_totals = FALSE,
  nest_data = FALSE,
  assign_to_environment = TRUE,
  widen_data = TRUE,
  join_data = TRUE,
  return_message = TRUE
)

path <- paste0("./player_analysis/fdata/NBA_bbref_Player_Adv_",season-1,".csv")
write.csv(df1, path)

## Multiple Seasons

for (season in 2001:2024) {
  df1 <- bref_players_stats(
    seasons = season,
    tables = c("advanced","per_game"),
    include_all_nba = FALSE,
    only_totals = FALSE,
    nest_data = FALSE,
    assign_to_environment = TRUE,
    widen_data = TRUE,
    join_data = TRUE,
    return_message = TRUE
  )

  # path <- paste0("./player_analysis/fdata/NBA_bbref_Player_Adv_",season-1,".csv")
  # write.csv(df1, path)

}
