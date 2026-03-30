library(tidyverse)
library(rjson)

article_data <- fromJSON(file=file.path(getwd(), "article_data.json"))
fact_check_data <- fromJSON(file.path(getwd(), "data", "fact_check_data.json"))

a
