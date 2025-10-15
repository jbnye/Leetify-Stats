import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import time
import requests
from playwright.sync_api import sync_playwright
from scrape.table_scraper import parse_table
from scrape.leetify_match_data_parser import leetify_match_data_parser
from scrape.merge_table_and_api_data import merge_table_and_api_data
from database.db import get_connection
from database.leetify_db_uploader import insert_match_and_players

URL = "https://leetify.com/app/match-details/7168d44e-ed88-45ad-9403-28187440b98e/overview"
requestURL = "https://api.cs-prod.leetify.com/api/games/7168d44e-ed88-45ad-9403-28187440b98e"

def main(headless=True):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        page.goto(URL, timeout=20000)
        page.wait_for_load_state("networkidle")

        title = page.title()
        print("Page Title:", title)

        table = page.locator("table.--use-min-width")
        table.wait_for(state="visible", timeout=15000)

        rows = table.locator("tbody tr")
        raw_table = []
        for i in range(rows.count()):
            row = rows.nth(i)
            cells = row.locator("td")
            row_data = [cells.nth(j).inner_text() for j in range(cells.count())]
            raw_table.append(row_data)

        teams, players = parse_table(raw_table)
        table_data = {"teams": teams, "players": players}
        print("Teams:", teams)
        print("Players:", players)

        page.screenshot(path="leetify_overview.png", full_page=True)
        browser.close()


    headers = {"Accept": "application/json"}
    response = requests.get(requestURL, headers=headers)

    if response.status_code == 200:
        data = response.json()
        api_parsed_data = leetify_match_data_parser(data)
    else:
        print("Failed to fetch API:", response.status_code, response.text)
        return


    merged_data = merge_table_and_api_data(api_parsed_data, table_data)

    print("\nMerged Player Stats:")
    for p in merged_data["player_stats"]:
        name = p.get("name") or "Unknown"
        team = p.get("team")
        won = p.get("won")
        aim_rating = p.get("aim_rating")
        print(f"{name:20} | Team: {team} | Won: {won} | Aim Rating: {aim_rating}")

    #db upload
    conn = get_connection()
    insert_match_and_players(conn, 
        match_data={
            "match_id": merged_data["match_id"],
            "data_source": merged_data.get("dataSource"),
            "hltv_match_id": merged_data.get("hltvMatchId"),
            "team_scores": merged_data.get("team_scores"),
            "winner_team": 0 if merged_data.get("team_scores", [0,0])[0] > merged_data.get("team_scores", [0,0])[1] else 1,
            "date": merged_data.get("date_finished_at")
        },
        player_data=merged_data["player_stats"]
    )
    conn.close()




if __name__ == "__main__":
    headless_flag = True
    if len(sys.argv) > 1 and sys.argv[1] == "show":
        headless_flag = False
    main(headless=headless_flag)