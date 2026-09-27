import pandas as pd
import requests

from sklearn.ensemble import RandomForestClassifier

from data import TEAM_ID, SEASON

FEATURES = [
    "Recent_10_WinPct",
    "Recent_10_RunsScored",
    "Recent_10_RunsAllowed",
    "Opponent_Recent_10_WinPct",
    "Opponent_Recent_10_RunsScored",
    "Opponent_Recent_10_RunsAllowed",
    "Home"
]

def build_dodgers_ml_games(schedule):

    schedule_url = (
        "https://statsapi.mlb.com/api/v1/schedule"
        f"?sportId=1"
        f"&teamId={TEAM_ID}"
        f"&season={SEASON}"
        f"&gameTypes=R,F,D,L,W"
    )

    response = requests.get(
        schedule_url,
        timeout=10
)
    response.raise_for_status()

    schedule_data = response.json()

    ml_game_rows = []

    for date_group in schedule_data["dates"]:

        for game in date_group["games"]:

            if (
                game["status"]["abstractGameState"]
                != "Final"
            ):
                continue

            home = game["teams"]["home"]
            away = game["teams"]["away"]

            if (
                "score" not in home
                or "score" not in away
            ):
                continue

            dodgers_are_home = (
                home["team"]["id"] == TEAM_ID
            )

            if dodgers_are_home:
                opponent = away["team"]["name"]
                dodgers_runs = home["score"]
                opponent_runs = away["score"]
                home_away = "Home"

            else:
                opponent = home["team"]["name"]
                dodgers_runs = away["score"]
                opponent_runs = home["score"]
                home_away = "Away"

            ml_game_rows.append({
                "Game_ID": game["gamePk"],
                "Date": game["officialDate"],
                "Game_Type": game["gameType"],
                "Opponent": opponent,
                "Home_Away": home_away,
                "Dodgers_Runs": dodgers_runs,
                "Opponent_Runs": opponent_runs,
                "Win": dodgers_runs > opponent_runs
            })

    ml_games = pd.DataFrame(ml_game_rows)

    ml_games["Date"] = pd.to_datetime(
        ml_games["Date"]
    )

    ml_games = (
        ml_games
        .drop_duplicates(subset=["Game_ID"])
        .sort_values(["Date", "Game_ID"])
        .reset_index(drop=True)
    )

    ml_games["Win"] = (
        ml_games["Win"].astype(int)
    )

    return ml_games

def add_dodgers_recent_features(ml_games):

    ml_games = (
        ml_games
        .sort_values(["Date", "Game_ID"])
        .reset_index(drop=True)
        .copy()
    )

    ml_games["Recent_10_WinPct"] = (
        ml_games["Win"]
        .shift(1)
        .rolling(
            window=10,
            min_periods=10
        )
        .mean()
    )

    ml_games["Recent_10_RunsScored"] = (
        ml_games["Dodgers_Runs"]
        .shift(1)
        .rolling(
            window=10,
            min_periods=10
        )
        .mean()
    )

    ml_games["Recent_10_RunsAllowed"] = (
        ml_games["Opponent_Runs"]
        .shift(1)
        .rolling(
            window=10,
            min_periods=10
        )
        .mean()
    )

    return ml_games

def get_league_game_history():

    schedule_url = (
        "https://statsapi.mlb.com/api/v1/schedule"
        f"?sportId=1"
        f"&season={SEASON}"
        f"&gameTypes=R,F,D,L,W"
    )

    response = requests.get(
        schedule_url,
        timeout=10
    )
    response.raise_for_status()

    schedule_data = response.json()

    league_games = []

    for date_group in schedule_data["dates"]:

        for game in date_group["games"]:

            if (
                game["status"]["abstractGameState"]
                != "Final"
            ):
                continue

            home = game["teams"]["home"]
            away = game["teams"]["away"]

            # Some postponed games can appear as Final
            # without actually having a final score.
            if (
                "score" not in home
                or "score" not in away
            ):
                continue

            league_games.append({
                "Game_ID": game["gamePk"],
                "Date": game["officialDate"],
                "Game_Type": game["gameType"],
                "Home_Team": home["team"]["name"],
                "Home_Team_ID": home["team"]["id"],
                "Away_Team": away["team"]["name"],
                "Away_Team_ID": away["team"]["id"],
                "Home_Runs": home["score"],
                "Away_Runs": away["score"]
            })

    league_games = pd.DataFrame(
        league_games
    )

    league_games["Date"] = pd.to_datetime(
        league_games["Date"]
    )

    home_games = pd.DataFrame({
        "Game_ID":
            league_games["Game_ID"],
        "Date":
            league_games["Date"],
        "Game_Type":
            league_games["Game_Type"],
        "Team":
            league_games["Home_Team"],
        "Team_ID":
            league_games["Home_Team_ID"],
        "Opponent":
            league_games["Away_Team"],
        "Runs_Scored":
            league_games["Home_Runs"],
        "Runs_Allowed":
            league_games["Away_Runs"]
    })

    away_games = pd.DataFrame({
        "Game_ID":
            league_games["Game_ID"],
        "Date":
            league_games["Date"],
        "Game_Type":
            league_games["Game_Type"],
        "Team":
            league_games["Away_Team"],
        "Team_ID":
            league_games["Away_Team_ID"],
        "Opponent":
            league_games["Home_Team"],
        "Runs_Scored":
            league_games["Away_Runs"],
        "Runs_Allowed":
            league_games["Home_Runs"]
    })

    team_games = pd.concat(
        [home_games, away_games],
        ignore_index=True
    )

    team_games["Win"] = (
        team_games["Runs_Scored"]
        > team_games["Runs_Allowed"]
    ).astype(int)

    team_games = (
        team_games
        .sort_values(
            ["Team_ID", "Date", "Game_ID"]
        )
        .reset_index(drop=True)
    )

    return team_games

def add_team_recent_features(team_games):

    team_games = (
        team_games
        .sort_values(["Team_ID", "Date", "Game_ID"])
        .reset_index(drop=True)
        .copy()
    )

    team_games["Team_Recent_10_WinPct"] = (
        team_games
        .groupby("Team_ID")["Win"]
        .transform(
            lambda x: (
                x.shift(1)
                .rolling(
                    window=10,
                    min_periods=10
                )
                .mean()
            )
        )
    )

    team_games["Team_Recent_10_RunsScored"] = (
        team_games
        .groupby("Team_ID")["Runs_Scored"]
        .transform(
            lambda x: (
                x.shift(1)
                .rolling(
                    window=10,
                    min_periods=10
                )
                .mean()
            )
        )
    )

    team_games["Team_Recent_10_RunsAllowed"] = (
        team_games
        .groupby("Team_ID")["Runs_Allowed"]
        .transform(
            lambda x: (
                x.shift(1)
                .rolling(
                    window=10,
                    min_periods=10
                )
                .mean()
            )
        )
    )

    return team_games

def add_opponent_recent_features(
    ml_games,
    team_games
):

    opponent_features = team_games[
        [
            "Game_ID",
            "Team",
            "Team_Recent_10_WinPct",
            "Team_Recent_10_RunsScored",
            "Team_Recent_10_RunsAllowed"
        ]
    ].copy()

    opponent_features = opponent_features.rename(
        columns={
            "Team": "Opponent",
            "Team_Recent_10_WinPct":
                "Opponent_Recent_10_WinPct",
            "Team_Recent_10_RunsScored":
                "Opponent_Recent_10_RunsScored",
            "Team_Recent_10_RunsAllowed":
                "Opponent_Recent_10_RunsAllowed"
        }
    )

    ml_games = ml_games.merge(
        opponent_features,
        on=["Game_ID", "Opponent"],
        how="left"
    )

    ml_games["Home"] = (
        ml_games["Home_Away"] == "Home"
    ).astype(int)

    return ml_games

def prepare_training_data(schedule):

    ml_games = build_dodgers_ml_games(
        schedule
    )

    ml_games = add_dodgers_recent_features(
        ml_games
    )

    team_games = get_league_game_history()

    team_games = add_team_recent_features(
        team_games
    )

    ml_games = add_opponent_recent_features(
        ml_games,
        team_games
    )

    training_data = (
        ml_games
        .dropna(
            subset=FEATURES + ["Win"]
        )
        .sort_values(["Date", "Game_ID"])
        .reset_index(drop=True)
    )

    return training_data, ml_games, team_games

def train_random_forest(training_data):

    X = training_data[FEATURES]
    y = training_data["Win"]

    model = RandomForestClassifier(
        n_estimators=500,
        max_depth=4,
        min_samples_leaf=5,
        random_state=42
    )

    model.fit(X, y)

    return model

def predict_dodgers_game(
    game,
    model,
    ml_games,
    team_games
):

    game_date = game["Date"]
    game_type = game["Game_Type"]
    opponent = game["Opponent"]
    home_away = game["Home_Away"]

    dodgers_last_10 = (
        ml_games[
            ml_games["Date"] < game_date
        ]
        .sort_values(["Date", "Game_ID"])
        .tail(10)
    )

    opponent_last_10 = (
        team_games[
            (team_games["Team"] == opponent) &
            (team_games["Date"] < game_date)
        ]
        .sort_values(["Date", "Game_ID"])
        .tail(10)
    )

    if (
        len(dodgers_last_10) < 10
        or len(opponent_last_10) < 10
    ):
        return None

    game_features = pd.DataFrame(
        [{
            "Recent_10_WinPct":
                dodgers_last_10["Win"].mean(),

            "Recent_10_RunsScored":
                dodgers_last_10["Dodgers_Runs"].mean(),

            "Recent_10_RunsAllowed":
                dodgers_last_10["Opponent_Runs"].mean(),

            "Opponent_Recent_10_WinPct":
                opponent_last_10["Win"].mean(),

            "Opponent_Recent_10_RunsScored":
                opponent_last_10["Runs_Scored"].mean(),

            "Opponent_Recent_10_RunsAllowed":
                opponent_last_10["Runs_Allowed"].mean(),

            "Home":
                1 if home_away == "Home" else 0
        }]
    )

    game_features = game_features[FEATURES]

    win_probability = model.predict_proba(
        game_features
    )[0, 1]

    return {
        "Date": game_date,
        "Game_Type": game_type,
        "Opponent": opponent,
        "Home_Away": home_away,
        "Dodgers_Win_Probability":
            win_probability
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