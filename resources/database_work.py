'''
Functions that add to, modify, and display the db
'''
import sqlite3
import datetime
from pandas import read_sql_query, option_context
import g_cal.gcal_integration as gcal_integration
from pathlib import Path
from objects.shift import Shift

records_db_path = Path("./resources/c_records.db")

def return_shift_from_date(date):
    '''Given a datetime.date object, returns a shift object generated from
    the db'''

    conn = sqlite3.connect(records_db_path)
    cur = conn.cursor()

    cur.execute("SELECT * FROM c_Shifts WHERE shift_date = ?", (date,))

    row = cur.fetchone()

    conn.close()

    return Shift.create_from_db(row)



def add_shifts_to_db(shift_list):
    '''Takes a list of Shifts, adds them to the db'''
    conn = sqlite3.connect(records_db_path)
    cur = conn.cursor()

    for a_shift in shift_list:

        row = cur.execute('''SELECT * FROM c_Shifts WHERE shift_date = ?''',
                          (str(a_shift.shift_date),)).fetchone()

        if row:
            cur.execute(a_shift.sqlite_update_statement(), a_shift.sql_values())
        else:
            cur.execute(a_shift.sqlite_insert_statement(), a_shift.sql_values())

    conn.commit()
    conn.close()

    print('Shifts added to database')

def check_if_week(week_id):
    '''Checks if a given week is in the DB, returns boolean'''
    conn = sqlite3.connect(records_db_path)
    cur = conn.cursor()

    week_exists =  bool(cur.execute("SELECT shift_date FROM c_Shifts WHERE week_id = ?", (week_id,)).fetchall())

    conn.close()

    return week_exists




def called_in_sick(date):
    '''Function that changes a shift to no hours, updates tables, and adds a note'''
    
    conn = sqlite3.connect(records_db_path)
    c = conn.cursor()

    #Check if shift already that date
    c.execute("SELECT * FROM c_Shifts WHERE shift_date = ?", (str(date),))
    row = c.fetchone()

    if row is None:
        print("There wasn't a shift that day in the database")
        return None

    else:

        new_shift = Shift.create_from_db(row)
        called_in_note = "Called in sick, shift was {} to {}".format(new_shift.dict['start_time'], new_shift.dict['end_time'])
        if new_shift.note != '':
            new_shift.note = new_shift.note + ', ' + called_in_note
        else:
            new_shift.note = called_in_note

        c.execute(new_shift.called_in_sick_insert_data(), new_shift.sql_values())

        conn.commit()

        print('Shift edited, get well.')

    conn.close()


def add_events_from_gcal():
    '''Add events from gcal to the db'''

    #Getting most recent day added to database


    gcal_events = gcal_integration.get_calendar_events(gcal_integration.google_authenticate(), *return_last_db_entry())
    
    print('There are {} events to add to the database'.format(len(gcal_events)))

    shift_objects = []
    for an_event in gcal_events:
        shift_objects.append(Shift.create_from_gcal(an_event))

    add_shifts_to_db(shift_objects)
    print('Shifts successfully logged')



def return_last_db_entry():
    '''Returns the last date in the db'''
    conn = sqlite3.connect(records_db_path)
    cur = conn.cursor()

    cur.execute("SELECT shift_date FROM c_Shifts ORDER BY strftime('%s', shift_date) DESC LIMIT 1")
    last_entry = datetime.datetime.strptime(cur.fetchone()[0], '%Y-%m-%d') + datetime.timedelta(days=1)

    days_to_check = (datetime.datetime.today() - last_entry).days + 21

    return last_entry, days_to_check


def pptest():
    '''test of pretty printing'''
    import pprint
    pp = pprint.PrettyPrinter()
    conn = sqlite3.connect(records_db_path)
    cur = conn.cursor()

    cur.execute('SELECT * FROM c_Shifts')
    rows = cur.fetchall()
    print(rows)
    input()
    pp.pprint(rows)
    input()



def db_query():
    '''pretty prints a db query'''
    conn = sqlite3.connect(records_db_path)
    c = conn.cursor()
    print("Enter your SQL commands to execute in sqlite3.")
    print("Enter a blank line to exit.")
    buffer = ""

    while True:

        inp = input()
        if inp is '':
            break
        buffer += inp
        if sqlite3.complete_statement(buffer):
            try:
                buffer = buffer.strip()
                with option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
                    print(read_sql_query(buffer, conn))

            except Exception as e:
                print("An error occurred:", str(e))

            buffer = ""

    conn.close()


def db_command():
    '''send commands into the db'''
    conn = sqlite3.connect(records_db_path)
    c = conn.cursor()

    print("Enter your SQL commands to execute in sqlite3.")
    print("Enter a blank line to exit.")
    buffer = ""

    while True:

        inp = input()
        if inp is '':
            break
        buffer += inp
        if sqlite3.complete_statement(buffer):
            try:
                buffer = buffer.strip()
                c.execute(buffer)
                print(c.fetchall())
                if input('Commit? (y/n) >> ') == 'y':
                    conn.commit()
                    print('Committed')


            except Exception as e:
                print("An error occurred:", str(e))

            buffer = ""

    conn.close()

def change_hours(date, start_time, end_time):
    '''modifies a shift entry, makes note of original time and prompts for note'''
    pass


def add_notes(date, note):
    '''Add notes to a shift'''
    
    conn = sqlite3.connect(records_db_path)
    cur = conn.cursor()

    #Checking if date in db
    cur.execute('SELECT shift_date, notes FROM c_Shifts WHERE shift_date = ?', (date,))
    
    row = cur.fetchone()

    if row:
        _, old_note = row
        if len(old_note) > 2:
            note = old_note + ' ' + note

        #Adding to db
        cur.execute('INSERT INTO c_Shifts (notes) VALUES (:note) WHERE shift_date = :shift_date',
                    {'note' : note, 'shift_date' : str(date)})

        conn.commit()
    else:
        print('No shift on that day in db')

    conn.close()
        


def log_pay(pay_date, pay_before, pay_after):
    '''Logs pay in db.  Provides info on expected, deviance, tax paid, etc.'''
    
    #First grab the expected pay from the db
    conn = sqlite3.connect(records_db_path)
    cur = conn.cursor()

    cur.execute('SELECT SUM(expected_pay) FROM c_Shifts WHERE pay_date = ?', (str(pay_date),))
    pay_expected = float(cur.fetchone()[0])

    #Printing information about it
    print('Expected pay is ${:.2f}, amount paid before taxes is ${:.2f}, and after taxes is ${:.2f}.'.format(pay_expected, pay_before, pay_after))
    print('Difference between expected and actual pay is ${:.2f}, {:.2f}% paid in taxes.'.format(pay_expected-pay_before,
                                                                                                ((pay_before-pay_after)/pay_before)*100))

    #Getting more data about past paydays, to return where this ranks.  Also total paid to date.
    #print(read_sql_query('SELECT * FROM c_Paydays', conn))
    cur.execute("SELECT pay_before_tax FROM c_Paydays")
    all_pay_before = cur.fetchall()
    cur.execute("SELECT SUM(pay_before_tax) FROM c_Paydays")
    pay_sum = float(cur.fetchone()[0])
    all_pay_before.sort()
    #Reading where this lays amongst other paydays.
    all_pay_before_lower = [x[0] for x in all_pay_before if x[0] < pay_before]
    print('This payday is ranked {}/{}'.format(len(all_pay_before_lower), len(all_pay_before)))
    print('${:.2f} total paid to date'.format(pay_sum))

    pay_period = str(pay_date - datetime.timedelta(days=18)) + ' - ' + str(pay_date - datetime.timedelta(days=5))
    #LOGGING IN DB
    log_dict = {'pay_period' : pay_period,
                'pay_expected' : pay_expected,
                'pay_before_tax' : pay_before,
                'pay_after_tax' : pay_after,
                'percentage' : (pay_before-pay_after)/pay_before,
                'pay_date' : str(pay_date)
                }
    # print(log_dict)
    cur.execute('''INSERT INTO c_Paydays (pay_period, pay_expected, pay_before_tax, pay_after_tax, percentage_tax, pay_date)
                VALUES (:pay_period, :pay_expected, :pay_before_tax, :pay_after_tax, :percentage, :pay_date)''', log_dict)
    
    conn.commit()
    conn.close()
    
    input()

def delete_week_events(week_id):
    '''Given a week id, removes all events from that week'''
    conn = sqlite3.connect(records_db_path)
    cur = conn.cursor()

    cur.execute('''DELETE FROM c_Shifts WHERE week_id = :week_id''', {'week_id' : week_id})
    # cur.execute('''SELECT shift_date FROM c_Shifts WHERE week_id = :week_id''', {'week_id' : week_id})
    # print(cur.fetchall())
    conn.commit()
    conn.close()



def display_week(date):
    '''Prints a display of given week's events'''
    
    week_id = date.strftime('%y-%W')

    conn = sqlite3.connect(records_db_path)
    cur = conn.cursor()

    print(read_sql_query("SELECT shift_date, start_time, end_time, hours_worked, hours_paid, expected_pay FROM c_Shifts WHERE week_id = '{}'".format(week_id),
        conn))
    print(read_sql_query('''SELECT SUM(expected_pay) AS 'Total_Pay', SUM(hours_worked) AS 'Total_Hours' FROM c_Shifts
        WHERE week_id = '{}' '''.format(week_id), conn))

    conn.close()
    