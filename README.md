# Schedule Creator

Takes input either from command line directly (more capable) or through the android app built using Kivy and Python.
Once a work schedule is given, or list of any events in a given week, using python and the google calendar API, bulk creates events.  The events are then logged to a SQLite database.  Logic is performed on the given calendar to calculate breaks in shifts, expected pay, etcetera.  Provides a summary before events are created showing the week schedule with hours total and total expected pay.
