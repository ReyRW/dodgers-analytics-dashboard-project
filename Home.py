import streamlit as st


st.set_page_config(
    page_title="Dodgers Analytics Dashboard",
    page_icon="⚾",
    layout="wide"
)


st.title("Los Angeles Dodgers Analytics Dashboard")

st.write(
    "An interactive dashboard for Los Angeles Dodgers statistics, "
    "performance analysis, and machine learning predictions."
)

st.subheader("Explore the Dashboard")

st.write(
    "Use the navigation menu to explore different areas of the dashboard."
)

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        """
        ### 📅 Schedule
        View the Dodgers' 2026 schedule, including regular-season and
        postseason games.

        ### ⚾ Batting
        Explore player batting statistics, rolling performance,
        comparisons, leaderboards, and trends.
        """
    )

with col2:
    st.markdown(
        """
        ### ⚾ Pitching
        Analyze pitcher statistics, rolling performance, comparisons,
        leaderboards, and trends.

        ### 🤖 Game Prediction
        View Random Forest model's estimated win probability for
        the Dodgers' next scheduled game.
        """
    )


st.divider()

st.subheader("About This Project")

st.write(
    "This project was built to analyze Los Angeles Dodgers performance "
    "using data retrieved from the MLB Stats API and also build my first Data Science project for school. Raw player, game, and "
    "schedule data is processed in Python to create additional statistics, "
    "performance metrics, and visualizations."
)

st.write(
    "Rather than relying solely on precalculated statistics from the API, "
    "metrics used throughout the project are calculated "
    "within Python. These include batting statistics such as AVG, OBP, "
    "SLG, and OPS, as well as pitching statistics such as ERA, WHIP, K/9, "
    "BB/9, and K/BB."
)

st.write(
    "This project also analyzes rolling performance, player splits, trends, "
    "and comparisons. I used a Random Forest machine learning model to use recent "
    "team performance to estimate the Dodgers' probability of winning their "
    "next scheduled game."
)

st.caption(
    "Data is retrieved from the MLB Stats API. "
    "Game predictions are statistical estimates and do not guarantee actual outcomes."
)