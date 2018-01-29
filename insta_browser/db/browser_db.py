import os
import tempfile

import json
import sqlite3
import datetime



class BrowserDB:
    user_counters_table = 'tmp_counters'
    sql_path = os.path.dirname(os.path.abspath(__file__))
    account_id = None

    def __init__(self, logger, db_path=tempfile.gettempdir()):
        self.logger = logger
        self.db = self.__connect_db(db_path)
        self.__init_db()

    def __connect_db(self, db_path):
        db_name = 'insta_browser.sqlite3'
        try:
            connect_path = os.path.join(db_path, db_name)
            db = sqlite3.connect(connect_path)
        except:
            connect_path = os.path.join(tempfile.gettempdir(), db_name)
            db = sqlite3.connect(connect_path)
        self.db_log('connected to {} database')
        return db

    def __init_db(self):
        db = self.db
        cursor = db.cursor()
        self.__create_update_db(self.__check_db_version())

    def __check_db_version(self):
        cur = self.db.cursor()
        q = 'SELECT version FROM db_version ORDER BY version DESC'
        self.db_log('query: {}'.format(q))
        try:
            cur.execute(q)
            ver = cur.fetchone()
        except sqlite3.OperationalError:
            ver = False
        self.db_log('result: {}'.format(ver))
        return ver

    def __create_update_db(self, version):
        db = self.db
        if not version:
            self.logger.log_to_file('')
            create_sql = open(os.path.join(self.sql_path, 'sql', 'init.sql'), 'r').read()
            db.cursor().executescript(create_sql)
            self.db_log('creating new db')
            version = (0,)

        migration_path = os.path.join(self.sql_path, 'sql', 'migrations')
        files = [f for f in os.listdir(migration_path) if
                 os.path.isfile(os.path.join(migration_path, f)) and int(f.replace('.sql', '')) > version[0]]
        files.sort(key=str.lower)
        for file in files:
            migration_sql = open(os.path.join(migration_path, file), 'r').read()
            db.cursor().executescript(migration_sql)
            self.db_log('migrate to {}'.format(file))
            db.cursor().execute("UPDATE db_version SET version={};".format(file.replace('.sql', '')))

    def get_user_counters(self, login):
        result = {'updated_at': (datetime.date.today() + datetime.timedelta(days=-40)).strftime("%Y-%m-%d")}
        query = 'SELECT * FROM {} WHERE login = ?'.format(self.user_counters_table)
        row = self.db.cursor().execute(query, [login]).fetchone()
        if row:
            result = {'updated_at': row[1], 'counters': json.loads(row[2])}
        return result

    def store_user_counters(self, login, counters):
        query = "REPLACE INTO {} (login, updated_at, counters) VALUES (?, strftime('%Y-%m-%d', 'now'), ?)".format(
            self.user_counters_table)
        self.db.cursor().execute(query, [login, json.dumps(counters)])

    def detect_account(self, login):
        cur = self.db.cursor()
        if not self.get_account_id(login):
            q = 'INSERT INTO accounts (username) VALUES (?)'
            p = [login]
            cur.execute(q, p)
            self.db.commit()
            self.db_log('query: {}, params: {}'.format(q, p))
            self.detect_account(login)

    def get_account_id(self, login):
        q = 'SELECT id FROM accounts WHERE username = :login;'
        params = {'login': login}
        row = self.db.cursor().execute(q, params).fetchone()
        self.db_log('query: {}, params: {}, result: {}'.format(q, params, row))
        if row:
            self.account_id = row[0]
        return self.account_id

    def get_like_limits_by_account(self):
        cur = self.db.cursor()
        row = cur.execute(SELECT_LIKE_LIMITS_QUERY, [self.account_id]).fetchone()
        return row

    def get_follow_limits_by_account(self):
        cur = self.db.cursor()
        row1 = cur.execute(SELECT_FOLLOW_TODAYS_LIMITS_QUERY, [self.account_id]).fetchone()
        row2 = cur.execute(SELECT_FOLLOW_HOURS_LIMITS_QUERY, [self.account_id]).fetchone()
        return {'daily': row1[0], 'hourly': row2[0], 'hours_left': row1[1]}

    def likes_increment(self):
        params = [self.account_id]
        self.db.execute(INSERT_UPDATE_LIKES_QUERY, params)
        self.db_log('query: {}, params: {}'.format(''.join(INSERT_UPDATE_LIKES_QUERY.splitlines()), params))
        self.db.commit()

    def follows_increment(self):
        params = [self.account_id]
        self.db.execute(INSERT_UPDATE_FOLLOWS_QUERY, params)
        self.db_log('query: {}, params: {}'.format(''.join(INSERT_UPDATE_FOLLOWS_QUERY.splitlines()), params))
        self.db.commit()

    def db_log(self, text):
        self.logger.log_to_file('[SQLITE] {}'.format(text))


SELECT_LIKE_LIMITS_QUERY = '''
SELECT
  ifnull(sum(likes), 0)      AS `limit`,
  24 - strftime('%H', 'now') AS hours_left
FROM activity
WHERE account_id = ? AND
      datetime(date) BETWEEN datetime('now', 'start of day') AND datetime('now', 'start of day', '+1 day', '-1 second');
'''

SELECT_FOLLOW_TODAYS_LIMITS_QUERY = '''
SELECT
  ifnull(sum(follows), 0)      AS `limit`,
  24 - strftime('%H', 'now') AS hours_left
FROM activity
WHERE account_id = ? AND
      datetime(date) BETWEEN datetime('now', 'start of day') AND datetime('now', 'start of day', '+1 day', '-1 second');
'''

SELECT_FOLLOW_HOURS_LIMITS_QUERY = '''
SELECT
  ifnull(sum(follows), 0)      AS `follows_in_hour`
FROM activity
WHERE account_id = ? AND
      datetime(date) BETWEEN (strftime('%Y-%m-%d %H', 'now') || ':00:00') AND (strftime('%Y-%m-%d %H', 'now') || ':59:59');
'''

INSERT_UPDATE_LIKES_QUERY = '''
WITH new (account_id, date) AS (VALUES (?, strftime('%Y-%m-%d %H', 'now') || ':00:00'))
INSERT OR REPLACE INTO activity (id, account_id, likes, comments, follows, unfollows, date)
  SELECT
    a.id,
    n.account_id,
    ifnull(a.likes, 0) + 1,
    ifnull(a.comments, 0),
    ifnull(a.follows, 0),
    ifnull(a.unfollows, 0),
    n.date
  FROM new n
    LEFT JOIN activity a ON a.account_id = n.account_id AND a.date = n.date;
'''

INSERT_UPDATE_FOLLOWS_QUERY = '''
WITH new (account_id, date) AS (VALUES (?, strftime('%Y-%m-%d %H', 'now') || ':00:00'))
INSERT OR REPLACE INTO activity (id, account_id, likes, comments, follows, unfollows, date)
  SELECT
    a.id,
    n.account_id,
    ifnull(a.likes, 0),
    ifnull(a.comments, 0),
    ifnull(a.follows, 0) + 1,
    ifnull(a.unfollows, 0),
    n.date
  FROM new n
    LEFT JOIN activity a ON a.account_id = n.account_id AND a.date = n.date;
'''
