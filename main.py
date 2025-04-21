#!/usr/bin/env python3

#
from datetime import datetime
from time import sleep
import csv
import os
import shutil
import re
import sys
from db_funcs import LootTracker

today = datetime.today().strftime('%Y%m%d_%H%M%S')

def main():
    print('Beginning setup')
    db = LootTracker()
    print('Setup finished')
    while True:
        print('MENU:')
        print('(update_roster) | (raid_loot) | (exit)')
        print("(guild_movement)")
        user_choice = input(str("input > "))
        if user_choice.lower() == 'raid_loot':
            submit_loot_log(db)
        elif user_choice.lower() == 'exit':
            sys.exit(3)
        elif user_choice.lower() == 'guild_movement':
            input_file = 'guild_log.csv'
            if input_file in os.listdir(os.getcwd()):
                with open(os.getcwd()+'/'+input_file,'r',encoding='utf-8') as f:
                    reader=csv.reader(f)
                    data = list(reader)[::-1]  # [::-1] reverses the order of the csv
                guild_movement(db, data)
            else:
                print(f'{input_file} does not exist!')
                sleep(2)
                continue
        else:
            print('invalid entry, try again')
            continue

def submit_loot_log(db):
    input_file = str(input("Path to input file: "))
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        logs = list(reader)

    for index, value in enumerate(logs):
        date, winner, item_id, soft_res, checksum = value
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
            db.insert_loot_record(date, winner_id, item_id, soft_res, checksum)
        except Exception as e:
            print(f"Exception occurred: {e}")
            print(f'The offending line was: Line +- 1 of {index}, record was: {value}')

        if winner == '_disenchanted':
            print(f'{item_name} was disenchanted on {loot_date}. Lame.')
        else:
            print(f'{winner} won {item_name} on {loot_date}! Hooray!')


    shutil.move(input_file, f'/var/secondmains_logs/loot_logs/{today}_lootlog.csv')
def guild_movement(db, data_movement_log):
    """
    :param db: the database object.
    :param data_movement_log: This is the guild_log.csv. copy and paste from the GRM mod in wow.
    :return:
    """
    join_guild_player_list = sorted([i[0] for i in db.get_all_players()])
    guilded_players = db.get_guilded_players()
    for i in data_movement_log:

        if 'has JOINED the guild!' in i[0]:
            # joined guild
            guilded_players = db.get_guilded_players()

            action = 'join_guild'
            action_id = db.get_guild_action_id_from_name(action)[0][0]

            pattern = r'([0-9]{4}-[0-9]{2}-[0-9]{2}) [0-9]{2}:[0-9]{2} : (\w+) has JOINED the guild! \(LVL: ([0-9]+)\) - Invited By: (\w+)'
            date, person_joined, level, officer_name = re.findall(pattern, i[0])[0]

            if person_joined not in join_guild_player_list:
                db.add_player(person_joined, 'Second Main', level, None, None, officer_name, None, None, None)
                db.insert_guild_movement(action_id, person_joined, date)
            else:
                continue

        elif 'has Left the guild' in i[0]:
            # gquit
            action = 'gquit'
            action_id = db.get_guild_action_id_from_name(action)[0][0]

            pattern = r'[0-9]{1,}\) ([0-9]{4}-[0-9]{2}-[0-9]{2}) [0-9]{2}:[0-9]{2} : (\S+) has Left the guild.*'
            date, player_who_left = re.findall(pattern, i[0])[0]
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
            date, officer_name, player_kicked = re.findall(pattern, i[0])[0]

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
            print(re.findall(pattern, i[0]))
            date, time, player, level = re.findall(pattern, i[0])[0]
            try:
                player_id = db.get_playerid_from_name(player)
            except IndexError:
                db.add_player(player, None, None, None, None, None, None, None, None, None)
                player_id = db.get_playerid_from_name(player)
            db.update_player_level_in_guild_roster(level, player_id)
            db.insert_into_level_log(date,time,player_id,level)
            # print(f'{player.title()} has reached level {level}')

        elif 'Level Cap!' in i[0]:
            #reached level cap
            pattern = r'^[0-9]{1,}\) ([0-9]{4}-[0-9]{2}-[0-9]{2}) ([0-9]{2}:[0-9]{2}) : (\S+) has Reached the ([0-9]{1,}) Level Cap!'
            date, time, player_name, level = re.findall(pattern, i[0])[0]
            try:
                player_id = db.get_playerid_from_name(player_name)
            except IndexError:
                db.add_player(player_name, None, None, None, None, None, None, None, None, None)
                player_id = db.get_playerid_from_name(player_name)
            db.update_player_level_in_guild_roster(level, player_id)
            db.insert_into_level_log(date, time, player_id, level)

        elif 'PROMOTED' in i[0] or 'DEMOTED' in i[0]:
            # promoted or #demoted
            pattern = r'^[0-9]{1,}\) ([0-9]{4}-[0-9]{2}-[0-9]{2}) [0-9]{2}:[0-9]{2} : (\S+) (?:has been )?(PROMOTED|DEMOTED) (\S+) from (.+?) to (.+?)$'

            try:
                date, officer, action, player_name, old_rank, new_rank = re.findall(pattern, i[0])[0]
            except IndexError as e:
                print('error occurred ', e)
                continue #TODO should come back and revisit.

            try:
                player_id = db.get_playerid_from_name(player_name)
            except IndexError:
                db.add_player(player_name, None, None, None, None, None, None, None, None, None)
                player_id = db.get_playerid_from_name(player_name)
            officer_id = db.get_playerid_from_name(officer)
            db.update_guild_rank(player_id, new_rank)
            db.insert_rank_change(player_id, officer_id, action.lower(), old_rank, new_rank, date)

        elif 'public note' in i[0].lower():
            #public note set
            set_pattern = r'''^[0-9]{1,}\) ([0-9]{4}-[0-9]{2}-[0-9]{2}) [0-9]{2}:[0-9]{2} : (\S+)'s PUBLIC Note: "(\S+)" was Added'''
            removed_pattern = r'''^[0-9]{1,}\) ([0-9]{4}-[0-9]{2}-[0-9]{2}) [0-9]{2}:[0-9]{2} : (\S+)'s PUBLIC Note: "(\S+)" was Removed'''

            if re.search(set_pattern, i[0]):
                action = 'public_note_set'
                action_id = db.get_guild_action_id_from_name(action)[0][0]
                # pattern  = r'''^[0-9]{1,}\) ([0-9]{4}-[0-9]{2}-[0-9]{2}) [0-9]{2}:[0-9]{2} : (\S+)'s PUBLIC Note: "(\S+)" was Added'''
                date, guild_mate, new_note = re.findall(set_pattern, i[0])[0]
            elif re.search(removed_pattern, i[0]):
                action = 'public_note_removed'
                action_id = db.get_guild_action_id_from_name(action)[0][0]
                # pattern  = r'''^[0-9]{1,}\) ([0-9]{4}-[0-9]{2}-[0-9]{2}) [0-9]{2}:[0-9]{2} : (\S+)'s PUBLIC Note: "(\S+)" was Added'''
                date, guild_mate, new_note = re.findall(removed_pattern, i[0])[0]
            else:
                continue

            if guild_mate not in guilded_players:
                try:
                    db.quick_add_player(guild_mate)
                except db.IntegrityError as e:
                    print(f'ERROR OCCURRED: {e}')

            db.update_public_note(guild_mate, new_note)
            db.insert_guild_movement(action_id, guild_mate, date)

        elif 'officer note' in i[0].lower():
            add_pattern = r'''^[ 0-9]{1,}\) ([0-9]{4}-[0-9]{2}-[0-9]{2}) [0-9]{2}:[0-9]{2} : (\S+)'s OFFICER Note: "(\S+)" was Added'''
            remove_pattern = r'''^[0-9]{1,}\) ([0-9]{4}-[0-9]{2}-[0-9]{2}) [0-9]{2}:[0-9]{2} : (\S+)'s OFFICER Note: "(\S+)" was Removed'''
            action = 'officer_note_set'
            action_id = db.get_guild_action_id_from_name(action)[0][0]

            #officer_note_set
            if re.search(add_pattern, i[0]):
                date, guild_mate, new_note = re.findall(add_pattern, i[0])[0]
            #officer_note_removed
            elif re.search(remove_pattern, i[0]):
                date, guild_mate, new_note = re.findall(remove_pattern, i[0])[0]
            else:
                continue

            if guild_mate not in guilded_players:
                try:
                    db.quick_add_player(guild_mate)
                except db.IntegrityError as e:
                    print(f'ERROR OCCURRED: {e}')

            db.update_officer_note(guild_mate, new_note)
            db.insert_guild_movement(action_id, guild_mate, date)

        elif 'custom note' in i[0].lower():
            #custom_note_set
            action = 'custom_note_set'
            action_id = db.get_guild_action_id_from_name(action)[0][0]
            set_pattern  = r'''^[0-9]{1,}\) ([0-9]{4}-[0-9]{2}-[0-9]{2}) [0-9]{2}:[0-9]{2} : (\S+) modified (\S+)'s CUSTOM Note: "(\S+)" was Added'''
            remove_pattern = r'''^[0-9]{1,}\) ([0-9]{4}-[0-9]{2}-[0-9]{2}) [0-9]{2}:[0-9]{2} : (\S+) modified (\S+)'s CUSTOM Note: "(\S+)" was Removed'''

            if re.search(set_pattern, i[0]):
                date, officer_name, guild_mate, new_note = re.findall(set_pattern, i[0])[0]
            elif re.search(remove_pattern, i[0]):
                date, officer_name, guild_mate, new_note = re.findall(remove_pattern, i[0])[0]
            else:
                continue

            if guild_mate not in guilded_players:
                try:
                    db.quick_add_player(guild_mate)
                except db.IntegrityError as e:
                    print(f'ERROR OCCURRED: {e}')

            db.update_custom_note(guild_mate, new_note)
            db.insert_guild_movement(action_id, guild_mate, date)

        elif 'BANNED' in i[0].lower():
            # banned
            pass #TODO

        elif 'REINVITED' in i[0].lower():
            pass #TODO

    # Last step, move the log file out.
    shutil.move(os.getcwd()+'/guild_log.csv',f'/tmp/{today}_guild_log.csv')
    print('end of guild_movement')


def _format_date_into_datetime(date_string):
    # returns a datetime object - "Day of Week, Day Month Year"
    return datetime.strptime(date_string, '%Y-%m-%d').strftime('%A, %d %B %Y')


if __name__ == '__main__':
    main()
