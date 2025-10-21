import numpy as np
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

def multiple_with_wins():
    metrics = ["aim_rating", "spray_accuracy", "accuracy_head", "reaction_time", "preaim", "accuracy_enemy_spotted", "accuracy_head", "counter_strafing_shots_good_ratio", "hltv_rating", "kd_ratio", "hsp", "dpr", "total_kills", "leetify_rating"]

    for metric in metrics:
        query = f"""
            SELECT 
                s.{metric},
                CASE WHEN s.team = m.winner_team THEN 1 ELSE 0 END AS won
            FROM match_player_stats s
            JOIN matches m ON s.match_id = m.match_id
            WHERE s.{metric} IS NOT NULL
        """
        df = pd.read_sql_query(query, engine)
        corr = df[metric].corr(df["won"])
        print(f"{metric}: correlation = {corr:.3f}")



def stat_vs_win_logistic(stat_name):

    engine = create_engine(db_url)

    # --- Query ---
    query = f"""
        SELECT 
            s.{stat_name} AS stat_value,
            CASE WHEN s.team = m.winner_team THEN 1 ELSE 0 END AS won
        FROM match_player_stats s
        JOIN matches m ON s.match_id = m.match_id
        WHERE s.{stat_name} IS NOT NULL
    """

    df = pd.read_sql_query(query, engine)
    engine.dispose()

    print(f"Loaded {len(df)} rows for stat: {stat_name}")

    if df.empty:
        print("No data found for this stat.")
        return

    # --- Prepare data ---
    X = sm.add_constant(df["stat_value"])
    y = df["won"]

    # --- Fit logistic regression ---
    logit_model = sm.Logit(y, X)
    result = logit_model.fit()

    # --- Print summary ---
    print(result.summary())

    # --- Predictions ---
    df["predicted_win_prob"] = result.predict(X)

    # --- Plot ---
    sns.set(style="whitegrid")
    plt.figure(figsize=(8,6))
    sns.scatterplot(x="stat_value", y="won", data=df, alpha=0.3, s=15)
    sns.lineplot(x="stat_value", y="predicted_win_prob", data=df, color="red")
    plt.xlabel(stat_name.replace("_", " ").title())
    plt.ylabel("Win Probability")
    plt.title(f"Logistic Regression: {stat_name.replace('_', ' ').title()} vs Win Probability")
    plt.show()


def all_stats_multi_regressive():
    query = """
    SELECT
        s.aim_rating,
        s.spray_accuracy,
        s.accuracy_enemy_spotted,
        s.hltv_rating,
        s.reaction_time,
        s.preaim,
        s.accuracy,
        s.counter_strafing_shots_good_ratio,
        s.accuracy_head,
        s.dpr,
        s.hsp,
        s.leetify_rating,
        s.kd_ratio,
        CASE WHEN s.team = m.winner_team THEN 1 ELSE 0 END AS won
    FROM match_player_stats s
    JOIN matches m ON s.match_id = m.match_id
    WHERE s.aim_rating IS NOT NULL
    """

    df = pd.read_sql_query(query, engine)
    print(f"Loaded {len(df)} rows")

    # ✅ Ensure numeric types only
    df = df.apply(pd.to_numeric, errors="coerce")

    # ✅ Drop any rows with NaN
    df = df.dropna()
    print(df.shape)
    print(df.isna().sum())

    # ✅ Define features and target
    X = df[[
        "aim_rating", "spray_accuracy", "accuracy_enemy_spotted", "hltv_rating", "reaction_time",
        "preaim", "accuracy", "counter_strafing_shots_good_ratio", "accuracy_head", "dpr",
        "hsp", "leetify_rating", "kd_ratio"
    ]]
    y = df["won"]

    # ✅ Add constant and check types
    X = sm.add_constant(X)
    assert X.dtypes.apply(lambda t: np.issubdtype(t, np.number)).all(), "Non-numeric columns remain"

    # ✅ Fit model
    model = sm.Logit(y, X).fit()
    print(model.summary())

    # ✅ Optional: sort by impact
    print("\nTop predictors by absolute coefficient:\n")
    print(model.params.sort_values(key=abs, ascending=False))

def all_stats_regression_team():
    # --- Step 1: Query team-level averaged stats ---
    query = """
        SELECT
            m.match_id,
            s.team AS team_id,
            CASE WHEN s.team = m.winner_team THEN 1 ELSE 0 END AS won,

            AVG(s.aim_rating) AS avg_aim_rating,
            AVG(s.spray_accuracy) AS avg_spray_accuracy,
            AVG(s.accuracy_enemy_spotted) AS avg_accuracy_enemy_spotted,
            AVG(s.preaim) AS avg_preaim,
            AVG(s.accuracy_head) AS avg_accuracy_head,
            AVG(s.counter_strafing_shots_good_ratio) AS avg_counter_strafing_shots_good_ratio,
            AVG(s.hltv_rating) AS avg_hltv_rating,
            AVG(s.reaction_time) AS avg_reaction_time,
            AVG(s.accuracy) AS avg_accuracy,
            AVG(s.flashbang_hit_foe) AS avg_flashbang_hit_foe,
            AVG(s.flashbang_thrown) AS avg_flashbang_thrown,
            AVG(s.flash_assist) AS avg_flash_assist,
            AVG(s.trade_kill_opportunities_per_round) AS avg_trade_kill_opportunities_per_round,
            AVG(s.trade_kills_success_percentage) AS avg_trade_kills_success_percentage,
            AVG(s.dpr) AS avg_dpr,
            AVG(s.hsp) AS avg_hsp,
            AVG(s.leetify_rating) AS avg_leetify_rating,
            AVG(s.kd_ratio) AS avg_kd_ratio

        FROM match_player_stats s
        JOIN matches m ON s.match_id = m.match_id
        WHERE s.aim_rating IS NOT NULL
        GROUP BY m.match_id, s.team, m.winner_team;"""

    df = pd.read_sql_query(query, engine)
    print(f"Loaded {len(df)} team-level rows")

    # --- Step 2: Clean data ---
    numeric_cols = df.select_dtypes(include=["number"]).columns
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")

    # Drop rows with NaNs in the numeric columns only
    df = df.dropna(subset=numeric_cols)
    print("After cleaning:", df.shape)

    # --- Step 3: Correlation (which stats correlate with winning) ---
    corr = df.corr(numeric_only=True)['won'].sort_values(ascending=False)
    print("\n📊 Pearson Correlation with Winning:\n")
    print(corr)

    # --- Step 4: Logistic Regression (which stats *predict* winning) ---
    X = df.drop(columns=["won", "match_id", "team_id"], errors="ignore")
    y = df["won"]

    X = sm.add_constant(X)
    model = sm.Logit(y, X).fit(disp=False)

    print("\n📈 Logistic Regression Summary:\n")
    print(model.summary())

    print("\nTop predictors by absolute coefficient:\n")
    print(model.params.sort_values(key=abs, ascending=False))

if __name__ == "__main__":
    # hltv_and_aim_rating()
    # team_aim_winrate()
    # aim_rating_vs_win_rate()
    # aim_rating_vs_win()
    # aim_rating_per_point_corr()
    # multiple_with_wins()
    # stat_vs_win_logistic("preaim")
    # stat_vs_win_logistic("spray_accuracy")
    # stat_vs_win_logistic("accuracy_enemy_spotted")
    # stat_vs_win_logistic("accuracy_head")
    # all_stats_multi_regressive()
    all_stats_regression_team()