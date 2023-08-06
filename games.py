import csv
from datetime import datetime, timedelta, timezone
import sys

import pytz
import requests

from config import DATA_DIR


BASE_URL = 'https://site.api.espn.com/apis/site/v2/sports/baseball/MLB/teams/{abbr}/schedule'
GAME_OFFSET = 5 # hours


def load_lookups() -> tuple[dict]:
    # venue name -> id lookup
    with open(DATA_DIR / 'venues.csv') as f:
        csvreader = csv.DictReader(f)
        VENUE_LOOKUP = {d['name']: d['venue_id'] for d in csvreader}

    # venue id -> timezone_offset
    with open(DATA_DIR / 'timezones.csv') as f:
        csvreader = csv.DictReader(f)
        TZ_LOOKUP = {d['venue_id']: d['timezone'] for d in csvreader}

    return VENUE_LOOKUP, TZ_LOOKUP


def parse_individual_team(team_dict: dict, prefix: str = '') -> dict:
    """Common fields for the home and away team"""
    prefix = prefix + '_' if prefix else prefix  # only add _ if not empty

    return {
        f'{prefix}team_id': int(team_dict['id']),
        f'{prefix}team_abbr': team_dict['team']['abbreviation'],
        f'{prefix}score': int(team_dict['score']['value']),
    }


def parse_teams(teams: list[dict], team_abbr: str) -> dict:
    """Given a list of two teams return a flattened dict from the perspective of the given team.
    i.e. if SEE is given, they are the primary team and the other team is the opponent."""
    assert len(teams) == 2

    d = dict()
    for team in teams:
        if team['team']['abbreviation'] == team_abbr:
            primary_team = parse_individual_team(team)
            primary_team['home'] = int(team['homeAway'] == 'home')
        else:
            opponent = parse_individual_team(team, 'opponent')

    return primary_team | opponent


def main():
    VENUE_LOOKUP, TZ_LOOKUP = load_lookups()

    with open(DATA_DIR / 'teams.csv') as f:
        csvreader = csv.DictReader(f)
        teams = [row for row in csvreader]

    results = []
    for team in teams:
        abbr = team['abbr']
        url = BASE_URL.format(abbr=abbr)
        data = requests.get(url).json()

        for event in data['events']:
            dt = datetime.fromisoformat(event['date'])

            # don't want future games. also add buffer for in progress games
            if dt + timedelta(hours=GAME_OFFSET) > datetime.now(timezone.utc):
                continue

            d = dict()
            d['game_id'] = event['id']
            d['game_dt'] = event['date']

            d['short_name'] = event['shortName']

            for comp in event['competitions']:
                notes = '\n'.join([n.get('headline') for n in comp.get('notes', [])])
                d['notes'] = notes if notes.strip() != '' else None

                venue_name = comp['venue']['fullName']
                venue_id = VENUE_LOOKUP.get(venue_name)
                if venue_id is None:
                    raise ValueError(f'Missing venue_id for {venue_name}')

                d['venue_id'] = venue_id

                local = dt.astimezone(pytz.timezone(TZ_LOOKUP.get(venue_id)))
                d['game_dt_local'] = local.isoformat()
                d['game_dt_dow'] = local.strftime('%A')

                d['attendance'] = comp['attendance']
                d['neutral_site'] = int(comp['neutralSite'])

                team_data = parse_teams(comp['competitors'], abbr)

                # skip away games since we are iterating through all teams
                if not team_data['home']:
                    continue
                else:  # don't need to keep this key since they will all be home
                    del team_data['home']

                # canceled games
                if team_data['score'] == 0 and team_data['opponent_score'] == 0:
                    team_data['winner'] = None
                elif team_data['score'] > team_data['opponent_score']:
                    team_data['winner'] = 1  # integer for sqlite
                else:
                    team_data['winner'] = 0

                team_data['canceled'] = 1 if team_data['winner'] is None else 0

                d |= team_data
                results.append(d)

    with open(DATA_DIR / 'games.csv', 'wt') as f:
        csvwriter = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        csvwriter.writeheader()
        csvwriter.writerows(results)
