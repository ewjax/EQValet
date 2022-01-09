# import the datetime class from the datetime module
from datetime import datetime
import re
import copy
import pickle


import myconfig
from smartbuffer import SmartBuffer 



#################################################################################################
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
# common data:
#       attacker_name       
#       target_name
#       eq_time                                                     for discrete events, the time.  For DOT's, the start time
#
# common methods:
#       set_instance_data(attacker_name, target_name, eq_timestamp) set instance info
#       damage_dealt()                                              returns amount of damage in this particular DamageEvent
#       damage_type()                                               returns the type of damage for summing
#       is_ticking()                                                only returns true for DOT spells that have yet to close out
#

#################################################################################################

#
# base class for all damage dealing events
#
class DamageEvent:

    # ctor
    def __init__(self):

        # common data, to be set when an instance of the DamageEvent is created
        self.attacker_name  = None
        self.target_name    = None
        self._eq_time       = None


    # set instance data
    # eq_timestamp assumed to be in the format of EQ logfile timestamp
    def set_instance_data(self, attacker_name, target_name, eq_timestamp):
        self.attacker_name  = attacker_name
        self.target_name    = target_name
        self._eq_time       = datetime.strptime(eq_timestamp[0:26], '[%a %b %d %H:%M:%S %Y]')

    # function to be overloaded by child classes
    def damage_dealt(self):
        return int(0)

    # function to return type of damage - spell name, or melee type, or non-melee, etc
    def damage_type(self):
        return None

    # only returns true for DOT spells that are not yet closed out
    def is_ticking(self):
        return False

#################################################################################################

#
# class for a one-time occurence of damage
#
class DiscreteDamageEvent(DamageEvent):

    # ctor
    # for the time parameter, pass at least, or all, of the actual log file line containing the timestamp
    # [Thu Oct 28 15:24:13 2021] A frost giant captain is engulfed in darkness.
    def __init__(self, attacker_name, target_name, eq_timestamp, dmg_type, dmg_amount):
        DamageEvent.__init__(self)
        self.set_instance_data(attacker_name, target_name, eq_timestamp)
        self.dmg_type       = dmg_type
        self.dmg_amount     = int(dmg_amount)

    # function to be overloaded by child classes
    def damage_dealt(self):
        return self.dmg_amount

    # function to return type of damage - spell name, or melee type, or non-melee, etc
    def damage_type(self):
        return self.dmg_type

    # overload funciton to allow object to print() to screen in sensible manner, for debugging with print()
    def __repr__(self):
        return '({}, {}, {}, {}, {})'.format(self.attacker_name, 
                                             self.target_name,
                                             self._eq_time,
                                             self.dmg_type,
                                             self.dmg_amount)


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

        # this will get set later
        self._end_time          = None


    # set the start time - shouldn't need this, normally would be set in set_instance_info(), but provide it just in case
    # using the very capable strptime() parsing function built into the datetime module
    # [Thu Oct 28 15:24:13 2021] A frost giant captain is engulfed in darkness.
    def set_start_time(self, eq_timestamp):
        self._eq_time = datetime.strptime(eq_timestamp[0:26], '[%a %b %d %H:%M:%S %Y]')

    # set the end time
    # using the very capable strptime() parsing function built into the datetime module
    # [Thu Oct 28 15:24:13 2021] A frost giant captain is engulfed in darkness.
    def set_end_time(self, eq_timestamp):
        self._end_time = datetime.strptime(eq_timestamp[0:26], '[%a %b %d %H:%M:%S %Y]')

    # helper function to get number of ticks elapsed 
    def elapsed_ticks(self):
        ticks = 0
        if (self._end_time and self._eq_time):
            elapsed_timedelta = self._end_time - self._eq_time
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

    # returns true if end time has not yet been set in this spell
    def is_ticking(self):
        rv = False
        if self._end_time == None:
            rv = True
        return rv

    # overload funciton to allow object to print() to screen in sensible manner, for debugging with print()
    def __repr__(self):
        return '({}, {}, {}, {}, {}, {}, {}, {})'.format(self.attacker_name,
                                                         self.target_name,
                                                         self._eq_time,
                                                         self._end_time,
                                                         self.spell_name,
                                                         self.max_duration_sec,
                                                         self.landed_message,
                                                         self.faded_message)


#################################################################################################


#
# Most DOT classes work on a linear damage model, i.e. X damage per tick
#
class LinearDOT_Spell(DOT_Spell):

    # ctor
    def __init__(self, spell_name, max_duration_sec, dmg_initial, dmg_per_tick, landed_message, faded_message = None):
        DOT_Spell.__init__(self, spell_name, max_duration_sec, landed_message, faded_message)
        self.dmg_initial    = int(dmg_initial)
        self.dmg_per_tick   = int(dmg_per_tick)

    # overload the damage_dealt() function
    def damage_dealt(self):
        damage = 0
        if (self._end_time and self._eq_time):
            ticks = self.elapsed_ticks()
            damage = self.dmg_initial + ticks * self.dmg_per_tick
        return damage


    # overload funciton to allow object to print() to screen in sensible manner, for debugging with print()
    def __repr__(self):
        return '({}, {}, {}, {}, {}, {}, {}, {}, {}, {})'.format(self.attacker_name,
                                                                 self.target_name,
                                                                 self._eq_time,
                                                                 self._end_time,
                                                                 self.spell_name,
                                                                 self.max_duration_sec,
                                                                 self.dmg_initial,
                                                                 self.dmg_per_tick,
                                                                 self.landed_message,
                                                                 self.faded_message)

#################################################################################################


#
# Nonlinear damage accrual (Splurt, others??)
#
class Splurt_Spell(DOT_Spell):

    # ctor
    def __init__(self):
        DOT_Spell.__init__(self, 'Splurt', 102, r'^(?P<target_name>[\w` ]+)\'s body begins to splurt', None)

    # overload the damage_dealt() function
    def damage_dealt(self):
        damage = 0
        if (self._end_time and self._eq_time):

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
        return '({}, {}, {}, {}, {}, {}, {})'.format(self.attacker_name,
                                                     self.target_name,
                                                     self._eq_time,
                                                     self._end_time,
                                                     self.spell_name,
                                                     self.max_duration_sec,
                                                     self.landed_message)





#################################################################################################

#
# class for Targets
#
class Target:

    # ctor
    def __init__(self):

        # target name
        self.target_name                = None
        self.in_combat                  = False
        self._first_combat_time         = None
        self._last_combat_time          = None

        # max value the target is hitting for
        self.max_melee                  = 0

        # a dictionary of lists, keys = attacker names, values = list[] of all DamageEvents done by that attacker
        self.damage_events_dict = {}

    # process a melee attack
    def check_melee(self, dmg):
        if self.max_melee < dmg:
            self.max_melee = dmg

    # implied target level, from max melee value
    def implied_level(self):
        level = 0
        if self.max_melee <= 60:
            level = self.max_melee / 2
        else:
            level = (self.max_melee  + 60) / 4
        return level

    # start combat
    def start_combat(self, target_name, eq_timestamp):
        self.target_name = target_name
        self._first_combat_time = datetime.strptime(eq_timestamp[0:26], '[%a %b %d %H:%M:%S %Y]')
        self._last_combat_time = datetime.strptime(eq_timestamp[0:26], '[%a %b %d %H:%M:%S %Y]')
        self.in_combat = True

    # end combat
    def end_combat(self, eq_timestamp):

        self._last_combat_time = datetime.strptime(eq_timestamp[0:26], '[%a %b %d %H:%M:%S %Y]')
        self.in_combat = False

        # for each attacker..
        for attacker in self.damage_events_dict:
            # get the list of DE events for this attacker
            de_list = self.damage_events_dict[attacker]
            # for each event in the list
            for de in de_list:
                if de.is_ticking():
                    de.set_end_time(eq_timestamp)

    # clear DE list
    def clear(self):
        self.target_name                = None
        self.in_combat                  = False
        self._first_combat_time         = None
        self._last_combat_time          = None
        self.max_melee                  = 0

        self.damage_events_dict.clear()


    # combat timeout time in seconds - time since last DamageEvent
    def combat_timeout_seconds(self, eq_timestamp):
        now = datetime.strptime(eq_timestamp[0:26], '[%a %b %d %H:%M:%S %Y]')
        elapsed_timedelta = now - self._last_combat_time
        elapsed_seconds = elapsed_timedelta.total_seconds()
        return elapsed_seconds

    # combat duration in seconds - first to last
    def combat_duration_seconds(self):
        elapsed_timedelta = self._last_combat_time - self._first_combat_time
        elapsed_seconds = elapsed_timedelta.total_seconds()
        return elapsed_seconds


    # add a damage event to the list
    def add_damage_event(self, de):

        # targets must match
        if (self.target_name.casefold() == de.target_name.casefold()) and self.in_combat:
            
            # is there an entry in the dictionary for this attacker?
            if de.attacker_name not in self.damage_events_dict:
                self.damage_events_dict[de.attacker_name] = []

            de_list = self.damage_events_dict[de.attacker_name]
            de_list.append(de)
            self._last_combat_time = de._eq_time

    # build a damage report, subtotaled by damage type
    async def damage_report(self, client):

        # total damage dealt to this target
        grand_total = 0

        # walk the list initially just to get attacker totals, save in a dictionary, key = attacker names, values = dmg total for that attacker
        attacker_summary_dict = {}

        # for each attacker in the damate_events_dict
        for attacker in self.damage_events_dict:

            # first one?
            if attacker not in attacker_summary_dict:
                attacker_summary_dict[attacker] = 0

            # for each DamageEvent in the list for this attacker...
            de_list = self.damage_events_dict[attacker]
            for de in de_list:
                dd = de.damage_dealt()
                attacker_summary_dict[attacker] += dd
                grand_total += dd

        # now create the output report
        sb = SmartBuffer()
        sb.add('Damage Report, Target: ====[{:^30}]==============================================\n'.format(self.target_name))
        sb.add('Implied Level: {}\n'.format(self.implied_level()))
        sb.add('Combat Duration (sec): {}\n'.format(self.combat_duration_seconds()))

        # walk the list of attackers, sort the attacker dictionary on total damage done...
        for (attacker, attacker_total) in sorted(attacker_summary_dict.items(), key = lambda tuple:tuple[1], reverse = True):
            sb.add('        {}\n'.format(attacker))

            # create a dictionary, keys = damage types, values = integer total damage done for that damage type
            dmg_type_summary_dict = {}
            de_list = self.damage_events_dict[attacker]

            # for each DamageEvent in the list...
            for de in de_list:
                if de.damage_type() not in dmg_type_summary_dict:
                    dmg_type_summary_dict[de.damage_type()] = 0
                dmg_type_summary_dict[de.damage_type()] += de.damage_dealt()

            # sort damage type report from highest to lowest damage
            for (type, type_damage_sum) in sorted(dmg_type_summary_dict.items(), key = lambda tuple:tuple[1], reverse = True):
                sb.add('{:>35}: {:>5}\n'.format(type, type_damage_sum))

            sb.add('{:>35}: {:>5} ({}%)\n'.format('Total', attacker_total, int(attacker_total/grand_total*100.0)))

        sb.add('\n')
        sb.add('{:>35}: {:>5} (100%)\n'.format('Grand Total', grand_total))

        sb.add('---------------------------------------------------------------------------------------------------------\n')

        # get the list of buffers and send each to discord
        bufflist = sb.get_bufflist()
        for b in bufflist:
            # surrounding the text with 3 back-ticks makes the resulting output code-formatted, i.e. a fixed width font for each table creation
            await client.send('```{}```'.format(b))





#################################################################################################

#
# class to do all the damage tracking work
#
class DamageTracker:

    # ctor
    def __init__(self, client):

        # pointer to the discord client for comms
        self.client                     = client

        # the target that is being attacked
        self.the_target                 = Target()

        # dictionary of all known DOT_Spells, keys = spell names, contents = DOT_Spell objects
        self.spell_dict                 = {}
        self.load_spell_dict()

        # use this flag for when we have detected the start of a spell cast and need to watch for the landed message
        # this is a pointer to the actual spell that is pending
        self.spell_pending              = None
        self.spell_pending_start        = None

        # combat timeout
        self.combat_timeout             = myconfig.COMBAT_TIMEOUT_SEC

        # set of player names
        self.player_names_set           = set()
        self.player_names_fname         = 'players.pickle'
        self.read_player_names()

    #
    # read in the player_names
    #
    def read_player_names(self):

        # throws and exception if file doesn't exist
        try:
            f = open(self.player_names_fname, 'rb')
            self.player_names_set = pickle.load(f)
            f.close()

            count = len(self.player_names_set)
            print('Read {} player names from [{}]'.format(count, self.player_names_fname))

            return True
        except:
            print('Unable to open filename: [{}]'.format(self.player_names_fname))
            return False

    #
    # write out the player_names
    #
    async def write_player_names(self):
        try:
            f = open(self.player_names_fname, 'wb')
            pickle.dump(self.player_names_set, f)
            f.close()

            count = len(self.player_names_set)
            await self.client.send('Wrote {} player names to [{}]'.format(count, self.player_names_fname))

            return True
        except:
            print('Unable to open filename: [{}]'.format(self.player_names_fname))
            # return False

    #
    # check for damage related items
    #
    async def process_line(self, line):

        # cut off the leading date-time stamp info
        trunc_line = line[27:]

        #
        # watch for conditions indicating combat is finished
        #
        if self.the_target.in_combat:

            end_combat = False

            # exp message
            target = r'^(You gain experience|You gain party experience)'
            m = re.match(target, trunc_line)
            if m:
                end_combat = True

            # target is slain by pet or anyone else
            target = r'^(?P<target_name>[\w` ]+) has been slain'
            m = re.match(target, trunc_line)
            if m:
                # extract RE data
                target_name = m.group('target_name')
                if target_name.casefold() == self.the_target.target_name.casefold():
                    end_combat = True

            # target is slain by player
            target = r'^You have slain (?P<target_name>[\w` ]+)'
            m = re.match(target, trunc_line)
            if m:
                # extract RE data
                target_name = m.group('target_name')
                if target_name.casefold() == self.the_target.target_name.casefold():
                    end_combat = True

            # combat timeout
            if self.the_target.combat_timeout_seconds(line) > self.combat_timeout:
                # ...then the combat timer has time out
                await self.client.send('*Combat: Timed out*')
                end_combat = True

            # close out damage tracking
            if end_combat:
                self.the_target.end_combat(line)
                await self.the_target.damage_report(self.client)
                self.the_target.clear()



        #
        # check for timeout on spell landed messages
        #
        if self.spell_pending:

            # get current time and check for timeout
            now = datetime.strptime(line[0:26], '[%a %b %d %H:%M:%S %Y]')
            elapsed_seconds = (now - self.spell_pending_start)
            if (elapsed_seconds.total_seconds() > myconfig.SPELL_PENDING_TIMEOUT_SEC):
                # ...then this spell pending is expired
                await self.client.send('*Spell ({}) no longer pending: Timed out*'.format(self.spell_pending.spell_name))
                self.spell_pending = None
                self.spell_pending_start = None

        #
        # watch for landed messages
        #
        if self.spell_pending:

            # get the landed message for the spell that is pending
            target = self.spell_pending.landed_message
            m = re.match(target, trunc_line)
            if m:

                # extract RE data
                target_name = m.group('target_name')

                # set the attacker name to the player name
                attacker_name = self.client.elf.char_name

                # any damage event indicates we are in combat
                if self.the_target.in_combat == False:
                    self.the_target.start_combat(target_name, line)
                    await self.client.send('*Combat begun: {}*'.format(target_name))

                # is this spell already in the DE list for the player, and still ticking?  if so, close the existing, and add the new one
                de_list = self.the_target.damage_events_dict.get(attacker_name)
                # for each event in the player's DE list
                if de_list:
                    for de in de_list:
                        if de.is_ticking():
                            if self.spell_pending.spell_name == de.spell_name:
                                de.set_end_time(line)
                                await self.client.send('*{} overwritten with new*'.format(de.spell_name))

                # add the DamageEvent
                de = copy.copy(self.spell_pending)
                de.set_instance_data(attacker_name, target_name, line)
                self.the_target.add_damage_event(de)

                # reset the spell pending flag
                self.spell_pending = None
                self.spell_pending_start = None


        #
        # watch for spell faded conditions -only check DamageEvents that are not closed, i.e. still ticking
        #
        if self.the_target.in_combat:
            attacker_name = self.client.elf.char_name
            de_list = self.the_target.damage_events_dict.get(attacker_name)
            # for each event in the player's DE list
            if de_list:
                for de in de_list:
                    if de.is_ticking():
                        target = de.faded_message
                        m = re.match(target, trunc_line)
                        if m:
                            de.set_end_time(line)
                            await self.client.send('*{} faded*'.format(de.spell_name))


        #
        # watch for casting messages
        #
        target = r'^You begin casting (?P<spell_name>[\w` ]+)\.'
        m = re.match(target, trunc_line)
        if m:

            # fetch the spell name
            spell_name = m.group('spell_name')

            # does the spell name match one of the pets we know about?
            if spell_name in self.spell_dict:
                self.spell_pending = self.spell_dict[spell_name]
                self.spell_pending_start = datetime.strptime(line[0:26], '[%a %b %d %H:%M:%S %Y]')


        #
        # watch for non-melee messages
        #
        target = r'^(?P<target_name>[\w` ]+) was hit by (?P<dmg_type>[\w`\- ]+) for (?P<damage>[\d]+) point(s)? of damage'
        m = re.match(target, trunc_line)
        if m:
            # extract RE data
            target_name = m.group('target_name')
            dmg_type = m.group('dmg_type')
            damage = int(m.group('damage'))

            # set the attacker name
            # will usually be player name, unless, this message is from a pet lifetap
            attacker_name = self.client.elf.char_name
            if damage < 100:
                if self.client.pet_tracker.current_pet:
                    if self.client.pet_tracker.current_pet.lifetap_pending:
                        attacker_name = self.client.pet_tracker.current_pet.pet_name

            # any damage event indicates we are in combat
            if self.the_target.in_combat == False:
                self.the_target.start_combat(target_name, line)
                await self.client.send('*Combat begun: {}*'.format(target_name))

            # add the DamageEvent
            dde = DiscreteDamageEvent(attacker_name, target_name, line, dmg_type, damage)
            self.the_target.add_damage_event(dde)


        #
        # watch for melee misses by me
        #
        target = r'^You try to (?P<dmg_type>(hit|slash|pierce|crush|claw|bite|sting|maul|gore|punch|kick|backstab|bash)) (?P<target_name>[\w` ]+), but miss!'
        m = re.match(target, trunc_line)
        if m:
            # extract RE data
            attacker_name = self.client.elf.char_name
            dmg_type = m.group('dmg_type')
            target_name = m.group('target_name')

            # any damage event indicates we are in combat
            if self.the_target.in_combat == False:
                self.the_target.start_combat(target_name, line)
                await self.client.send('*Combat begun: {}*'.format(target_name))

        #
        # watch for melee messages by me
        #
        target = r'^You (?P<dmg_type>(hit|slash|pierce|crush|claw|bite|sting|maul|gore|punch|kick|backstab|bash)) (?P<target_name>[\w` ]+) for (?P<damage>[\d]+) point(s)? of damage'
        m = re.match(target, trunc_line)
        if m:

            # extract RE data
            attacker_name = self.client.elf.char_name
            dmg_type = m.group('dmg_type')
            target_name = m.group('target_name')
            damage = int(m.group('damage'))

            # any damage event indicates we are in combat
            if self.the_target.in_combat == False:
                self.the_target.start_combat(target_name, line)
                await self.client.send('*Combat begun: {}*'.format(target_name))

            # add the DamageEvent
            dde = DiscreteDamageEvent(attacker_name, target_name, line, dmg_type, damage)
            self.the_target.add_damage_event(dde)


        #
        # watch for melee messages
        #
        target = r'^(?P<attacker_name>[\w` ]+) (?P<dmg_type>(hits|slashes|pierces|crushes|claws|bites|stings|mauls|gores|punches|kicks|backstabs|bashes)) (?P<target_name>[\w` ]+) for (?P<damage>[\d]+) point(s)? of damage'
        m = re.match(target, trunc_line)
        if m:

            # extract RE data
            attacker_name = m.group('attacker_name')
            dmg_type = m.group('dmg_type')
            target_name = m.group('target_name')
            damage = int(m.group('damage'))

            # if the target name is YOU, or target name is a name in the /who player database,
            # then the attacker is actually the target
            if (target_name == 'YOU') or (target_name in self.player_names_set):
                target_name = attacker_name

                if self.the_target:
                    self.the_target.check_melee(damage)

                # any damage event indicates we are in combat
                if self.the_target.in_combat == False:
                    self.the_target.start_combat(target_name, line)
                    await self.client.send('*Combat begun: {}*'.format(target_name))

            # don't track attacks on player
            else:

                # any damage event indicates we are in combat
                if self.the_target.in_combat == False:
                    self.the_target.start_combat(target_name, line)
                    await self.client.send('*Combat begun: {}*'.format(target_name))

                # add the DamageEvent
                dde = DiscreteDamageEvent(attacker_name, target_name, line, dmg_type, damage)
                self.the_target.add_damage_event(dde)

        #
        # watch for /who messages
        #
        target = r'^Players (in|on) EverQuest'
        m = re.match(target, trunc_line)
        if m:
            processing_names = True
            player_names_set_modified = False

#            # debugging output
#            print('===============/who detected: {}'.format(trunc_line), end = '')

#                [Sun Dec 19 20:33:44 2021] Players on EverQuest:
#                [Sun Dec 19 20:33:44 2021] ---------------------------
#                [Sun Dec 19 20:33:44 2021] [ANONYMOUS] Aijalon 
#                [Sun Dec 19 20:33:44 2021] [ANONYMOUS] Yihao 
#                [Sun Dec 19 20:33:44 2021] [54 Disciple] Weth (Iksar) <Safe Space>
#                [Sun Dec 19 20:33:44 2021] [54 Disciple] Rcva (Iksar) <Kingdom>
#                [Sun Dec 19 20:33:44 2021] [ANONYMOUS] Yula  <Force of Will>
#                [Sun Dec 19 20:33:44 2021] [57 Master] Twywu (Iksar) <Safe Space>
#                [Sun Dec 19 20:33:44 2021] [ANONYMOUS] Tenedorf  <Safe Space>
#                [Sun Dec 19 20:33:44 2021] [60 Grave Lord] Gratton (Troll) <Force of Will>
#                [Sun Dec 19 20:33:44 2021] [ANONYMOUS] Bloodreign 
#                [Sun Dec 19 20:33:44 2021] [60 Phantasmist] Azleep (Elemental) <Force of Will>
#                [Sun Dec 19 20:33:44 2021] There are 10 players in Trakanon's Teeth.

            # get next line - many dashes
            nextline = self.client.elf.readline()
            print(nextline, end = '')
            trunc_line = nextline[27:]

            # read all the name(s) in the /who report
            while processing_names:

                # get next line
                nextline = self.client.elf.readline()
                print(nextline, end = '')
                trunc_line = nextline[27:]

                # as a safety net, just presume this is not the next name on the report
                processing_names = False

#               from ninjalooter:
#                    MATCH_WHO = re.compile(
#                        TIMESTAMP +
#                        r"(?:AFK +)?(?:<LINKDEAD>)?\[(?P<level>\d+ )?(?P<class>[A-z ]+)\] +"
#                        r"(?P<name>\w+)(?: *\((?P<race>[\w ]+)\))?(?: *<(?P<guild>[\w ]+)>)?")

                # oddly, sometimes the name lists is preceeded by a completely blank line, usuall when a /who all command has been issued
                # this regex allows for a blank line
                name_target = r'(^(?: AFK +)?(?:<LINKDEAD>)?\[(?P<player_level>\d+ )?(?P<player_class>[A-z ]+)\] (?P<player_name>[\w` ]+)|^$)'
                m = re.match(name_target, trunc_line)
                if m:
                    # since we did successfully find a name, extend the processing for another line
                    processing_names = True

                    # process the name.  will return None if got here via the empty ^$ line that /who all puts out
                    player_name = m.group('player_name')
                    if player_name:
                        print(player_name)

                    player_level = m.group('player_level')
                    if player_level:
                        print(player_level)

                    player_class = m.group('player_class')
                    if player_class:
                        print(player_class)

                    if player_name not in self.player_names_set:
                        self.player_names_set.add(player_name)
                        player_names_set_modified = True

            # done processing /who list
            if player_names_set_modified:
                await self.write_player_names()





    #
    # create the dictionary of pet spells, with all pet spell info for each
    #
    def load_spell_dict(self):

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


        #
        # necro DOT spells
        #
        # all the linear dot spells
        spell_name = 'Disease Cloud'
        sp = LinearDOT_Spell(spell_name, 360,   5,   1, r'^(?P<target_name>[\w` ]+) doubles over in pain')
        self.spell_dict[spell_name] = sp

        spell_name = 'Clinging Darkness'
        sp = LinearDOT_Spell(spell_name,  36,   0,   5, r'^(?P<target_name>[\w` ]+) is surrounded by darkness')
        self.spell_dict[spell_name] = sp

        spell_name = 'Poison Bolt'
        sp = LinearDOT_Spell(spell_name,  42,   6,   5, r'^(?P<target_name>[\w` ]+) has been poisoned')
        self.spell_dict[spell_name] = sp

        spell_name = 'Engulfing Darkness'
        sp = LinearDOT_Spell(spell_name,  66,   0,  11, r'^(?P<target_name>[\w` ]+) is engulfed in darkness')
        self.spell_dict[spell_name] = sp

        spell_name = 'Heat Blood'
        sp = LinearDOT_Spell(spell_name,  60,   0,  17, r'^(?P<target_name>[\w` ]+)\'s blood simmers')
        self.spell_dict[spell_name] = sp

        spell_name = 'Leach'
        sp = LinearDOT_Spell(spell_name,  54,   0,   8, r'^(?P<target_name>[\w` ]+) pales')
        self.spell_dict[spell_name] = sp

        spell_name = 'Heart Flutter'
        sp = LinearDOT_Spell(spell_name,  72,   0,  12, r'^(?P<target_name>[\w` ]+) clutches their chest')
        self.spell_dict[spell_name] = sp

        spell_name = 'Infectious Cloud'
        sp = LinearDOT_Spell(spell_name, 126,  20,   5, r'^(?P<target_name>[\w` ]+) starts to wretch')
        self.spell_dict[spell_name] = sp

        spell_name = 'Boil Blood'
        sp = LinearDOT_Spell(spell_name, 126,   0,  24, r'^(?P<target_name>[\w` ]+)\'s blood boils')
        self.spell_dict[spell_name] = sp

        spell_name = 'Dooming Darkness'
        sp = LinearDOT_Spell(spell_name,  96,   0,  20, r'^(?P<target_name>[\w` ]+) is engulfed in darkness')
        self.spell_dict[spell_name] = sp

        spell_name = 'Vampiric Curse'
        sp = LinearDOT_Spell(spell_name,  54,   0,  21, r'^(?P<target_name>[\w` ]+) pales')
        self.spell_dict[spell_name] = sp

        spell_name = 'Venom of the Snake'
        sp = LinearDOT_Spell(spell_name,  48,  40,  59, r'^(?P<target_name>[\w` ]+) has been poisoned')
        self.spell_dict[spell_name] = sp

        spell_name = 'Scourge'
        sp = LinearDOT_Spell(spell_name, 126,  40,  24, r'^(?P<target_name>[\w` ]+) sweats and shivers, looking feverish')
        self.spell_dict[spell_name] = sp

        spell_name = 'Chilling Embrace'
        sp = LinearDOT_Spell(spell_name,  96,   0,  40, r'^(?P<target_name>[\w` ]+) is wracked by chilling poison')
        self.spell_dict[spell_name] = sp

        spell_name = 'Asystole'
        sp = LinearDOT_Spell(spell_name,  60,   0,  69, r'^(?P<target_name>[\w` ]+) clutches their chest')
        self.spell_dict[spell_name] = sp

        spell_name = 'Bond of Death'
        sp = LinearDOT_Spell(spell_name,  54,   0,  80, r'^(?P<target_name>[\w` ]+) staggers')
        self.spell_dict[spell_name] = sp

        spell_name = 'Cascading Darkness'
        sp = LinearDOT_Spell(spell_name,  96,   0,  72, r'^(?P<target_name>[\w` ]+) is engulfed in darkness')
        self.spell_dict[spell_name] = sp

        spell_name = 'Ignite Blood'
        sp = LinearDOT_Spell(spell_name, 126,   0,  56, r'^(?P<target_name>[\w` ]+)\'s blood ignites')
        self.spell_dict[spell_name] = sp

        spell_name = 'Envenomed Bolt'
        sp = LinearDOT_Spell(spell_name,  48, 110, 146, r'^(?P<target_name>[\w` ]+) has been poisoned')
        self.spell_dict[spell_name] = sp

        spell_name = 'Plague'
        sp = LinearDOT_Spell(spell_name, 132,  60,  55, r'^(?P<target_name>[\w` ]+) sweats and shivers, looking feverish')
        self.spell_dict[spell_name] = sp

        spell_name = 'Cessation of Cor'
        sp = LinearDOT_Spell(spell_name,  60, 100, 100, r'^(?P<target_name>[\w` ]+)\'s blood stills within their veins')
        self.spell_dict[spell_name] = sp

        spell_name = 'Vexing Mordinia'
        sp = LinearDOT_Spell(spell_name,  54,   0, 122, r'^(?P<target_name>[\w` ]+) staggers under the curse of Vexing Mordinia')
        self.spell_dict[spell_name] = sp

        spell_name = 'Pyrocruor'
        sp = LinearDOT_Spell(spell_name, 114,   0, 111, r'^(?P<target_name>[\w` ]+)\'s blood ignites')
        self.spell_dict[spell_name] = sp

        spell_name = 'Devouring Darkness'
        sp = LinearDOT_Spell(spell_name,  78,   0, 107, r'^(?P<target_name>[\w` ]+) is engulfed in devouring darkness')
        self.spell_dict[spell_name] = sp

        spell_name = 'Torment of Shadows'
        sp = LinearDOT_Spell(spell_name,  96,   0,  75, r'^(?P<target_name>[\w` ]+) is gripped by shadows of fear and terror')
        self.spell_dict[spell_name] = sp


        # the only non-linear dot spell
        spell_name = 'Splurt'
        sp = Splurt_Spell()
        self.spell_dict[spell_name] = sp


    # overload funciton to allow object to print() to screen in sensible manner, for debugging with print()
    def __repr__(self):
        return '({}'.format(self.spell_dict)





















def main():

#    sec = 17.999
#    print('ticks = {}'.format(sec/6.0))
#    print('ticks = {}'.format(int(sec/6.0)))

    line1 = '[Thu Oct 28 15:24:13 2021] A frost giant captain is engulfed in darkness.'
    line2 = '[Thu Oct 28 15:28:13 2021] A frost giant captain is engulfed in darkness.'
#
#    ds1 = LinearDOT_Spell(None, None, None, 'Cascading Darkness', 96, 0, 72, 'A frost giant captain is engulfed in darkness')
#    print(ds1)
#    ds1.set_start_time(line1)
#    ds1.set_end_time(line2)
#    print(ds1)
#
#    print(ds1.elapsed_ticks())
#    print(ds1.damage_dealt())


#    ds2 = LinearDOT_Spell('Envenomed Bolt', 48, 110, 146, 'landed message')
#    ds22 = copy.copy(ds2)
#
#    ds22.set_instance_data('Attakker', 'TheTarget', line1)
#    ds22.set_end_time(line2)
#
#    print(ds2)
#    print(ds22)
#
#    print(ds2.damage_dealt())
#    print(ds22.damage_dealt())


    target_name = 'a stingtooth piranha'
    the_target = Target()
    the_target.set_target_name(target_name)


    ds2 = LinearDOT_Spell('Envenomed Bolt', 48, 110, 146, 'landed message')
    ds22 = copy.copy(ds2)

    ds22.set_instance_data('Xytl', target_name, line1)
    ds22.set_end_time(line2)
    the_target.add_damage_event(ds22)


    ds3 = Splurt_Spell()
    ds33 = copy.copy(ds3)

    ds33.set_instance_data('Xytl', target_name, line1)
    ds33.set_end_time(line2)
    the_target.add_damage_event(ds33)


#
#    print(ds3)
#    print(ds3.damage_dealt())
#
#    print(ds33)
#    print(ds33.damage_dealt())




    line3 = '[Mon Sep 06 14:01:09 2021] Zarobab hits a stingtooth piranha for 26 points of damage.'
    line4 = '[Mon Sep 06 14:01:11 2021] Goliathette slashes a stingtooth piranha for 25 points of damage.'
    line44 = '[Mon Sep 06 14:01:11 2021] Goliathette slashes a stingtooth piranha for 125 points of damage.'
    line45 = '[Mon Sep 06 14:01:11 2021] Goliathette hits a stingtooth piranha for 99 points of damage.'
    melee_target = r'^(?P<attacker_name>[\w` ]+) (?P<dmg_type>(hits|slashes|pierces|crushes|claws|bites|stings|mauls|gores|punches|kicks|backstabs)) (?P<target_name>[\w` ]+) for (?P<damage>[\d]+) point(s)? of damage'

    m = re.match(melee_target, line3[27:], re.IGNORECASE)
    if m:
        attacker_name   = m.group('attacker_name')
        dmg_type        = m.group('dmg_type')
        target_name     = m.group('target_name')
        dmg             = m.group('damage')
#        print('Melee: Attacker / Type / Target / Damage: {}, {}, {}, {}'.format(attacker_name, dmg_type, target_name, dmg))
        dde             = DiscreteDamageEvent(attacker_name, target_name, line3, dmg_type, dmg)
#        print(dde)

        the_target.add_damage_event(dde)


    m = re.match(melee_target, line4[27:], re.IGNORECASE)
    if m:
        attacker_name   = m.group('attacker_name')
        dmg_type        = m.group('dmg_type')
        target_name     = m.group('target_name')
        dmg             = m.group('damage')
#        print('Melee: Attacker / Type / Target / Damage: {}, {}, {}, {}'.format(attacker_name, dmg_type, target_name, dmg))
        dde             = DiscreteDamageEvent(attacker_name, target_name, line4, dmg_type, dmg)
#        print(dde)

        the_target.add_damage_event(dde)


    m = re.match(melee_target, line44[27:], re.IGNORECASE)
    if m:
        attacker_name   = m.group('attacker_name')
        dmg_type        = m.group('dmg_type')
        target_name     = m.group('target_name')
        dmg             = m.group('damage')
#        print('Melee: Attacker / Type / Target / Damage: {}, {}, {}, {}'.format(attacker_name, dmg_type, target_name, dmg))
        dde             = DiscreteDamageEvent(attacker_name, target_name, line44, dmg_type, dmg)
#        print(dde)

        the_target.add_damage_event(dde)

    m = re.match(melee_target, line45[27:], re.IGNORECASE)
    if m:
        attacker_name   = m.group('attacker_name')
        dmg_type        = m.group('dmg_type')
        target_name     = m.group('target_name')
        dmg             = m.group('damage')
#        print('Melee: Attacker / Type / Target / Damage: {}, {}, {}, {}'.format(attacker_name, dmg_type, target_name, dmg))
        dde             = DiscreteDamageEvent(attacker_name, target_name, line45, dmg_type, dmg)
#        print(dde)

        the_target.add_damage_event(dde)





    line5 = '[Wed Dec 01 21:08:15 2021] a stingtooth piranha was hit by non-melee for 315 points of damage.'
    non_melee_target = r'^(?P<target_name>[\w` ]+) was hit by (?P<dmg_type>[\w`\- ]+) for (?P<damage>[\d]+) points of damage'

    m = re.match(non_melee_target, line5[27:], re.IGNORECASE)
    if m:
        attacker_name = 'Xytl'
        target_name = m.group('target_name')
        dmg_type        = m.group('dmg_type')
        dmg = m.group('damage')
#        print('Non-Melee: Type / Target / Damage: {}, {}, {}'.format(dmg_type, target_name, dmg))
        dde = DiscreteDamageEvent(attacker_name, target_name, line5, dmg_type, dmg)
#        print(dde)

        the_target.add_damage_event(dde)


    the_target.damage_report()

    print(the_target.damage_events_dict)
    the_target.clear()
    print(the_target.damage_events_dict)




if __name__ == '__main__':
    main()



