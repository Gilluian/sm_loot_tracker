# db_funcs.py

# handles the database functions that the item tracker will utilize.

import sqlite3
from sqlite3 import IntegrityError   # this may not be used in db_funcs, but it's used elsewhere. Don't delete me despite what pylint bitches about.
import csv
from time import sleep


class LootTracker:
    def __init__(self):
        self.conn = sqlite3.connect('item_tracker_dev.db')
        self.cur = self.conn.cursor()

        self.cur.execute('''CREATE TABLE IF NOT EXISTS items(
                        sql_itemid INTEGER PRIMARY KEY AUTOINCREMENT,
                        wow_itemid INTEGER UNIQUE,
                        item_name TEXT
                        );''')
        self.cur.execute('''CREATE TABLE IF NOT EXISTS players(
                        sql_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE,
                        guild_rank TEXT,
                        level INTEGER,
                        class TEXT,
                        race TEXT,
                        invited_by TEXT,
                        public_note TEXT,
                        officer_note TEXT,
                        custom_note TEXT,
                        main_flag INTEGER,
                        alts TEXT
                        );''')

        self.cur.execute('''CREATE TABLE IF NOT EXISTS loot_record(
                        sql_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT,
                        winner_id INTEGER REFERENCES players(sql_id) ON DELETE CASCADE,
                        item_id INTEGER NOT NULL REFERENCES items(wow_item_id) ON DELETE CASCADE,
                        soft_res INTEGER,
                        checksum INTEGER
                        );''')
        #               1 = true, 0 = false. 1 it was softressed or an offspec roll, 0 it wasn't.

        self.cur.execute('''CREATE TABLE IF NOT EXISTS guild_movement(
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        player_id INTEGER REFERENCES players(sql_id) ON DELETE CASCADE,
                        action_id INTEGER REFERENCES guild_actions(id) ON DELETE CASCADE,
                        date TEXT 
                        );''')

        self.cur.execute('''CREATE TABLE IF NOT EXISTS guild_actions(
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        action_name TEXT 
                        );''')

        self.cur.execute('''CREATE TABLE IF NOT EXISTS level_log(
                        sql_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        player_id INTEGER REFERENCES players(sql_id) ON DELETE CASCADE,
                        level INTEGER,
                        date TEXT,
                        time TEXT
                        );''')

        self.cur.execute('''CREATE TABLE IF NOT EXISTS rank_changes(
                        sql_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        player_id INTEGER REFERENCES players(sql_id) ON DELETE CASCADE,
                        officer_id INTEGER REFERENCES players(sql_id) ON DELETE CASCADE,
                        action TEXT,
                        old_rank TEXT,
                        new_rank TEXT,
                        date TEXT
                        );''' )

        try:
            self.cur.execute('''CREATE VIEW last_raid AS
                        SELECT p.name, p.race, p.class, i.item_name, lr.date
                        FROM loot_record lr
                        INNER JOIN players p ON lr.winner_id = p.sql_id
                        INNER JOIN items i ON lr.item_id = i.wow_itemid
                        WHERE lr.date = (SELECT max(date) from loot_record)
                        AND p.name != '_disenchanted'
                        AND guild_rank IS NOT NULL;
                      ''')
        except sqlite3.OperationalError as e:
            print(e)

        try:
            self.cur.execute('''CREATE VIEW last_raid_disenchanted AS
                        SELECT i.item_name, lr.date
                        FROM loot_record lr
                        INNER JOIN players p ON lr.winner_id = p.sql_id
                        INNER JOIN items i ON lr.item_id = i.wow_itemid
                        WHERE lr.date = (SELECT max(date) from loot_record)
                        AND p.name = '_disenchanted';
                      ''')
        except sqlite3.OperationalError as e:
            print(e)
        try:
            self.cur.execute('''CREATE VIEW last_raid_pug AS
                        SELECT p.name, i.item_name, lr.date
                        FROM loot_record lr
                        INNER JOIN players p ON lr.winner_id = p.sql_id
                        INNER JOIN items i ON lr.item_id = i.wow_itemid
                        WHERE lr.date = (SELECT max(date) from loot_record)
                        AND p.name != '_disenchanted'
                        AND guild_rank IS NULL;
                      ''')
        except sqlite3.OperationalError as e:
            print(e)

        self.initial_startup()

    def __del__(self):
        self.cur.execute('''DROP VIEW IF EXISTS last_raid;''')
        self.cur.execute('''DROP VIEW IF EXISTS last_raid_disenchanted;''')
        self.cur.execute('''DROP VIEW IF EXISTS last_raid_pug''')
        self.conn.close()

    def initial_startup(self):
        # if the players table is empty.
        if self.get_count_players()[0][0] == 0:
            print('Looks like this is the initial startup. Adding guildmates.')
            sleep(1)
            with open('guild_roster.csv', 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                roster = list(reader)

            self.quick_add_player('_disenchanted')
            for i in roster:
                print(i)
                name, rank, level, wow_class, race, main_flag, alts, public_note, officer_note, custom_note = i
                if public_note == '':
                    public_note = None
                if officer_note == '':
                    officer_note = None
                if custom_note == '':
                    custom_note = None

                if main_flag == 'Main':
                    main_flag = 1
                elif main_flag == 'Alt':
                    main_flag = 0
                else:
                    continue

                #self.add_player(name,rank,level,wow_class,race, None, public_note, officer_note, custom_note)
                self._guild_add_character_initial_startup(name, rank, level, wow_class, race, main_flag, alts, public_note, officer_note, custom_note)
        # if the items table is empty.
        if self.get_count_items()[0][0] == 0:
            print('Looks like initial startup. Adding items')
            sleep(1)
            with open('items.csv','r',encoding='utf-8') as f:
                reader = csv.reader(f)
                items = list(reader)
            print("Adding items to db.")
            self.initial_item_load(items)

        # If guild actions is empty, fill the table
        if self.get_guild_actions()[0][0]==0:

            actions = ['join_guild', 'gquit', 'gkick',
                   'level_up', 'reached_level_cap', 'promoted', 'demoted',
                   'public_note_set', 'officer_note_set', 'custom_note_set',
                   'banned','public_note_removed','officer_note_removed','custom_note_removed']
            for i in actions:
                statement = '''INSERT INTO guild_actions VALUES(?, ?)'''
                values = (None, i)
                self.cur.execute(statement, values)
            self.conn.commit()

# ITEM QUERIES
    def initial_item_load(self, list_of_items):
        """
        :param list_of_items: I want a list of lists that has the full item list of lists.
        each element will/should be [[item_id, item_name],[item2_id, item2_name]] etc.
        :return:
        """
        for i in list_of_items:
            assert len(i)==2
            statement = 'INSERT INTO items VALUES(?, ?, ?)'
            values = (None, i[0],i[1])
            try:
                self.cur.execute(statement, values)
            except sqlite3.IntegrityError as e:
                pass
                # print(f'Tried inserting {i}, received error: ', e)
        self.conn.commit()

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
        statement = 'SELECT wow_itemid FROM items WHERE item_name = ?'
        values = (item_name,)
        self.cur.execute(statement, values)
        data = self.cur.fetchall()
        return data[0][0]

    def get_item_name_from_id(self,id):
        statement = 'SELECT item_name FROM items WHERE wow_itemid = ?'
        values = (id,)
        self.cur.execute(statement, values)
        data = self.cur.fetchall()
        return data

# PLAYER/GUILD QUERIES

    def update_public_note(self, name, note):
        query = '''UPDATE players SET public_note = ? WHERE name = ?'''
        values = (note, name)
        self.cur.execute(query, values)
        self.conn.commit()

    def update_officer_note(self, name, note):
        query = '''UPDATE players SET officer_note = ? WHERE name = ?'''
        values = (note, name)
        self.cur.execute(query, values)
        self.conn.commit()

    def update_custom_note(self, name, note):
        query = '''UPDATE players SET custom_note = ? WHERE name = ?'''
        values = (note, name)
        self.cur.execute(query, values)
        self.conn.commit()


    def insert_rank_change(self, playerid, officerid, action, old_rank, new_rank, date):
        statement = '''INSERT INTO rank_changes VALUES(?,?,?,?,?,?,?)'''
        values = (None, playerid, officerid, action, old_rank, new_rank, date)
        self.cur.execute(statement,values)
        self.conn.commit()

    def quick_add_player(self, name):
        query = '''INSERT INTO players(name) VALUES(?)'''
        values = (name,)
        self.cur.execute(query,values)
        self.conn.commit()

    def get_guilded_players(self):
        self.cur.execute('''SELECT name FROM players WHERE guild_rank IS NOT NULL ORDER BY name''')
        return [name[0] for name in self.cur.fetchall()]

    def get_all_players(self):
        sql = '''SELECT name FROM players;'''
        self.cur.execute(sql)
        data = self.cur.fetchall()
        return data

    def get_count_players(self):
        sql = 'SELECT count(*) FROM players'
        self.cur.execute(sql)
        results = self.cur.fetchall()
        return results

        #eww gross you getting refactored,bud.
    def add_player(self, name, rank, level, wow_class, race, invited_by, public_note, officer_note, custom_note):
        sql = 'INSERT INTO players VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
        values = (None, name, rank, level, wow_class, race, invited_by, public_note, officer_note, custom_note)
        self.cur.execute(sql, values)
        self.conn.commit()


    def get_playerid_from_name(self, name):
        statement = 'SELECT sql_id FROM players WHERE name = ?'
        values = (name,)
        self.cur.execute(statement, values)
        data = self.cur.fetchall()
        return data[0][0]

    def get_playername_from_id(self, player_id):
        statement = 'SELECT name FROM players WHERE sql_id = ?'
        values = (player_id,)
        self.cur.execute(statement, values)
        data = self.cur.fetchall()
        return data[0][0]


    def update_player_level_in_guild_roster(self, level, playerid):
        update_player = '''UPDATE players SET level = ? WHERE sql_id = ?'''
        values = (level, playerid)
        self.cur.execute(update_player, values)
        self.conn.commit()

    def _guild_add_character_initial_startup(self, name, rank, level, wow_class, race, main_flag, alts, public_note, officer_note, custom_note):
        # plan for this is a temporary function. Add player sucks dick so gonna use this instead for now.
        query = '''INSERT INTO players(name, guild_rank, level, class, race, main_flag, alts, public_note, officer_note, custom_note)
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
        values = (name, rank, level, wow_class, race, main_flag, alts, public_note, officer_note, custom_note)
        self.cur.execute(query, values)
        self.conn.commit()

# LOOT RECORD QUERIES

    def insert_loot_record(self, date, winner_id, item_id, softres, checksum):
        insert_statement = 'INSERT INTO loot_record VALUES(?, ?, ?, ?, ?, ?)'
        values = (None, date, winner_id, item_id, softres, checksum)
        self.cur.execute(insert_statement, values)
        self.conn.commit()

# GUILD MOVEMENT

    def lookup_movements_by_name(self, player_name):
        player_id = self.get_playerid_from_name(player_name)

        query = ('''SELECT p.name, gm.action, gm.date FROM guild_movement gm
                 INNER JOIN players p ON gm.player_id = p.sql_id
                 WHERE gm.player_id = ?;''')
        values = (player_id,)
        self.cur.execute(query, values)
        results = self.cur.fetchall()
        return results

    def remove_from_guild(self, player_name):
        statement = '''UPDATE players SET guild_rank = NULL WHERE name = ?'''
        values = (player_name,)
        self.cur.execute(statement,values)
        self.conn.commit()

    def update_guild_rank(self, player_id, new_rank):
        statement = '''UPDATE players SET guild_rank = ? WHERE sql_id = ?'''
        values = (new_rank, player_id)
        self.cur.execute(statement, values)
        self.conn.commit()

# GUILD ACTIONS
    def get_guild_actions(self):
        sql = 'SELECT count(*) FROM guild_actions'
        self.cur.execute(sql)
        results = self.cur.fetchall()
        return results

    def get_guild_action_id_from_name(self, guild_action):
        statement = 'SELECT id FROM guild_actions WHERE action_name = ?'
        values = (guild_action,)
        self.cur.execute(statement, values)
        results = self.cur.fetchall()
        return results

    def insert_guild_movement(self, action_id, name, date):
        player_id = self.get_playerid_from_name(name)
        statement =  'INSERT INTO guild_movement VALUES(?, ?, ?, ?);'
        values = (None, player_id, action_id, date)
        self.cur.execute(statement, values)
        self.conn.commit()

# LEVEL LOG COMMANDS
    def insert_into_level_log(self, date, time, player_id, level):
        statement = '''INSERT INTO level_log VALUES(?, ?, ?, ?, ?)'''
        values = (None, player_id, level, date, time)
        self.cur.execute(statement,values)
        self.conn.commit()
