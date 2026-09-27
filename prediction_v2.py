import pandas as pd
import requests

from sklearn.ensemble import RandomForestClassifier

MODEL_SEASONS = [
    2023,
    2024,
    2025,
    2026
]

MODEL_FEATURES = [
    "Recent_10_WinPct",
    "Recent_10_RunsScored",
    "Recent_10_RunsAllowed",
    "Season_WinPct",
    "Season_RunDiff_Per_Game",
    "Opponent_Recent_10_WinPct",
    "Opponent_Recent_10_RunsScored",
    "Opponent_Recent_10_RunsAllowed",
    "Opponent_Season_WinPct",
    "Opponent_Season_RunDiff_Per_Game",
]

def get_mlb_games_for_season(season):

    url = (
        "https://statsapi.mlb.com/api/v1/schedule"
        f"?sportId=1&season={season}&gameType=R"
    )

    response = requests.get(
        url,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    game_rows = []

    for date_group in data.get("dates", []):

        for game in date_group.get("games", []):

            if game["status"]["abstractGameState"] != "Final":
                continue

            home = game["teams"]["home"]
            away = game["teams"]["away"]

            home_runs = home.get("score")
            away_runs = away.get("score")

            if home_runs is None or away_runs is None:
                continue

            game_rows.append(
                {
                    "Game_ID": game["gamePk"],
                    "Date": game["gameDate"],
                    "Season": season,
                    "Home_Team_ID": home["team"]["id"],
                    "Home_Team": home["team"]["name"],
                    "Away_Team_ID": away["team"]["id"],
                    "Away_Team": away["team"]["name"],
                    "Home_Runs": home_runs,
                    "Away_Runs": away_runs,
                    "Home_Win": int(
                        home_runs > away_runs
                    )
                }
            )

        games = pd.DataFrame(game_rows)

    if not games.empty:

        games["Date"] = pd.to_datetime(
            games["Date"],
            utc=True
        )

        # Remove duplicate schedule entries for
        # suspended/resumed MLB games.
        games = (
            games
            .sort_values(
                ["Date", "Game_ID"]
            )
            .drop_duplicates(
                subset="Game_ID",
                keep="last"
            )
            .reset_index(drop=True)
        )

    return games

def build_team_game_history(games):

    team_rows = []

    for _, game in games.iterrows():

        team_rows.append(
            {
                "Game_ID": game["Game_ID"],
                "Date": game["Date"],
                "Season": game["Season"],
                "Team_ID": game["Home_Team_ID"],
                "Team": game["Home_Team"],
                "Opponent_ID": game["Away_Team_ID"],
                "Opponent": game["Away_Team"],
                "Home": 1,
                "Runs_Scored": game["Home_Runs"],
                "Runs_Allowed": game["Away_Runs"],
                "Win": game["Home_Win"]
            }
        )

        team_rows.append(
            {
                "Game_ID": game["Game_ID"],
                "Date": game["Date"],
                "Season": game["Season"],
                "Team_ID": game["Away_Team_ID"],
                "Team": game["Away_Team"],
                "Opponent_ID": game["Home_Team_ID"],
                "Opponent": game["Home_Team"],
                "Home": 0,
                "Runs_Scored": game["Away_Runs"],
                "Runs_Allowed": game["Home_Runs"],
                "Win": 1 - game["Home_Win"]
            }
        )
    team_games = pd.DataFrame(team_rows)

    team_games = (
        team_games
        .sort_values(
            ["Season", "Team_ID", "Date", "Game_ID"]
        )
        .reset_index(drop=True)
    )

    return team_games

def add_team_features(team_games):

    games = team_games.copy()

    games = (
        games
        .sort_values(
            ["Season", "Team_ID", "Date", "Game_ID"]
        )
        .reset_index(drop=True)
    )

    grouped = games.groupby(
        ["Season", "Team_ID"],
        group_keys=False
    )

    # Previous 10 games only.
    games["Recent_10_WinPct"] = grouped["Win"].transform(
        lambda x: x.shift(1).rolling(
            window=10,
            min_periods=10
        ).mean()
    )

    games["Recent_10_RunsScored"] = grouped[
        "Runs_Scored"
    ].transform(
        lambda x: x.shift(1).rolling(
            window=10,
            min_periods=10
        ).mean()
    )

    games["Recent_10_RunsAllowed"] = grouped[
        "Runs_Allowed"
    ].transform(
        lambda x: x.shift(1).rolling(
            window=10,
            min_periods=10
        ).mean()
    )

    # Season-to-date features.
    # shift(1) prevents the current game from entering
    # its own prediction features.
    games["Season_Games_Before"] = grouped.cumcount()

    games["Season_Wins_Before"] = grouped["Win"].transform(
        lambda x: x.shift(1).fillna(0).cumsum()
    )

    games["Season_RunsScored_Before"] = grouped[
        "Runs_Scored"
    ].transform(
        lambda x: x.shift(1).fillna(0).cumsum()
    )

    games["Season_RunsAllowed_Before"] = grouped[
        "Runs_Allowed"
    ].transform(
        lambda x: x.shift(1).fillna(0).cumsum()
    )

    valid_games = games["Season_Games_Before"] > 0

    games["Season_WinPct"] = 0.0
    games["Season_RunDiff_Per_Game"] = 0.0

    games.loc[
        valid_games,
        "Season_WinPct"
    ] = (
        games.loc[
            valid_games,
            "Season_Wins_Before"
        ]
        / games.loc[
            valid_games,
            "Season_Games_Before"
        ]
    )

    games.loc[
        valid_games,
        "Season_RunDiff_Per_Game"
    ] = (
        (
            games.loc[
                valid_games,
                "Season_RunsScored_Before"
            ]
            -
            games.loc[
                valid_games,
                "Season_RunsAllowed_Before"
            ]
        )
        / games.loc[
            valid_games,
            "Season_Games_Before"
        ]
    )

    return games

def add_opponent_features(team_features):

    games = team_features.copy()

    feature_columns = [
        "Recent_10_WinPct",
        "Recent_10_RunsScored",
        "Recent_10_RunsAllowed",
        "Season_WinPct",
        "Season_RunDiff_Per_Game"
    ]

    opponent_features = games[
        [
            "Game_ID",
            "Team_ID",
            *feature_columns
        ]
    ].copy()

    opponent_features = opponent_features.rename(
        columns={
            "Team_ID": "Opponent_ID",
            "Recent_10_WinPct":
                "Opponent_Recent_10_WinPct",
            "Recent_10_RunsScored":
                "Opponent_Recent_10_RunsScored",
            "Recent_10_RunsAllowed":
                "Opponent_Recent_10_RunsAllowed",
            "Season_WinPct":
                "Opponent_Season_WinPct",
            "Season_RunDiff_Per_Game":
                "Opponent_Season_RunDiff_Per_Game"
        }
    )

    games = games.merge(
        opponent_features,
        on=[
            "Game_ID",
            "Opponent_ID"
        ],
        how="left",
        validate="many_to_one"
    )

    return games

def build_model_data():

    season_datasets = []

    for season in MODEL_SEASONS:

        season_games = get_mlb_games_for_season(
            season
        )

        season_datasets.append(
            season_games
        )

    mlb_games = pd.concat(
        season_datasets,
        ignore_index=True
    )

    team_games = build_team_game_history(
        mlb_games
    )

    team_features = add_team_features(
        team_games
    )

    matchup_features = add_opponent_features(
        team_features
    )

    model_data = matchup_features[
        matchup_features["Home"] == 1
    ].copy()

    model_data = model_data.dropna(
        subset=MODEL_FEATURES + ["Win"]
    )

    return model_data, team_games

def train_v2_model(model_data):

    X = model_data[
        MODEL_FEATURES
    ]

    y = model_data[
        "Win"
    ]

    model = RandomForestClassifier(
        n_estimators=500,
        max_depth=6,
        min_samples_leaf=10,
        random_state=42,
        n_jobs=-1
    )

    model.fit(
        X,
        y
    )

    return model

def get_latest_team_features(
    team_games,
    team_id,
    season
):

    team_history = team_games[
        (team_games["Team_ID"] == team_id)
        & (team_games["Season"] == season)
    ].copy()

    team_history = team_history.sort_values(
        ["Date", "Game_ID"]
    )

    if len(team_history) < 10:
        return None

    recent_10 = team_history.tail(10)

    return {
        "Recent_10_WinPct":
            recent_10["Win"].mean(),

        "Recent_10_RunsScored":
            recent_10["Runs_Scored"].mean(),

        "Recent_10_RunsAllowed":
            recent_10["Runs_Allowed"].mean(),

        "Season_WinPct":
            team_history["Win"].mean(),

        "Season_RunDiff_Per_Game":
            (
                team_history["Runs_Scored"].sum()
                - team_history["Runs_Allowed"].sum()
            )
            / len(team_history)
    }

def predict_dodgers_game_v2(
    next_game,
    model,
    team_games
):

    season = next_game["Date"].year
    opponent = next_game["Opponent"]
    home_away = next_game["Home_Away"]

    season_games = team_games[
        team_games["Season"] == season
    ]

    dodgers_rows = season_games[
        season_games["Team"] == "Los Angeles Dodgers"
    ]

    opponent_rows = season_games[
        season_games["Team"] == opponent
    ]

    if (
        dodgers_rows.empty
        or opponent_rows.empty
    ):
        return None

    dodgers_id = dodgers_rows[
        "Team_ID"
    ].iloc[0]

    opponent_id = opponent_rows[
        "Team_ID"
    ].iloc[0]

    if home_away == "Home":
        home_id = dodgers_id
        away_id = opponent_id
    else:
        home_id = opponent_id
        away_id = dodgers_id

    home_features = get_latest_team_features(
        team_games,
        home_id,
        season
    )

    away_features = get_latest_team_features(
        team_games,
        away_id,
        season
    )

    if (
        home_features is None
        or away_features is None
    ):
        return None

    prediction_features = pd.DataFrame(
        [
            {
                "Recent_10_WinPct":
                    home_features["Recent_10_WinPct"],

                "Recent_10_RunsScored":
                    home_features["Recent_10_RunsScored"],

                "Recent_10_RunsAllowed":
                    home_features["Recent_10_RunsAllowed"],

                "Season_WinPct":
                    home_features["Season_WinPct"],

                "Season_RunDiff_Per_Game":
                    home_features["Season_RunDiff_Per_Game"],

                "Opponent_Recent_10_WinPct":
                    away_features["Recent_10_WinPct"],

                "Opponent_Recent_10_RunsScored":
                    away_features["Recent_10_RunsScored"],

                "Opponent_Recent_10_RunsAllowed":
                    away_features["Recent_10_RunsAllowed"],

                "Opponent_Season_WinPct":
                    away_features["Season_WinPct"],

                "Opponent_Season_RunDiff_Per_Game":
                    away_features["Season_RunDiff_Per_Game"]
            }
        ],
        columns=MODEL_FEATURES
    )

    home_win_probability = model.predict_proba(
        prediction_features
    )[0, 1]

    if home_away == "Home":
        dodgers_win_probability = (
            home_win_probability
        )
    else:
        dodgers_win_probability = (
            1 - home_win_probability
        )

    return {
        "Game_Type": next_game["Game_Type"],
        "Opponent": opponent,
        "Home_Away": home_away,
        "Date": next_game["Date"],
        "Dodgers_Win_Probability":
            dodgers_win_probability
    }

def get_next_dodgers_game(schedule):

    upcoming_games = schedule[
        (schedule["Status"] == "Preview")
        & (schedule["Detailed_Status"] == "Scheduled")
    ].copy()

    upcoming_games = (
        upcoming_games
        .sort_values(["Date", "Game_ID"])
        .reset_index(drop=True)
    )

    if upcoming_games.empty:
        return None

    return upcoming_games.iloc[0]

def get_next_dodgers_game(schedule):

    upcoming_games = schedule[
        (schedule["Status"] == "Preview")
        & (schedule["Detailed_Status"] == "Scheduled")
    ].copy()

    upcoming_games = (
        upcoming_games
        .sort_values(["Date", "Game_ID"])
        .reset_index(drop=True)
    )

    if upcoming_games.empty:
        return None

    return upcoming_games.iloc[0]