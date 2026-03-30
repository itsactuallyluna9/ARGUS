library(tidyverse)
library(rjson)

article_data <- fromJSON(file=file.path(getwd(), "article_data.json"))
fact_check_data <- fromJSON(file=file.path(getwd(), "fact_check_data.json"))

View(article_data)
View(fact_check_data)
