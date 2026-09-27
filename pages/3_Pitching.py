import streamlit as st
import requests

from data import (
    get_dodgers_pitching,
    get_dodgers_pitching_games
)

from analytics import (
    add_pitching_stats,
    add_pitching_rolling_stats,
    get_pitching_leaderboard,
    calculate_pitching_trends,
    get_pitching_home_away_splits
)

st.title("Dodgers Pitching Analytics")

st.subheader("Dodgers Pitching")

try:
    pitching = get_dodgers_pitching()
    pitching_games = get_dodgers_pitching_games(pitching)

except requests.exceptions.RequestException:
    st.error(
        "Unable to retrieve Dodgers pitching data right now. "
        "Please try again later."
    )
    st.stop()

if pitching.empty:
    st.warning(
        "No Dodgers pitching data is currently available."
    )
    st.stop()

if pitching_games.empty:
    st.warning(
        "No Dodgers pitching game logs are currently available."
    )
    st.stop()

pitching = add_pitching_stats(pitching)

pitching_display = pitching[
    [
        "Player",
        "Position",
        "Games",
        "GS",
        "IP",
        "Wins",
        "Losses",
        "Hits",
        "Runs",
        "ER",
        "HR",
        "BB",
        "SO",
        "Saves",
        "Calc_ERA",
        "Calc_WHIP",
        "Calc_K9",
        "Calc_BB9",
        "Calc_KBB"
    ]
].copy()


pitching_display = pitching_display.rename(
    columns={
        "Calc_ERA": "ERA",
        "Calc_WHIP": "WHIP",
        "Calc_K9": "K/9",
        "Calc_BB9": "BB/9",
        "Calc_KBB": "K/BB"
    }
)


st.dataframe(
    pitching_display,
    use_container_width=True,
    hide_index=True,
    column_config={
        "ERA": st.column_config.NumberColumn(
            "ERA",
            format="%.2f"
        ),
        "WHIP": st.column_config.NumberColumn(
            "WHIP",
            format="%.2f"
        ),
        "K/9": st.column_config.NumberColumn(
            "K/9",
            format="%.2f"
        ),
        "BB/9": st.column_config.NumberColumn(
            "BB/9",
            format="%.2f"
        ),
        "K/BB": st.column_config.NumberColumn(
            "K/BB",
            format="%.2f"
        )
    }
)

pitching_games = add_pitching_rolling_stats(
    pitching_games
)

st.subheader("Pitcher Analysis")

pitcher_names = sorted(
    pitching["Player"].unique()
)

selected_pitcher = st.selectbox(
    "Select a pitcher",
    pitcher_names,
    key="selected_pitcher"
)

pitcher = pitching[
    pitching["Player"] == selected_pitcher
].iloc[0]

st.markdown(f"### {selected_pitcher}")

pitch_col1, pitch_col2, pitch_col3, pitch_col4 = st.columns(4)

with pitch_col1:
    st.metric(
        "ERA",
        f"{pitcher['Calc_ERA']:.2f}"
    )

with pitch_col2:
    st.metric(
        "WHIP",
        f"{pitcher['Calc_WHIP']:.2f}"
    )

with pitch_col3:
    st.metric(
        "K/9",
        f"{pitcher['Calc_K9']:.2f}"
    )

with pitch_col4:
    st.metric(
        "BB/9",
        f"{pitcher['Calc_BB9']:.2f}"
    )

pitch_col5, pitch_col6, pitch_col7, pitch_col8 = st.columns(4)

with pitch_col5:
    st.metric(
        "K/BB",
        f"{pitcher['Calc_KBB']:.2f}"
    )

with pitch_col6:
    st.metric(
        "IP",
        f"{pitcher['IP']}"
    )

with pitch_col7:
    st.metric(
        "SO",
        int(pitcher["SO"])
    )

with pitch_col8:
    st.metric(
        "Saves",
        int(pitcher["Saves"])
    )

st.markdown("### 5-Appearance Rolling Performance")

pitching_metric_columns = {
    "ERA": "Rolling_5_ERA",
    "WHIP": "Rolling_5_WHIP",
    "K/9": "Rolling_5_K9",
    "BB/9": "Rolling_5_BB9",
    "K/BB": "Rolling_5_KBB"
}

selected_pitching_metric = st.selectbox(
    "Select a pitching metric",
    list(pitching_metric_columns.keys()),
    key="pitching_metric"
)

selected_pitching_column = pitching_metric_columns[
    selected_pitching_metric
]

pitcher_games = pitching_games[
    pitching_games["Player"] == selected_pitcher
].copy()

pitcher_games = pitcher_games[
    pitcher_games[selected_pitching_column].notna()
]

pitching_chart_data = (
    pitcher_games[
        ["Date", selected_pitching_column]
    ]
    .set_index("Date")
)

pitching_chart_data = pitching_chart_data.rename(
    columns={
        selected_pitching_column: selected_pitching_metric
    }
)

st.line_chart(
    pitching_chart_data,
    y=selected_pitching_metric
)

st.markdown("### Home vs Away")

pitching_splits = get_pitching_home_away_splits(
    pitching_games,
    selected_pitcher
)

pitching_splits_display = pitching_splits.copy()

for column in [
    "ERA",
    "WHIP",
    "K/9",
    "BB/9",
    "K/BB"
]:
    pitching_splits_display[column] = (
        pitching_splits_display[column].round(2)
    )

st.dataframe(
    pitching_splits_display,
    use_container_width=True,
    hide_index=True
)

st.markdown("### Pitcher Comparison")

pitcher_comparison_col1, pitcher_comparison_col2 = st.columns(2)

with pitcher_comparison_col1:
    pitcher_1 = st.selectbox(
        "Pitcher 1",
        pitcher_names,
        key="pitcher_1"
    )

with pitcher_comparison_col2:
    pitcher_2 = st.selectbox(
        "Pitcher 2",
        pitcher_names,
        index=1 if len(pitcher_names) > 1 else 0,
        key="pitcher_2"
    )

pitcher_comparison_metric = st.selectbox(
    "Pitcher Comparison Metric",
    [
        "ERA",
        "WHIP",
        "K/9",
        "BB/9",
        "K/BB"
    ],
    key="pitcher_comparison_metric"
)

pitcher_comparison_columns = {
    "ERA": "Rolling_5_ERA",
    "WHIP": "Rolling_5_WHIP",
    "K/9": "Rolling_5_K9",
    "BB/9": "Rolling_5_BB9",
    "K/BB": "Rolling_5_KBB"
}

pitcher_comparison_column = pitcher_comparison_columns[
    pitcher_comparison_metric
]

pitcher_1_data = pitching_games[
    pitching_games["Player"] == pitcher_1
][["Date", pitcher_comparison_column]].copy()

pitcher_2_data = pitching_games[
    pitching_games["Player"] == pitcher_2
][["Date", pitcher_comparison_column]].copy()

pitcher_1_data = pitcher_1_data.rename(
    columns={
        pitcher_comparison_column: pitcher_1
    }
)

pitcher_2_data = pitcher_2_data.rename(
    columns={
        pitcher_comparison_column: pitcher_2
    }
)

pitcher_comparison_data = pitcher_1_data.merge(
    pitcher_2_data,
    on="Date",
    how="outer"
)

pitcher_comparison_data = (
    pitcher_comparison_data
    .sort_values("Date")
    .set_index("Date")
)

pitcher_comparison_data = (
    pitcher_comparison_data.interpolate(
        method="time",
        limit_area="inside"
    )
)

st.line_chart(
    pitcher_comparison_data
)

st.subheader("Pitching Leaderboard")

pitch_leader_col1, pitch_leader_col2, pitch_leader_col3 = st.columns(3)

with pitch_leader_col1:
    pitching_leaderboard_metric = st.selectbox(
        "Pitching Metric",
        [
            "ERA",
            "WHIP",
            "K/9",
            "BB/9",
            "K/BB",
            "SO",
            "Saves"
        ],
        key="pitching_leaderboard_metric"
    )

with pitch_leader_col2:
    pitching_leaderboard_top_n = st.slider(
        "Top Pitchers",
        min_value=3,
        max_value=15,
        value=5,
        step=1
    )

with pitch_leader_col3:
    pitching_leaderboard_min_ip = st.slider(
        "Minimum IP",
        min_value=0,
        max_value=200,
        value=20,
        step=10
    )

pitching_leaderboard = get_pitching_leaderboard(
    pitching,
    pitching_leaderboard_metric,
    pitching_leaderboard_top_n,
    pitching_leaderboard_min_ip
)

pitching_leaderboard_columns = {
    "ERA": "Calc_ERA",
    "WHIP": "Calc_WHIP",
    "K/9": "Calc_K9",
    "BB/9": "Calc_BB9",
    "K/BB": "Calc_KBB",
    "SO": "SO",
    "Saves": "Saves"
}

pitching_leaderboard_column = pitching_leaderboard_columns[
    pitching_leaderboard_metric
]

pitching_leaderboard_display = pitching_leaderboard[
    [
        "Player",
        "Calc_IP",
        pitching_leaderboard_column
    ]
].copy()

pitching_leaderboard_display.insert(
    0,
    "Rank",
    range(
        1,
        len(pitching_leaderboard_display) + 1
    )
)

pitching_leaderboard_display = (
    pitching_leaderboard_display.rename(
        columns={
            "Calc_IP": "IP",
            pitching_leaderboard_column:
                pitching_leaderboard_metric
        }
    )
)

st.dataframe(
    pitching_leaderboard_display,
    use_container_width=True,
    hide_index=True
)

st.subheader("Pitching Trends")

pitching_trends = calculate_pitching_trends(
    pitching_games
)

pitching_trends_display = pitching_trends.copy()

pitching_trends_display["Previous_5_ERA"] = (
    pitching_trends_display["Previous_5_ERA"].round(2)
)

pitching_trends_display["Recent_5_ERA"] = (
    pitching_trends_display["Recent_5_ERA"].round(2)
)

pitching_trends_display["ERA_Change"] = (
    pitching_trends_display["ERA_Change"].round(2)
)

pitching_trends_display = (
    pitching_trends_display
    .sort_values("ERA_Change")
    .reset_index(drop=True)
)

pitching_trends_display = pitching_trends_display.rename(
    columns={
        "Previous_5_ERA": "Previous 5 ERA",
        "Recent_5_ERA": "Recent 5 ERA",
        "ERA_Change": "ERA Change"
    }
)

st.dataframe(
    pitching_trends_display,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Previous 5 ERA": st.column_config.NumberColumn(
            "Previous 5 ERA",
            format="%.2f"
        ),
        "Recent 5 ERA": st.column_config.NumberColumn(
            "Recent 5 ERA",
            format="%.2f"
        ),
        "ERA Change": st.column_config.NumberColumn(
            "ERA Change",
            format="%+.2f"
        )
    }
)

st.subheader("Pitching Game Logs")

pitching_logs_display = pitching_games[
    [
        "Date",
        "Player",
        "Opponent",
        "Home_Away",
        "Win",
        "IP",
        "Hits",
        "Runs",
        "ER",
        "HR",
        "BB",
        "SO"
    ]
].copy()

pitching_logs_display = (
    pitching_logs_display
    .sort_values("Date", ascending=False)
    .reset_index(drop=True)
)

pitching_logs_display["Date"] = (
    pitching_logs_display["Date"]
    .dt.strftime("%b %d, %Y")
)

pitching_logs_display = pitching_logs_display.rename(
    columns={
        "Home_Away": "Location"
    }
)

st.dataframe(
    pitching_logs_display,
    use_container_width=True,
    hide_index=True
)