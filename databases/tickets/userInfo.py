import os
import sqlite3

DATABASE = os.getcwd()+'/databases/tickets/TicketData.db'
TABLE = 'Tickets'


class Ticket:
    def __init__(self, bot, ctx):
        self.bot = bot
        self.ctx = ctx

        self.ticket_creator_id = None

        self.conn = None
        self.conn = sqlite3.connect(DATABASE)
        self.cursor = self.conn.cursor()

        self._create_table()

    def _create_table(self):
        query = f"""CREATE TABLE IF NOT EXISTS {TABLE} (creator_id BIGINT, id BIGINT, type TEXT, extras TEXT)"""
        self.cursor.execute(query)
        self.conn.commit()

    def create_ticket(self, ticket_creator_id, ticket_id, ticket_type):
        query = f"""INSERT INTO {TABLE} VALUES (?, ?, ?, ?)"""
        self.cursor.execute(query, (ticket_creator_id, ticket_id, ticket_type, "[]"))
        self.conn.commit()

    def find_ticket(self, ticket_creator_id=None, ticket_type=None, ticket_id=None):
        if ticket_id is not None:
            query = f"SELECT * FROM {TABLE} WHERE id = ?"
            self.cursor.execute(query, (ticket_id,))
        else:
            query = f"SELECT * FROM {TABLE} WHERE creator_id = ? AND type = ?"
            self.cursor.execute(query, (ticket_creator_id, ticket_type))
        info = self.cursor.fetchall()
        if not info:
            return None

        self.ticket_creator_id = ticket_creator_id
        self._get_ticket_info(info[0][0], info[0][2])
        return self

    def update_value(self, ticket_id, column, value):
        query = f"UPDATE {TABLE} set {column} = ? WHERE id = ?"
        self.cursor.execute(query, (value, ticket_id))
        self.conn.commit()

    def _get_ticket_info(self, ticket_creator_id, ticket_type):
        query = f"SELECT * FROM {TABLE} WHERE creator_id = ? AND type = ?"
        self.cursor.execute(query, (ticket_creator_id, ticket_type))
        info = self.cursor.fetchall()

        self.creator_id = info[0][0]
        self.id = info[0][1]
        self.type = info[0][2]
        self.extras = info[0][3]

    def delete_ticket(self):
        query = f"DELETE FROM {TABLE} WHERE id = ?"
        self.cursor.execute(query, (self.id,))
