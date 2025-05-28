# !/usr/bin/env python3

from datetime import datetime
from csv import reader
from os import listdir, environ
from os import name as os_name
from shutil import move as move_file
from re import findall, search
from sys import exit as sysexit
from db_funcs import LootTracker
from sqlite3 import IntegrityError
import json

today = datetime.today().strftime('%Y%m%d_%H%M%S')

if os_name == 'nt':
    environ['loot_log_input_file'] = r'E:\python_projects\sm_loot_tracker\lootlog.csv'
    environ['guild_log_input_file'] = r'E:\python_projects\sm_loot_tracker\guild_log.csv'
    environ['LOOT_LOG_LOCATION'] = r'E:\second_mains\loot_logs\lootlog_master.csv'
    environ['master_guildMovementLog_location'] = r'E:\second_mains\guild_movement_logs\guild_movement_log.csv'
    environ['loot_log_temp'] = r'C:\Users\Public\second_mains\logs\loot_logs\\'
    environ['guild_log_temp'] = r'C:\Users\Public\second_mains\logs\guild_movement_logs\\'
elif os_name == 'posix':
    environ['loot_log_input_file'] = r'/mnt/e/python_projects/sm_loot_tracker/lootlog.csv'
    environ['guild_log_input_file'] = r'/mnt/e/python_projects/sm_loot_tracker/guild_log.csv'
    environ['LOOT_LOG_LOCATION'] = r'/mnt/e/second_mains/loot_logs/lootlog_master.csv'
    environ['master_guildMovementLog_location'] = r'/mnt/e/second_mains/guild_movement_logs/guild_movement_log.csv'
    environ['loot_log_temp'] = r'/mnt/c/users/public/second_mains/logs/loot_logs/'
    environ['guild_log_temp'] = r'/mnt/c/users/public/second_mains/logs/guild_movement/'
else:
    print('OS not recognized. Exiting.')
    sysexit(3)

def main():
    db = LootTracker()
    # If the loot log file exists:
    if 'lootlog.csv' in listdir():
        submit_loot_log(db)
    if 'guild_log.csv' in listdir():
        with open('guild_log.csv', 'r', encoding='utf-8') as f:
             readercsv = reader(f)
             data = list(readercsv)[::-1]  # [::-1] reverses the order of the csv
        guild_movement(db, data)

def submit_loot_log(db):
    with open(environ['loot_log_input_file'], 'r', encoding='utf-8') as f:
        readercsv = reader(f)
        logs = list(readercsv)
        # Append the loot log to the master file
        with open(environ['LOOT_LOG_LOCATION'], 'a', encoding='utf-8') as lootlog_output:
            for i in logs:
                lootlog_output.write(','.join(i))
                lootlog_output.write('\n')

    for index, value in enumerate(logs):
        date, winner, item_id, off_spec, checksum = value
        item_name = db.get_item_name_from_id(item_id)[0][0]
        loot_date = _format_date_into_datetime(date)
        try:
            winner_id = db.get_playerid_from_name(winner)
        except IndexError as e:
            print(e)
            db.quick_add_player(winner)
            winner_id = db.get_playerid_from_name(winner)
            print(winner, 'was not in the database. Added.')

        try:
            db.insert_loot_record(date, winner_id, item_id, off_spec, checksum)
        except Exception as e:
            pass
            # TODO  When logging is added, we need to log this! checksum must be unique
            # print(f"Exception occurred: {e}")
            # print(f'Line {index}, record was: {value}')

        # if winner == '_disenchanted':
        #     print(f'{item_name} was disenchanted on {loot_date}. Lame.')
        # else:
        #     print(f'{winner} won {item_name} on {loot_date}! Hooray!')

    # End, move the log file out of the working directory and into the log
    move_file(environ['loot_log_input_file'], environ['loot_log_temp'] + rf'\{today}_lootlog.csv')

def guild_movement(db, data_movement_log):
    """
    :param db: the database object.
    :param data_movement_log: This is the guild_log.csv. copy and paste from the GRM mod in wow.
    :return:
    """
    # append the data file into the guild movement master file
    append_log_to_csv(environ['master_guildMovementLog_location'], data_movement_log)

    join_guild_player_list = sorted([i[0] for i in db.get_all_players()])
    guilded_players = db.get_guilded_players()
    for i in data_movement_log:

        if 'has JOINED the guild!' in i[0]:
            # joined guild
            guilded_players = db.get_guilded_players()

            action = 'join_guild'
            action_id = db.get_guild_action_id_from_name(action)[0][0]

            pattern = r'([0-9]{4}-[0-9]{2}-[0-9]{2}) [0-9]{2}:[0-9]{2} : (\w+) has JOINED the guild! \(LVL: ([0-9]+)\) - Invited By: (\w+)'
            date, person_joined, level, officer_name = findall(pattern, i[0])[0]

            if person_joined not in join_guild_player_list:
                db.quick_add_player(person_joined)
                db.insert_guild_movement(action_id, person_joined, date)
            else:
                continue

        elif 'has Left the guild' in i[0]:
            # gquit
            action = 'gquit'
            action_id = db.get_guild_action_id_from_name(action)[0][0]

            pattern = r'[0-9]{1,}\) ([0-9]{4}-[0-9]{2}-[0-9]{2}) [0-9]{2}:[0-9]{2} : (\S+) has Left the guild.*'
            date, player_who_left = findall(pattern, i[0])[0]
            if player_who_left in guilded_players:
                # remove from guild
                db.remove_from_guild(player_who_left)
                # Add entry to guild movement
                db.insert_guild_movement(action_id, player_who_left, date)
            else:
                continue

        elif 'KICKED' in i[0]:
            # gkick
            action = 'gkick'
            action_id = db.get_guild_action_id_from_name(action)[0][0]

            pattern = r'[0-9]{1,}\) ([0-9]{4}-[0-9]{2}-[0-9]{2}) [0-9]{2}:[0-9]{2} : (\S+) KICKED (\S+) from the Guild!*'
            date, officer_name, player_kicked = findall(pattern, i[0])[0]

            if player_kicked in guilded_players:
                # remove from guild
                db.remove_from_guild(player_kicked)
                # Add entry to guild movement
                db.insert_guild_movement(action_id, player_kicked, date)
            else:
                continue

        elif 'has Leveled to' in i[0]:
            #level up
            # update guild roster, insert into level log
            pattern = r'\d+\) (\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) : (\S+)(?: \(\S+\))?(?: \([^)]+\))? has Leveled to (\d+) \(\+\d+ level[s]?\),?'
            date, time, player, level = findall(pattern, i[0])[0]
            try:
                player_id = db.get_playerid_from_name(player)
            except IndexError:
                db.quick_add_player(player)
                player_id = db.get_playerid_from_name(player)
            db.update_player_level_in_guild_roster(level, player_id)
            db.insert_into_level_log(date,time,player_id,level)
            # print(f'{player.title()} has reached level {level}')

        elif 'Level Cap!' in i[0]:
            #reached level cap
            pattern = r'^[0-9]{1,}\) ([0-9]{4}-[0-9]{2}-[0-9]{2}) ([0-9]{2}:[0-9]{2}) : (\S+) .+ has Reached the ([0-9]{1,}) Level Cap!'
            date, time, player_name, level = findall(pattern, i[0])[0]
            try:
                player_id = db.get_playerid_from_name(player_name)
            except IndexError:
                db.quick_add_player(player_name)
                player_id = db.get_playerid_from_name(player_name)
            db.update_player_level_in_guild_roster(level, player_id)
            db.insert_into_level_log(date, time, player_id, level)

        elif 'PROMOTED' in i[0] or 'DEMOTED' in i[0]:
            # promoted or #demoted
            pattern = r'^[0-9]{1,}\) ([0-9]{4}-[0-9]{2}-[0-9]{2}) [0-9]{2}:[0-9]{2} : (\S+) (?:has been )?(PROMOTED|DEMOTED) (\S+) from (.+?) to (.+?)$'

            try:
                date, officer, action, player_name, old_rank, new_rank = findall(pattern, i[0])[0]
            except IndexError as e:
                print('error occurred ', e)
                continue

            try:
                player_id = db.get_playerid_from_name(player_name)
            except IndexError:
                db.quick_add_player(player_name)
                player_id = db.get_playerid_from_name(player_name)
            officer_id = db.get_playerid_from_name(officer)
            db.update_guild_rank(player_id, new_rank)
            db.insert_rank_change(player_id, officer_id, action.lower(), old_rank, new_rank, date)

        elif 'public note' in i[0].lower():
            #public note set
            set_pattern = r'''^[0-9]{1,}\) ([0-9]{4}-[0-9]{2}-[0-9]{2}) [0-9]{2}:[0-9]{2} : (\S+)'s PUBLIC Note: "(\S+)" was Added'''
            removed_pattern = r'''^[0-9]{1,}\) ([0-9]{4}-[0-9]{2}-[0-9]{2}) [0-9]{2}:[0-9]{2} : (\S+)'s PUBLIC Note: "(\S+)" was Removed'''

            if search(set_pattern, i[0]):
                action = 'public_note_set'
                action_id = db.get_guild_action_id_from_name(action)[0][0]
                # pattern  = r'''^[0-9]{1,}\) ([0-9]{4}-[0-9]{2}-[0-9]{2}) [0-9]{2}:[0-9]{2} : (\S+)'s PUBLIC Note: "(\S+)" was Added'''
                date, guild_mate, new_note = findall(set_pattern, i[0])[0]
            elif search(removed_pattern, i[0]):
                action = 'public_note_removed'
                action_id = db.get_guild_action_id_from_name(action)[0][0]
                # pattern  = r'''^[0-9]{1,}\) ([0-9]{4}-[0-9]{2}-[0-9]{2}) [0-9]{2}:[0-9]{2} : (\S+)'s PUBLIC Note: "(\S+)" was Added'''
                date, guild_mate, new_note = findall(removed_pattern, i[0])[0]
            else:
                continue

            if guild_mate not in guilded_players:
                try:
                    db.quick_add_player(guild_mate)
                except IntegrityError as e:
                    print(f'ERROR OCCURRED: {e}')

            db.update_public_note(guild_mate, new_note)
            db.insert_guild_movement(action_id, guild_mate, date)

        elif 'officer note' in i[0].lower():
            add_pattern = r'''^[ 0-9]{1,}\) ([0-9]{4}-[0-9]{2}-[0-9]{2}) [0-9]{2}:[0-9]{2} : (\S+)'s OFFICER Note: "(\S+)" was Added'''
            remove_pattern = r'''^[0-9]{1,}\) ([0-9]{4}-[0-9]{2}-[0-9]{2}) [0-9]{2}:[0-9]{2} : (\S+)'s OFFICER Note: "(\S+)" was Removed'''
            action = 'officer_note_set'
            action_id = db.get_guild_action_id_from_name(action)[0][0]

            #officer_note_set
            if search(add_pattern, i[0]):
                date, guild_mate, new_note = findall(add_pattern, i[0])[0]
            #officer_note_removed
            elif search(remove_pattern, i[0]):
                date, guild_mate, new_note = findall(remove_pattern, i[0])[0]
            else:
                continue

            if guild_mate not in guilded_players:
                try:
                    db.quick_add_player(guild_mate)
                except IntegrityError as e:
                    print(f'ERROR OCCURRED IN OFFICER NOTE - IntegrityError: {e}')

            db.update_officer_note(guild_mate, new_note)
            db.insert_guild_movement(action_id, guild_mate, date)

        elif 'custom note' in i[0].lower():
            #custom_note_set
            action = 'custom_note_set'
            action_id = db.get_guild_action_id_from_name(action)[0][0]
            set_pattern  = r'''^[0-9]{1,}\) ([0-9]{4}-[0-9]{2}-[0-9]{2}) [0-9]{2}:[0-9]{2} : (\S+) modified (\S+)'s CUSTOM Note: "(\S+)" was Added'''
            remove_pattern = r'''^[0-9]{1,}\) ([0-9]{4}-[0-9]{2}-[0-9]{2}) [0-9]{2}:[0-9]{2} : (\S+) modified (\S+)'s CUSTOM Note: "(\S+)" was Removed'''

            if search(set_pattern, i[0]):
                date, officer_name, guild_mate, new_note = findall(set_pattern, i[0])[0]
            elif search(remove_pattern, i[0]):
                date, officer_name, guild_mate, new_note = findall(remove_pattern, i[0])[0]
            else:
                continue

            if guild_mate not in guilded_players:
                try:
                    db.quick_add_player(guild_mate)
                except db.IntegrityError as e:
                    print(f'ERROR OCCURRED: {e}')

            db.update_custom_note(guild_mate, new_note)
            db.insert_guild_movement(action_id, guild_mate, date)

        elif 'REINVITED' in i[0].lower():
            pattern = r'''^[0-9]{1,}\) ([0-9]{4}-[0-9]{2}-[0-9]{2}) [0-9]{2}:[0-9]{2} : \S+ has REINVITED (\S+) to the guild \(LVL: ([0-9]{1,})\)'''
            action = 'reinvited'
            action_id = db.get_guild_action_id_from_name(action)[0][0]

            date, player, level = findall(pattern, i[0])[0]
            player_id = db.get_playerid_from_name(player)

            db.update_guild_rank(player_id, 'Second Main')
            db.insert_guild_movement(action_id, player, date)

    # Last step, move the log file out
    move_file(environ['guild_log_input_file'], environ['guild_log_temp'] + rf'{today}_guild_movement_log.csv')
    print('end of guild_movement')


def _format_date_into_datetime(date_string):
    # returns a datetime object - "Day of Week, Day Month Year"
    # Only used in the terminal when the loot log is parsed.
    return datetime.strptime(date_string, '%Y-%m-%d').strftime('%A, %d %B %Y')

def append_log_to_csv(file_location, data_in):
    """
    :param file_location: the file to write to.
    :return:
    """
    with open(file_location, 'a', encoding='utf-8') as f:
        for i in data_in:
            f.write(','.join(i))
            f.write('\n')


if __name__ == '__main__':
    main()
