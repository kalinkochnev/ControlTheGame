DROP TABLE IF EXISTS game_log;

CREATE TABLE game_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    start_time INTEGER NOT NULL,
    end_time INTEGER,
    max_time INTEGER
);