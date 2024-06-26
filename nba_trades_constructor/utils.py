import requests
from bs4 import BeautifulSoup

# should prob move these two things to a constants.py file
headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "DNT": "1",
    "Pragma": "no-cache",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:56.0) Gecko/20100101 Firefox/56.0",
}

NBA_SEASON = "2024-25"


def get_taxpayer_levels(season: str = NBA_SEASON):
    url = "https://basketball.realgm.com/nba/info/salary_cap"
    response = requests.get(url)
    print(response.status_code)
    soup = BeautifulSoup(response.content, "html.parser")

    table = soup.find("table", {"class": "basketball compact"})
    headers = table.find("thead").find_all("tr").pop()
    body = soup.find("tbody").find_all("tr")
    realgm_season = "-20".join(season.split("-"))
    cap_levels = dict()

    for row in body:
        # used to be >=, not ==...why?
        if row.find("td", {"data-th": "Season"}).text >= realgm_season:
            fmt_season = row.find("td", {"data-th": "Season"}).text.split("-")
            fmt_season = fmt_season[0] + "-" + fmt_season[1][-2:]
            cap_levels[fmt_season] = {
                td["data-th"]: int(td["rel"])
                for td in row.find_all(lambda x: x.has_attr("data-th"))
            }

    return cap_levels[season]


def team_taxpayer_status(team_salary, cap_levels):
    taxpayer_status = None
    if team_salary <= cap_levels["Salary Cap"]:
        taxpayer_status = "Cap Team"
    elif team_salary <= cap_levels["Luxury Tax"]:
        # ignoring apron stuff for now
        taxpayer_status = "Tax Team"
    elif team_salary <= cap_levels["1st Apron"]:
        taxpayer_status = "1st Apron Team"
    else:
        taxpayer_status = "2nd Apron Team"
    return taxpayer_status


def get_max_incoming_salary(total_salary, tax_status):
    if tax_status == "Cap Team":
        if total_salary < 6533333:
            max_incoming_salary = 1.75 * total_salary + 100000
        elif total_salary < 19600000:
            max_incoming_salary = total_salary + 5000000
        else:
            max_incoming_salary = 1.25 * total_salary + 100000
    elif tax_status == "Tax Team":
        # both Tax teams and Cap teams w/ salary over $19.6M are subject
        # to this rule
        max_incoming_salary = 1.25 * total_salary + 100000
    else:
        max_incoming_salary = 1.1 * total_salary + 100000

    return max_incoming_salary


def get_min_incoming_salary(total_salary, tax_status):
    if tax_status == "Cap Team":
        if total_salary < 6533333:
            min_incoming_salary = (total_salary - 100000) / 1.75
        elif total_salary < 19600000:
            min_incoming_salary = total_salary - 5000000
        else:
            min_incoming_salary = (total_salary - 100000) / 1.25
    elif tax_status == "Tax Team":
        min_incoming_salary = (total_salary - 100000) / 1.25
    else:
        # apron team
        min_incoming_salary = (total_salary - 100000) / 1.1

    return min_incoming_salary


def find_trades(
    n_returning_players, total_salary, outgoing_team, team_salaries, tax_levels
):
    outgoing_tax_status = team_salaries[outgoing_team]["tax_status"]
    possible_trades = dict()
    max_incoming_salary = get_max_incoming_salary(total_salary, outgoing_tax_status)

    for team_name, team_data in team_salaries.items():
        possible_team_deals = list()
        if team_name == outgoing_team:
            continue

        # this logic needs to be moved to after the combinations are made
        # or it could be in both places to cut down on the number of combos?
        min_incoming_salary = get_min_incoming_salary(
            total_salary, team_data["tax_status"]
        )

        remove_players = list()
        for player, salaries in team_data["players"].items():
            if salaries[NBA_SEASON] > max_incoming_salary:
                remove_players.append(player)

        player_pool = {
            k: v for k, v in team_data["players"].items() if k not in remove_players
        }

        for combo in itertools.combinations(player_pool.keys(), n_returning_players):
            combined_salary = sum(
                [
                    salaries[NBA_SEASON]
                    for player, salaries in player_pool.items()
                    if player in combo
                ]
            )
            # check if team_data["total_salary"] - total_salary (rename?)
            # + combined_salary changes the tax status?
            #
            new_outgoing_team_salary = (
                team_salaries[outgoing_team]["total_salary"]
                - total_salary
                + combined_salary
            )
            new_incoming_team_salary = (
                team_data["total_salary"] + total_salary - combined_salary
            )
            new_outgoing_tax_status = team_taxpayer_status(
                new_outgoing_team_salary, tax_levels
            )
            new_incoming_tax_status = team_taxpayer_status(
                new_incoming_team_salary, tax_levels
            )

            max_incoming_salary = get_max_incoming_salary(
                total_salary, new_outgoing_tax_status
            )
            min_incoming_salary = get_min_incoming_salary(
                total_salary, new_incoming_tax_status
            )

            if (combined_salary >= min_incoming_salary) and (
                combined_salary <= max_incoming_salary
            ):
                possible_team_deals.append(", ".join(combo))
        possible_trades[team_name] = possible_team_deals

    return possible_trades
