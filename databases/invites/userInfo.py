import os
import sqlite3

DATABASE = os.getcwd()+'/databases/tickets/InviteData.db'
TABLE = 'Invites'


class Invite:
    def __init__(self, bot, user):
        self.bot = bot
        self.user = user

        self.conn = None
        self.conn = sqlite3.connect(DATABASE)
        self.cursor = self.conn.cursor()

        self._create_table()
        self._get_invite_info()

    def _create_table(self):
        query = f"""CREATE TABLE IF NOT EXISTS {TABLE} (user_id BIGINT, claimed_invites BIGINT)"""
        self.cursor.execute(query)
        self.conn.commit()

    def create_invites(self):
        query = f"""INSERT INTO {TABLE} VALUES (?, ?)"""
        self.cursor.execute(query, (self.user.id, 0))
        self.conn.commit()

    def update_value(self, column, value):
        query = f"UPDATE {TABLE} set {column} = ? WHERE user_id = ?"
        self.cursor.execute(query, (value, self.user.id))
        self.conn.commit()

    def _get_invite_info(self):
        query = f"SELECT * FROM {TABLE} WHERE user_id = ?"
        self.cursor.execute(query, (self.user.id,))
        info = self.cursor.fetchall()
        if info:
            self.user_id = info[0][0]
            self.claimed_invites = info[0][1]
        else:
            self.create_invites()
            self._get_invite_info()
