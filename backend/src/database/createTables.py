from src.database.db import get_connection

schema_sql = """
CREATE TABLE IF NOT EXISTS matches (
    match_id VARCHAR(64) PRIMARY KEY,
    data_source VARCHAR(64),
    hltv_match_id VARCHAR(64),
    team_scores INTEGER[],
    winner_team INTEGER,
    date_finished_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS players (
    steam64_id VARCHAR(32) PRIMARY KEY,
    name TEXT,
    leetify_user_id VARCHAR(64)
);

CREATE TABLE IF NOT EXISTS faceit_steam_ids (
    steam64_id VARCHAR(32) PRIMARY KEY,
    region VARCHAR(10)
);

CREATE TABLE IF NOT EXISTS match_player_stats (
    match_id VARCHAR(64) REFERENCES matches(match_id) ON DELETE CASCADE,
    steam64_id VARCHAR(32) REFERENCES players(steam64_id) ON DELETE CASCADE,
    team INTEGER,
    won BOOLEAN,
    preaim FLOAT,
    reaction_time FLOAT,
    accuracy FLOAT,
    accuracy_enemy_spotted FLOAT,
    accuracy_head FLOAT,
    counter_strafing_shots_good_ratio FLOAT,
    flashbang_hit_foe INTEGER,
    flashbang_leading_to_kill INTEGER,
    flashbang_thrown INTEGER,
    flash_assist INTEGER,
    spray_accuracy FLOAT,
    kd_ratio FLOAT,
    hltv_rating FLOAT,
    hsp FLOAT,
    dpr FLOAT,
    total_kills INTEGER,
    total_deaths INTEGER,
    leetify_rating FLOAT,
    trade_kill_opportunities_per_round FLOAT,
    trade_kills_success_percentage FLOAT,
    traded_deaths_success_percentage FLOAT,
    traded_deaths_opportunities_per_round FLOAT,
    aim_rating FLOAT,
    PRIMARY KEY (match_id, steam64_id)
);
"""

if __name__ == "__main__":
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(schema_sql)
    conn.commit()
    cursor.close()
    conn.close()
    print("Tables created successfully.")