from src.database.db import get_connection

def get_steam_ids():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT steam64_id FROM faceit_steam_ids")
    rows = cursor.fetchall()
    conn.close()
    return {row[0] for row in rows}


