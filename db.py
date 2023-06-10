import csv
import os
import sqlite3

from config import DATA_DIR, RELOAD_DB


DB_NAME = 'attendance.db'
TABLES = ['teams', 'venues', 'games']


def load_sql_file(fname: str) -> str:
    with open(fname) as f:
        data = f.read()
    return data


def main():
    # destroy and reload
    if os.path.exists(DB_NAME) and RELOAD_DB:
        os.remove(DB_NAME)

    conn = sqlite3.connect(DB_NAME)
    schema = load_sql_file('schema.sql')
    conn.executescript(schema)
    conn.commit()

    for table in TABLES:
        with open(DATA_DIR / f'{table}.csv') as f:
            csvreader = csv.reader(f)
            header = next(csvreader)
            columns = ','.join(header)
            placeholders = ','.join(['?'] * len(header))

            query = f'INSERT OR IGNORE INTO {table} ({columns}) VALUES ({placeholders})'
            conn.executemany(query, [row for row in csvreader])
            conn.commit()


if __name__ == '__main__':
    main()
