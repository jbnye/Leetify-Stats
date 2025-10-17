from src.database.db import get_connection
def get_all_matches_ids():
    conn = get_connection()
    cursor = conn.cursor()
    get_matches_query = """
        SELECT match_id FROM matches
    """
    cursor.execute(get_matches_query, )
    rows = cursor.fetchall()
    conn.close()
    return {row[0] for row in rows}
