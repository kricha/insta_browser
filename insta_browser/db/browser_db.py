import os
import sqlite3
import tempfile


class BrowserDB:
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
        else:
            self.db_log('migrations will be provided in future.')

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
        row = cur.execute(SELECT_LIMITS_QUERY, [self.account_id]).fetchone()
        return row

    def likes_increment(self):
        params = [self.account_id]
        self.db.execute(INSERT_UPDATE_LIKES_QUERY, params)
        self.db_log('query: {}, params: {}'.format(''.join(INSERT_UPDATE_LIKES_QUERY.splitlines()), params))
        self.db.commit()

    def db_log(self, text):
        self.logger.log_to_file('[SQLITE] {}'.format(text))

SELECT_LIMITS_QUERY = '''
SELECT
  ifnull(sum(likes), 0)      AS `limit`,
  24 - strftime('%H', 'now') AS hours_left
FROM activity
WHERE account_id = ? AND
      datetime(date) BETWEEN datetime('now', 'start of day') AND datetime('now', 'start of day', '+1 day', '-1 second');
'''

INSERT_UPDATE_LIKES_QUERY = '''
WITH new (account_id, likes, date) AS (VALUES (?, 1, strftime('%Y-%m-%d %H', 'now') || ':00:00'))
INSERT OR REPLACE INTO activity (id, account_id, likes, date)
  SELECT
    a.id,
    n.account_id,
    ifnull(a.likes, 0) + 1,
    n.date
  FROM new n
    LEFT JOIN activity a ON a.account_id = n.account_id AND a.date = n.date;
'''