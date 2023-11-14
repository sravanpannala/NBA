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


df <- read.csv("./Shot_Charts/ShotLocationData/NBA_Shot_Loc_2023.csv")

df_made <- df %>% filter(is_made == "True")
df_miss <- df %>% filter(is_made == "False")

p1 <- ggplot(df_made, aes(x = poss_length, y = team_name)) +
    geom_density_ridges(alpha = 0.5, quantile_lines = TRUE, quantiles = 2) +
    # from = 18, to = 40, quantile_lines = TRUE, quantiles = 2) +
    geom_density_ridges(data = df_miss, aes(x = poss_length, y = team_name), alpha = 0.5, quantile_lines = TRUE, quantiles = 2) +
    theme_sravan +
    labs(x = "Possession Length", y = "Team")
p1
ggsave("./figs/R/Team_Poss_Length.png", p1, w = 8, h = 15, dpi = 600)


df_team <- df %>% filter(team_name == "Boston Celtics")

df$mulp <- as.integer(as.logical(df$is_made))
df$pts <- df$shot_value*df$mulp

p2 <- ggplot(df, aes(x = poss_length)) +
    geom_density(
        alpha = 0.3,
        color = "black", fill = "red"
    ) +
    geom_density(aes(weights =  pts),
        alpha = 0.3,
        color = "black", fill = "green"
    ) +

    facet_wrap(vars(team_name)) +
    theme_sravan +
    theme(strip.text = element_text(face = "bold", margin = margin())) +
    labs(x = "Possession Length", y = "Team")
p2
