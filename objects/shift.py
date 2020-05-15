'''
Contains shift master class
'''
import datetime

class Shift():
    """A Shift object, contains start and end time, as well as
    other data created using that.
    Contains: start_time, end_time, wage, hours_worked, hours_paid,
        amount_earned, note, break_length, pay_date
    It error checks the fuck outta itself."""
    def __init__(self, start_date, end_date, note=None):
        super(Shift, self).__init__()
        #start_date and end_date must be datetime.datetime objects
        #Creating the shift date, it should be a datetime.date
        self.shift_date = start_date.date()

        #the start and end times should be datetime.time objects
        self.start_date, self.end_date = start_date, end_date

        if note is None:
            self.note = ''

        else:
            self.note = note

        self.generate_data()

    def generate_data(self):
        '''Generates all the needed data based on start and end time'''

        #Packaging into a dictionary
        self.dict = {}

        self.dict['start_time'] = str(self.start_date.time())
        self.dict['end_time'] = str(self.end_date.time())

        self.dict['wage'] = 16.00 if self.shift_date.weekday() != 6 else 20.00

        self.dict['hours_worked'] = (self.end_date - self.start_date).seconds / (60*60)

        self.dict['hours_paid'] = self.dict['hours_worked'] if self.dict['hours_worked'] <= 5 \
             else self.dict['hours_worked'] - 0.5

        self.dict['amount_earned'] = self.dict['wage'] * self.dict['hours_paid']
        #Break is upaid, paid
        self.dict['break_length'] = str((0.25 if self.dict['hours_worked'] < 8.5 else 0.5,
                                     0 if self.dict['hours_worked'] <= 5 else 0.5))

        sunday_date = self.shift_date + datetime.timedelta(days=(6 - self.shift_date.weekday()))

        if (sunday_date - datetime.date(2018, 9, 30)).days % 14 != 0:
            sunday_date = sunday_date + datetime.timedelta(days=7)

        #Now, moving from the pay period end to the paydate for that pay period
        self.dict['pay_date'] = sunday_date + datetime.timedelta(days=5)

    def called_in_sick_insert_data(self):
        '''Called in sick function.  Returns a dictionary of modified values to write to database.'''

        return '''INSERT INTO c_Shifts 
            (week_id, shift_date, start_time, end_time, hours_worked, hours_paid, breaks, wage, expected_pay, notes, pay_date) 
            VALUES (:week_id, :shift_date, '', '', 0, 0, (0, 0), :wage, 0, :note, :pay_date)'''

    @classmethod
    def create_from_gcal(cls, gcal_event):
        '''Creates a shift object from a gcal event'''

        start_date = datetime.datetime.strptime(gcal_event['start']['dateTime'][:16],
                                              '%Y-%m-%dT%H:%M')

        end_date = datetime.datetime.strptime(gcal_event['end']['dateTime'][:16],
                                              '%Y-%m-%dT%H:%M')

        return cls(start_date, end_date)

    @classmethod
    def create_from_strings(cls, shift_date_str, start_time_str, end_time_str, note=None):
        '''Creates shift objects from strings representing start and end
        shift_date must be YYYY-MM-DD, start and end must be HH:MM:SS'''

        shift_date = datetime.datetime.strptime(shift_date_str, '%Y-%m-%d').date()

        start_time = datetime.datetime.strptime(start_time_str, '%H:%M:%S').time()
        end_time = datetime.datetime.strptime(end_time_str, '%H:%M:%S').time()

        start_date = datetime.datetime.combine(shift_date, start_time)
        end_date = datetime.datetime.combine(shift_date, end_time)


        return cls(start_date, end_date, note)

    @classmethod
    def create_from_db(cls, row):
        '''Creates a shift object from the return from db, from SELECT *'''

        shift_date_str, start_time_str, end_time_str, note = row[2], row[3], row[4], row[10]

        return cls.create_from_strings(shift_date_str, start_time_str, end_time_str, note)



    def __str__(self):

        return "{s.shift_date} : {d[start_time]} - {d[end_time]}  {d[hours_worked]} total hours, {d[hours_paid]} paid hours.".format(s=self, d=self.dict)

    @staticmethod
    def sqlite_insert_statement():
        '''String to insert a shift'''

        return '''INSERT INTO c_Shifts 
            (week_id, shift_date, start_time, end_time, hours_worked, hours_paid, breaks, wage, expected_pay, notes, pay_date) 
            VALUES (:week_id, :shift_date, :start_time, :end_time, :hours_worked, :hours_paid, :break_length, :wage, :amount_earned, :note, :pay_date)'''

    @staticmethod
    def sqlite_update_statement():
        '''Returns update statement for db'''

        return '''UPDATE c_Shifts SET
            start_time = :start_time,
            end_time = :end_time,
            breaks = :break_length,
            expected_pay = :amount_earned,
            hours_worked = :hours_worked,
            hours_paid = :hours_paid,
            notes = :note
            WHERE shift_date = :shift_date'''



    def sql_values(self):
        '''Returns the data to insert the shift into database (or update)'''

        ret_dict = {'week_id' : str(self.shift_date.strftime('%y-%W')),
                    'shift_date' : str(self.shift_date),
                    'note' : self.note}
        return dict(ret_dict, **self.dict)


    # def insert_or_update_db(self):
    #     '''Inserts into c_records.db'''

    #     conn = sqlite3.connect('c_records.db')
    #     cur = conn.cursor()

    #     row = cur.execute('''SELECT * FROM c_Shifts WHERE shift_date = ?''',
    #                       (str(self.shift_date),)).fetchone()

    #     if row:
            
    #         cur.execute(Shift.sqlite_update_statement(), self.sql_values())
        
    #     else:
            
    #         cur.execute(Shift.sqlite_insert_statement(), self.sql_values())

    #     conn.commit()
    #     conn.close()
            
