# import the datetime class from the datetime module
from datetime import datetime


import re


#
# class for Targets
#
class Target:

    # ctor
    def __init__(self, name):

        self.name                       = name
        self.player_damage_event_list   = []
        self.pet_damage_event_list      = []


    # add a damage event to the list
    def add_damage_event(self, de):
        pass

    # clear DE list
    def clear_damage_event_list(self):
        pass

    # build a damage report, subtotaled by damage type
    def damage_report(self):
        pass       

# 
# Inheritance Diagram:
#         
#                         DamageEvent
#                            /   \
#                           /     \
#          DiscreteDamageEvent   DOT_Spell
#                                    /   \
#                                   /     \
#                      LinearDOT_Spell   Splurt_Spell
#         
# common methods:
#       damage_dealt()      returns amount of damage in this particular DamageEvent
#       damage_type()       returns the type of damage for summing
#

#################################################################################################

#
# base class for all damage dealing events
#
class DamageEvent:

    # ctor
    def __init__(self):
        pass


    # function to be overloaded by child classes
    def damage_dealt(self):
        return 0

    # function to return type of damage - spell name, or melee type, or non-melee, etc
    def damage_type(self):
        return None

#################################################################################################

#
# class for a one-time occurence of damage
#
class DiscreteDamageEvent(DamageEvent):

    # ctor
    # for the time parameter, pass at least, or all, of the actual log file line containing the timestamp
    # [Thu Oct 28 15:24:13 2021] A frost giant captain is engulfed in darkness.
    def __init__(self, dmg_type, dmg_amount, eq_timestamp):
        DamageEvent.__init__(self)
        self.dmg_type       = dmg_type
        self.dmg_amount     = dmg_amount
        self.eq_time        = datetime.strptime(eq_timestamp[0:26], '[%a %b %d %H:%M:%S %Y]')

    # function to be overloaded by child classes
    def damage_dealt(self):
        return self.dmg_amount

    # function to return type of damage - spell name, or melee type, or non-melee, etc
    def damage_type(self):
        return self.dmg_type

    # overload funciton to allow object to print() to screen in sensible manner, for debugging with print()
    def __repr__(self):
        return '({}, {}, {})'.format(self.dmg_type,
                                     self.dmg_amount,
                                     self.eq_time)


#################################################################################################


#
# base class for other DOT spells
#
class DOT_Spell(DamageEvent):

    # ctor
    #
    # the 'faded_message' parameter is an opportunity to provide a custom message.  Passing 'None' will cause 
    # the default faded message to be set to 'Your XXX spell has worn off'
    def __init__(self, spell_name, max_duration_sec, landed_message, faded_message = None):
        DamageEvent.__init__(self)

        self.spell_name         = spell_name
        self.max_duration_sec   = int(max_duration_sec)
        self.landed_message     = landed_message
        self.faded_message      = faded_message

        if self.faded_message == None:
            self.faded_message = '^Your ' + self.spell_name + ' spell has worn off'

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

    # function to return type of damage - spell name, or melee type, or non-melee, etc
    def damage_type(self):
        return self.spell_name

    # overload funciton to allow object to print() to screen in sensible manner, for debugging with print()
    def __repr__(self):
        return '({}, {}, {}, {})'.format(self.spell_name,
                                         self.max_duration_sec,
                                         self.start_time,
                                         self.end_time)


#################################################################################################


#
# Most DOT classes work on a linear damage model, i.e. X damage per tick
#
class LinearDOT_Spell(DOT_Spell):

    # ctor
    def __init__(self, spell_name, max_duration_sec, dmg_initial, dmg_per_tick, landed_message, faded_message = None):
        DOT_Spell.__init__(self, spell_name, max_duration_sec, landed_message, faded_message)
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
        return '({}, {}, {}, {}, {}, {}, {}, {})'.format(self.spell_name,
                                                         self.max_duration_sec,
                                                         self.dmg_initial,
                                                         self.dmg_per_tick,
                                                         self.landed_message,
                                                         self.faded_message,
                                                         self.start_time,
                                                         self.end_time)

#################################################################################################


#
# Nonlinear damage accrual (Splurt, others??)
#
class Splurt_Spell(DOT_Spell):

    # ctor
    def __init__(self):
        DOT_Spell.__init__(self, 'Splurt', 102, '^{s}\'s body begins to splurt', None)

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
                                         self.max_duration_sec,
                                         self.landed_message,
                                         self.start_time,
                                         self.end_time)



#################################################################################################





#
# class to do all the damage tracking work
class DamageTracker:

    # ctor
    def __init__(self, client):

        # pointer to the discord client for comms
        self.client         = client

        # a dictionary hash on spell name
        self.spell_dict     = {}
        self.load_spell_dict()



    #
    # check for damage related items
    #
    async def process_line(self, line):

        # cut off the leading date-time stamp info
        trunc_line = line[27:]


        #
        # watch for casting messages
        #
        target = r'^You begin casting (?P<spell_name>[\w` ]+)\.'

        # return value m is either None of an object with information about the RE search
        m = re.match(target, trunc_line)
        if m:

            # fetch the spell name
            spell_name = m.group('spell_name')

            # does the spell name match one of the pets we know about?
            if spell_name in self.spell_dict:
                dmg_spell = self.spell_dict[spell_name]
                await self.client.send('*Spell ({}) being cast*'.format(spell_name))


        #
        # watch for non-melee messages
        #


        #
        # watch for melee messages
        #




    #
    # create the dictionary of pet spells, with all pet spell info for each
    #
    def load_spell_dict(self):

#        #
#        # discrete damage events
#        #
#        ev_type = 'Non-melee'
#        dde = DiscreteDamageEvent(ev_type, r'^(?P<target_name>[\w` ]+) was hit by non-melee for (?P<damage>[\d]+) points of damage')
#        self.spell_dict[ev_type] = dde
#
#        ev_type = 'Melee'
#        dde = DiscreteDamageEvent(ev_type, r'^{} (hits|slashes|pierces|crushes|claws|bites|stings|mauls|gores|punches) (?P<target_name>[\w` ]+) for (?P<damage>[\d]+) point(s)? of damage')
#        self.spell_dict[ev_type] = dde




        #
        # enchanter DOT spells
        #
        spell_name = 'Shallow Breath'
        sp = LinearDOT_Spell(spell_name, 18,  5,  0, r'^(?P<target_name>[\w` ]+) begins to choke')
        self.spell_dict[spell_name] = sp

        spell_name = 'Suffocating Sphere'
        sp = LinearDOT_Spell(spell_name, 18, 10,  8, r'^(?P<target_name>[\w` ]+) gasps for breath')
        self.spell_dict[spell_name] = sp

        spell_name = 'Choke'
        sp = LinearDOT_Spell(spell_name, 36, 20, 12, r'^(?P<target_name>[\w` ]+) begins to choke')
        self.spell_dict[spell_name] = sp

        spell_name = 'Suffocate'
        sp = LinearDOT_Spell(spell_name, 108, 65, 11, r'^(?P<target_name>[\w` ]+) begins to choke')
        self.spell_dict[spell_name] = sp

        spell_name = 'Gasping Embrace'
        sp = LinearDOT_Spell(spell_name, 120, 50, 33, r'^(?P<target_name>[\w` ]+) begins to choke')
        self.spell_dict[spell_name] = sp

        spell_name = 'Torment of Argli'
        sp = LinearDOT_Spell(spell_name, 120,  0, 28, r'^(?P<target_name>[\w` ]+) screams from the Torment of Argli')
        self.spell_dict[spell_name] = sp

        spell_name = 'Asphyxiate'
        sp = LinearDOT_Spell(spell_name, 120, 50, 45, r'^(?P<target_name>[\w` ]+) begins to choke')
        self.spell_dict[spell_name] = sp









    # overload funciton to allow object to print() to screen in sensible manner, for debugging with print()
    def __repr__(self):
        return '({}'.format(self.spell_dict)





















def main():

    sec = 17.999
    print('ticks = {}'.format(sec/6.0))
    print('ticks = {}'.format(int(sec/6.0)))

    line1 = '[Thu Oct 28 15:24:13 2021] A frost giant captain is engulfed in darkness.'
    line2 = '[Thu Oct 28 15:28:13 2021] A frost giant captain is engulfed in darkness.'

    ds1 = LinearDOT_Spell('Cascading Darkness', 96, 0, 72, 'A frost giant captain is engulfed in darkness')
    print(ds1)
    ds1.set_start_time(line1)
    ds1.set_end_time(line2)
    print(ds1)

    print(ds1.elapsed_ticks())
    print(ds1.damage_dealt())


    ds2 = LinearDOT_Spell('Envenomed Bolt', 48, 110, 146, 'landed message')
    ds2.set_start_time(line1)
    ds2.set_end_time(line2)
    print(ds2)

    print(ds2.damage_dealt())


    ds3 = Splurt_Spell()
    ds3.set_start_time(line1)
    ds3.set_end_time(line2)
    print(ds3)

    print(ds3.damage_dealt())



    line3 = '[Mon Sep 06 14:01:09 2021] Zarobab hits a stingtooth piranha for 26 points of damage.'
    line4 = '[Mon Sep 06 14:01:11 2021] Goliathette slashes a stingtooth piranha for 25 points of damage.'
    melee_target = r'^(?P<attacker_name>[\w` ]+) (?P<dmg_type>(hits|slashes|pierces|crushes|claws|bites|stings|mauls|gores|punches|kicks|backstabs)) (?P<target_name>[\w` ]+) for (?P<damage>[\d]+) point(s)? of damage'

    m = re.match(melee_target, line3[27:], re.IGNORECASE)
    if m:
        attacker_name   = m.group('attacker_name')
        dmg_type        = m.group('dmg_type')
        target_name     = m.group('target_name')
        dmg             = m.group('damage')
        print('Melee: Attacker / Type / Target / Damage: {}, {}, {}, {}'.format(attacker_name, dmg_type, target_name, dmg))
        dde             = DiscreteDamageEvent(dmg_type, dmg, line3)
        print(dde)
    m = re.match(melee_target, line4[27:], re.IGNORECASE)
    if m:
        attacker_name   = m.group('attacker_name')
        dmg_type        = m.group('dmg_type')
        target_name     = m.group('target_name')
        dmg             = m.group('damage')
        print('Melee: Attacker / Type / Target / Damage: {}, {}, {}, {}'.format(attacker_name, dmg_type, target_name, dmg))
        dde             = DiscreteDamageEvent(dmg_type, dmg, line3)
        print(dde)


    line5 = '[Wed Dec 01 21:08:15 2021] a kiraikuei was hit by non-melee for 315 points of damage.'
    non_melee_target = r'^(?P<target_name>[\w` ]+) was hit by (?P<dmg_type>[\w`\- ]+) for (?P<damage>[\d]+) points of damage'

    m = re.match(non_melee_target, line5[27:], re.IGNORECASE)
    if m:
        target_name = m.group('target_name')
        dmg_type        = m.group('dmg_type')
        dmg = m.group('damage')
        print('Non-Melee: Type / Target / Damage: {}, {}, {}'.format(dmg_type, target_name, dmg))
        dde = DiscreteDamageEvent('non-melee', dmg, line3)
        print(dde)



    dt = DamageTracker(None)
    print(dt)




if __name__ == '__main__':
    main()



