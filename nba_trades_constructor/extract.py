import logging
import json
from random import uniform
from time import sleep

import requests
from bs4 import BeautifulSoup
from nba_api.stats.static import teams
from tqdm import tqdm
from utils import headers

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

NBA_SEASON = "2023-24"


def get_taxpayer_levels():
    url = "https://basketball.realgm.com/nba/info/salary_cap"
    response = requests.get(url)
    print(response.status_code)
    soup = BeautifulSoup(response.content, "html.parser")

    table = soup.find("table")
    headers = table.find("thead").find_all("tr").pop()
    body = soup.find("tbody").find_all("tr")
    realgm_season = "-20".join(NBA_SEASON.split("-"))
    cap_levels = None

    for row in body:
        if row.find("td", {"data-th": "Season"}).text == realgm_season:
            print(f"found the season!! {realgm_season}")
            cap_levels = {
                td["data-th"]: int(td["rel"])
                for td 
                in row.find_all(lambda x: x.has_attr("data-th"))
            }
            break

    return cap_levels


def team_taxpayer_status(team_salary, cap_levels):
    taxpayer_status = None
    if team_salary <= cap_levels["Salary Cap"]:
        taxpayer_status = "Cap Team"
    elif team_salary <= cap_levels["Luxury Tax"]:
        # ignoring apron stuff for now
        taxpayer_status = "Tax Team"
    else:
        taxpayer_status = "Apron Team"
    return taxpayer_status


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
        td.get_text().replace("/", "_")
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
        if player_salaries["2023_24"] > 1000000:
            team_dict[player_name] = player_salaries

    return team_dict


def main():
    team_list = [team["full_name"] for team in teams.get_teams()]
    team_salaries = dict.fromkeys(team_list)
    cap_levels = get_taxpayer_levels()
    print(cap_levels)

    for team in tqdm(team_list):
        team_data = dict()
        team_data["players"] = get_hoops_hype_salary(team, NBA_SEASON)
        
        team_data["total_salary"] = sum(
            [
                v["2023_24"] 
                for k, v 
                in team_data["players"].items()
            ]
        )
        team_data["tax_status"] = team_taxpayer_status(team_data["total_salary"], cap_levels)
        team_salaries[team] = team_data

    # json file
    with open("data/salaries.json", "w") as outfile:
        json.dump(team_salaries, outfile)


if __name__ == "__main__":
    main()
