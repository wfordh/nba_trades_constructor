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

NBA_SEASON = "2023-24"


def get_taxpayer_levels():
    url = "https://basketball.realgm.com/nba/info/salary_cap"
    response = requests.get(url)
    print(response.status_code)
    soup = BeautifulSoup(response.content, "html.parser")

    table = soup.find("table", {"class": "basketball compact"})
    headers = table.find("thead").find_all("tr").pop()
    body = soup.find("tbody").find_all("tr")
    realgm_season = "-20".join(NBA_SEASON.split("-"))
    cap_levels = None

    for row in body:
        if row.find("td", {"data-th": "Season"}).text == realgm_season:
            print(f"found the season!! {realgm_season}")
            cap_levels = {
                td["data-th"]: int(td["rel"])
                for td in row.find_all(lambda x: x.has_attr("data-th"))
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
    elif team_salary <= cap_levels["1st Apron"]:
        taxpayer_status = "1st Apron Team"
    else:
        taxpayer_status = "2nd Apron Team"
    return taxpayer_status
