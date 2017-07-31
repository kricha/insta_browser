CREATE TABLE accounts
(
  id       INTEGER PRIMARY KEY,
  username TEXT
);
CREATE TABLE db_version
(
  version INTEGER PRIMARY KEY
);
CREATE TABLE activity
(
  id         INTEGER PRIMARY KEY,
  account_id INTEGER,
  likes      INTEGER DEFAULT 0,
  comments   INTEGER DEFAULT 0,
  follows    INTEGER DEFAULT 0,
  unfollows  INTEGER DEFAULT 0,
  date       TEXT,
  CONSTRAINT likes_accounts_id_fk FOREIGN KEY (account_id) REFERENCES accounts (id)
);
INSERT INTO db_version (version) VALUES (strftime('%s', 'now'));