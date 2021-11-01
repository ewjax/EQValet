# import the datetime class from the datetime module
from datetime import datetime


import re


#
# base class for other DOT spells
#
class DOT_Spell:

    # ctor
    def __init__(self, spell_name, landed_message, faded_message, max_duration_sec):

        self.spell_name         = spell_name
        self.landed_message     = landed_message
        self.faded_message      = faded_message
        self.max_duration_sec   = int(max_duration_sec)

        self.start_time         = None
        self.end_time           = None

    # set the start time
    # using the very capable strptime() parsing function built into the datetime module
    # [Thu Oct 28 15:24:13 2021] A frost giant captain is engulfed in darkness.
    def set_start_time(self, eq_timestamp):
        self.start_time = datetime.strptime(eq_timestamp[0:26], '[%a %b %d %H:%M:%S %Y]')

    # set the end time
    # using the very capable strptime() parsing function built into the datetime module
    # [Thu Oct 28 15:24:13 2021] A frost giant captain is engulfed in darkness.
    def set_end_time(self, eq_timestamp):
        self.end_time = datetime.strptime(eq_timestamp[0:26], '[%a %b %d %H:%M:%S %Y]')

    # helper function to get number of ticks elapsed 
    def elapsed_ticks(self):
        ticks = 0
        if (self.end_time and self.start_time):
            elapsed_timedelta = self.end_time - self.start_time
            elapsed_seconds = elapsed_timedelta.total_seconds()
            if elapsed_seconds > self.max_duration_sec:
                elapsed_seconds = self.max_duration_sec
            ticks = int(elapsed_seconds/6.0)
        return ticks

    # function to be overloaded by child classes
    def damage_dealt(self):
        return 0

    # overload funciton to allow object to print() to screen in sensible manner, for debugging with print()
    def __repr__(self):
        return '({}, {}, {}, {})'.format(self.spell_name,
                                       self.start_time,
                                       self.end_time,
                                       self.max_duration_sec)




#
# Most DOT classes work on a linear damage model, i.e. X damage per tick
#
class LinearDOT_Spell(DOT_Spell):

    # ctor
    def __init__(self, spell_name, landed_message, faded_message, max_duration_sec, dmg_initial, dmg_per_tick):
        DOT_Spell.__init__(self, spell_name, landed_message, faded_message, max_duration_sec)
        self.dmg_initial    = dmg_initial
        self.dmg_per_tick   = dmg_per_tick

    # overload the damage_dealt() function
    def damage_dealt(self):
        damage = 0
        if (self.end_time and self.start_time):
            ticks = self.elapsed_ticks()
            damage = self.dmg_initial + ticks * self.dmg_per_tick
        return damage




    # overload funciton to allow object to print() to screen in sensible manner, for debugging with print()
    def __repr__(self):
        return '({}, {}, {}, {}, {}, {})'.format(self.spell_name,
                                       self.start_time,
                                       self.end_time,
                                       self.max_duration_sec,
                                       self.dmg_initial,
                                       self.dmg_per_tick)



#
# Nonlinear damage accrual (Splurt, others??)
#
class Splurt_Spell(DOT_Spell):

    # ctor
    def __init__(self):
        DOT_Spell.__init__(self, 'Splurt', 'landed_message', 'faded_message', 102)

    # overload the damage_dealt() function
    def damage_dealt(self):
        damage = 0
        if (self.end_time and self.start_time):

            ticks = self.elapsed_ticks()
            base_damage = ticks * 11

            incremental_damage = 0
            i = 0
            while i < ticks:
                incremental_damage += (i * 12)
                i += 1

            damage = base_damage + incremental_damage

        return damage



    # overload funciton to allow object to print() to screen in sensible manner, for debugging with print()
    def __repr__(self):
        return '({}, {}, {}, {})'.format(self.spell_name,
                                       self.start_time,
                                       self.end_time,
                                       self.max_duration_sec)


def main():

    sec = 17.999
    print('ticks = {}'.format(sec/6.0))
    print('ticks = {}'.format(int(sec/6.0)))

    line1 = '[Thu Oct 28 15:24:13 2021] A frost giant captain is engulfed in darkness.'
    line2 = '[Thu Oct 28 15:28:13 2021] A frost giant captain is engulfed in darkness.'

    ds1 = LinearDOT_Spell('Cascading Darkness', 'A frost giant captain is engulfed in darkness', 'faded message', 96, 0, 72)
    print(ds1)
    ds1.set_start_time(line1)
    ds1.set_end_time(line2)
    print(ds1)

    print(ds1.elapsed_ticks())
    print(ds1.damage_dealt())


    ds2 = LinearDOT_Spell('Envenomed Bolt', 'landed message', 'faded message', 48, 110, 146)
    ds2.set_start_time(line1)
    ds2.set_end_time(line2)
    print(ds2)

    print(ds2.damage_dealt())


    ds3 = Splurt_Spell()
    ds3.set_start_time(line1)
    ds3.set_end_time(line2)
    print(ds3)

    print(ds3.damage_dealt())





if __name__ == '__main__':
    main()



