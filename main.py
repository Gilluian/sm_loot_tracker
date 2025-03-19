# main.py
#
import csv
from datetime import datetime, timedelta
from db_funcs import LootTracker
import shutil

def main():
    print('Beginning setup')
    db = LootTracker()
    print('Setup finished')
    while True:
        print('MENU:')
        print('(update_roster) | (raid_loot) | (exit)')
        user_choice = input(str("input > "))
        if user_choice.lower() == 'update_roster':
            update_guild_roster()
        elif user_choice.lower() == 'raid_loot':
            submit_loot_log(db)
        elif user_choice.lower() == 'exit':
            exit(3)
        else:
            raise ValueError("Enter a correct option")


def update_guild_roster():
    print()
    pass


def submit_loot_log(db):
    input_file = str(input("Path to input file: "))
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        logs = list(reader)

    for index, value in enumerate(logs):
        item_id, winner, date, soft_res, offspec = value[0].split(';')
        try:
            winner_id = db.get_playerid_from_name(winner)
        except IndexError as e:
            db.add_player(winner, None, None, None, None)
            winner_id = db.get_playerid_from_name(winner)
            print(winner, 'was not in the database. Added.')

        try:
            db.insert_loot_record(item_id, winner_id, date, soft_res, offspec)
        except Exception as e:
            print(f"Exception occurred: {e}")
            print(f'The offending line was: Line {index}, record was: {value}')

        if winner == '_disenchanted':
            print(f'{db.get_item_name_from_id(item_id)[0][0]} were disenchanted on {_format_date_into_datetime(date)}. Lame.')
        else:
            print(f'{winner} won {db.get_item_name_from_id(item_id)[0][0]} on {_format_date_into_datetime(date)}! Hooray!')

    today = datetime.today().strftime('%Y%M%d')
    shutil.move(input_file, f'G:\\second_mains\\loot_logs\\{today}_lootlog.csv')
def _format_date_into_datetime(date_string):
    '''
    :param date_string:
    :return:
    This will turn a date into a datetime object.
    '''

    return datetime.strptime(date_string, '%Y-%m-%d').strftime('%A, %d %B %Y')

if __name__ == '__main__':
    main()
