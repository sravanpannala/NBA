library(tidyverse)
library(nflverse)
library(scales)
library(gt)
library(ggimage)
library(extrafont)
library(patchwork)
extrafont::loadfonts(quiet=TRUE)

plt_func <- function(df, mapping, varn) {
  p <- ggplot(df, mapping) + # nolint
  geom_point() + # nolint
  geom_smooth() + # nolint
  labs(y = element_blank()) + # nolint
  ggtitle(varn) + # nolint
  theme_sravan +
  theme( # nolint
    plot.title = element_text(face = "bold", size = 16), # nolint
  )
}

theme_sravan <- theme_minimal(base_size = 9, base_family = "Tahoma") +
  theme(
    panel.grid.minor = element_blank(),
    plot.background = element_rect(fill = "ghostwhite", color = "ghostwhite"),
    plot.title.position = "plot",
    legend.position = "none",
    plot.title = element_text(face = "bold", size = 20),
    plot.margin = margin(10, 10, 15, 10),
    axis.text.x = element_text(size = 10, face = "bold", color = "black"),
    axis.text.y = element_text(size = 10, face = "bold", color = "black"),
    axis.title.x = element_text(size = 12, face = "bold", colour = "black"),
    axis.title.y = element_text(size = 12, face = "bold", colour = "black"),
    plot.caption = element_text(size = 12, colour = "black")
  )

df <- load_nextgen_stats(
  seasons = 2023,
  stat_type = c("passing"),
  file_type = getOption("nflreadr.prefer", default = "rds")
)

write.csv(df, "./R/nfl_nextgen_2023.csv")

df1 <- df %>% filter(player_display_name == "Jordan Love")

df2 <- df1  %>%  slice(-1)

# plot


p1 <- plt_func(df2, aes(x = week, y = avg_completed_air_yards), "Avg Comp Air Yds")
p2 <- plt_func(df2, aes(x = week, y = avg_air_distance), "Avg Air Dist")
p3 <- plt_func(df2, aes(x = week, y = attempts), "Pass Attempts")
p4 <- plt_func(df2, aes(x = week, y = pass_yards), "Pass Yds")
p5 <- plt_func(df2, aes(x = week, y = completion_percentage), "Completion %")
p6 <- plt_func(df2, aes(x = week, y = passer_rating), "Passer Rating")

p <- p1 + p2 + p3 + p4 + p5 + p6 + plot_layout(ncol = 2) + plot_annotation(
  theme = theme_sravan,
  title = "Jordan Love 2023 Passing Stats",
  caption = "@sradjoker | Source: nflverse"
)
ggsave("./figs/R/Jordan_Love_2023.png", p, w = 10, h = 8, dpi = 300)

# table
dft <- df2 %>%
  select(week, avg_completed_air_yards, avg_air_distance, attempts,
         pass_yards, completion_percentage, passer_rating)  %>%
  gt() %>%
  tab_header(
    title = md("**Jalen Hurts Stats 2023**")
  ) %>%
  cols_align(align = "center")  %>%
  cols_label(
    week = "Week", avg_completed_air_yards = "Avg Comp Air Yds", pass_yards = "Pass Yds",
    passer_rating = "Passer Rating", completion_percentage = "Compl %", avg_air_distance = "Avg Air Dist",
    attempts = "Attempts"
  ) %>%
  data_color(columns = -c("week"), palette = "PRGn") %>%
  fmt_number(columns = -c("week", "pass_yards"), decimals = 1) %>%
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
    data_row.padding = px(4)
  ) %>%
  tab_source_note(
    source_note = "@sradjoker | Source: nflverse"
  ) %>%
  gtsave("./figs/R/Jalen_Hurts_2023.png", zoom = 5)
dft


df <- load_player_stats(
  seasons = most_recent_season(),
  stat_type = c("offense", "defense", "kicking"),
  file_type = getOption("nflreadr.prefer", default = "rds")
)

write.csv(df, "./R/nfl_offense_2023.csv")


df1 <- df %>% filter(player_display_name == "Dak Prescott")

df2 <- df1 %>%
  slice(-1) %>%
  select(week, attempts, completions, passing_yards,
         passing_tds, passing_air_yards, passing_yards_after_catch, passing_first_downs,
         passing_epa, dakota)

p1 <- plt_func(df2, aes(x = week, y = attempts), "Pass Attempts")
p2 <- plt_func(df2, aes(x = week, y = completions), "Completions")
p3 <- plt_func(df2, aes(x = week, y = passing_air_yards), "Pass Air Yds")
p4 <- plt_func(df2, aes(x = week, y = passing_yards_after_catch), "Pass YAC")
p5 <- plt_func(df2, aes(x = week, y = passing_epa), "Passing EPA")
p6 <- plt_func(df2, aes(x = week, y = dakota), "Adjusted EPA + CPOE")

p <- p1 + p2 + p3 + p4 + p5 + p6 + plot_layout(ncol = 2) + plot_annotation(
  theme = theme_sravan,
  title = "Dak Prescott 2023 Passing Stats",
  caption = "@sradjoker | Source: nflverse"
)
ggsave("./figs/R/Dak_Prescott_2023.png", p, w = 10, h = 8, dpi = 300)
