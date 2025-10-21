import requests
from psycopg2.extras import execute_values
from src.database.db import get_connection

BASE_URL = "https://api.cs-prod.leetify.com/api/games/"

def main():
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT match_id FROM matches")
        match_ids = [r[0] for r in cur.fetchall()]
        print(f"Found {len(match_ids)} matches")

        for i, match_id in enumerate(match_ids, start=1):
            url = f"{BASE_URL}{match_id}"
            try:
                resp = requests.get(url, timeout=10)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"[{i}/{len(match_ids)}] Error fetching {match_id}: {e}")
                continue

            values = []
            for player in data.get("playerStats", []):
                ratio = player.get("counterStrafingShotsGoodRatio")
                steam64_id = player.get("steam64Id")
                if ratio is not None and steam64_id:
                    values.append((ratio, match_id, steam64_id))

            if values:
                execute_values(cur, """
                    UPDATE match_player_stats AS m
                    SET counter_strafing_shots_good_ratio = v.ratio
                    FROM (VALUES %s) AS v(ratio, match_id, steam64_id)
                    WHERE m.match_id = v.match_id AND m.steam64_id = v.steam64_id
                """, values)
                conn.commit()

            print(f"[{i}/{len(match_ids)}] Updated {len(values)} players in match {match_id}")

if __name__ == "__main__":
    main()