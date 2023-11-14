# Code to plot ball calls based on L2M Reports for Teams
# Load packages
library(tidyverse)
library(extrafont)
library(ggtext)
library(patchwork)
library(vroom)
library(nbastatR)

# Get team names
# bref <- dictionary_bref_teams()
# bref$teams <- word(bref$nameTeamBREF, -1)

# need this for later
`%notin%` <- Negate(`%in%`)

# custom theme
theme_owen <- function() {
  theme_minimal(base_size = 9, base_family = "Consolas") %+replace%
    theme(
      panel.grid.minor = element_blank(),
      plot.background = element_rect(fill = "floralwhite", color = "floralwhite")
    )
}

# Read in full l2m data
dat <- vroom("https://raw.githubusercontent.com/atlhawksfanatic/L2M/master/1-tidy/L2M/L2M.csv")

# Select relevant columns
df <- dat %>% select(game_details, game_date, period, time, comments, call_type, committing_team, disadvantaged_team, decision, season)

# Remove duplicates
df <- df %>% distinct()

# Limit data to 2021
# df <- df %>% filter(season > 2015) %>% filter(season < 2024)
# df <- df %>% filter(season > 2023)

# Count times a player committed a foul, but wasnt called for it
player_inc <- df %>%
  filter(decision == "INC") %>%
  count(committing_team) %>%
  arrange(desc(n))

# Count times opponent was called for a foul, but didnt actually commit -- thus favoring the player
opponent_ic <- df %>%
  filter(decision == "IC" & !is.na(disadvantaged_team)) %>%
  count(disadvantaged_team) %>%
  arrange(desc(n))

# get total bad calls that went in player's favor
favor <- full_join(player_inc, opponent_ic, by = c("committing_team" = "disadvantaged_team"))

# rename columns
favor <- favor %>%
  rename(
    "player_inc" = "n.x",
    "opponent_ic" = "n.y"
  )

# Calculate total bad calls in players favor
favor <- favor %>%
  rowwise() %>%
  mutate(total = sum(player_inc, opponent_ic, na.rm = TRUE))

# Count times a player was called for a foul that they didn't commit
player_ic <- df %>%
  filter(decision == "IC" & !is.na(committing_team)) %>%
  count(committing_team) %>%
  arrange(desc(n))

# Count times an opponent committed a foul, but wasn't called for it
opponent_inc <- df %>%
  filter(decision == "INC") %>%
  count(disadvantaged_team) %>%
  arrange(desc(n))

# Get total bad calls that went against a player
oppose <- full_join(player_ic, opponent_inc, by = c("committing_team" = "disadvantaged_team"))

# rename columsns
oppose <- oppose %>%
  rename(
    "player_ic" = "n.x",
    "opponent_inc" = "n.y"
  )

# Calculate total bad calls against player
oppose <- oppose %>%
  rowwise() %>%
  mutate(total = sum(player_ic, opponent_inc, na.rm = TRUE))

# combine two bad call dataframes into one
badcalls_df <- full_join(favor, oppose, by = "committing_team")

# Replace all NAs with 0s
# badcalls_df <- badcalls_df %>% mutate_all(funs(replace_na(., 0))) %>% filter(committing != 0)
# badcalls_df <- badcalls_df %>% filter(committing != NA)
badcalls_df <- na.omit(badcalls_df)
# Find the players who have been (dis)advantaged at least 3x
badcalls_df <- badcalls_df %>%
  rename(
    "favor" = "total.x",
    "oppose" = "total.y"
  ) %>%
  rename("player" = "committing_team") # %>%
# filter((oppose >= 20 | favor >= 20) & player != "Lakers" )
# filter((oppose >= 40 | favor >= 25) )
# filter((oppose >= 3 | favor >= 3) & player %notin% bref$teams & player != "Trail Blazers")

# Pivot data longer and make multiply disadvantaged calls by -1 (going left)
badcalls_df1 <- badcalls_df %>%
  select(player, player_inc, opponent_ic, player_ic, opponent_inc) %>%
  pivot_longer(-player) %>%
  mutate(
    value = as.numeric(value),
    value = case_when(
      name == "player_ic" ~ value * 1,
      name == "opponent_inc" ~ value * 1,
      name == "player_inc" ~ value * -1,
      name == "opponent_ic" ~ value * -1,
      TRUE ~ value
    )
  )

badcalls_df <- badcalls_df %>%
  select(player, player_inc, opponent_ic, player_ic, opponent_inc) %>%
  pivot_longer(-player) %>%
  mutate(
    value = as.numeric(value),
    value = case_when(
      name == "player_ic" ~ value * -1,
      name == "opponent_inc" ~ value * -1,
      #  name == "player_inc" ~ value * -1,
      #  name == "opponent_inc" ~ value * -1,
      TRUE ~ value
    )
  )

# Get a dataframe of players who have been involvd in the most bad calls
shortstick <- badcalls_df1 %>%
  select(player, value) %>%
  group_by(player) %>%
  summarise(value = sum(value)) %>%
  rename("badcall" = "value")

# Get a dataframe of players who have been involvd in the most bad calls
shortstick1 <- badcalls_df %>%
  select(player, value) %>%
  group_by(player) %>%
  summarise(value = sum(abs(value))) %>%
  rename("badcall" = "value")

# Make chart of bad calls in players favor
favor_chart <- badcalls_df %>%
  filter(name %in% c("player_inc", "opponent_ic")) %>%
  left_join(., shortstick, by = "player") %>%
  ggplot(aes(x = value, y = fct_reorder(player, badcall), fill = fct_rev(name))) +
  geom_col(color = "floralwhite", width = 1) +
  scale_fill_manual(values = c("#008A80FF", "#99E3DDFF")) +
  scale_x_continuous(limits = c(0, 300), breaks = seq(0, 300, 50)) +
  # geom_vline(xintercept = seq(1, 300, 1), color = 'floralwhite') +
  theme_owen() +
  coord_cartesian(clip = "off") +
  theme(
    plot.margin = margin(10, 10, 15, 0),
    legend.position = "none",
    axis.text.y = element_text(hjust = .5, size = 6, margin = margin(0, 0, 0, -15)),
    panel.grid.major.y = element_blank(),
    panel.grid.minor.y = element_blank(),
    axis.title.x = element_markdown(size = 6.5)
  ) +
  labs(
    x = "Bad Calls That Have <span style='color:#008A80FF'>**Advantaged**</span><br>A Team From 2015-2023",
    y = ""
  )
# annotate(geom = 'text', x = 10, y = 38, label = "Incorrect no call on player", size = 2.5, fontface = 'bold', color = "#008A80FF", family = "Consolas", hjust = .5) +
# annotate(geom = 'text', x = 10, y = 35, label = "Incorrect call against opponent", size = 2.5, fontface = 'bold', color = "#33C6BBFF", family = "Consolas", hjust = .5)

# Make chart of bad calls that went against a player
oppose_chart <- badcalls_df %>%
  filter(name %in% c("player_ic", "opponent_inc")) %>%
  left_join(., shortstick, by = "player") %>%
  ggplot(aes(x = value, y = fct_reorder(player, badcall), fill = (name))) +
  geom_col(color = "floralwhite", width = 1) +
  scale_fill_manual(values = c("#BE4A47FF", "#FEA19EFF")) +
  scale_x_continuous(limits = c(-300, 0), breaks = c(-300, -250, -200, -150, -100, -50, 0), labels = c("300", "250", "200", "150", "100", "50", "0")) +
  scale_y_discrete(position = "right") +
  # geom_vline(xintercept = seq(-300, -1, 1), color = 'floralwhite') +
  theme_owen() +
  coord_cartesian(clip = "off") +
  theme(
    plot.margin = margin(10, 0, 15, 10),
    legend.position = "none",
    axis.text.y = element_blank(),
    panel.grid.major.y = element_blank(),
    panel.grid.minor.y = element_blank(),
    axis.title.x = element_markdown(size = 6.5)
  ) +
  labs(
    x = "Bad Calls That Have <span style='color:#BE4A47FF'>**Disadvantaged**</span><br>A Team From 2015-2023",
    y = ""
  )
# annotate(geom = 'text', x = -10, y = 38, label = "Incorrect no call on opponent", size = 2.5,  fontface = 'bold',  color = "#BE4A47FF", family = "Consolas", hjust = .5) +
# annotate(geom = 'text', x = -10, y = 35, label = "Incorrect call against player", size = 2.5,  fontface = 'bold', color = "#FEA19EFF", family = "Consolas", hjust = .5)

# use the patchwork package to combine plots
p <- oppose_chart + favor_chart

# add title and subtitle
p <- p +
  plot_annotation(
    title = "Bad Calls That Have <span style='color:#BE4A47FF'>**Disadvantaged**</span> Or <span style='color:#008A80FF'>**Advantaged**</span> A Team From 2015-23",
    subtitle = "A call is considered to have disadvantaged a team if it was an incorrect no call on their opponent or a incorrect call against them\nand visa versa for calls that advantage a team",
    caption = "graph: @SravanNBA |code: @owenlhjphillips | Source: github.com/atlhawksfanatic/L2M",
    theme = theme(
      plot.title = element_markdown(face = "bold", family = "Consolas", size = 9.5),
      plot.subtitle = element_text(family = "Consolas", size = 5.25),
      plot.background = element_rect(fill = "floralwhite", color = "floralwhite"),
      plot.caption = element_text(family = "Consolas")
    )
  )

# Save plot
ggsave("./figs/R/BadCalls_team_diff_2015_23.png", p, w = 6, h = 8, dpi = 600)
