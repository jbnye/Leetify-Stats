def leetify_match_data_parser(data):
    match_id = data.get("id")
    dataSource = data.get("dataSource")
    hltvMatchId = data.get("hltvMatchId")
    team_scores = data.get("teamScores", [])
    date_finished_at = data.get("finishedAt")
    player_stats = []
    for player in data.get("playerStats", []):
        player_stats.append({
            "name": player.get("name"),
            "steam64_id": player.get("steam64Id"),
            "preaim": player.get("preaim"),
            "reactionTime": player.get("reactionTime"),
            "accuracy": player.get("accuracy"),
            "accuracyEnemySpotted": player.get("accuracyEnemySpotted"),
            "accuracyHead": player.get("accuracyHead"),
            "counterStrafingShtsGoodRatio": player.get("counterStrafingShtsGoodRatio"),
            "flashbangHitFoe": player.get("flashbangHitFoe"),
            "flashbangLeadingToKill": player.get("flashbangLeadingToKill"),
            "flashbangThrown": player.get("flashbangThrown"),
            "flashAssist": player.get("flashAssist"),
            "sprayAccuracy": player.get("sprayAccuracy"),
            "kdRatio": player.get("kdRatio"),
            "hltvRating": player.get("hltvRating"),
            "hsp": player.get("hsp"),
            "dpr": player.get("dpr"),
            "totalKills": player.get("totalKills"),
            "totalDeaths": player.get("totalDeaths"),
            "leetifyRating": player.get("leetifyRating"),
            "tradeKillOpportunitiesPerRound": player.get("tradeKillOpportunitiesPerRound"),
            "tradeKillsSuccessPercentage": player.get("tradeKillsSuccessPercentage"),
            "tradedDeathsSuccessPercentage": player.get("tradedDeathsSuccessPercentage"),
            "tradedDeathsOpportunitiesPerRound": player.get("tradedDeathsOpportunitiesPerRound"),
            "leetifyUserId": player.get("leetifyUserId"),
        })

    return {
        "match_id": match_id,
        "dataSource": dataSource,
        "hltvMatchId": hltvMatchId,
        "team_scores": team_scores,
        "date_finished_at": date_finished_at,
        "player_stats": player_stats,
    }




