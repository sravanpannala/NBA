library(tidyverse)

game_str <- "[2024-10-22]-0022400061-NYK@BOS"
game_str <- "[2024-10-22]-0022400062-MIN@LAL"
df <- read.csv(paste0("./data/share/iztok_poss/",game_str,".csv"))


# get only shots (makes and misses), turnovers and free throws
# rebounds after misses are counted already with this
poss_type <- c("shot","turnover","free throw")
df1 <- df %>% filter(event_type %in% poss_type)

# now we have to filter only free throws with 2 or 3 trips
df2 <- df1 %>% filter(!(event_type == "free throw" & type == "free throw 1/1" ))
# further filering only last free throws in a strip
df2 <- df2 %>% filter(!(event_type == "free throw" & type == "free throw 1/2" ))
df2 <- df2 %>% filter(!(event_type == "free throw" & type == "free throw 1/3" ))
df2 <- df2 %>% filter(!(event_type == "free throw" & type == "free throw 2/3" ))

df3 <-  df2 
# duplicate team row for comparison
df3$team1 <- df3$team
# shift the team row up for comparison
df3$team2 <- dplyr::lead(df3$team)
# duplicate period row for comparison
df3$period1 <- df3$period
# shift the period row up for comparison
df3$period2 <- dplyr::lead(df3$period)
# keep only the last event of consecutive events in which the same team has the ball
# make sure that the consecutive events are in the same period 
df3 <- df3 %>% filter(!(team==team2 & period1==period2))


write.csv(df3, paste0("./R/export/",game_str,"_poss.csv"), row.names=FALSE)

# streaks function from https://data-and-the-world.onrender.com/posts/streaks-in-r/
get_streaks <- function(vec){
    x <- data.frame(trials=vec)
    x <- x %>% mutate(lagged=lag(trials)) %>%  #note: that's dplyr::lag, not stats::lag
            mutate(start=(trials != lagged))
    x[1, "start"] <- TRUE
    x <- x %>% mutate(streak_id=cumsum(start))
    x <- x %>% group_by(streak_id) %>% mutate(streak=row_number()) %>%
        ungroup()
    return(x$streak)
}

# First team 
teams <- unique(df3$team)
df4 <- df3  %>% filter(team==teams[1])
# mark possesions where the team scored
df4 <- df4  %>% mutate(score = ifelse(points > 0,1,0))
df4$score <- df4$score %>% replace_na(0)
# get streaks for both scoring and not scoring
df4 <- df4  %>% mutate(streak = get_streaks(score)) 
# Second team 
df5 <- df3  %>% filter(team==teams[2])
df5 <- df5  %>% mutate(score = ifelse(points > 0,1,0))
df5$score <- df5$score %>% replace_na(0)
df5 <- df5  %>% mutate(streak = get_streaks(score)) 
# Combine
df_out <- bind_rows(df4, df5)

write.csv(df_out, paste0("./R/export/",game_str,"_streak.csv"), row.names=FALSE)

# result <- df %>%
#   mutate(consecutive = value == lag(value)) %>%
#   filter(consecutive)



