# Load Packages
library(tidyverse)
library(rvest)
library(nbastatR)
library(scales)
library(fuzzyjoin)
library(gt)

Sys.setenv("VROOM_CONNECTION_SIZE" = 131072 * 2)
# Scrape mvp tracker table
url <- "https://www.basketball-reference.com/friv/mvp.html"

df <- url %>%
  read_html() %>%
  html_table(header = TRUE) %>%
  as.data.frame()

# Clean up the % probability variable
df <- df %>%
  mutate(Prob. = parse_number(Prob.)) %>%
  rename("Prob" = "Prob.")

# Get a list of active NBA players and their headshots
players <- nba_players()
players <- players %>%
  filter(isActive == TRUE) %>%
  select(namePlayer, urlPlayerHeadshot) %>%
  rename("Player" = "namePlayer")

# Fuzzy join the MVP dataframe with the players dataframe (since player names are not spelled the same in both datasets)
df <- stringdist_left_join(df, players, by = "Player", distance_col = NULL)
# df <- left_join(df, players, by = "Player")
df <- filter(df, Player.y != "Nikola Jovic")

# Get a list of all nba teams and their logos
tms <- nba_teams()
tms <- tms %>% filter(isNonNBATeam == 0)
tms <- tms %>%
  select(slugTeam, urlThumbnailTeam) %>%
  rename("Team" = "slugTeam") %>%
  mutate(Team = case_when(
    Team == "BKN" ~ "BRK",
    Team == "PHX" ~ "PHO",
    Team == "CHA" ~ "CHO",
    TRUE ~ Team
  ))

# Join the MVP dataframe with the team logos dataframe
df <- left_join(df, tms, by = "Team")

# Select variables we care about make table
df %>%
  select(urlPlayerHeadshot, Player.x, urlThumbnailTeam, G, W.L., PTS, TRB, AST, Prob) %>%
  mutate(
    Prob = percent(Prob / 100, .1),
    W.L. = percent(W.L., .1)
  ) %>%
  gt() %>%
  tab_header(
    title = md("**Basketball-Reference MVP Award Tracker**"),
    subtitle = md(paste0("As of ", format(Sys.Date(), format = "%B %d, %Y")))
  ) %>%
  cols_align(
    align = "left",
    columns = 2
  ) %>%
  cols_align(
    align = "center",
    columns = 3
  ) %>%
  cols_align(
    align = "right",
    columns = 4:9
  ) %>%
  cols_label(
    urlPlayerHeadshot = (""),
    Player.x = md("PLAYER"),
    urlThumbnailTeam = ("TEAM"),
    W.L. = md("WIN %"),
    PTS = md("PPG"),
    TRB = md("RPG"),
    AST = md("APG"),
    Prob = md("MVP %")
  ) %>%
  text_transform(
    locations = cells_body(c(urlPlayerHeadshot, urlThumbnailTeam)),
    fn = function(x) {
      web_image(url = x)
    }
  ) %>%
  cols_width(2 ~ px(127.5)) %>%
  opt_row_striping() %>%
  tab_options(
    table.background.color = "floralwhite",
    column_labels.font.size = 12,
    column_labels.font.weight = "bold",
    row_group.font.weight = "bold",
    row_group.background.color = "#E5E1D8",
    table.font.size = 10,
    heading.title.font.size = 20,
    heading.subtitle.font.size = 12.5,
    table.font.names = "Consolas",
    data_row.padding = px(2)
  ) %>%
  tab_source_note(
    source_note = md("@sradjoker | **Source**: Basketball-Reference MVP Tracker")
  ) # %>% gtsave("./figs/R/bbref_MVP_table.png")
