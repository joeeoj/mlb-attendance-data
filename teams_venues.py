"""Request individual team data from the MLB v2 API and split into two CSVs: teams and venues
Found the API here: https://gist.github.com/akeaswaran/b48b02f1c94f873c6655e7129910fc3b#mlb
"""
import csv

import requests

from config import DATA_DIR


URL = 'http://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams'
TEAM_URL = f'{URL}/{{abbr}}'


def additional_team_data(team_data: dict) -> dict:
    """Data is json blob from overall teams endpoint. This requests individual team data for each team in the list."""
    abbr = team_data['team']['abbreviation']
    d = requests.get(TEAM_URL.format(abbr=abbr)).json()

    venue_id = int(d['team']['franchise']['venue']['id'])

    d = {
        'team': {
            'team_id': int(d['team']['id']),
            'name': d['team']['name'],
            'abbr': d['team']['abbreviation'],
            'full_name': d['team']['displayName'],
            'location': d['team']['location'],
            'venue_id': venue_id,  # foreign key
        },
        'venue': {
            'venue_id': venue_id,
            'name': d['team']['franchise']['venue']['fullName'],
            'capacity': d['team']['franchise']['venue']['capacity'],
            'indoor': d['team']['franchise']['venue']['indoor'],
            'grass': d['team']['franchise']['venue']['grass'],
            'city': d['team']['franchise']['venue']['address']['city'],
            'state': d['team']['franchise']['venue']['address']['state'],
            'zipcode': d['team']['franchise']['venue']['address'].get('zipCode'),  # no zipcodes for Canada
        },
    }

    # fix data error with Oriole Park at Camden Yards -- it does not have a roof
    if d['venue']['venue_id'] == 1:
        d['venue']['indoor'] = False

    return d


def main():
    data = requests.get(URL).json()
    team_data_blob = data['sports'][0]['leagues'][0]['teams']
    parsed_data = [additional_team_data(t) for t in team_data_blob]

    teams = [d['team'] for d in parsed_data]
    with open(DATA_DIR / 'teams.csv', 'wt') as f:
        csvwriter = csv.DictWriter(f, fieldnames=list(teams[0].keys()))
        csvwriter.writeheader()
        csvwriter.writerows(teams)

    # usually neutral sites added manually
    with open(DATA_DIR / 'additional_venues.csv') as f:
        csvreader = csv.DictReader(f)
        add_venues = [row for row in csvreader]

    venues = [d['venue'] for d in parsed_data]
    venues.extend(add_venues)
    with open(DATA_DIR / 'venues.csv', 'wt') as f:
        csvwriter = csv.DictWriter(f, fieldnames=list(venues[0].keys()))
        csvwriter.writeheader()
        csvwriter.writerows(venues)
