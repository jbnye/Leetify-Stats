import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import time
import requests
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from scrape.table_scraper import parse_table
from scrape.leetify_match_data_parser import leetify_match_data_parser
from scrape.merge_table_and_api_data import merge_table_and_api_data
from database.db import get_connection
from database.leetify_db_uploader import insert_match_and_players

# URL = "https://leetify.com/app/match-details/7168d44e-ed88-45ad-9403-28187440b98e/overview"
# requestURL = "https://api.cs-prod.leetify.com/api/games/7168d44e-ed88-45ad-9403-28187440b98e"
profileURL = "https://api.cs-prod.leetify.com/api/profile/id/76561198089612542"
URL = "https://leetify.com/app/match-details/ed7d411b-876d-4481-b45d-a44f826426e5/overview"
requestURL = "https://api.cs-prod.leetify.com/api/games/ed7d411b-876d-4481-b45d-a44f826426e5"


def scrape_match_with_retry(page, match_id, headers, retries=3, delay=5):
    """Scrape a single match with up to `retries` attempts."""
    URL = f"https://leetify.com/app/match-details/{match_id}/overview"
    requestURL = f"https://api.cs-prod.leetify.com/api/games/{match_id}"

    for attempt in range(1, retries + 1):
        try:
            print(f"\n[Attempt {attempt}] Fetching match {match_id}")
            page.goto(URL, timeout=20000)
            page.wait_for_load_state("networkidle", timeout=30000)

            title = page.title()
            print("Page Title:", title)

            table = page.locator("table.--use-min-width")
            table.wait_for(state="visible", timeout=15000)

            rows = table.locator("tbody tr")
            raw_table = []
            row_count = rows.count()
            for i in range(row_count):
                row = rows.nth(i)
                cells = row.locator("td")
                cell_count = cells.count()
                row_data = [cells.nth(j).inner_text() for j in range(cell_count)]
                raw_table.append(row_data)


            teams, players = parse_table(raw_table)
            table_data = {"teams": teams, "players": players}


            response = requests.get(requestURL, headers=headers)
            if response.status_code != 200:
                print(f"Failed to fetch match API ({response.status_code}), skipping.")
                return None

            api_parsed_data = leetify_match_data_parser(response.json())
            merged_data = merge_table_and_api_data(api_parsed_data, table_data)
            return merged_data

        except PlaywrightTimeoutError:
            print(f"Timeout while scraping match {match_id} (attempt {attempt}/{retries})")
        except Exception as e:
            print(f"Unexpected error scraping match {match_id}: {e}")

        if attempt < retries:
            print(f"Retrying in {delay}s...")
            time.sleep(delay)

    print(f"Failed to scrape {match_id} after {retries} retries.")
    return None


def main(headless=True):
    headers = {"Accept": "application/json"}
    count = 0

    response = requests.get(profileURL, headers=headers)
    if response.status_code != 200:
        print("Failed to fetch profile API:", response.status_code, response.text)
        return

    profile_data = response.json()
    faceit_matches = [
        g for g in profile_data.get("games", [])
        if g.get("dataSource") == "faceit"
    ][:50]

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()

        for match in faceit_matches:
            match_id = match["gameId"]

            merged_data = scrape_match_with_retry(page, match_id, headers)

            if not merged_data:
                print(f"Skipping match {match_id} after all retries.")
                continue

            conn = get_connection()
            match_payload = {
                "match_id": merged_data["match_id"],
                "dataSource": merged_data.get("dataSource"),
                "hltvMatchId": merged_data.get("hltvMatchId"),
                "team_scores": merged_data.get("team_scores"),
                "winner_team": 0 if merged_data.get("team_scores", [0,0])[0] > merged_data.get("team_scores", [0,0])[1] else 1,
                "date_finished_at": merged_data.get("date_finished_at"),
                "player_stats": merged_data["player_stats"]
            }
            insert_match_and_players(conn, match_payload)
            conn.close()

            count += 1
            print(f" Uploaded match {count}")

        browser.close()

    print(f"{count} matches uploaded successfully.")


if __name__ == "__main__":
    main(headless=True)