import pandas as pd

def add_batting_rolling_stats(dodgers_games):

    rolling_columns = [
        "Hits",
        "AB",
        "BB",
        "HBP",
        "SF",
        "Doubles",
        "Triples",
        "HR"
    ]

    for column in rolling_columns:

        dodgers_games[f"Rolling_10_{column}"] = (
            dodgers_games
            .groupby("Player")[column]
            .transform(
                lambda x: x.rolling(
                    10,
                    min_periods=10
                ).sum()
            )
        )

    dodgers_games["Rolling_10_AVG"] = (
        dodgers_games["Rolling_10_Hits"]
        / dodgers_games["Rolling_10_AB"]
    )

    dodgers_games["Rolling_10_OBP"] = (
        (
            dodgers_games["Rolling_10_Hits"]
            + dodgers_games["Rolling_10_BB"]
            + dodgers_games["Rolling_10_HBP"]
        )
        /
        (
            dodgers_games["Rolling_10_AB"]
            + dodgers_games["Rolling_10_BB"]
            + dodgers_games["Rolling_10_HBP"]
            + dodgers_games["Rolling_10_SF"]
        )
    )

    dodgers_games["Rolling_10_Singles"] = (
        dodgers_games["Rolling_10_Hits"]
        - dodgers_games["Rolling_10_Doubles"]
        - dodgers_games["Rolling_10_Triples"]
        - dodgers_games["Rolling_10_HR"]
    )

    dodgers_games["Rolling_10_Total_Bases"] = (
        dodgers_games["Rolling_10_Singles"]
        + 2 * dodgers_games["Rolling_10_Doubles"]
        + 3 * dodgers_games["Rolling_10_Triples"]
        + 4 * dodgers_games["Rolling_10_HR"]
    )

    dodgers_games["Rolling_10_SLG"] = (
        dodgers_games["Rolling_10_Total_Bases"]
        / dodgers_games["Rolling_10_AB"]
    )

    dodgers_games["Rolling_10_OPS"] = (
        dodgers_games["Rolling_10_OBP"]
        + dodgers_games["Rolling_10_SLG"]
    )

    return dodgers_games

def get_player_summary(dodgers_batting, player_name):

    player = dodgers_batting[
        dodgers_batting["Player"] == player_name
    ]

    if player.empty:
        return None

    return player.iloc[0]

def calculate_batting_trends(dodgers_games):
    trend_rows = []

    for player_name, player_data in dodgers_games.groupby("Player"):

        player_data = player_data.sort_values("Date")

        
        if len(player_data) < 20:
            continue

        previous_10 = player_data.iloc[-20:-10]
        recent_10 = player_data.iloc[-10:]

        def calculate_ops(games):

            hits = games["Hits"].sum()
            doubles = games["Doubles"].sum()
            triples = games["Triples"].sum()
            home_runs = games["HR"].sum()
            at_bats = games["AB"].sum()
            walks = games["BB"].sum()
            hbp = games["HBP"].sum()
            sac_flies = games["SF"].sum()

            singles = hits - doubles - triples - home_runs

            total_bases = (
                singles
                + 2 * doubles
                + 3 * triples
                + 4 * home_runs
            )

            obp_denominator = (
                at_bats + walks + hbp + sac_flies
            )

            obp = (
                (hits + walks + hbp) / obp_denominator
                if obp_denominator > 0
                else 0
            )

            slg = (
                total_bases / at_bats
                if at_bats > 0
                else 0
            )

            return obp + slg

        previous_ops = calculate_ops(previous_10)
        recent_ops = calculate_ops(recent_10)

        trend_rows.append({
            "Player": player_name,
            "Previous_10_OPS": previous_ops,
            "Recent_10_OPS": recent_ops,
            "OPS_Change": recent_ops - previous_ops
        })

    return pd.DataFrame(trend_rows)

def get_batting_leaderboard(
    dodgers_batting,
    metric,
    top_n=5,
    min_ab=100
):

    metric_columns = {
        "AVG": "Calc_AVG",
        "OBP": "Calc_OBP",
        "SLG": "Calc_SLG",
        "OPS": "Calc_OPS",
        "HR": "HR",
        "RBI": "RBI",
        "Hits": "Hits"
    }

    selected_column = metric_columns[metric]

    qualified = dodgers_batting[
        dodgers_batting["AB"] >= min_ab
    ].copy()

    leaderboard = (
        qualified
        .sort_values(
            selected_column,
            ascending=False
        )
        .head(top_n)
        .reset_index(drop=True)
    )

    leaderboard.index = leaderboard.index + 1

    return leaderboard

def calculate_batting_split(games):

    hits = games["Hits"].sum()
    doubles = games["Doubles"].sum()
    triples = games["Triples"].sum()
    home_runs = games["HR"].sum()
    at_bats = games["AB"].sum()
    walks = games["BB"].sum()
    hbp = games["HBP"].sum()
    sac_flies = games["SF"].sum()

    singles = hits - doubles - triples - home_runs

    total_bases = (
        singles
        + 2 * doubles
        + 3 * triples
        + 4 * home_runs
    )

    avg = hits / at_bats if at_bats > 0 else 0

    obp_denominator = at_bats + walks + hbp + sac_flies

    obp = (
        (hits + walks + hbp) / obp_denominator
        if obp_denominator > 0
        else 0
    )

    slg = total_bases / at_bats if at_bats > 0 else 0

    ops = obp + slg

    return avg, obp, slg, ops

def get_home_away_splits(dodgers_games, player_name):

    player_data = dodgers_games[
        dodgers_games["Player"] == player_name
    ]

    split_rows = []

    for split in ["Home", "Away"]:

        split_data = player_data[
            player_data["Home_Away"] == split
        ]

        avg, obp, slg, ops = calculate_batting_split(
            split_data
        )

        split_rows.append({
            "Split": split,
            "Games": len(split_data),
            "AVG": avg,
            "OBP": obp,
            "SLG": slg,
            "OPS": ops
        })

    return pd.DataFrame(split_rows)

def innings_to_outs(ip):

    ip = str(ip)

    if "." in ip:
        innings, outs = ip.split(".")
    else:
        innings = ip
        outs = "0"

    return int(innings) * 3 + int(outs)


def add_pitching_stats(dodgers_pitching):

    dodgers_pitching["Outs"] = (
        dodgers_pitching["IP"]
        .apply(innings_to_outs)
    )

    dodgers_pitching["Calc_IP"] = (
        dodgers_pitching["Outs"] / 3
    )

    valid_ip = dodgers_pitching["Calc_IP"] > 0

    dodgers_pitching["Calc_ERA"] = 0.0
    dodgers_pitching["Calc_WHIP"] = 0.0
    dodgers_pitching["Calc_K9"] = 0.0
    dodgers_pitching["Calc_BB9"] = 0.0
    dodgers_pitching["Calc_KBB"] = 0.0

    dodgers_pitching.loc[valid_ip, "Calc_ERA"] = (
        dodgers_pitching.loc[valid_ip, "ER"] * 9
        / dodgers_pitching.loc[valid_ip, "Calc_IP"]
    )

    dodgers_pitching.loc[valid_ip, "Calc_WHIP"] = (
        (
            dodgers_pitching.loc[valid_ip, "BB"]
            + dodgers_pitching.loc[valid_ip, "Hits"]
        )
        / dodgers_pitching.loc[valid_ip, "Calc_IP"]
    )

    dodgers_pitching.loc[valid_ip, "Calc_K9"] = (
        dodgers_pitching.loc[valid_ip, "SO"] * 9
        / dodgers_pitching.loc[valid_ip, "Calc_IP"]
    )

    dodgers_pitching.loc[valid_ip, "Calc_BB9"] = (
        dodgers_pitching.loc[valid_ip, "BB"] * 9
        / dodgers_pitching.loc[valid_ip, "Calc_IP"]
    )

    valid_bb = dodgers_pitching["BB"] > 0

    dodgers_pitching.loc[valid_bb, "Calc_KBB"] = (
        dodgers_pitching.loc[valid_bb, "SO"]
        / dodgers_pitching.loc[valid_bb, "BB"]
    )

    return dodgers_pitching

def add_pitching_rolling_stats(dodgers_pitching_games):

    rolling_pitching_columns = [
        "Outs",
        "ER",
        "Hits",
        "BB",
        "SO"
    ]

    for column in rolling_pitching_columns:

        dodgers_pitching_games[f"Rolling_5_{column}"] = (
            dodgers_pitching_games
            .groupby("Player")[column]
            .transform(
                lambda x: x.rolling(
                    5,
                    min_periods=5
                ).sum()
            )
        )

    dodgers_pitching_games["Rolling_5_IP"] = (
        dodgers_pitching_games["Rolling_5_Outs"] / 3
    )

    valid_ip = dodgers_pitching_games["Rolling_5_IP"] > 0

    dodgers_pitching_games["Rolling_5_ERA"] = 0.0
    dodgers_pitching_games["Rolling_5_WHIP"] = 0.0
    dodgers_pitching_games["Rolling_5_K9"] = 0.0
    dodgers_pitching_games["Rolling_5_BB9"] = 0.0
    dodgers_pitching_games["Rolling_5_KBB"] = 0.0

    dodgers_pitching_games.loc[valid_ip, "Rolling_5_ERA"] = (
        dodgers_pitching_games.loc[valid_ip, "Rolling_5_ER"] * 9
        / dodgers_pitching_games.loc[valid_ip, "Rolling_5_IP"]
    )

    dodgers_pitching_games.loc[valid_ip, "Rolling_5_WHIP"] = (
        (
            dodgers_pitching_games.loc[valid_ip, "Rolling_5_BB"]
            + dodgers_pitching_games.loc[valid_ip, "Rolling_5_Hits"]
        )
        / dodgers_pitching_games.loc[valid_ip, "Rolling_5_IP"]
    )

    dodgers_pitching_games.loc[valid_ip, "Rolling_5_K9"] = (
        dodgers_pitching_games.loc[valid_ip, "Rolling_5_SO"] * 9
        / dodgers_pitching_games.loc[valid_ip, "Rolling_5_IP"]
    )

    dodgers_pitching_games.loc[valid_ip, "Rolling_5_BB9"] = (
        dodgers_pitching_games.loc[valid_ip, "Rolling_5_BB"] * 9
        / dodgers_pitching_games.loc[valid_ip, "Rolling_5_IP"]
    )

    valid_bb = dodgers_pitching_games["Rolling_5_BB"] > 0

    dodgers_pitching_games.loc[valid_bb, "Rolling_5_KBB"] = (
        dodgers_pitching_games.loc[valid_bb, "Rolling_5_SO"]
        / dodgers_pitching_games.loc[valid_bb, "Rolling_5_BB"]
    )

    return dodgers_pitching_games

def get_pitching_leaderboard(
    dodgers_pitching,
    metric,
    top_n=5,
    min_ip=20
):

    metric_columns = {
        "ERA": "Calc_ERA",
        "WHIP": "Calc_WHIP",
        "K/9": "Calc_K9",
        "BB/9": "Calc_BB9",
        "K/BB": "Calc_KBB",
        "SO": "SO",
        "Saves": "Saves"
    }

    selected_column = metric_columns[metric]

    qualified = dodgers_pitching[
        dodgers_pitching["Calc_IP"] >= min_ip
    ].copy()

    if metric in ["ERA", "WHIP", "BB/9"]:
        ascending = True
    else:
        ascending = False

    leaderboard = (
        qualified
        .sort_values(
            selected_column,
            ascending=ascending
        )
        .head(top_n)
        .reset_index(drop=True)
    )

    return leaderboard

def calculate_pitching_trends(dodgers_pitching_games):

    trend_rows = []

    for player in dodgers_pitching_games["Player"].unique():

        player_games = (
            dodgers_pitching_games[
                dodgers_pitching_games["Player"] == player
            ]
            .sort_values("Date")
        )

        if len(player_games) < 10:
            continue

        previous_5 = player_games.iloc[-10:-5]
        recent_5 = player_games.iloc[-5:]

        previous_outs = previous_5["Outs"].sum()
        recent_outs = recent_5["Outs"].sum()

        if previous_outs == 0 or recent_outs == 0:
            continue

        previous_ip = previous_outs / 3
        recent_ip = recent_outs / 3

        previous_era = (
            previous_5["ER"].sum() * 9
            / previous_ip
        )

        recent_era = (
            recent_5["ER"].sum() * 9
            / recent_ip
        )

        trend_rows.append({
            "Player": player,
            "Previous_5_ERA": previous_era,
            "Recent_5_ERA": recent_era,
            "ERA_Change": recent_era - previous_era
        })

    return pd.DataFrame(trend_rows)

def calculate_pitching_split(games):

    outs = games["Outs"].sum()
    earned_runs = games["ER"].sum()
    hits = games["Hits"].sum()
    walks = games["BB"].sum()
    strikeouts = games["SO"].sum()

    innings = outs / 3

    if innings > 0:
        era = earned_runs * 9 / innings
        whip = (walks + hits) / innings
        k9 = strikeouts * 9 / innings
        bb9 = walks * 9 / innings
    else:
        era = 0
        whip = 0
        k9 = 0
        bb9 = 0

    kbb = (
        strikeouts / walks
        if walks > 0
        else 0
    )

    return era, whip, k9, bb9, kbb


def get_pitching_home_away_splits(
    dodgers_pitching_games,
    player_name
):

    player_data = dodgers_pitching_games[
        dodgers_pitching_games["Player"] == player_name
    ]

    split_rows = []

    for split in ["Home", "Away"]:

        split_data = player_data[
            player_data["Home_Away"] == split
        ]

        era, whip, k9, bb9, kbb = (
            calculate_pitching_split(split_data)
        )

        split_rows.append({
            "Split": split,
            "Games": len(split_data),
            "ERA": era,
            "WHIP": whip,
            "K/9": k9,
            "BB/9": bb9,
            "K/BB": kbb
        })

    return pd.DataFrame(split_rows)