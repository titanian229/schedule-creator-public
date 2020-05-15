'''
Handles file moving and renaming.
Backs up DB
Move pdf with pay stubs.
'''
from os import rename, startfile
from shutil import copy2 as shucopy
from pathlib import Path
import datetime


def backup_db():
    '''Backs up the database file'''
    sc_path = Path("~/Documents/Programming Projects/ScheduleCreator")
    records_db_path = sc_path / 'resources' / 'c_records.db'
    backup_path = sc_path / 'backups'
    backup_name = 'c_records_' + str(datetime.date.today()) + '.db'
    shucopy(records_db_path, backup_path / backup_name)
    print('Database backed up')


def get_payday_list():
    '''Gets a list of the three fridays prior'''

    #Check if today or yesterday is a payday
    first_payday = datetime.date(2018, 10, 5)
    today = datetime.date.today()
    #Work to friday
    nearest_friday = today + datetime.timedelta(days=(4-today.weekday()))

    #check if it's a payday
    if ((nearest_friday - first_payday).days) % 14 != 0:
        nearest_friday -= datetime.timedelta(days=7)

    friday_list = (
                   nearest_friday,
                   nearest_friday - datetime.timedelta(days=14),
                   nearest_friday - datetime.timedelta(days=28))

    return friday_list

def choose_payday(friday_list):
    '''Accepts list of 3 paydays, returns chosen'''

    for ind, a_fri in enumerate(friday_list, 1):
        print(ind, ' : ', str(a_fri))

    while True:
        try:
            selected_payday = friday_list[int(input('Select the payday being logged : ')) - 1]
            break
        except:
            print('Input error')

    return selected_payday

def move_paystub(selected_payday):
    '''Moves and renames the paystub, from the name passed to it'''

    new_filename = str(selected_payday) + '.pdf'
    paystub_init_path = Path("~/Downloads/untitled.pdf")
    new_path = stubs_folder_path / new_filename
    if not paystub_init_path.exists():
        print('The paystub is not in the downloads folder, please download then hit enter.  If it has been moved already enter (n)')
        if input() == 'n':
            return selected_payday

    rename(paystub_init_path, new_path)

    startfile(new_path)

    return selected_payday

def move_paystub_cli():
    '''Runs the paystub mover, if run through GUI'''
    return move_paystub(choose_payday(get_payday_list()))


def log(data_to_write):
    '''Logs to a text file,
    format is yy-mm-dd : Log data'''

    log_file_path = Path("./resources/program_log.txt")
    if not log_file_path.exists():
        raise ValueError('Logfile not present')
    try:
        logfile = open(log_file_path, 'a')
    except:
        print('Logfile open error')
        return

    data_to_write = str(datetime.datetime.now()) + ' : ' + data_to_write
    logfile.write(data_to_write)
    logfile.write('\n')
    logfile.close()





