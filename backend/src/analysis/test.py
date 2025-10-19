from src.database.db import get_connection
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import statsmodels.api as sm


load_dotenv()

db_user = os.getenv("DB_USER")
db_pass = os.getenv("DB_PASS")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

db_url = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
engine = create_engine(db_url)


def hltv_and_aim_rating_winning_team():
    conn = get_connection()
    hltv_aim_query = """
        SELECT 
            stats.hltv_rating,
            stats.aim_rating
        FROM
            match_player_stats AS stats
        JOIN 
            matches as m
            ON stats.match_id = m.match_id
        WHERE stats.team  = m.winner_team
        AND stats.hltv_rating is NOT NULL
        AND stats.aim_rating is NOT NULL
    """
    df = pd.read_sql_query(hltv_aim_query, conn)
    conn.close()


    sns.set(style="whitegrid")
    plt.figure(figsize=(8,6))
    sns.regplot(x="hltv_rating", y="aim_rating", data=df, scatter_kws={"alpha": 0.5})
    plt.title("HLTV Rating vs Aim Rating (Winning Teams)")
    plt.xlabel("HLTV Rating")
    plt.ylabel("Aim Rating")
    plt.show()


def hltv_and_aim_rating():
    conn = get_connection()
    hltv_aim_query = """
        SELECT 
            hltv_rating,
            aim_rating
        FROM
            match_player_stats
    """
    df = pd.read_sql_query(hltv_aim_query, conn)
    conn.close()

    correlation = df["hltv_rating"].corr(df["aim_rating"])
    print(f"Correlation between HLTV Rating and Aim Rating: {correlation:.3f}")
    sns.set(style="whitegrid")
    plt.figure(figsize=(8,6))
    sns.regplot(x="hltv_rating", y="aim_rating", data=df, scatter_kws={"alpha": 0.5})
    plt.title("HLTV Rating vs Aim Rating (Winning Teams)")
    plt.xlabel("HLTV Rating")
    plt.ylabel("Aim Rating")
    plt.show()


def team_aim_winrate():
    conn = get_connection()
    
    query = """
        SELECT 
            m.match_id,
            s.team,
            CASE WHEN s.team = m.winner_team THEN 1 ELSE 0 END AS is_winner,
            s.aim_rating
        FROM match_player_stats s
        JOIN matches m ON s.match_id = m.match_id
        WHERE s.aim_rating IS NOT NULL
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()


    team_avg = (
        df.groupby(["match_id", "team", "is_winner"])["aim_rating"]
        .mean()
        .reset_index()
        .rename(columns={"aim_rating": "avg_aim_rating"})
    )

    merged = team_avg.merge(
        team_avg,
        on="match_id",
        suffixes=("_team1", "_team2")
    )

    merged = merged[merged["team_team1"] != merged["team_team2"]]

    merged["team1_had_higher_aim"] = merged["avg_aim_rating_team1"] > merged["avg_aim_rating_team2"]
    merged["team1_won"] = merged["is_winner_team1"] == 1

    total_matches = len(merged["match_id"].unique())
    higher_aim_wins = merged[(merged["team1_had_higher_aim"]) & (merged["team1_won"])]

    win_rate = len(higher_aim_wins["match_id"].unique()) / total_matches * 100

    print(f"Teams with higher average aim rating won {win_rate:.2f}% of matches.")


def aim_rating_vs_win():

    engine = create_engine(db_url)

    query = """
        SELECT 
            s.aim_rating,
            CASE WHEN s.team = m.winner_team THEN 1 ELSE 0 END AS won
        FROM match_player_stats s
        JOIN matches m ON s.match_id = m.match_id
        WHERE s.aim_rating IS NOT NULL
    """

    df = pd.read_sql_query(query, engine)

    print(f"Loaded {len(df)} player-match rows")

    sns.set(style="whitegrid")
    plt.figure(figsize=(8,6))
    sns.regplot(
        x="aim_rating",
        y="won",
        data=df,
        logistic=True,
        scatter_kws={"alpha": 0.4, "s": 15},
        line_kws={"color": "red"}
    )
    plt.title("Player Aim Rating vs Win Probability")
    plt.xlabel("Aim Rating")
    plt.ylabel("Win Probability")
    plt.show()

    corr = df["aim_rating"].corr(df["won"])
    print(f"Correlation between aim rating and winning: {corr:.3f}")

def aim_rating_per_point_corr():
        # Query data
    query = """
        SELECT 
            s.aim_rating,
            CASE WHEN s.team = m.winner_team THEN 1 ELSE 0 END AS won
        FROM match_player_stats s
        JOIN matches m ON s.match_id = m.match_id
        WHERE s.aim_rating IS NOT NULL
    """
    df = pd.read_sql_query(query, engine)
    print(f"Loaded {len(df)} rows")

    # Prepare data for logistic regression
    X = df["aim_rating"]
    y = df["won"]

    # Add constant term for intercept
    X = sm.add_constant(X)

    # Fit logistic regression model
    logit_model = sm.Logit(y, X)
    result = logit_model.fit()

    # Print summary
    print(result.summary())

    # Optional: calculate predicted probabilities
    df["predicted_win_prob"] = result.predict(X)

    # Plot
    import matplotlib.pyplot as plt
    import seaborn as sns

    sns.set(style="whitegrid")
    plt.figure(figsize=(8,6))
    sns.scatterplot(x="aim_rating", y="won", data=df, alpha=0.3, s=15)
    sns.lineplot(x="aim_rating", y="predicted_win_prob", data=df, color="red")
    plt.xlabel("Aim Rating")
    plt.ylabel("Win Probability")
    plt.title("Logistic Regression: Aim Rating vs Win Probability")
    plt.show()


if __name__ == "__main__":
    # hltv_and_aim_rating()
    # team_aim_winrate()
    # aim_rating_vs_win_rate()
    # aim_rating_vs_win()
    aim_rating_per_point_corr()