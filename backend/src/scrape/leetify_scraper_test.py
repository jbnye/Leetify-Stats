import sys
import os
import time
import requests
from fake_useragent import UserAgent
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scrape.table_scraper import parse_table
from scrape.leetify_match_data_parser import leetify_match_data_parser
from scrape.merge_table_and_api_data import merge_table_and_api_data
from database.db import get_connection
from database.get_db_matches import get_all_matches_ids
from database.leetify_db_uploader import insert_match_and_players
from database.get_db_faceit_steam_ids import get_steam_ids

# URL = "https://leetify.com/app/match-details/7168d44e-ed88-45ad-9403-28187440b98e/overview" # requestURL = "https://api.cs-prod.leetify.com/api/games/7168d44e-ed88-45ad-9403-28187440b98e" # profileURL = "https://api.cs-prod.leetify.com/api/profile/id/76561198089612542" # URL = "https://leetify.com/app/match-details/ed7d411b-876d-4481-b45d-a44f826426e5/overview" # requestURL = "https://api.cs-prod.leetify.com/api/games/ed7d411b-876d-4481-b45d-a44f826426e5"


ua = UserAgent()

def get_random_headers():
    return {
        "User-Agent": ua.random,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive"
    }


def scrape_match_with_retry(page, match_id, retries=3, delay=5):
    """Scrape a single match with retry and random User-Agent rotation."""
    for attempt in range(1, retries + 1):
        headers = get_random_headers()
        URL = f"https://leetify.com/app/match-details/{match_id}/overview"
        requestURL = f"https://api.cs-prod.leetify.com/api/games/{match_id}"

        try:
            print(f"\n[Attempt {attempt}] Fetching match {match_id} with UA: {headers['User-Agent']}")
            page.set_extra_http_headers(headers)
            page.goto(URL, timeout=60000)
            page.wait_for_load_state("networkidle", timeout=60000)

            table = page.locator("table.--use-min-width")
            table.wait_for(state="visible", timeout=60000)

            rows = table.locator("tbody tr")
            raw_table = []
            for i in range(rows.count()):
                cells = rows.nth(i).locator("td")
                row_data = [cells.nth(j).inner_text() for j in range(cells.count())]
                raw_table.append(row_data)

            teams, players = parse_table(raw_table)
            table_data = {"teams": teams, "players": players}

            response = requests.get(requestURL, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"Failed to fetch match API ({response.status_code}), skipping.")
                return None

            api_parsed_data = leetify_match_data_parser(response.json())
            merged_data = merge_table_and_api_data(api_parsed_data, table_data)
            return merged_data

        except PlaywrightTimeoutError:
            print(f"Timeout while scraping match {match_id} (attempt {attempt}/{retries})")
        except requests.exceptions.Timeout:
            print(f"Request timeout for match {match_id} (attempt {attempt}/{retries})")
        except Exception as e:
            print(f"Unexpected error scraping match {match_id}: {e}")

        if attempt < retries:
            print(f"Rotating User-Agent and retrying in {delay}s...")
            time.sleep(delay)

    print(f"Failed to scrape {match_id} after {retries} retries.")
    return None


def main(headless=True):
    faceit_steam_ids = get_steam_ids()
    conn = get_connection()
    cursor = conn.cursor()

    for index, steam_id in enumerate(faceit_steam_ids):
        database_match_ids = get_all_matches_ids()
        count = 0
        headers = get_random_headers()

        profileURL = f"https://api.cs-prod.leetify.com/api/profile/id/{steam_id}"
        response = requests.get(profileURL, headers=headers, timeout=15)
        if response.status_code != 200:
            print("Failed to fetch profile API for:", response.status_code, steam_id)
            continue

        profile_data = response.json()
        faceit_matches = [
            g for g in profile_data.get("games", [])
            if g.get("dataSource") == "faceit"
        ][:50]

        with sync_playwright() as pw:
            random_ua = ua.random
            browser = pw.chromium.launch(headless=headless)
            context = browser.new_context(user_agent=random_ua)
            page = context.new_page()

            for match in faceit_matches:
                match_id = match["gameId"]
                if match_id in database_match_ids:
                    print(f"Skipping already-uploaded match {match_id}")
                    continue

                merged_data = scrape_match_with_retry(page, match_id)
                if not merged_data:
                    print(f"Skipping match {match_id} after all retries.")
                    continue

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

                count += 1
                print(f"✅ Uploaded match {count} for player {index}")

            browser.close()

        print(f"{count} matches uploaded successfully for player {index}")
    conn.close()


if __name__ == "__main__":
    main(headless=True)