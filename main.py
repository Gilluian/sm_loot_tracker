# main.py
#
import csv, os, shutil, re
from datetime import datetime
from db_funcs import LootTracker
from time import sleep


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
        if user_choice.lower() == 'update_roster':
            update_guild_roster()
        elif user_choice.lower() == 'raid_loot':
            submit_loot_log(db)
        elif user_choice.lower() == 'exit':
            exit(3)
        elif user_choice.lower() == 'guild_movement':
            if 'guild_log.csv' in os.listdir(os.getcwd()+'\\guild_roster'):
                with open(os.getcwd()+'\\guild_roster\\guild_log.csv','r',encoding='utf-8') as f:
                    reader=csv.reader(f)
                    data = list(reader)[::-1]  # [::-1] reverses the order of the csv
                guild_movement(db, data)
            else:
                print('/guild_roster/guild_log.csv does not exist')
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
        try:
            winner_id = db.get_playerid_from_name(winner)
        except IndexError as e:
            db.add_player(winner, None, None, None, None, None, None, None, None, None)
            winner_id = db.get_playerid_from_name(winner)
            print(winner, 'was not in the database. Added.')

        try:
            db.insert_loot_record(date, winner_id, item_id, soft_res, checksum)
        except Exception as e:
            print(f"Exception occurred: {e}")
            print(f'The offending line was: Line +- 1 of {index}, record was: {value}')

        if winner == '_disenchanted':
            print(f'{db.get_item_name_from_id(item_id)[0][0]} was disenchanted on {_format_date_into_datetime(date)}. Lame.')
        else:
            print(f'{winner} won {db.get_item_name_from_id(item_id)[0][0]} on {_format_date_into_datetime(date)}! Hooray!')


    shutil.move(input_file, f'G:\\second_mains\\loot_logs\\{today}_lootlog.csv')

def guild_movement(db, data_movement_log):
    # This function will process the activity log from the GRM mod.
    join_guild_player_list = sorted([i[0] for i in db.get_all_players()])
    guilded_players = db.get_guilded_players()


    for i in data_movement_log:
        # joined guild
        print(i)
        if 'has JOINED the guild!' in i[0]:
            action = 'join_guild'
            action_id = db.get_guild_action_id_from_name(action)[0][0]

            pattern = r'([0-9]{4}-[0-9]{2}-[0-9]{2}) [0-9]{2}:[0-9]{2} : (\w+) has JOINED the guild! \(LVL: ([0-9]+)\) - Invited By: (\w+)'
            date, person_joined, level, officer_name = re.findall(pattern, i[0])[0]

            if person_joined not in join_guild_player_list:
                db.add_player(person_joined, 'Second Main', level, None, None, officer_name, None, None, None, None)
                print(f'{person_joined} added to guild as a Second Main')
                db.insert_guild_movement(action_id, person_joined, date)
                print(f'{person_joined} added to guild movement')

        #gquit
        elif 'has Left the guild' in i[0]:
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

        #gkick
        elif 'KICKED' in i[0]:
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


        #level up
        elif 'has Leveled to' in i[0]:
            # update guild roster, insert into level log
            pattern = r'[0-9]{1,}\) ([0-9]{4}-[0-9]{2}-[0-9]{2}) ([0-9]{2}:[0-9]{2}) : (\S+) has Leveled to ([0-9]{1,})*'
            date, time, player, level = re.findall(pattern, i[0])[0]
            try:
                player_id = db.get_playerid_from_name(player)
            except IndexError:
                db.add_player(player, None, None, None, None, None, None, None, None, None)
                player_id = db.get_playerid_from_name(player)
            db.update_player_level_in_guild_roster(level, player_id)
            db.insert_into_level_log(date,time,player_id,level)
            # print(f'{player.title()} has reached level {level}')

        #reached level cap
        elif 'Level Cap!' in i[0]:
            pattern = r'^[0-9]{1,}\) ([0-9]{4}-[0-9]{2}-[0-9]{2}) ([0-9]{2}:[0-9]{2}) : (\S+) has Reached the ([0-9]{1,}) Level Cap!'
            date, time, player_name, level = re.findall(pattern, i[0])[0]
            try:
                player_id = db.get_playerid_from_name(player_name)
            except IndexError:
                db.add_player(player_name, None, None, None, None, None, None, None, None, None)
                player_id = db.get_playerid_from_name(player_name)
            db.update_player_level_in_guild_roster(level, player_id)
            db.insert_into_level_log(date, time, player_id, level)

        #promoted or #demoted
        elif 'PROMOTED' in i[0] or 'DEMOTED' in i[0]:
            pattern = r'^[0-9]{1,}\) ([0-9]{4}-[0-9]{2}-[0-9]{2}) [0-9]{2}:[0-9]{2} : (\S+) (?:has been )?(PROMOTED|DEMOTED) (\S+) from (.+?) to (.+?)$'

            try:
                date, officer, action, player_name, old_rank, new_rank = re.findall(pattern, i[0])[0]
            except IndexError as e:
                continue #TODO should come back and revisit.

            try:
                player_id = db.get_playerid_from_name(player_name)
            except IndexError:
                db.add_player(player_name, None, None, None, None, None, None, None, None, None)
                player_id = db.get_playerid_from_name(player_name)
            officer_id = db.get_playerid_from_name(officer)
            db.update_guild_rank(player_id, new_rank)
            db.insert_rank_change(player_id, officer_id, action.lower(), old_rank, new_rank, date)

       #public note set
        elif 'public note' in i[0].lower():
            pass #TODO

        #officer_note_set
        elif 'officer note' in i[0].lower():
            pass #TODO

        #custom_note_set
        elif 'custom note' in i[0].lower():
            pass #TODO

        #banned
        elif 'BANNED' in i[0].lower():
            pass #TODO


        elif 'REINVITED' in i[0].lower():
            pass #TODO


    # Last step, move the log file out.
    print('end')
    # shutil.move(os.getcwd()+'\\guild_roster\\guild_log.csv',f'G:\\second_mains\\guild_movement_logs\\{today}_guild_log.csv')


def update_guild_roster():
    print()
    pass


def _format_date_into_datetime(date_string):
    # returns a datetime object - "Day of Week, Day Month Year"
    return datetime.strptime(date_string, '%Y-%m-%d').strftime('%A, %d %B %Y')


if __name__ == '__main__':
    main()
