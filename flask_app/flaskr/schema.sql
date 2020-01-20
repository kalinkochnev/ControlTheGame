CREATE TABLE [IF NOT EXISTS] game_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT;
    start_time TEXT NOT NULL;
    end_time TEXT NOT NULL;
    game_name TEXT NOT NULL;
);