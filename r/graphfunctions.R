library(tidyverse)
library(ggdensity)

fact_checks <- read_csv("~/data/fact_check_data.csv")

bias_scores_by_source <- function(sources=NULL, start_date=NULL, end_date=NULL, data=fact_checks) {
  
  data <- data |> select(
    accuracy_score, 
    completeness_score, 
    emotional_language_score, 
    sensationalism_score, 
    political_score,
    site, site_name, sitename,
    date
    ) |> mutate(date = as.Date(date))
  
  if(!is.null(sources)) {
    data <- data |> filter(site %in% sources | site_name %in% sources | sitename %in% sources)
  }
  
  if(!is.null(start_date)) {data <- data |> filter(date >= start_date)}
  if(!is.null(end_date)) {data <- data |> filter(date <= end_date)}
  
  data <- data |> group_by(sitename) |> 
    summarize(
      Accuracy = mean(accuracy_score),
      Completeness = mean(completeness_score),
      `Political Bias` = mean(political_score),
      Sensationalism = mean(sensationalism_score),
      `Emotional Language` = mean(emotional_language_score)
      )
  
  data |> 
    pivot_longer(!sitename, names_to = "type", values_to = "score") |> 
    filter(!(type %in% c("Accuracy", "Completeness"))) |>
    ggplot(aes(x=score, y=type, fill=type)) + geom_col() + facet_wrap(~sitename) + xlim(0, 100) + labs(
      title = "Mean Bias Scores by Source",
      subtitle = "As evaluated by ARGUS",
      x = "", y = ""
    ) + scale_fill_discrete(name = "")
}


#takes vector c(...) of sources to display. if none specified display all
accuracy_completeness_scores_by_source <- function(sources=NULL, data=fact_checks) {
  
  data <- data |> select(
    accuracy_score, 
    completeness_score, 
    emotional_language_score, 
    sensationalism_score, 
    political_score,
    site, site_name, sitename,
    date
    ) |> mutate(date = as.Date(date))
  
  if(!is.null(sources)) {
    data <- data |> filter(site %in% sources | site_name %in% sources | sitename %in% sources)
  }
  
  data <- data |> group_by(sitename) |> 
    summarize(
      Accuracy = mean(accuracy_score),
      Completeness = mean(completeness_score),
      `Political Bias` = mean(political_score),
      Sensationalism = mean(sensationalism_score),
      `Emotional Language` = mean(emotional_language_score)
      )
  
  data |> 
    pivot_longer(!sitename, names_to = "type", values_to = "score") |> 
    filter(type %in% c("Accuracy", "Completeness")) |>
    ggplot(aes(x=score, y=type, fill=type)) + geom_col() + facet_wrap(~sitename) + xlim(0, 100) + labs(
      title = "Mean Accuracy and Completeness Scores by Source",
      subtitle = "As evaluated by ARGUS",
      x = "", y = ""
    ) + scale_fill_discrete(name = "")
}


scores_by_time <- function(sources = NULL, start_date=NULL, end_date=NULL, data=fact_checks) {
  
  data <- data |> select(
    accuracy_score, 
    completeness_score, 
    emotional_language_score, 
    sensationalism_score, 
    political_score,
    site, site_name, sitename,
    date
    ) |> mutate(date = as.Date(date))
  
  if(!is.null(sources)) {
    data <- data |> filter(site %in% sources | site_name %in% sources | sitename %in% sources)
  }
  
  if(!is.null(start_date)) {data <- data |> filter(date >= start_date)}
  if(!is.null(end_date)) {data <- data |> filter(date <= end_date)}
  
  data <- data |> group_by(date) |> 
    summarize(
      Accuracy = mean(accuracy_score),
      Completeness = mean(completeness_score),
      `Political Bias` = mean(political_score),
      Sensationalism = mean(sensationalism_score),
      `Emotional Language` = mean(emotional_language_score)
      )
  
  data |> 
    pivot_longer(!date, names_to = "type", values_to = "score") |>
    ggplot(aes(x=date, y=score, color=type)) + 
    geom_line() + 
    geom_point() +
    scale_x_date(date_breaks = "1 week", date_labels = "%d-%b") +
    labs(
      title = "Scores Over Time",
      subtitle = "As evaluated by ARGUS",
      x = "Date", 
      y = "Score"
    ) + 
    scale_color_discrete(name = "Metric") +
    ylim(0, 100)
}
