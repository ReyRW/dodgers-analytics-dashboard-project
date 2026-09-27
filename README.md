# Los Angeles Dodgers Analytics Dashboard

This is an interactive baseball analytics dashboard project built with Python and Streamlit that uses live MLB data to explore Los Angeles Dodgers performance and generate machine learning-based game predictions.

**Live Dashboard:** https://dodgers-analytics-dashboard-project.streamlit.app

## Overview

Wanting to start my first data science project for university combined with my love for baseball, I started this project in Microsoft Excel as a prototype. After costructing the basic graphs and calcualtions and realizing I wanted to expand this into Machine Learning as well, I transitioned to a full-on Python project. The dashboard retrieves live MLB data, processes and calculcates player and team statistics, provides interactive batting and pitching statistics, and uses a Random Forest ML model to estimate the probability of winning their next game.

This project was built to explore the intersection of data science, machine learning, and sports analytics.

## Features

- **Live MLB Data** — Retrieves current Dodgers schedule, batting, and pitching data from the MLB Stats API.
- **Batting Analytics** — Explore player performance and offensive statistics.
- **Pitching Analytics** — Analyze Dodgers pitchers and pitching performance.
- **Schedule Tracking** — Displays the Dodgers schedule and automatically identifies the next upcoming game.
- **Game Prediction** — Uses a Random Forest ML model to estimate the Dodgers' probability of winning their next game.
- **Interactive Dashboard** — Multipage interface for exploring data and statistics.

## Technologies

- Python
- Streamlit
- pandas
- scikit-learn
- MLB Stats API
- Git & GitHub

## Machine Learning

The Game Prediction page uses a Random Forest classifier trained on completed MLB regular-season games from 2023 through 2026.

Rather than training only on Dodgers games, the model uses league-wide MLB game data to learn relationships between team performance and game outcomes.

### Model Features

For both teams in each matchup, the model considers:

- Recent 10-game win percentage
- Recent 10-game average runs scored
- Recent 10-game average runs allowed
- Season-to-date win percentage
- Season-to-date run differential per game

To prevent data leakage, historical game features are calculated using only games that occurred before the game being predicted.

### Model Development

Multiple approaches were evaluated during development, including Logistic Regression and Random Forest models. Additional experiments tested starting-pitcher statistics and difference-based features.

The model is intended as a sports analytics experiment rather than a guarantee of game outcomes.