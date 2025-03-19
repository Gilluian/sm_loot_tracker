# db_funcs.py

# handles the database functions that the item tracker will utilize.


import sqlite3
import csv
from time import sleep
from datetime import datetime

class LootTracker:
    def __init__(self):
        self.conn = sqlite3.connect('item_tracker_dev.db')
        self.cur = self.conn.cursor()

        self.cur.execute('''CREATE TABLE IF NOT EXISTS items(
                        sql_itemid INTEGER PRIMARY KEY AUTOINCREMENT,
                        wow_itemid INTEGER UNIQUE,
                        item_name TEXT
                        );''')
        self.cur.execute('''CREATE TABLE IF NOT EXISTS players (
                        sql_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        guild_rank TEXT,
                        level INTEGER,
                        class TEXT,
                        race TEXT
                        );''')
        self.cur.execute('''CREATE TABLE IF NOT EXISTS loot_record(
                        sql_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        item_id INTEGER NOT NULL REFERENCES items(wow_item_id) ON DELETE CASCADE,
                        winner_id INTEGER REFERENCES players(sql_id) ON DELETE CASCADE,
                        date TEXT,
                        soft_res INTEGER,
                        offspec INTEGER
                        );''') # 1 = true, 0 = false. 1 it was softressed or an offspec roll, 0 it wasn't.

        self.initial_startup()

    def __del__(self):
        self.conn.close()

    def initial_startup(self):
        if self.get_count_players()[0][0] == 0:
            print('Looks like this is the initial startup. Adding guildmates.')
            sleep(1)
            with open('guild_roster.csv','r',encoding='utf-8') as f:
                reader = csv.reader(f)
                roster = list(reader)
            for i in roster:
                name, rank, level, wow_class, race = i[0].split(';')
                self.add_player(name,rank,level,wow_class,race)
                print(f'added {name} to database')

            pass  #TODO if it's empty, we need to take the guild roster and load it into the DB

        if self.get_count_items()[0][0] == 0:
            print('Looks like initial startup. Adding items')
            sleep(1)
            with open('items.csv','r',encoding='utf-8') as f:
                reader = csv.reader(f)
                items = list(reader)
            print("Adding items to db.")
            for i in items:
                try:
                    id, item_name = i
                except ValueError as e:
                    print('exception occurred:')
                    print('error thrown', e)
                    print(i)
                    continue
                self.add_item_to_item_tracker(id,item_name)
                # self.add_item_on_startup(id, itemname)

            pass #TODO if it's empty, we need to take the items csv and load it into the DB
        pass

# ITEM QUERIES

    def get_count_items(self):
        sql = 'SELECT count(*) FROM items'
        self.cur.execute(sql)
        results = self.cur.fetchall()
        return results


    def add_item_to_item_tracker(self, wow_item_id, item_name):
        sql_statement = 'INSERT INTO items VALUES(?, ?, ?)'
        values = (None, wow_item_id, item_name)
        try:
            self.cur.execute(sql_statement, values)
        except sqlite3.IntegrityError as e:
            print(f'Error occurred during add_item_to_item_tracker\nerror: {e}\nItem {item_name},ID {wow_item_id}')
        self.conn.commit()

    def get_item_id_from_name(self, item_name):
        statement = ('SELECT wow_itemid FROM items WHERE item_name = ?')
        values = (item_name,)
        self.cur.execute(statement, values)
        data = self.cur.fetchall()
        return data[0][0]

    def get_item_name_from_id(self,id):
        statement = ('SELECT item_name FROM items WHERE wow_itemid = ?')
        values = (id,)
        self.cur.execute(statement, values)
        data = self.cur.fetchall()
        return data

# PLAYER QUERIES

    def get_count_players(self):
        sql = 'SELECT count(*) FROM players'
        self.cur.execute(sql)
        results = self.cur.fetchall()
        return results


    def add_player(self, name, rank, level, wow_class, race):
        sql = 'INSERT INTO players VALUES(?, ?, ?, ?, ?, ?)'
        values = (None, name, rank, level, wow_class, race)
        self.cur.execute(sql, values)
        self.conn.commit()

    def get_playerid_from_name(self, name):
        statement = 'SELECT sql_id FROM players WHERE name = ?'
        values = (name,)
        self.cur.execute(statement, values)
        data = self.cur.fetchall()
        return data[0][0]

    def get_playername_from_id(self, id):
        statement = 'SELECT name FROM players WHERE sql_id = ?'
        values = (id,)
        self.cur.execute(statement, values)
        data = self.cur.fetchall()
        return data[0][0]

# LOOT RECORD QUERIES

    def insert_loot_record(self, item_id, winner_id, date, softres, offspec):
        insert_statement = ('INSERT INTO loot_record VALUES(?, ?, ?, ?, ?, ?)')
        values = (None, item_id, winner_id, date, softres, offspec)
        self.cur.execute(insert_statement, values)
        self.conn.commit()

