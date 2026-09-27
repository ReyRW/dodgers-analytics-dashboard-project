import requests
import pandas as pd
import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed

TEAM_ID = 119
SEASON = 2026

@st.cache_data
def get_dodgers_schedule():

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

    games = []

    for date_group in schedule_data["dates"]:

        for game in date_group["games"]:

            home_team = game["teams"]["home"]["team"]
            away_team = game["teams"]["away"]["team"]

            dodgers_are_home = (
                home_team["id"] == TEAM_ID
            )

            games.append({
                "Game_ID": game["gamePk"],
                "Date": game["officialDate"],
                "Game_Type": game["gameType"],
                "Opponent": (
                    away_team["name"]
                    if dodgers_are_home
                    else home_team["name"]
                ),
                "Home_Away": (
                    "Home"
                    if dodgers_are_home
                    else "Away"
                ),
                "Status": (
                    game["status"]["abstractGameState"]
                ),
                "Detailed_Status": (
                    game["status"]["detailedState"]
                )
            })

    schedule = pd.DataFrame(games)

    schedule["Date"] = pd.to_datetime(
        schedule["Date"]
    )

    schedule = (
        schedule
        .sort_values(["Date", "Game_ID"])
        .reset_index(drop=True)
    )

    return schedule

@st.cache_data
def get_dodgers_batting():

    player_batting_url = (
        "https://statsapi.mlb.com/api/v1/stats"
        f"?stats=season"
        f"&group=hitting"
        f"&season={SEASON}"
        f"&teamId={TEAM_ID}"
        f"&playerPool=ALL"
        f"&limit=1000"
    )

    response = requests.get(
        player_batting_url,
        timeout=10
    )
    response.raise_for_status()

    data = response.json()

    player_batting_rows = []

    for split in data["stats"][0]["splits"]:

        stat = split["stat"]
        player = split["player"]

        player_batting_rows.append({
            "Player": player["fullName"],
            "Player_ID": player["id"],
            "Position": split.get(
                "position", {}
            ).get("abbreviation", ""),
            "Games": stat.get("gamesPlayed", 0),
            "AB": stat.get("atBats", 0),
            "Hits": stat.get("hits", 0),
            "Doubles": stat.get("doubles", 0),
            "Triples": stat.get("triples", 0),
            "HR": stat.get("homeRuns", 0),
            "RBI": stat.get("rbi", 0),
            "BB": stat.get("baseOnBalls", 0),
            "HBP": stat.get("hitByPitch", 0),
            "SF": stat.get("sacFlies", 0),
            "SO": stat.get("strikeOuts", 0),
            "AVG": stat.get("avg", ".000"),
            "OBP": stat.get("obp", ".000"),
            "SLG": stat.get("slg", ".000"),
            "OPS": stat.get("ops", ".000")
        })

    dodgers_batting = pd.DataFrame(
        player_batting_rows
    )


    dodgers_batting["Calc_AVG"] = (
        dodgers_batting["Hits"] / dodgers_batting["AB"]
    ).fillna(0)



    dodgers_batting["Calc_OBP"] = (
        (
            dodgers_batting["Hits"]
            + dodgers_batting["BB"]
            + dodgers_batting["HBP"]
        )
        /
        (
            dodgers_batting["AB"]
            + dodgers_batting["BB"]
            + dodgers_batting["HBP"]
            + dodgers_batting["SF"]
        )
    ).fillna(0)


    dodgers_batting["Singles"] = (
        dodgers_batting["Hits"]
        - dodgers_batting["Doubles"]
        - dodgers_batting["Triples"]
        - dodgers_batting["HR"]
    )

    dodgers_batting["Total_Bases"] = (
        dodgers_batting["Singles"]
        + (2 * dodgers_batting["Doubles"])
        + (3 * dodgers_batting["Triples"])
        + (4 * dodgers_batting["HR"])
    )


    dodgers_batting["Calc_SLG"] = (
        dodgers_batting["Total_Bases"]
        / dodgers_batting["AB"]
    ).fillna(0)


    dodgers_batting["Calc_OPS"] = (
        dodgers_batting["Calc_OBP"]
        + dodgers_batting["Calc_SLG"]
    )

    return dodgers_batting

@st.cache_data
def get_dodgers_batting_games(dodgers_batting):

    def get_player_games(player):

        player_id = player["Player_ID"]
        player_name = player["Player"]

        game_log_url = (
            f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats"
            f"?stats=gameLog"
            f"&group=hitting"
            f"&season={SEASON}"
        )

        response = requests.get(
            game_log_url,
            timeout=10
        )
        response.raise_for_status()

        data = response.json()

        player_game_rows = []

        try:
            games = data["stats"][0]["splits"]

            for game in games:

                stat = game["stat"]

                player_game_rows.append({
                    "Player": player_name,
                    "Player_ID": player_id,
                    "Date": game["date"],
                    "Opponent": game["opponent"]["name"],
                    "Home_Away": (
                        "Home"
                        if game["isHome"]
                        else "Away"
                    ),
                    "Win": game["isWin"],
                    "Game_ID": game["game"]["gamePk"],
                    "AB": stat.get("atBats", 0),
                    "Hits": stat.get("hits", 0),
                    "Doubles": stat.get("doubles", 0),
                    "Triples": stat.get("triples", 0),
                    "HR": stat.get("homeRuns", 0),
                    "RBI": stat.get("rbi", 0),
                    "Runs": stat.get("runs", 0),
                    "BB": stat.get("baseOnBalls", 0),
                    "SO": stat.get("strikeOuts", 0),
                    "HBP": stat.get("hitByPitch", 0),
                    "SF": stat.get("sacFlies", 0)
                })

        except (IndexError, KeyError):
            print(
                f"No game logs found for {player_name}"
            )

        return player_game_rows

    all_game_rows = []

    with ThreadPoolExecutor(max_workers=10) as executor:

        futures = [
            executor.submit(
                get_player_games,
                player
            )
            for _, player in dodgers_batting.iterrows()
        ]

        for future in as_completed(futures):
            all_game_rows.extend(
                future.result()
            )

    dodgers_games = pd.DataFrame(all_game_rows)

    dodgers_games["Date"] = pd.to_datetime(
        dodgers_games["Date"]
    )

    dodgers_games = (
        dodgers_games
        .sort_values(["Player", "Date"])
        .reset_index(drop=True)
    )

    return dodgers_games

@st.cache_data
def get_dodgers_pitching():

    player_pitching_url = (
        "https://statsapi.mlb.com/api/v1/stats"
        f"?stats=season"
        f"&group=pitching"
        f"&season={SEASON}"
        f"&teamId={TEAM_ID}"
        f"&playerPool=ALL"
        f"&limit=1000"
    )

    response = requests.get(
        player_pitching_url,
        timeout=10
    )
    response.raise_for_status()

    data = response.json()

    pitching_rows = []

    for split in data["stats"][0]["splits"]:

        stat = split["stat"]
        player = split["player"]

        pitching_rows.append({
            "Player": player["fullName"],
            "Player_ID": player["id"],
            "Position": split.get(
                "position", {}
            ).get("abbreviation", ""),
            "Games": stat.get("gamesPlayed", 0),
            "GS": stat.get("gamesStarted", 0),
            "IP": stat.get("inningsPitched", "0.0"),
            "Wins": stat.get("wins", 0),
            "Losses": stat.get("losses", 0),
            "ERA": stat.get("era", ".---"),
            "Hits": stat.get("hits", 0),
            "Runs": stat.get("runs", 0),
            "ER": stat.get("earnedRuns", 0),
            "HR": stat.get("homeRuns", 0),
            "BB": stat.get("baseOnBalls", 0),
            "SO": stat.get("strikeOuts", 0),
            "WHIP": stat.get("whip", ".---"),
            "Saves": stat.get("saves", 0),
            "Holds": stat.get("holds", 0)
        })

    dodgers_pitching = pd.DataFrame(
        pitching_rows
    )

    return dodgers_pitching

@st.cache_data
def get_dodgers_pitching_games(dodgers_pitching):

    def get_pitcher_games(pitcher):

        player_id = pitcher["Player_ID"]
        player_name = pitcher["Player"]

        game_log_url = (
            f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats"
            f"?stats=gameLog"
            f"&group=pitching"
            f"&season={SEASON}"
        )

        response = requests.get(
            game_log_url,
            timeout=10
        )
        response.raise_for_status()

        data = response.json()

        pitcher_game_rows = []

        try:
            games = data["stats"][0]["splits"]

            for game in games:

                stat = game["stat"]

                pitcher_game_rows.append({
                    "Player": player_name,
                    "Player_ID": player_id,
                    "Date": game["date"],
                    "Opponent": game["opponent"]["name"],
                    "Home_Away": (
                        "Home"
                        if game["isHome"]
                        else "Away"
                    ),
                    "Win": game["isWin"],
                    "Game_ID": game["game"]["gamePk"],
                    "GS": stat.get("gamesStarted", 0),
                    "IP": stat.get("inningsPitched", "0.0"),
                    "Outs": stat.get("outs", 0),
                    "Hits": stat.get("hits", 0),
                    "Runs": stat.get("runs", 0),
                    "ER": stat.get("earnedRuns", 0),
                    "HR": stat.get("homeRuns", 0),
                    "BB": stat.get("baseOnBalls", 0),
                    "SO": stat.get("strikeOuts", 0),
                    "HBP": stat.get("hitBatsmen", 0),
                    "Pitches": stat.get("numberOfPitches", 0),
                    "Strikes": stat.get("strikes", 0),
                    "Batters_Faced": stat.get("battersFaced", 0),
                    "Saves": stat.get("saves", 0),
                    "Holds": stat.get("holds", 0)
                })

        except (IndexError, KeyError):
            print(
                f"No game logs found for {player_name}"
            )

        return pitcher_game_rows

    all_game_rows = []

    with ThreadPoolExecutor(max_workers=10) as executor:

        futures = [
            executor.submit(
                get_pitcher_games,
                pitcher
            )
            for _, pitcher in dodgers_pitching.iterrows()
        ]

        for future in as_completed(futures):
            all_game_rows.extend(
                future.result()
            )

    dodgers_games = pd.DataFrame(all_game_rows)

    dodgers_games["Date"] = pd.to_datetime(
        dodgers_games["Date"]
    )

    dodgers_games = (
        dodgers_games
        .sort_values(["Player", "Date"])
        .reset_index(drop=True)
    )

    return dodgers_games