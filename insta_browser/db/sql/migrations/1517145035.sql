CREATE TABLE tmp_counters
(
    login VARCHAR(128) PRIMARY KEY,
    updated_at DATE NOT NULL,
    counters TEXT NOT NULL
);