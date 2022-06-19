import json
import math
import os
import random

import discord
import mariadb
from datetime import datetime


class NoSeller(Exception):
    """Raised when no seller is found"""


class NoSerial(Exception):
    """Raised when no seller is found"""


class NoGame(Exception):
    """Raised when no seller is found"""


class API:
    def __init__(self):
        self.conn = mariadb.connect(host="localhost", port=3306, user="api", password="^573uqcN", database="api")
        self.cursor = self.conn.cursor()

    def use_payment_id(self, payment_id, used_by):
        query = "INSERT INTO payments VALUES (?, ?)"
        self.cursor.execute(query, (payment_id, used_by))
        self.conn.commit()
        return True

    def check_payment_id(self, payment_id):
        query = "SELECT * FROM payments WHERE payment_id = ?"
        self.cursor.execute(query, (payment_id,))
        return self.cursor.fetchall()

    def get_sellers(self):
        query = f"SELECT id FROM accounts"
        self.cursor.execute(query)
        info = self.cursor.fetchall()
        return [Seller(seller_id[0]) for seller_id in info]

    def get_games(self):
        query = "SELECT id FROM games"
        self.cursor.execute(query)
        info = self.cursor.fetchall()
        return [Game(gameid[0]) for gameid in info]

    def register_seller(self, user: discord.Member):
        query = f"INSERT INTO accounts VALUES (?, ?, ?, ?, ?)"
        self.cursor.execute(query, (user.id, user.name, 1, 0, 0))
        self.conn.commit()

    def close(self):
        self.conn.close()


class Seller:
    def __init__(self, seller_id):
        self.conn = mariadb.connect(host="localhost", port=3306, user="api", password="^573uqcN", database="api")
        self.cursor = self.conn.cursor()
        self.config = json.load(open(os.getcwd() + '/config/config.json'))

        self.is_seller = False
        self.id = seller_id
        self.username = None
        self.genkeys = None
        self.unrestricted = None
        self.raw_owed = None

        self.get_info()

    @property
    def owed(self):
        return self.raw_owed / 100

    def get_info(self):
        query = "SELECT * FROM accounts WHERE id = ?"
        self.cursor.execute(query, (self.id,))
        info = self.cursor.fetchall()
        if info:
            self.is_seller = True
            self.id = info[0][0]
            self.username = info[0][1]
            self.genkeys = info[0][2]
            self.unrestricted = info[0][3]
            self.raw_owed = info[0][4]
            return

        raise NoSeller

    def update(self, column, value):
        if self.is_seller:
            query = f"UPDATE accounts set {column} = ? WHERE id = ?"
            self.cursor.execute(query, (value, self.id))
            self.conn.commit()
            self.get_info()
            return

        raise NoSeller

    def get_keys(self):
        if self.is_seller:
            query = "SELECT serial FROM serials WHERE resellerid = ?"
            self.cursor.execute(query, (self.id,))
            info = self.cursor.fetchall()
            return [Serial(serial[0]) for serial in info]

        raise NoSeller

    def gen_key(self, duration, gameid, count):
        serials = []
        for _ in range(count):
            query = f"""INSERT INTO serials VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            serial = self.random_serial(gameid)
            self.cursor.execute(query, (serial, duration, None, datetime.today(), None, None, gameid, self.id, 0, None))
            self.conn.commit()
            serials.append(serial)
        return serials

    def random_serial(self, gameid, serialsize=40):
        game = Game(gameid)
        serial = f'{game.name.split(" ")[0]}-'
        mask_part_size = serialsize - len(serial)
        mask_part = ''.join(random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890') for _ in range(mask_part_size))
        mask_dash_split = math.floor(len(mask_part) / 3)

        # Adding dashes to the serial
        mask_part = f"{mask_part[:mask_dash_split]}-{mask_part[mask_dash_split + 1:]}"
        mask_dash_split += mask_dash_split
        mask_part = f"{mask_part[:mask_dash_split]}-{mask_part[mask_dash_split + 1:]}"
        mask_dash_split += mask_dash_split
        return f"{serial}{mask_part}"

    def close(self):
        self.conn.close()


class Serial:
    def __init__(self, serial):
        self.conn = mariadb.connect(host="localhost", port=3306, user="api", password="^573uqcN", database="api")
        self.cursor = self.conn.cursor()

        self.is_valid = False

        self.serial = serial
        self.duration = None
        self.registered = None
        self.created = None
        self.gameid = None
        self.resellerid = None
        self.resetcount = None
        self.claimedby = None

        self.get_info()

    def get_info(self):
        query = "SELECT serial, duration, registered, created, gameid, resellerid, resetcount, claimedby FROM serials WHERE serial = ?"
        self.cursor.execute(query, (self.serial,))
        info = self.cursor.fetchall()
        if info:
            self.is_valid = True
            self.serial = info[0][0]
            self.duration = info[0][1]
            self.registered = info[0][2]
            self.created = info[0][3]
            self.gameid = info[0][4]
            self.resellerid = info[0][5]
            self.resetcount = info[0][6]
            self.claimedby = info[0][7]
            return

        raise NoSerial

    def update(self, column, value):
        if self.is_valid:
            query = f"UPDATE serials set {column} = ? WHERE serial = ?"
            self.cursor.execute(query, (value, self.serial))
            self.conn.commit()
            self.get_info()
            return

        raise NoSerial

    def delete(self):
        if self.is_valid:
            query = f"DELETE FROM serials WHERE serial = ?"
            self.cursor.execute(query, (self.serial,))
            self.conn.commit()
            return

        raise NoSerial

    def close(self):
        self.conn.close()


class Game:
    def __init__(self, gameid):
        self.conn = mariadb.connect(host="localhost", port=3306, user="api", password="^573uqcN", database="api")
        self.cursor = self.conn.cursor()

        self.is_game = False

        self.id = gameid
        self.name = None
        self.channelname = None
        self.status = None
        self.reseller_prices = {}
        self.prices = {}

        self.get_info()

    def get_info(self):
        query = "SELECT * FROM games WHERE id = ?"
        self.cursor.execute(query, (self.id,))
        info = self.cursor.fetchall()
        if info:
            self.is_game = True
            self.id = info[0][0]
            self.name = info[0][1]
            self.channelname = info[0][2]
            self.status = info[0][3]
            self.reseller_prices["1"] = info[0][4]
            self.reseller_prices["3"] = info[0][5]
            self.reseller_prices["7"] = info[0][6]
            self.reseller_prices["31"] = info[0][7]
            self.reseller_prices["36500"] = info[0][8]
            self.prices["1"] = info[0][9]
            self.prices["3"] = info[0][10]
            self.prices["7"] = info[0][11]
            self.prices["31"] = info[0][12]
            self.prices["36500"] = info[0][13]
            return

        raise NoGame

    def update(self, column, value):
        if self.is_game:
            query = f"UPDATE games set {column} = ? WHERE id = ?"
            self.cursor.execute(query, (value, self.id))
            self.conn.commit()
            self.get_info()
            return

        raise NoGame

    def close(self):
        self.conn.close()
