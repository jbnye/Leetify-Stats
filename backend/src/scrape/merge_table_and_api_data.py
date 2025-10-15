def merge_table_and_api_data(api_parsed, table_data):
    players_with_aim = table_data["players"]
    teams = table_data["teams"]

    team_scores = api_parsed.get("team_scores", [0, 0])
    winning_team = 0 if team_scores[0] > team_scores[1] else 1


    aim_lookup = {}
    for p in players_with_aim:
        name_lower = p["name"].lower()
        aim_lookup[name_lower] = {
            "aim_rating": p["aim_rating"],
            "team": p["team"]
        }

    merged_players = []
    for player in api_parsed["player_stats"]:
        name = player.get("name")
        key = name.lower() if isinstance(name, str) else None
        aim_data = aim_lookup.get(key)
        if aim_data:
            player["aim_rating"] = aim_data["aim_rating"]
            player["team"] = aim_data["team"]
            player["won"] = (aim_data["team"] == winning_team)
        else:
            player["aim_rating"] = None
            player["team"] = None
            player["won"] = None

        merged_players.append(player)

    api_parsed["player_stats"] = merged_players
    return api_parsed