# NBA Trades Constructor

## Introduction

Hello and welcome to the NBA trades constructor! This tool is for coming up
with all possible combinations of players for return in a trade according
to the NBA's salary matching rules. It does _not_ say if a trade is fair
or balanced, nor does it handle other trade eligibility details like no-trade clauses or players who only become eligible on certain dates. 

At least yet. This app is in a proof-of-concept stage! It also does currently includes players who were bought out by a team since their salaries are still on the team's cap sheet even though they are no longer on the team and therefore cannot be traded by the team. 


## How to Use It

To use it, please select a team and hit submit. Then select which players
to send out in the deal, with a maximum of 3, and hit submit. Lastly, select
the number of players you want in return for the outgoing players and hit
submit.

This will show you the outgoing players and their total salary and list
all of the possible player based trade returns, by team.

## Roadmap

Improving the usability of the tool, primarily in output presentation, is one of the main targets in addition to fleshing out the handling of NBA trade rules and contracts. I envision each team having a collapsible section with a header listing the number of possible trades for them. The section displays all of the possible trades when expanded and, for cases where there are and many options for "filler" players, that the "filler" players are grouped together to reduce the number of results one has to scroll through. Here is a [rough mockup](https://whimsical.com/nba-trades-constructor-wireframe-JkgrJjieo1tqRgWezm4nyo).

The step after that would be bringing in information around player quality and impacts to a team's cap, similar to existing NBA trade machines.