# MLB Attendance data

Downloads teams, venues, and games for the current season and saves as CSV files in the data folder. Also creates a sqlite database called attendance.db with the three tables and some helper views.

## usage

* Download all data and load the database: `python main.py`
* Only load the database: `python db.py`

If `RELOAD_DB` in config.py is changed to True (default False) then db.py will first delete the attendance.db file before recreating.

### dependencies

requests and pytz

### primary data

* games.csv - Individual home game data with attendance, game datetime, opponent, and score
* teams.csv - MLB teams with a link to their home stadium with venue_id
* venues.csv - Venues for all MLB teams plus anything in additional_venues.csv

`venue_id` can be used to join all of the tables together

### manually maintained data

* additional_venues.csv - Neutral sites, not downloaded by teams_venues.py. I'm using descending negative integers as the venue_id for these.
* timezones.csv - Timezone for each venue, used to create localized game datetime in games.csv
* events.csv - Things like firework nights and bobblehead giveaways for later analysis

## data issues

The `missing_attendance_data` view contains games with no attendance but were not canceled. These are single ticketed doubleheader games which only report attendance for the second game. For the purposes generating aggregated and cumulative attendance data, this is ok.

----------

## why

To collect daily MLB attendance data. I could only find yearly aggregations online.

## future development

* Figure out how to tie together doubleheader games, maybe through a game_id foreign key
* Subdivide the data folder by season to start collecting data over time
* Look for APIs with historical attendance data
