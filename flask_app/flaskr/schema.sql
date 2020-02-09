DROP TABLE IF EXISTS program_log;

CREATE TABLE program_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    start_time INTEGER NOT NULL,
    end_time ,
    time_remaining INTEGER,
    max_time INTEGER
);