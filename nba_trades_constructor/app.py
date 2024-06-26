"""
- want to cut down search space however possible
        - avoid two way players? how?

KNAPSACK PROBLEM
- a variation on it
- we have a range for our "weight", W
- we are trying to get all possible matches instead of maximizing "profit"
        - profit is nebulous here due to player valuations and draft pick compensation
- we want to fix the number of items in the bag (do we?? or all less than it?)
"""

import json
import itertools

import streamlit as st

from utils import get_taxpayer_levels, team_taxpayer_status

# https://basketball.realgm.com/nba/info/salary_cap

NBA_SEASON = "2024-25"

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
    if total_salary == 0:
        return {}
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


def main():
    with open("data/salaries.json", "r") as infile:
        team_salaries = json.load(infile)
    teams = list(team_salaries.keys())
    tax_levels = get_taxpayer_levels(NBA_SEASON)
    print(tax_levels)

    st.title("NBA Trades Constructor")

    st.write(
        """
        Hello and welcome to the NBA trades constructor! This tool is for coming up
        with all possible combinations of players for return in a trade according
        to the NBA's salary matching rules. It does _not_ say if a trade is fair
        or balanced, nor does it handle other trade eligibility details like no-trade
        clauses or players who only become eligible on certain dates. At least yet.

        To use it, please select a team and hit submit. Then select which players
        to send out in the deal, with a maximum of 3, and hit submit. Lastly, select
        the number of players you want in return for the outgoing players and hit
        submit.

        **NOTE: The tool is still more proof-of-concept than fully-fledged. It's also
        currently hard-coded for using salaries from the 2024-25 NBA season. For more
        information, read this [blog post](https://fordhiggins.com/sports/2024/04/23/building_nba_trades_constructor.md)
        or visit the [GitHub repository](https://github.com/wfordh/nba_trades_constructor/).**
        """
    )

    with st.form(key="team_selection"):
        team_input = st.selectbox(
            "Which team would you like to construct a trade for?",
            options=teams,
            placeholder="Select a team...",
        )
        st.form_submit_button(label="Submit team")

    with st.form(key="outgoing_players"):
        if team_input:
            players = [
                player 
                for player, player_salaries 
                in team_salaries[team_input]["players"].items() 
                if player_salaries[NBA_SEASON] > 0
            ]
            player_input = st.multiselect(
                "Which players would you like to include? (Max 3)",
                options=players,
                placeholder="Select players...",
                max_selections=3,
            )
        st.form_submit_button(label="Submit players")

    with st.form(key="n_returning_players"):
        n_returning_players = st.radio(
            "How many players should be coming back in the trade?", 
            options=[1, 2, 3, 4],
            horizontal=True,
        )
        st.form_submit_button(label="Submit number of returning players")

    total_salary = sum(
        [
            v[NBA_SEASON]
            for k, v in team_salaries[team_input]["players"].items()
            if k in player_input
        ]
    )
    st.write(
        """
        The output is outgoing players and their total salary, followed by a list 
        of all the possible player based trade returns, by team. Each line under
        a team represents _one_ possible trade.
        """
    )
    st.write(
        f"Total {team_input} salary from {', '.join(player_input)}: ${total_salary:,}"
    )
    if (team_salaries[team_input]["tax_status"] == "2nd Apron Team") and len(player_input) > 1:
        st.write(f"WARNING - The {team_input} are a 2nd apron team and cannot aggregate outgoing salaries!")

    trades = find_trades(
        n_returning_players=n_returning_players,
        total_salary=total_salary,
        outgoing_team=team_input,
        team_salaries=team_salaries,
        tax_levels=tax_levels,
    )
    st.write(f"Number of possible trades: {sum([len(v) for k, v in trades.items()])}")
    st.json(trades)


if __name__ == "__main__":
    main()
