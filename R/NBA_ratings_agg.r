# Aggregate Strength Adjusted Net Rating from different sources
#Load Packages
library(tidyverse)
library(rvest)
library(nbastatR)
library(scales)
library(fuzzyjoin)
library(gt)

header.true <- function(df) {
  names(df) <- as.character(unlist(df[1,]))
  df[-1,]
}

Sys.setenv("VROOM_CONNECTION_SIZE" = 131072 * 2)

tms <- nba_teams()
tms <- tms %>% filter(isNonNBATeam == 0)
tms <- tms %>% 
  select(slugTeam, nameTeam) %>% 
  rename("sTeam" = "slugTeam") %>%
  rename("Team" = "nameTeam") # %>%  
#   mutate(sTeam = case_when(
#          sTeam == "BKN" ~ "BRK", 
#          sTeam == "PHX" ~ "PHO", 
#          sTeam == "CHA" ~ "CHO", 
#          TRUE ~ sTeam))

#Dunks and Threes Net Ratings
url <- "https://dunksandthrees.com/"

df1 <- url %>% 
  read_html() %>%
  html_table(header=TRUE) %>%
  as.data.frame() 

df <- header.true(df1)
rownames(df)=NULL
df <- df %>% select(Team,aNET,aORTG,aDRTG)  %>% rename("sTeam"="Team")
df <- head(df,-2)

df$sTeam <- gsub('[0-9.]', '', df$sTeam)
df$aNET <- gsub("\\n.*","",df$aNET)
df$aORTG <- gsub("\\n.*","",df$aORTG)
df$aDRTG <- gsub("\\n.*","",df$aDRTG)
df$aNET <- gsub("\u2212","-",df$aNET)

df <- transform(df,
  aNET = as.numeric(aNET),
  aORTG = as.numeric(aORTG),
  aDRTG = as.numeric(aDRTG)
)

df$aNET_Rank <- rank(df$aNET)
df$aORTG_Rank <- rank(df$aORTG)
df$aDRTG_Rank <- rank(df$aDRTG)

df_dnt <- df

df_all1 = df_dnt  %>% left_join(., tms, by = "sTeam")

url <- "https://www.espn.com/nba/bpi"

df1 <- url %>% 
  read_html() %>%
  html_table(header=TRUE) %>%
  as.data.frame() 

df <- header.true(df1)
rownames(df)=NULL
df <- df[,-2]
df <- df %>% select(Team,BPI,OFF,DEF)  
df$Team <- gsub("LA Clippers","Los Angeles Clippers",df$Team)
df <- df %>% rename("O_BPI"="OFF") %>% rename("D_BPI"="DEF") 

df <- transform(df,
  BPI = as.numeric(BPI),
  O_BPI = as.numeric(O_BPI),
  D_BPI = as.numeric(D_BPI)
)

df$BPI_Rank <- rank(df$BPI)
df$O_BPI_Rank <- rank(df$O_BPI)
df$D_BPI_Rank <- rank(df$D_BPI)

df_espn <- df

df_all2 = df_all1  %>%  left_join(., df_espn, by = "Team")




url <- "https://www.basketball-reference.com/leagues/NBA_2024_ratings.html"

df1 <- url %>% 
  read_html() %>%
  html_table(header=TRUE) %>%
  as.data.frame() 

df <- header.true(df1)
rownames(df)=NULL
df <- df %>% select(Team,"NRtg/A","ORtg/A","DRtg/A")  %>% 
      rename("aNRtg"="NRtg/A","aORtg"="ORtg/A","aDRtg"="DRtg/A")

df$aNRtg_Rank <- rank(df$aNRtg)
df$aORtg_Rank <- rank(df$aORtg)
df$aDRtg_Rank <- rank(df$aDRtg)

df <- transform(df,
  aNRtg = as.numeric(aNRtg),
  aORtg = as.numeric(aORtg),
  aDRtg = as.numeric(aDRtg)
)


df_bbref <- df


df_all3 <- df_all2  %>%  left_join(., df_bbref, by = "Team")

df_all <- df_all3


url <- "https://cleaningtheglass.com/stats/league/summary"

df1 <- url %>% 
  read_html() %>%
  html_table(header=TRUE) %>%
  as.data.frame() 

df <- header.true(df1)
rownames(df)=NULL










df_all %>% 
  select(Team,aORTG,aDRTG,aNET,O_BPI,D_BPI,BPI,aORtg,aDRtg,aNRtg) %>% 
  gt()%>%
  tab_header(
    title = md("**NBA Net Rating Leaders 2023-24**")) %>%
    data_color(columns = aORTG, palette = c("red", "green")) %>%
    data_color(columns = aDRTG, palette = c("green","red")) %>%
    data_color(columns = aNET, palette = c("red", "green")) %>%
    data_color(columns = O_BPI, palette = c("red", "green")) %>%
    data_color(columns = D_BPI, palette = c("red", "green")) %>%
    data_color(columns = BPI, palette = c("red", "green")) %>%
    data_color(columns = aORtg, palette = c("red", "green")) %>%
    data_color(columns = aDRtg, palette = c("green","red")) %>%
    data_color(columns = aNRtg, palette = c("red", "green")) %>%
    # cols_align(align = "center",columns = c("#",OFF_RTG,O_RANK,DEF_RTG,D_RANK,NET_RTG))  %>%
    tab_spanner(
      label = "Dunks and Threes",
      columns = vars(aORTG, aDRTG, aNET)
    ) %>% 
    tab_spanner(
      label = "ESPN BPI",
      columns = vars(O_BPI, D_BPI, BPI)
    ) %>%
    tab_spanner(
      label = "Basketball Ref",
      columns = vars(aORtg, aDRtg, aNRtg)
    ) %>% 
    tab_options(
        table.background.color = "floralwhite",
        column_labels.font.size = 12,
        column_labels.font.weight = 'bold',
        row_group.font.weight = 'bold',
        row_group.background.color = "#E5E1D8",
        table.font.size = 10,
        heading.title.font.size = 20,
        heading.subtitle.font.size = 12.5,
        table.font.names = "Consolas", 
        data_row.padding = px(2)
    ) %>% 
    tab_source_note(source_note = "@SravanNBA | Source: basketball-reference, DunksandThrees, ESPN"
    ) %>% gtsave("./figs/R/NBA_rat_comp.png",zoom=5)
