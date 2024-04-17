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


def find_trades(
    n_returning_players, 
    total_salary, 
    outgoing_team, 
    team_salaries,
    tax_levels
):
    outgoing_tax_status = team_salaries[outgoing_team]["tax_status"]
    possible_trades = dict()
    if outgoing_tax_status == "Cap Team":
        if total_salary < 6533333:
            max_incoming_salary = 1.75 * total_salary + 100000
        elif total_salary < 19600000:
            max_incoming_salary = total_salary + 5000000
        else:
            max_incoming_salary = 1.25 * total_salary + 100000
    elif outgoing_tax_status == "Tax Team":
        # both Tax teams and Cap teams w/ salary over $19.6M are subject
        # to this rule
        max_incoming_salary = 1.25 * total_salary + 100000
    else:
        max_incoming_salary = 1.1 * total_salary + 100000

    for team_name, team_data in team_salaries.items():
        possible_team_deals = list()
        if team_name == outgoing_team:
            continue
        
        # this logic needs to be moved to after the combinations are made
        # or it could be in both places to cut down on the number of combos?
        if team_data["tax_status"] == "Cap Team":
            if total_salary < 6533333:
                min_incoming_salary = (total_salary - 100000) / 1.75
            elif total_salary < 19600000:
                min_incoming_salary = total_salary - 5000000
            else:
                min_incoming_salary = (total_salary - 100000) / 1.25
        elif team_data["tax_status"] == "Tax Team":
            min_incoming_salary = (total_salary - 100000) / 1.25
        else:
            # apron team
            min_incoming_salary = (total_salary - 100000) / 1.1

        remove_players = list()
        for player, salaries in team_data["players"].items():
            if salaries["2023_24"] > max_incoming_salary:
                remove_players.append(player)

        player_pool = {k: v for k, v in team_data["players"].items() if k not in remove_players}

        for combo in itertools.combinations(
            player_pool.keys(), n_returning_players
        ):
            combined_salary = sum(
                [
                    salaries["2023_24"]
                    for player, salaries in player_pool.items()
                    if player in combo
                ]
            )
            # check if team_data["total_salary"] - total_salary (rename?) 
            # + combined_salary changes the tax status?
            #
            new_outgoing_team_salary = team_salaries[outgoing_team]["total_salary"] - total_salary + combined_salary
            new_incoming_team_salary = team_data["total_salary"] + total_salary - combined_salary
            new_outgoing_tax_status = team_taxpayer_status(new_outgoing_team_salary, tax_levels)
            new_incoming_tax_status = team_taxpayer_status(new_incoming_team_salary, tax_levels)
            if new_outgoing_tax_status == "Cap Team":
                if total_salary < 6533333:
                    max_incoming_salary = 1.75 * total_salary + 100000
                elif total_salary < 19600000:
                    max_incoming_salary = total_salary + 5000000
                else:
                    max_incoming_salary = 1.25 * total_salary + 100000
            elif new_outgoing_tax_status == "Tax Team":
                # both Tax teams and Cap teams w/ salary over $19.6M are subject
                # to this rule
                max_incoming_salary = 1.25 * total_salary + 100000
            else:
                max_incoming_salary = 1.1 * total_salary + 100000

            if new_incoming_tax_status == "Cap Team":
                if total_salary < 6533333:
                    min_incoming_salary = (total_salary - 100000) / 1.75
                elif total_salary < 19600000:
                    min_incoming_salary = total_salary - 5000000
                else:
                    min_incoming_salary = (total_salary - 100000) / 1.25
            elif new_incoming_tax_status == "Tax Team":
                min_incoming_salary = (total_salary - 100000) / 1.25
            else:
                # apron team
                min_incoming_salary = (total_salary - 100000) / 1.1

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
    tax_levels = get_taxpayer_levels()

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

        This will show you the outgoing players and their total salary and list
        all of the possible player based trade returns, by team.
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
            players = list(team_salaries[team_input]["players"].keys())
            player_input = st.multiselect(
                "Which players would you like to include? (Max 3)",
                options=players,
                placeholder="Select players...",
                max_selections=3,
            )
        st.form_submit_button(label="Submit players")

    with st.form(key='n_returning_players'):
        n_returning_players = st.select_slider(
            "How many players should be coming back in the trade?",
            options=[1, 2, 3, 4]
        )
        st.form_submit_button(label="Submit number of returning players")

    total_salary = sum(
        [
            v["2023_24"]
            for k, v in team_salaries[team_input]["players"].items()
            if k in player_input
        ]
    )
    st.write(
        f"Total {team_input} salary from {', '.join(player_input)}: ${total_salary:,}"
    )

    trades = find_trades(
        n_returning_players=n_returning_players,
        total_salary=total_salary,
        outgoing_team=team_input,
        team_salaries=team_salaries,
        tax_levels=tax_levels
    )
    st.write(f"Number of possible trades: {sum([len(v) for k, v in trades.items()])}")
    st.json(trades)


if __name__ == "__main__":
    main()
