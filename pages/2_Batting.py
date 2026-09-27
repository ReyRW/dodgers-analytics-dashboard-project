import streamlit as st
import requests

from data import (
    get_dodgers_batting,
    get_dodgers_batting_games
)

from analytics import (
    add_batting_rolling_stats,
    get_player_summary,
    calculate_batting_trends,
    get_batting_leaderboard,
    get_home_away_splits
)

st.title("Dodgers Batting Analytics")

st.subheader("Dodgers Batting")

try:
    batting = get_dodgers_batting()
    batting_games = get_dodgers_batting_games(batting)

except requests.exceptions.RequestException:
    st.error(
        "Unable to retrieve Dodgers batting data right now. "
        "Please try again later."
    )
    st.stop()

if batting.empty:
    st.warning(
        "No Dodgers batting data is currently available."
    )
    st.stop()

if batting_games.empty:
    st.warning(
        "No Dodgers batting game logs are currently available."
    )
    st.stop()

batting_display = batting[
    [
        "Player",
        "Position",
        "Games",
        "AB",
        "Hits",
        "Doubles",
        "Triples",
        "HR",
        "RBI",
        "BB",
        "HBP",
        "SF",
        "SO",
        "Calc_AVG",
        "Calc_OBP",
        "Calc_SLG",
        "Calc_OPS"
    ]
].copy()

batting_display = batting_display.rename(
    columns={
        "Calc_AVG": "AVG",
        "Calc_OBP": "OBP",
        "Calc_SLG": "SLG",
        "Calc_OPS": "OPS"
    }
)

st.dataframe(
    batting_display,
    use_container_width=True,
    hide_index=True,
    column_config={
        "AVG": st.column_config.NumberColumn(
            "AVG",
            format="%.3f"
        ),
        "OBP": st.column_config.NumberColumn(
            "OBP",
            format="%.3f"
        ),
        "SLG": st.column_config.NumberColumn(
            "SLG",
            format="%.3f"
        ),
        "OPS": st.column_config.NumberColumn(
            "OPS",
            format="%.3f"
        )
    }
)

batting_games = add_batting_rolling_stats(batting_games)

batting_trends = calculate_batting_trends(
    batting_games
)

st.subheader("Player Analysis")

player_names = sorted(
    batting["Player"].unique()
)

selected_player = st.selectbox(
    "Select a player",
    player_names
)

player = get_player_summary(
    batting,
    selected_player
)

if player is not None:

    st.markdown(f"### {selected_player}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "AVG",
            f"{player['Calc_AVG']:.3f}"
        )

    with col2:
        st.metric(
            "OBP",
            f"{player['Calc_OBP']:.3f}"
        )

    with col3:
        st.metric(
            "SLG",
            f"{player['Calc_SLG']:.3f}"
        )

    with col4:
        st.metric(
            "OPS",
            f"{player['Calc_OPS']:.3f}"
        )

    col5, col6, col7, col8, col9 = st.columns(5)

    with col5:
        st.metric("HR", int(player["HR"]))

    with col6:
        st.metric("RBI", int(player["RBI"]))

    with col7:
        st.metric("Hits", int(player["Hits"]))

    with col8:
        st.metric("BB", int(player["BB"]))

    with col9:
        st.metric("SO", int(player["SO"]))

    st.markdown("### 10-Game Rolling Performance")

    metric_columns = {
        "AVG": "Rolling_10_AVG",
        "OBP": "Rolling_10_OBP",
        "SLG": "Rolling_10_SLG",
        "OPS": "Rolling_10_OPS"
    }

    selected_metric = st.selectbox(
        "Select a metric",
        list(metric_columns.keys())
    )

    selected_column = metric_columns[selected_metric]

    player_games = batting_games[
        batting_games["Player"] == selected_player
    ].copy()

    player_games = player_games[
        player_games[selected_column].notna()
    ]

    chart_data = (
    player_games[
        ["Date", selected_column]
    ]
    .set_index("Date")
    )

    chart_data = chart_data.rename(
        columns={
            selected_column: selected_metric
        }
    )

    st.line_chart(
        chart_data,
        y=selected_metric
    )

    st.markdown("### Home vs. Away")

    home_away_splits = get_home_away_splits(
        batting_games,
        selected_player
    )

    st.dataframe(
        home_away_splits,
        use_container_width=True,
        hide_index=True,
        column_config={
            "AVG": st.column_config.NumberColumn(
                "AVG",
                format="%.3f"
            ),
            "OBP": st.column_config.NumberColumn(
                "OBP",
                format="%.3f"
            ),
            "SLG": st.column_config.NumberColumn(
                "SLG",
                format="%.3f"
            ),
            "OPS": st.column_config.NumberColumn(
                "OPS",
                format="%.3f"
            )
        }
    )

st.markdown("### Player Comparison")

comparison_col1, comparison_col2 = st.columns(2)

with comparison_col1:
    player_1 = st.selectbox(
        "Player 1",
        player_names,
        key="player_1"
    )

with comparison_col2:
    player_2 = st.selectbox(
        "Player 2",
        player_names,
        index=1 if len(player_names) > 1 else 0,
        key="player_2"
    )

comparison_metric = st.selectbox(
    "Comparison Metric",
    ["AVG", "OBP", "SLG", "OPS"]
)

comparison_metric_columns = {
    "AVG": "Rolling_10_AVG",
    "OBP": "Rolling_10_OBP",
    "SLG": "Rolling_10_SLG",
    "OPS": "Rolling_10_OPS"
}

comparison_column = comparison_metric_columns[
    comparison_metric
]

player_1_data = batting_games[
    batting_games["Player"] == player_1
][["Date", comparison_column]].copy()

player_2_data = batting_games[
    batting_games["Player"] == player_2
][["Date", comparison_column]].copy()

player_1_data = player_1_data.rename(
    columns={comparison_column: player_1}
)

player_2_data = player_2_data.rename(
    columns={comparison_column: player_2}
)

comparison_data = player_1_data.merge(
    player_2_data,
    on="Date",
    how="outer"
)

comparison_data = (
    comparison_data
    .sort_values("Date")
    .set_index("Date")
)

comparison_data = comparison_data.interpolate(
    method="time",
    limit_area="inside"
)

st.line_chart(comparison_data)

st.subheader("Batting Leaderboard")

leaderboard_col1, leaderboard_col2, leaderboard_col3 = st.columns(3)

with leaderboard_col1:
    leaderboard_metric = st.selectbox(
        "Metric",
        ["AVG", "OBP", "SLG", "OPS", "HR", "RBI", "Hits"],
        index=3,
        key="leaderboard_metric"
    )

with leaderboard_col2:
    leaderboard_top_n = st.slider(
        "Top",
        min_value=3,
        max_value=15,
        value=5,
        step=1
    )

with leaderboard_col3:
    leaderboard_min_ab = st.slider(
        "Minimum AB",
        min_value=0,
        max_value=500,
        value=100,
        step=25
    )

batting_leaderboard = get_batting_leaderboard(
    batting,
    leaderboard_metric,
    leaderboard_top_n,
    leaderboard_min_ab
)

leaderboard_metric_columns = {
    "AVG": "Calc_AVG",
    "OBP": "Calc_OBP",
    "SLG": "Calc_SLG",
    "OPS": "Calc_OPS",
    "HR": "HR",
    "RBI": "RBI",
    "Hits": "Hits"
}

leaderboard_column = leaderboard_metric_columns[
    leaderboard_metric
]

leaderboard_display = batting_leaderboard[
    ["Player", "AB", leaderboard_column]
].copy()

leaderboard_display.insert(
    0,
    "Rank",
    range(1, len(leaderboard_display) + 1)
)

leaderboard_display = leaderboard_display.rename(
    columns={leaderboard_column: leaderboard_metric}
)

st.dataframe(
    leaderboard_display,
    use_container_width=True,
    hide_index=True
)

st.subheader("Batting Trends")

batting_trends = batting_trends.sort_values(
    "OPS_Change",
    ascending=False
)

st.dataframe(
    batting_trends,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Previous_10_OPS": st.column_config.NumberColumn(
            "Previous 10 OPS",
            format="%.3f"
        ),
        "Recent_10_OPS": st.column_config.NumberColumn(
            "Recent 10 OPS",
            format="%.3f"
        ),
        "OPS_Change": st.column_config.NumberColumn(
            "OPS Change",
            format="%+.3f"
        )
    }
)

st.subheader("Player Game Logs")

batting_logs_display = batting_games[
    [
        "Date",
        "Player",
        "Opponent",
        "Home_Away",
        "Win",
        "AB",
        "Hits",
        "Doubles",
        "Triples",
        "HR",
        "RBI",
        "Runs",
        "BB",
        "SO",
        "HBP",
        "SF"
    ]
].copy()

batting_logs_display = (
    batting_logs_display
    .sort_values("Date", ascending=False)
    .reset_index(drop=True)
)

batting_logs_display["Date"] = (
    batting_logs_display["Date"]
    .dt.strftime("%b %d, %Y")
)

batting_logs_display = batting_logs_display.rename(
    columns={
        "Home_Away": "Location"
    }
)

st.dataframe(
    batting_logs_display,
    use_container_width=True,
    hide_index=True
)