'''
Schedule Creator 4
James Lee; April 19, 2019
'''
import datetime

# from objects.shift import Shift
import resources.file_worker as file_worker

from colorama import init, Fore, Style, Back

# from sys import argv
import argparse
import os

import resources.database_work as db_work
from objects.shift import Shift
from g_cal.gcal_integration import add_shifts_to_gcal, get_gcal_event_on_date, modify_event_to_match_shiftobject, google_authenticate, remove_gcal_event
from resources.file_worker import move_paystub_cli, log




####FOR UPDATING, create shift, then change attributes of shift either manually or using a method
#then pass it in


def option_menu(menuoptions):
    '''Accepts a dictionary of menu options, prints them, returns the choice as tuple.  Last option is always exit, as is x'''

    while True:
        #awaiting menu option, exiting when recieved

        print(Fore.WHITE + Back.BLUE + '\n' + '*' * 80)
        print(menuoptions['title'].center(80))
        print('*' * 80)
        print(Style.RESET_ALL, end='')
        for anoption in range(1, len(menuoptions)):
            print(Fore.CYAN + f" {anoption} : {menuoptions[anoption]}")
        print(Fore.CYAN + f' {len(menuoptions)} : Exit')

        print(Fore.GREEN, end='')

        chosenoption = input("\nPlease choose menu option : ")

        optlist = [str(x) for x in list(menuoptions.keys())]
        if chosenoption in optlist:
            break
        elif chosenoption in ['x', str(len(menuoptions))]:
            chosenoption = "Exit"
            break
        else:
            print("\nInvalid choice\n")


    print(Style.RESET_ALL, end='')

    return (chosenoption,)


def prompt_for_date(prompt=None):
    '''Prompts for date, passes a datetime object'''
    
    while True:
        if prompt == None:
            prompt = 'Enter date (yy-mm-dd) : '
        inp = input(prompt)
        try:
            date_return = datetime.datetime.strptime(inp, '%y-%m-%d').date()
            break
        except:
            print('Input error\n')

    return date_return

def prompt_for_hours(prompt=None):
    '''Gets two strings, makes datetime objects.  Can be start-end, or start+hours'''

    while True:
        if prompt == None:
            prompt = 'Enter new hours (hhmm-hhmm) : '
        inp = input(prompt)
        # try:
        splitdash = inp.split('-')
        if len(splitdash) == 2:
            start_raw, end_raw = splitdash
            start_time = datetime.datetime.strptime(start_raw, '%H%M').time()
            end_time = datetime.datetime.strptime(end_raw, '%H%M').time()
            break
        elif len(splitdash) == 1 and splitdash[0] != '':
            splitplus = inp.split('+')
            print(splitplus)
            start_time = datetime.datetime.strptime(splitplus[0], '%H%M')
            end_time = start_time + datetime.timedelta(hours=float(splitplus[1]))
            start_time = start_time.time()
            break
        elif len(splitdash) == 1 and splitdash[0] == '':
            #Empty intentionally?
            start_time = None
            end_time = None
            break
        # except:
        #     print('Input error')

    return start_time, end_time

def prompt_for_string(prompt=None):
    '''Prompts for a string and passes it'''
    if prompt == None:
        prompt = '\t: '
    return input(prompt)


def prompt_for_week():
    '''Prompts for input to create a week of shifts'''
    print("Enter week information\n")
    print(Fore.CYAN + 'Date the week begins on (yy-mm-dd)')

    while True:
        monday_date_raw = input(' : ')
        try:
            monday_date = datetime.datetime.strptime(monday_date_raw, '%y-%m-%d').date()
            if monday_date.weekday() == 0:
                break
            print('Given date is not a Monday.')

        except:
            print('Input error, ensure format is yy-mm-dd')

    #Making tuple of days in that week
    week_days = []
    for i in range(7):
        week_days.append(monday_date + datetime.timedelta(days=i))

    print('Enter start and end time for each shift, in format hhmm-hhmm.  Leave blank for no shift.')
    week_shifts_raw = []
    #Getting start and end times for each shift
    for a_day in week_days:
        while True:
            try:
                print(Fore.CYAN + str(a_day) + ' : ', end='')
                print(Fore.GREEN, end='')
                start_time, end_time = prompt_for_hours('')
                if start_time is not None and end_time is not None:
                    start_date = datetime.datetime.combine(a_day, start_time)
                    end_date = datetime.datetime.combine(a_day, end_time)
                    week_shifts_raw.append((start_date, end_date))
                break
                # print(Fore.CYAN + str(a_day) + ' : ', end='')
                # print(Fore.GREEN, end='')
                # inp = input().split('-')
                # if len(inp) == 2:
                #     start_time_raw, end_time_raw = inp
                #     start_date = datetime.datetime.combine(a_day, datetime.datetime.strptime(start_time_raw, '%H%M').time())
                #     end_date = datetime.datetime.combine(a_day, datetime.datetime.strptime(end_time_raw, '%H%M').time())
                #     week_shifts_raw.append((start_date, end_date))
                #     break
                # elif len(inp) == 1 and inp[0] == '':
                #     break

            except Exception as e:
                print('Input Error')
                print(e)
    print(Style.RESET_ALL, end='')

    return week_shifts_raw


def create_week_shifts(shift_list):
    '''Accepts a list of tuples (start_date, end_date) generated from input, creates
    shift objects'''
    week_shifts = []
    for a_day in shift_list:
        week_shifts.append(Shift(*a_day))

    return week_shifts

def add_week_schedule(shift_objects):
    '''creates gcal events for the given shifts, and adds to db'''
    
    #First making gcal events
    add_shifts_to_gcal(shift_objects)

    #Now adding to db
    db_work.add_shifts_to_db(shift_objects)



def log_pay_prompt(payday_date):
    '''prompts for pay before and after, passes to db_work'''

    print('Enter the amount paid before taxes and after')

    while True:

        try:
            pay_before = float(input('Pay before taxes : $'))
            pay_after = float(input('Pay after taxes : $'))
            break
        except:
            print('Input error')


    return payday_date, pay_before, pay_after

def get_gcal_event_and_db_shift(date):
    '''Given a date, gets a shift from the db and makes a shift object.
    Also gets the ID of the google calendar event'''

    shift = db_work.return_shift_from_date(date)
    modify_event_to_match_shiftobject(shift)
    # get_gcal_event_on_date(shift.shift_date, shift.start_date.time(), shift.end_date.time())


def sleep_math(shift_date = datetime.date.today() + datetime.timedelta(days=1)):
    '''Based on when the shift tomorrow (or passed in day) begins, when to get up, when to leave, etc.'''

    '''Bulk this out, into a simple flag to return information about the next shift.  How many hours it is,
    what breaks there are, etc.'''

    #Currently assuming morning shift.

    shift_start = db_work.return_shift_from_date(shift_date).start_date
    time_to_wake = shift_start - datetime.timedelta(hours=3)
    time_to_be_asleep = time_to_wake - datetime.timedelta(hours=8)
    time_to_be_in_bed = time_to_be_asleep - datetime.timedelta(hours=1)

    print('''
    Your shift tomorrow is at {}.
    You should wake at {}
    For 8 hours of sleep aim to be in bed by {} and asleep by {}'''.format(shift_start, time_to_wake, time_to_be_in_bed, time_to_be_asleep)) 


def confirm_week(shift_objects):
    '''Given a set of shift objects, prints the total hours, total pay, etc.  Returns true or false based on input'''

    #Check if already a week in db
    if db_work.check_if_week(shift_objects[0].shift_date.strftime('%y-%W')):
        print('That week is already in the db')
        if input('Would you like to still add it? (y/n) : ').lower() == 'n':
            return False

    total_hours = 0
    total_paid_hours = 0
    total_pay = 0

    for a_shift in shift_objects:
        print(str(a_shift))
        total_hours += a_shift.dict['hours_worked']
        total_paid_hours += a_shift.dict['hours_paid']
        total_pay += a_shift.dict['amount_earned']

    print("In week {}:\n{} total hours, {} paid hours.\n${} total pay.".format(
            shift_objects[0].shift_date.strftime('%y-%W'),
            total_hours,
            total_paid_hours,
            total_pay))
    if input('Is this correct? (y/n) :') == 'y':
        return True
    else:
        return False

def convert_string_to_date(datestring):
    '''Converts yy-mm-dd to date object'''
    while True:
        try:
            return datetime.datetime.strptime(datestring, '%y-%m-%d').date() 
        except:
            print('Invalid string')
            datestring = input('yy-mm-dd : ')

def testing():
    '''Function to test new things'''
    # sleep_math()
    g_cal = google_authenticate()

    date = datetime.datetime(2019, 9, 16, 0, 0)

    gcal_event, _ = get_gcal_event_on_date(date, g_cal=g_cal)

    if gcal_event:
        print(gcal_event['start'])
    else:
        print("Success, congrats on navigating Google's fuckery")


def erase_week(first_day):
    '''Takes a Monday (datetime object), erases that week from the database and removes the gcal events for it'''

    week_id = first_day.strftime('%y-%W')

    if not db_work.check_if_week(week_id):
        print('That week is not present in the database')
        return False

    # #Removing the shifts from gcal, iterating one day at a time to see if there are any events in the CC calendar
    g_cal = google_authenticate()
    for i in range(7):
        gcal_event, _ = get_gcal_event_on_date(first_day + datetime.timedelta(days=i), g_cal=g_cal)
        print(i)
        if gcal_event:
            remove_gcal_event(gcal_event, g_cal)




    #Removes all matching rows with that week_id in database
    db_work.delete_week_events(week_id)




def main():
    '''Main program'''
    '''ACCEPT ARGV INPUT, can override making GUI to return options
    options like just query db, just add events from gcal, return week, etc.'''
    log('Program launched')
    #Arg parsing
    parser = argparse.ArgumentParser(description='Work with schedules, create google calendar events, log to database')
    parser.add_argument('-G', action='store_true', dest='scan_gcal',
        help='Updates the database by scanning google calendar events') #Just updates from gcal, prints when done

    parser.add_argument('-q', action='store_true', dest='query_db', help='Send database queries') #Query db
    parser.add_argument('-a', action='store_true', dest='create_week', help='Create a new week schedule, add to gcal and database') #add week
    parser.add_argument('-backup', action='store_true', dest='backup', help='Backup the database') #backup db
    parser.add_argument('-pay', action='store_true', dest='log_pay', help='Log amount paid, move pdf and date') #log pay
    parser.add_argument('-update', action='store_true', dest='update_shift', help='Update a shift') #update shift
    parser.add_argument('-sick', dest='called_in', help='Log called in sick.  Enter the yy-mm-dd called in sick.')
    parser.add_argument('-test', action='store_true', dest='testing', help='Testing branch')

    args = parser.parse_args()
    
    if args.scan_gcal or args.query_db or args.create_week or args.backup or args.log_pay or args.update_shift or args.called_in or args.testing:
        no_args = False
        opt_chosen = []
    else:
        no_args = True

    if args.testing:
        testing()
        return

    if args.scan_gcal:
        opt_chosen.append('2')
    if args.query_db:
        db_work.db_query()
    if args.create_week:
        opt_chosen.append('1')
    if args.backup:
        file_worker.backup_db()
    if args.log_pay:
        opt_chosen.append('3')
    if args.update_shift:
        opt_chosen.append('8')
    if args.called_in is not None:
        # opt_chosen.append('5')
        date = convert_string_to_date(args.called_in)
        # print(date)
        db_work.called_in_sick(date)
    
    #Checking for arguments, to override the CLI GUI menu


    init()
    if no_args:
        _ = os.system('cls')
        print(Fore.RED + '-' * 80)
        print("Welcome to the Schedule Creator v4".center(80))
        print('James Lee April 19 2019'.center(80))
        print('Program started successfully'.center(80))
        print('-' * 80 + '\n')
        print(Fore.CYAN + '\n')


        main_menu_options = {
            'title' : 'Main Menu',
            1 : 'Add week schedule to gcal and database',
            2 : 'Update database from Google Calendar',
            3 : 'Log pay',
            4 : 'Add notes to shift',
            5 : 'Log called in sick',
            6 : 'Work with database',
            7 : 'Display week information',
            8 : 'Update a shift',
            9 : 'Add a shift',
            10 : 'Delete a week (gcal and db)'
            }



    while True:
        if no_args:
            opt_chosen = option_menu(main_menu_options)

        if 'Exit' in opt_chosen:
            _ = os.system('cls')
            break

        if '10' in opt_chosen:

            print('Deleting week')
            print('Enter the date (yy-mm-dd) of the Monday the week begins with')

            while True:
                monday_date_raw = input(' : ')
                try:
                    monday_date = datetime.datetime.strptime(monday_date_raw, '%y-%m-%d')
                    if monday_date.weekday() == 0:
                        break
                    print('Given date is not a Monday.')

                except:
                    print('Input error, ensure format is yy-mm-dd')

            erase_week(monday_date)

            print('Week Erased')



        if '1' in opt_chosen:
            week_tuples = prompt_for_week()
            shift_objects = create_week_shifts(week_tuples)
            if confirm_week(shift_objects):
                add_week_schedule(shift_objects)

        if '2' in opt_chosen:
            db_work.add_events_from_gcal()

        if '3' in opt_chosen:
            selected_payday = move_paystub_cli()
            payday_date, pay_before, pay_after = log_pay_prompt(selected_payday)
            db_work.log_pay(payday_date, pay_before, pay_after)

        if '4' in opt_chosen:

            date = prompt_for_date()
            note = prompt_for_string()

            db_work.add_notes(date, note)

        if '5' in opt_chosen:

            print('Enter the date you called in sick')
            date = prompt_for_date()

            db_work.called_in_sick(date)

        if '6' in opt_chosen:
            '''6 : 'Query database',
            7 : 'Edit database',
            '''
            sub_options = {'title' : 'Database operations', 1 : 'Backup database', 2 : 'Query database', 3 : 'Edit database'}
            sub_opt = option_menu(sub_options)

            if '1' in sub_opt:
                file_worker.backup_db()

            if '2' in sub_opt:
                db_work.db_query()

            if '3' in sub_opt:
                db_work.db_command()

        if '7' in opt_chosen:

            date = prompt_for_date()
            db_work.display_week(date)

        if '8' in opt_chosen:

            print("Enter the date of the shift you'd like to change")
            date = prompt_for_date()
            shift = db_work.return_shift_from_date(date)

            print('The shift that day was from {} to {}'.format(shift.dict['start_time'], shift.dict['end_time']))
            shift.note = 'Shift changed, original hours were {}-{}'.format(shift.dict['start_time'], shift.dict['end_time'])
            print('Enter the new start and end hours in format hhmm-hhmm')
            start_time, end_time = prompt_for_hours()

            start_date = datetime.datetime.combine(date, start_time)
            end_date = datetime.datetime.combine(date, end_time)

            shift.start_date = start_date
            shift.end_date = end_date
            shift.generate_data()

            db_work.add_shifts_to_db((shift,))

            print('Would you like to edit the shift in gcal?')

            if input('(y/n) : ') == 'y':
                
                modify_event_to_match_shiftobject(shift)

        if '9' in opt_chosen:
            print('Enter the date of the added shift')
            date = prompt_for_date()
            start_time, end_time = prompt_for_hours()
            new_shift = Shift(datetime.datetime.combine(date, start_time), datetime.datetime.combine(date, end_time), note='Manually added shift')
            add_week_schedule((new_shift,))
            print('Success')


        #Checking for empty options
        if len(opt_chosen) == 0:
            break
        #Prevent inf loop if run from command line with args
        if not no_args:
            break

if __name__ == '__main__':
    main()
