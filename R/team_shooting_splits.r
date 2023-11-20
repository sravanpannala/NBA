library(tidyverse)
library(nbastatR)
library(hrbrthemes)
library(ggridges)
library(patchwork)
library(ggtext)
library(ggfx)
Sys.setenv("VROOM_CONNECTION_SIZE" = 131072 * 50)

# custom ggplot2 theme
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
    axis.title.y = element_text(size = 12, face = "bold", colour = "black")
  )


df <- read.csv("./R/fdata/nba_team_shooting_splits.csv")


df1 <- df %>% pivot_longer(r00_8:r24_)


p1 <- ggplot(df1, aes(x = Team, y = value, fill = name)) +
  geom_col() +
  scale_fill_discrete(name="Shot Distance", labels = c("<8 ft", "8-16 ft", "16-24 ft", "24+ ft")) +
  # geom_bar(position = "dodge", stat = "identity") +
  # facet_wrap(~Team) +
  coord_flip() +
  # theme_sravan +
  theme(
    axis.title.y = element_blank(),
    axis.title.x = element_blank()
  )  +
  labs(
    title = "NBA Shot Distribution by Distance",
    caption = "@SravanNBA | Source: nba.com/stats"
  ) +
  theme(
    plot.title.position = "plot",
    plot.title = element_text(face = "bold", size = 24, hjust = 0.5),
    plot.margin = margin(10, 10, 15, 10),
    plot.subtitle = element_text(size = 18),
    plot.caption = element_text(size = 12)
  ) 
p1
ggsave("./figs/R/Team_Shooting_Splits.png", p1, w = 8, h = 6, dpi = 600)
