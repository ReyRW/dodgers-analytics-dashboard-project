import streamlit as st
import requests

from data import get_dodgers_schedule


st.title("Dodgers Schedule")

try:
    schedule = get_dodgers_schedule()

except requests.exceptions.RequestException:
    st.error(
        "Unable to retrieve MLB schedule data right now. "
        "Please try again shortly."
    )
    st.stop()

if schedule.empty:
    st.warning(
        "No Dodgers schedule data is currently available."
    )
    st.stop()

st.subheader("Upcoming Game")

upcoming_games = schedule[
    (schedule["Status"] == "Preview")
    & (schedule["Detailed_Status"] == "Scheduled")
].copy()

upcoming_games = upcoming_games.sort_values("Date")

if not upcoming_games.empty:

    next_game = upcoming_games.iloc[0]

    next_opponent = next_game["Opponent"]
    next_location = next_game["Home_Away"]
    next_date = next_game["Date"]

    if next_location == "Home":
        matchup = f"Dodgers vs. {next_opponent}"
        location_text = "at home"
    else:
        matchup = f"Dodgers at {next_opponent}"
        location_text = "on the road"

    st.markdown(f"### {matchup}")

    st.write(
        f"The Dodgers' next scheduled game is "
        f"**{next_date.strftime('%A, %B %d, %Y')}**, "
        f"{location_text}."
    )

else:
    st.info("There are currently no upcoming scheduled games.")

schedule_display = schedule[
    [
        "Date",
        "Game_Type",
        "Opponent",
        "Home_Away"
    ]
].copy()

schedule_display = (
    schedule_display
    .sort_values("Date", ascending=False)
    .reset_index(drop=True)
)

game_type_labels = {
    "R": "Regular Season",
    "F": "Wild Card",
    "D": "Division Series",
    "L": "League Championship Series",
    "W": "World Series"
}

schedule_display["Game_Type"] = (
    schedule_display["Game_Type"]
    .map(game_type_labels)
    .fillna(schedule_display["Game_Type"])
)


schedule_display["Date"] = (
    schedule_display["Date"]
    .dt.strftime("%b %d, %Y")
)


schedule_display = schedule_display.rename(
    columns={
        "Game_Type": "Game Type",
        "Home_Away": "Location"
    }
)

st.dataframe(
    schedule_display,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Date": st.column_config.TextColumn(
            "Date",
            width="medium"
        ),
        "Game Type": st.column_config.TextColumn(
            "Game Type",
            width="medium"
        ),
        "Opponent": st.column_config.TextColumn(
            "Opponent",
            width="large"
        ),
        "Location": st.column_config.TextColumn(
            "Location",
            width="small"
        )
    }
)