# main.py
#
import csv, os, shutil, re, logging
from datetime import datetime, timedelta
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
                    data = list(reader)[::-1]
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
            db.add_player(winner, None, None, None, None)
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

    for i in data_movement_log:
        # joined guild
        if 'has JOINED the guild!' in i[0]:
            action = 'join_guild'
            pattern = r'([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}) : (\w+) has JOINED the guild! \(LVL: ([0-9]+)\) - Invited By: (\w+)'
            date, person_joined, level, officer_name = re.findall(pattern, i[0])[0]

            # check if the person is in the guild
            try:
                player_id = db.get_playerid_from_name(person_joined)
            except IndexError as f: # If they're not, add them to the guild.
                db.add_player(person_joined, None, level, None, None)
                player_id = db.get_playerid_from_name(person_joined)
                print(f'Player Joined: {person_joined} ID {player_id} level {level}')

        #gquit
        elif 'has Left the guild' in i[0]:
            action = 'gquit'
            pattern = r'[0-9]{1,}\) ([0-9]{4}-[0-9]{2}-[0-9]{2}) [0-9]{2}:[0-9]{2} : (\S+) has Left the guild.*'
            date, player_who_left = re.findall(pattern, i[0])[0]
            db.remove_from_guild(player_who_left)
            try:
                db.insert_guild_movement(action, player_who_left, date)
            except IndexError:
                # if we get this error, the player was in the guild but not in the program DB.
                # We'll add the player and then add it to the log.
                db.add_player(player_who_left, None, None, None, None)
                db.insert_guild_movement(action,player_who_left, date)

        #gkick
        elif 'KICKED' in i[0]:
            pass

        #level up
        elif 'has Leveled to' in i[0]:
            pass

        #reached level cap

        #promoted

        #demoted

        #public note set

        #officer_note_set

        #custom_note_set

        #banned


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
