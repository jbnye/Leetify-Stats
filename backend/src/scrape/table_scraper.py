def parse_table(raw_table):
    team_counter = 0
    teams =[[],[]]
    players = []

    for row in raw_table:
        if not row:
            team_counter += 1
            continue
        if team_counter > 1:
            break
        
        player_name = row[0]
        aim_rating = float(row[6])
        teams[team_counter].append(player_name)
        players.append({
            "name": player_name,
            "aim_rating": aim_rating,
            "team": team_counter
        })

    return teams, players