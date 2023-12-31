CREATE TABLE IF NOT EXISTS venues (
    id INTEGER PRIMARY KEY,
    venue_id INTEGER NOT NULL UNIQUE,
    name VARCHAR(50),
    capacity INTEGER,
    indoor BOOLEAN,
    grass BOOLEAN,
    city VARCHAR(30),
    state VARCHAR(30),
    zipcode VARCHAR(10)
);

CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY,
    team_id INT NOT NULL UNIQUE,
    name VARCHAR(20),
    abbr CHAR(3),
    full_name VARCHAR(50),
    location VARCHAR(30),
    venue_id INTEGER,

    FOREIGN KEY (venue_id) REFERENCES venues(venue_id)
);

CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY,
    game_id INTEGER NOT NULL UNIQUE,
    game_dt DATETIME,
    short_name VARCHAR(15),
    notes VARCHAR(200),
    venue_id INTEGER NOT NULL,
    game_dt_local DATETIME,
    game_dt_dow VARCHAR(10),
    attendance INTEGER,
    neutral_site BOOLEAN,
    team_id INTEGER NOT NULL,
    team_abbr CHAR(3),
    score INTEGER,
    opponent_team_id INTEGER,
    opponent_team_abbr CHAR(3),
    opponent_score INTEGER,
    winner BOOLEAN,
    canceled BOOLEAN,

    FOREIGN KEY(team_id) REFERENCES team(team_id),
    FOREIGN KEY(opponent_team_id) REFERENCES team(team_id),
    FOREIGN KEY(venue_id) REFERENCES venues(venue_id)
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY,
    venue_id INTEGER NOT NULL,
    team_abbr CHAR(3),
    game_date_local DATE,
    event VARCHAR(500),
    short_desc VARCHAR(100),

    FOREIGN KEY(venue_id) REFERENCES venues(venue_id),
    UNIQUE(team_abbr, game_date_local, event) ON CONFLICT IGNORE
);

CREATE TABLE IF NOT EXISTS revenue (
    id INTEGER PRIMARY KEY,
    game_id INTEGER NOT NULL UNIQUE,
    revenue INTEGER,

    FOREIGN KEY(game_id) REFERENCES games(game_id)
);

CREATE VIEW IF NOT EXISTS attendance_ratio_daily AS
SELECT
    g.game_dt
    ,g.game_dt_dow
    ,v.venue_id
    ,t.team_id
    ,v.name as venue_name
    ,t.name as team_name
    ,g.opponent_team_abbr
    ,t.abbr
    ,g.attendance
    ,v.capacity
    ,g.attendance / CAST(v.capacity AS FLOAT) as attendance_ratio
FROM games g
JOIN venues v
    ON g.venue_id = v.venue_id
JOIN teams t
    ON t.venue_id = v.venue_id
ORDER BY
    g.game_dt
;

CREATE VIEW IF NOT EXISTS attendance_ratio_avg AS
SELECT
    v.venue_id
    ,t.team_id
    ,v.name as venue_name
    ,t.name as team_name
    ,t.abbr
    ,AVG(g.attendance) / v.capacity as attendance_ratio
FROM games g
JOIN venues v
    ON g.venue_id = v.venue_id
JOIN teams t
    ON t.venue_id = v.venue_id
GROUP BY
    v.venue_id
    ,v.name
    ,t.team_id
    ,t.abbr
    ,t.name
ORDER BY 6 DESC
;

CREATE VIEW IF NOT EXISTS min_max_attendance_ratio AS
SELECT
    g.venue_id
    ,v.name as venue_name
    ,t.abbr
    ,v.capacity
    ,MIN(g.attendance) as min_attendance
    ,MAX(g.attendance) as max_attendance
    ,MIN(g.attendance) / CAST(v.capacity AS FLOAT) as min_attendance_ratio
    ,MAX(g.attendance) / CAST(v.capacity AS FLOAT) as max_attendance_ratio
FROM games g
JOIN venues v
    ON g.venue_id = v.venue_id
-- inner join means neutral sites are excluded
JOIN teams t
    ON t.venue_id = v.venue_id
WHERE
    -- exclude canceled and "no attendance" games (makeups with no attendance data)
    g.attendance > 0
GROUP BY 1, 2, 3, 4
ORDER BY 7 DESC
;

-- seems to be single-ticketed double headers where the attendance data
-- is only reported for the second game
CREATE VIEW IF NOT EXISTS missing_attendance_data AS
SELECT *
FROM games
WHERE
    attendance = 0
    AND canceled = 0
ORDER BY
    game_dt
;

CREATE VIEW IF NOT EXISTS events_and_scores AS
SELECT
    e.id
    ,e.venue_id
    ,v.name
    ,g.game_dt_local
    ,g.game_dt_dow
    ,COALESCE(NULLIF(e.short_desc, ''), e.event) as event
    ,g.attendance
    ,v.capacity
    ,g.attendance / CAST(v.capacity AS FLOAT) as attenance_pct
    ,e.team_abbr
    ,g.opponent_team_abbr
    ,g.winner
    ,g.score
    ,g.opponent_score
    ,g.score - g.opponent_score as run_diff
FROM events e
JOIN games g
    ON e.game_date_local = SUBSTR(g.game_dt_local, 1, 10)
    AND e.team_abbr = g.team_abbr
JOIN venues v
    ON e.venue_id = v.venue_id
ORDER BY
    e.venue_id
    ,g.game_dt_local
;

CREATE VIEW IF NOT EXISTS revenue_with_attendance AS
SELECT
    r.*
    ,g.attendance
    ,r.revenue / CAST(g.attendance as FLOAT) as avg_revenue_per_seat
FROM revenue r
JOIN games g
    ON r.game_id = g.game_id
;
