from teams_venues import main as get_teams_and_venues
from games import main as get_games
from db import main as create_db


if __name__ == '__main__':
    print('loading teams and venues')
    get_teams_and_venues()

    print('loading game data')
    get_games()

    print('creating database')
    create_db()
