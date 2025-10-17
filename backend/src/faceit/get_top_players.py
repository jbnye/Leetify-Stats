import requests
import os
from dotenv import load_dotenv
from src.database.db import get_connection

load_dotenv()
API_KEY = os.getenv("FACEIT_API_KEY")


headers = {
    "Authorization": f"Bearer {API_KEY}"
}

regions = {
    "EU": 700,
    "NA": 300
}

for region, total_players in regions.items():
    fetched = 0
    conn = get_connection()
    cursor = conn.cursor()

    while fetched < total_players:
        limit = min(100, total_players - fetched)
        params = {"limit": limit, "offset": fetched}

        top_players_response = requests.get(
            f"https://open.faceit.com/data/v4/rankings/games/cs2/regions/{region}",
            headers=headers,
            params=params
        )

        if top_players_response.status_code != 200:
            print(f"Failed response: {top_players_response.status_code}, stopping region {region}")
            break

        top_players_data = top_players_response.json()

        for index, player in enumerate(top_players_data.get("items", [])):
            player_response = requests.get(f"https://open.faceit.com/data/v4/players/{player['player_id']}", headers=headers)
            player_data = player_response.json()

            steam_id = player_data.get("steam_id_64")
            region_id = player_data.get("games", {}).get("cs2", {}).get("region")
            game_player_id = player_data.get("games", {}).get("cs2", {}).get("game_player_id")

            if steam_id:
                cursor.execute(
                    "INSERT INTO faceit_steam_ids (steam64_id, region) VALUES (%s, %s) ON CONFLICT (steam64_id) DO NOTHING",
                    (steam_id, region_id)
                )
                print(f"UPLOADED PLAYER #{fetched + index} {steam_id}, {region_id}")
            elif game_player_id:
                cursor.execute(
                    "INSERT INTO faceit_steam_ids (steam64_id, region) VALUES (%s, %s) ON CONFLICT (steam64_id) DO NOTHING",
                    (game_player_id, region_id)
                )
                print(f"UPLOADED PLAYER #{fetched + index} {game_player_id}, {region_id}")
            else:
                print(f"NO STEAMID for PLAYER #{fetched + index}: {player_data.get('nickname')}")

        conn.commit()
        fetched += limit  

    conn.close()
    print(f"Finished uploading {region} players.\n")