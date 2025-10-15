import psycopg2
from psycopg2.extras import execute_values
from database.db import get_connection

def insert_match_and_players(conn, match_data):
    """
    Inserts a match and all player stats into the database.
    match_data: result from merge_table_and_api_data()
    """

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO matches (match_id, data_source, hltv_match_id, team_scores, winner_team, date)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (match_id) DO NOTHING
        """, (
            match_data["match_id"],
            match_data.get("dataSource"),
            match_data.get("hltvMatchId"),
            match_data.get("team_scores"),
            max(range(len(match_data.get("team_scores", []))), key=lambda i: match_data["team_scores"][i]) if match_data.get("team_scores") else None,
            match_data.get("date_finished_at")
        ))

        for p in match_data["player_stats"]:
            cur.execute("""
                INSERT INTO players (steam64_id, name, leetify_user_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (steam64_id) DO NOTHING
            """, (
                p.get("steam64Id"),
                p.get("name"),
                p.get("leetifyUserId")
            ))

        values = []
        for p in match_data["player_stats"]:
            values.append((
                match_data["match_id"],
                p.get("steam64Id"),
                p.get("team"),
                p.get("won"),
                p.get("preaim"),
                p.get("reactionTime"),
                p.get("accuracy"),
                p.get("accuracyEnemySpotted"),
                p.get("accuracyHead"),
                p.get("counterStrafingShtsGoodRatio"),
                p.get("flashbangHitFoe"),
                p.get("flashbangLeadingToKill"),
                p.get("flashbangThrown"),
                p.get("flashAssist"),
                p.get("sprayAccuracy"),
                p.get("kdRatio"),
                p.get("hltvRating"),
                p.get("hsp"),
                p.get("dpr"),
                p.get("totalKills"),
                p.get("totalDeaths"),
                p.get("leetifyRating"),
                p.get("tradeKillOpportunitiesPerRound"),
                p.get("tradeKillsSuccessPercentage"),
                p.get("tradedDeathsSuccessPercentage"),
                p.get("tradedDeathsOpportunitiesPerRound"),
                p.get("aim_rating")
            ))

        execute_values(cur, """
            INSERT INTO match_player_stats (
                match_id, steam64_id, team, won, preaim, reaction_time, accuracy,
                accuracy_enemy_spotted, accuracy_head, counter_strafing_shots_good_ratio,
                flashbang_hit_foe, flashbang_leading_to_kill, flashbang_thrown, flash_assist,
                spray_accuracy, kd_ratio, hltv_rating, hsp, dpr, total_kills, total_deaths,
                leetify_rating, trade_kill_opportunities_per_round, trade_kills_success_percentage,
                traded_deaths_success_percentage, traded_deaths_opportunities_per_round, aim_rating
            ) VALUES %s
            ON CONFLICT (match_id, steam64_id) DO NOTHING
        """, values)

        conn.commit()