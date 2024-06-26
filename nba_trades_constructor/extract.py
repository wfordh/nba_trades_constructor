import argparse
import logging
import json
from random import uniform
from time import sleep

import requests
from bs4 import BeautifulSoup
from nba_api.stats.static import teams
from tqdm import tqdm
from utils import headers, get_taxpayer_levels, team_taxpayer_status, NBA_SEASON

"""
{
	"Golden State Warriors":
		[
			{"player": "Stephen Curry", "salary_2024":...}
		]
		{"Stephen Curry": {"salary_2024":..., "salary_2025": ...}}
}

skip two-way contracts: check for 'style="color:rgb(168, 0, 212)"'
"""

parser = argparse.ArgumentParser()

parser.add_argument(
    "-s",
    "--season",
    help="The season to use for analysis. Must be formatted as YYYY-YY, eg 2023-24.",
    required=True,
    type=str
)

def get_hoops_hype_salary(team, season=NBA_SEASON):
    """
    Scrapes and cleans salary data from Hoops Hype, if the team existed at the time.
    If it did not, then nothing is returned.
    """
    sleep(uniform(1.1, 2))

    url = f"https://hoopshype.com/salaries/{team.lower().replace(' ', '_')}/{season}/"
    response = requests.get(url, headers=headers)
    # response status code
    soup = BeautifulSoup(response.content, "html.parser")

    salary_table = soup.find(
        "table",
        {"class": "hh-salaries-team-table hh-salaries-table-sortable responsive"},
    )

    team_dict = {}
    columns = [
        td.get_text().replace("/", "-")
        for td in salary_table.find("thead")
        .find("tr", {"class": "table-index"})
        .find_all("td")
    ]
    # don't want player column
    # columns.pop(0)
    body = salary_table.find("tbody").find_all("tr")
    for row in body:
        player_salaries = dict()
        for idx, td in enumerate(row.find_all("td")):
            if td.get("data-value"):
                player_salaries[columns[idx]] = int(td.get("data-value"))
            else:
                player_name = td.get_text().strip()
        # trying to avoid two-way and 10-day contract players
        # https://basketball.realgm.com/nba/info/minimum_scale/2017
        if player_salaries["2023-24"] > 1000000:
            team_dict[player_name] = player_salaries

    return team_dict


def main():
    team_list = [team["full_name"] for team in teams.get_teams()]
    team_salaries = dict.fromkeys(team_list)
    cap_levels = get_taxpayer_levels()

    for team in tqdm(team_list):
        team_data = dict()
        team_data["players"] = get_hoops_hype_salary(team, NBA_SEASON)

        team_data["total_salary"] = sum(
            [v["2023-24"] for k, v in team_data["players"].items()]
        )
        team_data["tax_status"] = team_taxpayer_status(
            team_data["total_salary"], cap_levels[NBA_SEASON]
        )
        team_salaries[team] = team_data

    # json file
    with open("data/salaries.json", "w") as outfile:
        json.dump(team_salaries, outfile)

    with open("data/cap_levels.json", "w") as outfile:
        json.dump(cap_levels, outfile)


if __name__ == "__main__":
    main()
