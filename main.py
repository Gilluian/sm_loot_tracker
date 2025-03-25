# main.py
#
import csv, os, shutil, re
from datetime import datetime, timedelta
from db_funcs import LootTracker


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
                print('Guild Log file not present')
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

    today = datetime.today().strftime('%Y%m%d_%H%M%S')
    shutil.move(input_file, f'G:\\second_mains\\loot_logs\\{today}_lootlog.csv')

def guild_movement(db, data_movement_log):
    # This function will process the activity log from the GRM mod.
    # we'll need a character id

    pass


def update_guild_roster():
    print()
    pass


def _format_date_into_datetime(date_string):
    # returns a datetime object - "Day of Week, Day Month Year"
    return datetime.strptime(date_string, '%Y-%m-%d').strftime('%A, %d %B %Y')


if __name__ == '__main__':
    main()
