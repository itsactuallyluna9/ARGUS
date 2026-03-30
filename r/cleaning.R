library(tidyverse)

article_data <- read_csv(file.path(getwd(), "data", "article_data.csv"))
fact_check_data <- read_csv(file.path(getwd(), "data", "fact_check_data.csv"))

# article_data <- article_data |> 
#   mutate(date = as.Date(date))

article_data |> write_csv(file.path(getwd(), "data", "article_data_clean.csv"))
fact_check_data |> write_csv(file.path(getwd(), "data", "fact_check_data_clean.csv"))