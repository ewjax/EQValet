# import the datetime class from the datetime module
import copy
import pyperclip
import re
from datetime import datetime

import PetParser
import config
import util
from util import starprint
from CaseInsensitiveDict import CaseInsensitiveDict


#################################################################################################
# 
# Inheritance Diagram:
#         
#                           DamageEvent
#                            /    \   \___________
#                           /      \              \
#           DiscreteDamageEvent  DotSpell      DirectDamageSpell
#                                  /   \
#                                 /     \
#                      LinearDotSpell  SplurtSpell
#         
# common data:
#       attacker_name       
#       target_name
#       event_datetime  (for discrete events, the time.  For DOT's, the start time)
#
# common methods:
#       set_instance_data(attacker_name, target_name, eq_timestamp)     (set instance info)
#       damage_dealt()  (returns amount of damage in this particular DamageEvent)
#       damage_type()   (returns the type of damage for summing)
#       is_ticking()    (only returns true for DOT spells that have yet to close out)
#       is_aoe()        (only returns true for AOE spells that could hit more than one target)
#

#################################################################################################

#
# base class for all damage dealing events
#
class DamageEvent:
    """
    Base class for all damage dealing events
    """

    # ctor
    def __init__(self):
        # common data, to be set when an instance of the DamageEvent is created
        self.attacker_name = None
        self.target_name = None
        self.event_datetime = None
        self.aoe = False

    # set instance data
    # eq_timestamp assumed to be in the format of EQ logfile timestamp
    def set_instance_data(self, attacker_name: str, target_name: str, eq_timestamp: str) -> None:
        """
        The phrase 'instance data' in this case refers to the names of the attacker and target, and the EQ timestamp of the event

        Args:
            attacker_name: Name of the attacker
            target_name: Name of the target
            eq_timestamp: EQ timestamp, e.g. '[Thu Oct 28 15:24:13 2021]' (or the whole line)
        """
        self.attacker_name = attacker_name
        self.target_name = target_name
        self.event_datetime = datetime.strptime(eq_timestamp[0:26], '[%a %b %d %H:%M:%S %Y]')

    # function to be overloaded by child classes
    def damage_dealt(self) -> int:
        """
        Function to be overloaded by child classes

        Returns:
            Amount of damage done by this event
        """
        return int(0)

    # function to return type of damage - spell name, or melee type, or non-melee, etc
    def damage_type(self) -> str:
        """
        Returns:
            Return type of damage - spell name, or melee type, or non-melee, etc
        """
        return ''

    # only returns true for DOT spells that are not yet closed out
    def is_ticking(self) -> bool:
        """
        Returns:
            Returns true for DOT spells that are not yet closed out
        """
        return False

    # only returns true for AOE spells that could hit more than one target
    def is_aoe(self) -> bool:
        """
        Returns:
            Returns true for AOE spells that could hit more than one target
        """
        return self.aoe


#################################################################################################

#
# class for a one-time occurence of damage
#
class DiscreteDamageEvent(DamageEvent):
    """
    Class for a one-time occurence of damage
    """

    # ctor
    # for the time parameter, pass at least, or all, of the actual log logfile line containing the timestamp
    # [Thu Oct 28 15:24:13 2021] A frost giant captain is engulfed in darkness.
    def __init__(self, attacker_name: str, target_name: str, eq_timestamp: str, dmg_type: str, dmg_amount: int, aoe: bool = False):
        """
        Discrete Damage Event ctor

        Args:
            attacker_name: Name of the attacker
            target_name: Name of the target
            eq_timestamp: EQ timestamp, e.g. '[Thu Oct 28 15:24:13 2021]' (or the whole line)
            dmg_type: Type of damage, e.g. spell name, or melee type, or non-melee, etc
            dmg_amount: Amount of damage
            aoe: Boolean for is this an AOE
        """
        DamageEvent.__init__(self)
        self.set_instance_data(attacker_name, target_name, eq_timestamp)
        self.dmg_type = dmg_type
        self.dmg_amount = int(dmg_amount)
        self.aoe = aoe

    # function to be overloaded by child classes
    def damage_dealt(self) -> int:
        """
        Function to be overloaded by child classes

        Returns:
            Amount damage done by this event
        """
        return self.dmg_amount

    # function to return type of damage - spell name, or melee type, or non-melee, etc
    def damage_type(self) -> str:
        """
        Returns:
            Return type of damage - spell name, or melee type, or non-melee, etc
        """
        return self.dmg_type

    # overload function to allow object to print() to screen in sensible manner, for debugging with print()
    def __repr__(self) -> str:
        return '({}, {}, {}, {}, {}, {})'.format(self.attacker_name,
                                                 self.target_name,
                                                 self.event_datetime,
                                                 self.dmg_type,
                                                 self.dmg_amount,
                                                 self.aoe)


#################################################################################################

#
# class for a DD spell
#
class DirectDamageSpell(DamageEvent):
    """
    Class for a DD spell
    """

    # ctor
    #
    def __init__(self, spell_name: str, landed_message: str, aoe: bool = False):
        """
        Direct Damage spell

        Args:
            spell_name: Name of the spell
            landed_message: Message when spell successfully lands on target
            aoe: is this spell AOE
        """
        DamageEvent.__init__(self)
        self.spell_name = spell_name
        self.landed_message = landed_message
        self.aoe = aoe

    # function to return type of damage - spell name, or melee type, or non-melee, etc
    def damage_type(self) -> str:
        """
        Returns:
            Return type of damage - spell name, or melee type, or non-melee, etc
        """
        return self.spell_name

    # overload function to allow object to print() to screen in sensible manner, for debugging with print()
    def __repr__(self) -> str:
        return '({}, {}, {}, {}, {}, {})'.format(self.attacker_name,
                                                 self.target_name,
                                                 self.event_datetime,
                                                 self.spell_name,
                                                 self.landed_message,
                                                 self.aoe)


#################################################################################################

#
# base class for other DOT spells
#
class DotSpell(DamageEvent):
    """
    Base class for other DOT spells
    """

    # ctor
    def __init__(self, spell_name: str, max_duration_sec: int, landed_message: str, faded_message: str = None, aoe: bool = False):
        """
        Generic DOT spell

        Args:
            spell_name: Name of the spell
            max_duration_sec: Maximum duration (seconds)
            landed_message: Message when spell successfully lands on target
            faded_message: Custom faded message. Passing 'None' will cause the default faded message to be set to 'Your XXX spell has worn off'
            aoe: is this spell AOE
        """
        DamageEvent.__init__(self)

        self.spell_name = spell_name
        self.max_duration_sec = int(max_duration_sec)
        self.landed_message = landed_message
        self.faded_message = faded_message
        self.aoe = aoe

        if self.faded_message is None:
            self.faded_message = '^Your ' + self.spell_name + ' spell has worn off'

        # this will get set later
        self.end_datetime = None

    #
    #
    def set_start_time(self, eq_timestamp: str) -> None:
        """
        Set the start time - shouldn't need this, normally would be set in set_instance_info(), but provide just in case.
        This uses the very capable strptime() parsing function built into the datetime module.

        [Thu Oct 28 15:24:13 2021] A frost giant captain is engulfed in darkness.

        Args:
            eq_timestamp: EQ timestamp, e.g. '[Thu Oct 28 15:24:13 2021]' (or the whole line)
        """
        self.event_datetime = datetime.strptime(eq_timestamp[0:26], '[%a %b %d %H:%M:%S %Y]')

    #
    #
    def set_end_time(self, eq_timestamp: str) -> None:
        """
        Set the end time, using the very capable strptime() parsing function built into the datetime module.

        [Thu Oct 28 15:24:13 2021] A frost giant captain is engulfed in darkness.

        Args:
            eq_timestamp: EQ timestamp, e.g. '[Thu Oct 28 15:24:13 2021]' (or the whole line)
        """
        self.end_datetime = datetime.strptime(eq_timestamp[0:26], '[%a %b %d %H:%M:%S %Y]')

    #
    #
    def elapsed_ticks(self) -> int:
        """
        Helper function to get number of ticks elapsed

        Returns:
            Number of ticks
        """
        ticks = 0
        if self.end_datetime and self.event_datetime:
            elapsed_timedelta = self.end_datetime - self.event_datetime
            elapsed_seconds = elapsed_timedelta.total_seconds()
            if elapsed_seconds > self.max_duration_sec:
                elapsed_seconds = self.max_duration_sec
            ticks = int(elapsed_seconds / 6.0)
        return ticks

    #
    #
    def damage_dealt(self) -> int:
        """
        Function to be overloaded by child classes

        Returns:
            Amount of damage dealt by this event
        """
        return 0

    #
    #
    def damage_type(self) -> str:
        """
        Function to return type of damage - spell name, or melee type, or non-melee, etc

        Returns:
            Type of damage
        """
        return self.spell_name

    #
    #
    def is_ticking(self) -> bool:
        """
        Returns:
            Returns true if end time has not yet been set in this spell
        """
        rv = False
        if self.end_datetime is None:
            rv = True
        return rv

    # overload funciton to allow object to print() to screen in sensible manner, for debugging with print()
    def __repr__(self) -> str:
        return '({}, {}, {}, {}, {}, {}, {}, {}, {})'.format(self.attacker_name,
                                                             self.target_name,
                                                             self.event_datetime,
                                                             self.end_datetime,
                                                             self.spell_name,
                                                             self.max_duration_sec,
                                                             self.landed_message,
                                                             self.faded_message,
                                                             self.aoe)


#################################################################################################


#
# Most DOT spells work on a linear damage model, i.e. X damage per tick
#
class LinearDotSpell(DotSpell):
    """
    Most DOT spells work on a linear damage model, i.e. X damage per tick
    """

    # ctor
    def __init__(self, spell_name: str, max_duration_sec: int, dmg_initial: int, dmg_per_tick: int,
                 landed_message: str, faded_message: str = None, aoe: bool = False):
        """
        LinearDotSpell ctor

        Args:
            spell_name: Name of the spell
            max_duration_sec: Max duration
            dmg_initial: Initial damage
            dmg_per_tick: Damage per tick
            landed_message: Landed message
            faded_message: Faded message
            aoe: True if AOE
        """
        DotSpell.__init__(self, spell_name, max_duration_sec, landed_message, faded_message)
        self.dmg_initial = int(dmg_initial)
        self.dmg_per_tick = int(dmg_per_tick)
        self.aoe = aoe

    #
    #
    def damage_dealt(self) -> int:
        """
        Overload the damage_dealt() function for LinearDotSpell class

        Returns:
            Damage dealt by this particular spell
        """
        damage = 0
        if self.end_datetime and self.event_datetime:
            ticks = self.elapsed_ticks()
            # actually, the initial damage is detectable as non-melee, so don't double count it here
            # damage = self.dmg_initial + ticks * self.dmg_per_tick
            damage = ticks * self.dmg_per_tick
        return damage

    # overload funciton to allow object to print() to screen in sensible manner, for debugging with print()
    def __repr__(self) -> str:
        return '({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})'.format(self.attacker_name,
                                                                     self.target_name,
                                                                     self.event_datetime,
                                                                     self.end_datetime,
                                                                     self.spell_name,
                                                                     self.max_duration_sec,
                                                                     self.dmg_initial,
                                                                     self.dmg_per_tick,
                                                                     self.landed_message,
                                                                     self.faded_message,
                                                                     self.aoe)


#################################################################################################


#
# Nonlinear damage accrual (Splurt, Shaman epic Curse of the Spirits)
#
class SplurtSpell(DotSpell):
    """
    Nonlinear damage accrual (Splurt, Shaman epic Curse of the Spirits)
    """

    # ctor
    def __init__(self, spell_name: str, max_duration_sec: int, landed_message: str):
        DotSpell.__init__(self, spell_name, max_duration_sec, landed_message)

    #
    # overload the damage_dealt() function
    def damage_dealt(self) -> int:
        """
        Overload the damage_dealt() function for SplurtSpell class

        Returns:
            Damage dealt by this particular spell
        """
        damage = 0
        if self.end_datetime and self.event_datetime:

            ticks = self.elapsed_ticks()
            base_damage = ticks * 11

            incremental_damage = 0
            for i in range(ticks):
                incremental_damage += (i * 12)

            damage = base_damage + incremental_damage

        return damage

    # overload funciton to allow object to print() to screen in sensible manner, for debugging with print()
    def __repr__(self) -> str:
        return '({}, {}, {}, {}, {}, {}, {}, {})'.format(self.attacker_name,
                                                         self.target_name,
                                                         self.event_datetime,
                                                         self.end_datetime,
                                                         self.spell_name,
                                                         self.max_duration_sec,
                                                         self.landed_message,
                                                         self.aoe)


#################################################################################################

#
# class for Targets
#
class Target:
    """
    Class for Targets

    Keeps track of combat being done TO, and being done BY, this target.
    """

    # ctor
    def __init__(self, target_name=None):

        # target name
        self.target_name = target_name
        self.in_combat = False
        self.first_combat_datetime = None
        self.last_combat_datetime = None

        # max value the target is hitting for
        self.max_melee = 0

        # running total of discrete damage - use this to help guess which target just died, if more than
        # one are active
        self.discrete_damage_sum = 0

        # incoming damage TO this target
        # a dictionary of lists,
        #   keys = attacker (player) names,
        #   values = list[] of all DamageEvents done by that attacker to this target (mob)
        self.incoming_damage_events_dict = {}

        # outgoing damage BY this target
        # a dictionary of lists,
        #   keys = target names (player names)
        #   values = list[] of all DamageEvents done by this Target (mob) to that Player
        self.outgoing_damage_events_dict = {}

    #
    #
    def check_max_melee(self, dmg: int) -> None:
        """
        Check if max_melee needs to be updated

        Args:
            dmg: Damage of this attack
        """
        if self.max_melee < dmg:
            self.max_melee = dmg

    #
    #
    def implied_level(self) -> float:
        """
        Implied target level, from max melee value

        Returns:
            Implied mob level
        """
        if self.max_melee <= 60:
            level = (self.max_melee / 2)
        else:
            level = (self.max_melee + 60) / 4
        return level

    #
    #
    def start_combat(self, eq_timestamp: str) -> None:
        """
        Start combat

        Args:
            eq_timestamp: EQ timestamp, e.g. '[Thu Oct 28 15:24:13 2021]' (or the whole line)
        """
        self.first_combat_datetime = datetime.strptime(eq_timestamp[0:26], '[%a %b %d %H:%M:%S %Y]')
        self.last_combat_datetime = datetime.strptime(eq_timestamp[0:26], '[%a %b %d %H:%M:%S %Y]')
        self.in_combat = True

    #
    #
    def end_combat(self, eq_timestamp: str) -> None:
        """
        End combat

        Args:
            eq_timestamp: EQ timestamp, e.g. '[Thu Oct 28 15:24:13 2021]' (or the whole line)
        """
        self.last_combat_datetime = datetime.strptime(eq_timestamp[0:26], '[%a %b %d %H:%M:%S %Y]')
        self.in_combat = False

        # for each attacker..
        for attacker in self.incoming_damage_events_dict:
            # get the list of DE events for this attacker
            de_list = self.incoming_damage_events_dict[attacker]
            # for each event in the list
            for de in de_list:
                if de.is_ticking():
                    de.set_end_time(eq_timestamp)

        # for each target..
        for target in self.outgoing_damage_events_dict:
            # get the list of DE events for this target
            de_list = self.outgoing_damage_events_dict[target]
            # for each event in the list
            for de in de_list:
                if de.is_ticking():
                    de.set_end_time(eq_timestamp)

    #
    #
    def combat_timeout_seconds(self, eq_timestamp: str) -> float:
        """
        Used to check for combat timeout condition.
        Calculate elapsed time in seconds between
        1) last known DamageEvent vs this target, to
        2) the time contained in the passed timestamp

        Args:
            eq_timestamp: EQ timestamp, e.g. '[Thu Oct 28 15:24:13 2021]' (or the whole line)

        Returns:
            Elapsed seconds in combat
        """

        try:
            now = datetime.strptime(eq_timestamp[0:26], '[%a %b %d %H:%M:%S %Y]')
            elapsed_timedelta = now - self.last_combat_datetime
            elapsed_seconds = elapsed_timedelta.total_seconds()
            return elapsed_seconds
        except ValueError:
            return 0.0

    #
    #
    def combat_duration_seconds(self) -> float:
        """
        Combat duration in seconds - first DamageEvent to the last

        Returns:
            Duration in seconds
        """
        elapsed_timedelta = self.last_combat_datetime - self.first_combat_datetime
        elapsed_seconds = elapsed_timedelta.total_seconds()
        return elapsed_seconds

    #
    #
    def add_incoming_damage_event(self, de: DamageEvent) -> None:
        """
        Add an incoming damage event to the incoming list
        e.g. player hits mob for XXX

        Args:
            de: Instance of DamageEvent class
        """
        # is there an entry in the dictionary for this attacker?
        if de.attacker_name not in self.incoming_damage_events_dict:
            self.incoming_damage_events_dict[de.attacker_name] = []

        de_list = self.incoming_damage_events_dict[de.attacker_name]
        de_list.append(de)
        self.last_combat_datetime = de.event_datetime

        self.discrete_damage_sum += de.damage_dealt()

    #
    #
    def add_outgoing_damage_event(self, de: DamageEvent) -> None:
        """
        Add an outgoing damage event to the outgoing list
        e.g. mob hits player for XXX

        Args:
            de: Instance of DamageEvent class
        """
        # is there an entry in the dictionary for this player?
        if de.target_name not in self.outgoing_damage_events_dict:
            self.outgoing_damage_events_dict[de.target_name] = []

        de_list = self.outgoing_damage_events_dict[de.target_name]
        de_list.append(de)
        self.last_combat_datetime = de.event_datetime

    #
    #
    def damage_report(self) -> None:
        """
        Build a damage report, subtotaled by damage type
        """
        # total damage dealt to this target
        grand_total_incoming = 0        # damage incoming, i.e. TO this Target
        grand_total_outgoing = 0        # damage outgoing, i.e. BY this Target

        # walk the list initially just to get attacker totals, save in a dictionary,
        incoming_summary_dict = {}      # {k:V} = {attacker_name : damage total for that attacker}
        outgoing_summary_dict = {}      # {k:v} = {target_name : damage total done to that target}

        # for each attacker in the incoming_damage_events_dict
        for attacker in self.incoming_damage_events_dict:

            # first one?
            if attacker not in incoming_summary_dict:
                incoming_summary_dict[attacker] = 0

            # for each DamageEvent in the list for this attacker...
            de_list = self.incoming_damage_events_dict[attacker]
            for de in de_list:
                dd = de.damage_dealt()
                incoming_summary_dict[attacker] += dd
                grand_total_incoming += dd

        # for each target in the damage_events_dict
        for target in self.outgoing_damage_events_dict:

            # first one?
            if target not in outgoing_summary_dict:
                outgoing_summary_dict[target] = 0

            # for each DamageEvent in the list for this target...
            de_list = self.outgoing_damage_events_dict[target]
            for de in de_list:
                dd = de.damage_dealt()
                outgoing_summary_dict[target] += dd
                grand_total_outgoing += dd

        dps_outgoing = 0.0
        if self.combat_duration_seconds() > 0:
            dps_outgoing = grand_total_outgoing / self.combat_duration_seconds()

        # bell sound
        if config.config_data.getboolean('EQValet', 'bell'):
            print('\a')

        # now create the output report
        width = util.REPORT_WIDTH
        fill1 = '.'
        fill2 = '='
        reportbuffer = f'\n'
        reportbuffer += f'{"":{fill2}^{width}}\n'
        reportbuffer += f'Damage Report, Target: **{self.target_name}**\n'
        reportbuffer += f'Implied Level: {self.implied_level()}\n'
        reportbuffer += f'Combat Duration (sec): {self.combat_duration_seconds():.0f}\n'
        reportbuffer += f'Damage To:\n'

        # walk the list of targets, sort the target dictionary on total damage done...
        for (target, target_total) in sorted(outgoing_summary_dict.items(), key=lambda val: val[1], reverse=True):
            reportbuffer += f'        {str(target)}\n'

            # create a dictionary, keys = damage types, values = integer total damage done for that damage type
            dmg_type_summary_dict = {}
            de_list = self.outgoing_damage_events_dict[target]

            # for each DamageEvent in the list...
            for de in de_list:
                if de.damage_type() not in dmg_type_summary_dict:
                    dmg_type_summary_dict[de.damage_type()] = 0
                dmg_type_summary_dict[de.damage_type()] += de.damage_dealt()

            # sort damage type report from highest to lowest damage
            for (dmg_type, dmg_type_sum) in sorted(dmg_type_summary_dict.items(), key=lambda val: val[1], reverse=True):
                reportbuffer += f'{dmg_type:>35}: {dmg_type_sum:>5}\n'

            frac = 0.0
            if grand_total_outgoing != 0:
                frac = round(target_total / grand_total_outgoing * 100.0)

            dps = 0.0
            if self.combat_duration_seconds() > 0:
                dps = target_total / self.combat_duration_seconds()

            reportbuffer += f'{"Total":>35}: {target_total:>5} ({frac}%) (@{dps:.1f} dps)\n'

        reportbuffer += '\n'
        reportbuffer += f'{"Grand Total":>35}: {grand_total_outgoing:>5} (100%) (@{dps_outgoing:.1f} dps)\n'
        reportbuffer += f'{"":{fill1}^{width}}\n'
        reportbuffer += f'Damage By:\n'

        # walk the list of attackers, sort the attacker dictionary on total damage done...
        for (attacker, attacker_total) in sorted(incoming_summary_dict.items(), key=lambda val: val[1], reverse=True):
            reportbuffer += f'        {attacker}\n'

            # create a dictionary, keys = damage types, values = integer total damage done for that damage type
            dmg_type_summary_dict = {}
            de_list = self.incoming_damage_events_dict[attacker]

            # for each DamageEvent in the list...
            for de in de_list:
                if de.damage_type() not in dmg_type_summary_dict:
                    dmg_type_summary_dict[de.damage_type()] = 0
                dmg_type_summary_dict[de.damage_type()] += de.damage_dealt()

            # sort damage type report from highest to lowest damage
            for (dmg_type, dmg_type_sum) in sorted(dmg_type_summary_dict.items(), key=lambda val: val[1], reverse=True):
                reportbuffer += f'{dmg_type:>35}: {dmg_type_sum:>5}\n'

            frac = 0
            if grand_total_incoming != 0:
                frac = round(attacker_total / grand_total_incoming * 100)

            dps = 0.0
            if self.combat_duration_seconds() > 0:
                dps = attacker_total / self.combat_duration_seconds()

            reportbuffer += f'{"Total":>35}: {attacker_total:>5} ({frac}%) (@{dps:.1f} dps)\n'

        dps_incoming = 0.0
        if self.combat_duration_seconds() > 0:
            dps_incoming = grand_total_incoming / self.combat_duration_seconds()

        reportbuffer += f'\n'
        reportbuffer += f'{"Grand Total":>35}: {grand_total_incoming:>5} (100%) (@{dps_incoming:.1f} dps)\n'

        reportbuffer += f'{"":{fill2}^{width}}\n'
        print(reportbuffer)

    #
    #
    def damage_report_clipboard(self) -> None:
        """
        Create a damage report and force it into the windows clipboard, ready to paste into game
        """
        # sample
        # Leatherfoot Deputy in 113s, 467 @4 // Kenobtik 321 [68.74%] // Xythe 146 [31.26%]
        # Veteran Yllhaydm in 190s, 24512 @129 | Alou 10987@(63 in 174s) | Sergeant Brunfel 7132@(39 in 185s) | Lonobtik 4707@(25 in 190s)

        # total damage dealt to this target
        grand_total_incoming = 0        # damage incoming, i.e. TO this Target

        # walk the list initially just to get attacker totals, save in a dictionary,
        incoming_summary_dict = {}      # {k:V} = {attacker_name : damage total for that attacker}

        # for each attacker in the incoming_damage_events_dict
        for attacker in self.incoming_damage_events_dict:

            # first one?
            if attacker not in incoming_summary_dict:
                incoming_summary_dict[attacker] = 0

            # for each DamageEvent in the list for this attacker...
            de_list = self.incoming_damage_events_dict[attacker]
            for de in de_list:
                dd = de.damage_dealt()
                incoming_summary_dict[attacker] += dd
                grand_total_incoming += dd

        # start with the target
        dps = 0.0
        if self.combat_duration_seconds() > 0:
            dps = grand_total_incoming / self.combat_duration_seconds()
        clipboard_report = f'{self.target_name}, {grand_total_incoming} hp in {self.combat_duration_seconds():.0f}sec (@{dps:.1f} dps)'

        # walk the list of attackers, sort the attacker dictionary on total damage done...
        for (attacker, attacker_total) in sorted(incoming_summary_dict.items(), key=lambda val: val[1], reverse=True):
            fraction = 0
            if grand_total_incoming != 0:
                fraction = round(attacker_total / grand_total_incoming * 100.0)
            dps = 0
            if self.combat_duration_seconds() > 0:
                dps = round(attacker_total / self.combat_duration_seconds())

            clipboard_report += f' | {attacker} {attacker_total}@{dps} [{fraction}%]'

        # send this to clipboard
        pyperclip.copy(clipboard_report)


#################################################################################################

#
# class to do all the damage tracking work
#
class DamageParser:
    """
    Class to do all the damage tracking work
    """
    prev_dde: DiscreteDamageEvent

    # ctor
    def __init__(self):

        # the target that is being attacked
        # dictionary of {k:v} = {target_name, Target object}
        self.active_target_dict = CaseInsensitiveDict()
        self.inactive_target_list = []

        # dictionary of all known DOT_Spells, keys = spell names, contents = DOT_Spell objects
        self.spell_dict = dict()
        self.load_spell_dict()

        # use this flag for when we have detected the start of a spell cast and need to watch for the landed message
        # this is a pointer to the actual spell that is pending
        self.spell_pending = None

        # slain message
        self.slain_datetime = None

        # set of pet names
        self.pet_names_set = set()
        self.read_pet_names()

        # keep track of the previous non-melee DirectDamageEvent (for mage fire/watere pet proc messages)
        self.prev_dde = None
        self.prev_target = None

    #
    #
    def get_target(self, target_name: str) -> Target:
        """
        Check if there is currently a target by this name, and if so, return that Target object.
        If not, create a new Target() and return that one

        Args:
            target_name: name of target mob

        Returns:
            Target object for this mob
        """
        if target_name in self.active_target_dict:
            rv: Target = self.active_target_dict[target_name]
        else:
            rv = Target(target_name)
            self.active_target_dict[target_name] = rv
        return rv

    #
    #
    def get_likely_target(self) -> Target:
        """
        If we know combat has ended (exp message perhaps) but we DON'T know which Target just died, we have to guess.
        Just guess that the mob in the current list with the most accumulated melee damage = what just died

        Returns:
            Target object for the likely target
        """
        max_dmg = -1
        likely_target = None
        for t in self.active_target_dict.values():
            if t.discrete_damage_sum > max_dmg:
                max_dmg = t.discrete_damage_sum
                likely_target = t

        return likely_target

    #
    #
    def end_combat(self, target_name: str, line: str) -> None:
        """
        End combat sequence of events on target_name

        Args:
            target_name: combat target name
            line: log logfile line
        """

        # remove this target from the active Target dictionary, and add it to the inactive target list
        if target_name in self.active_target_dict:
            the_target = self.active_target_dict.pop(target_name)
            self.inactive_target_list.append(the_target)
            the_target.end_combat(line)
            the_target.damage_report()
            the_target.damage_report_clipboard()
        else:
            starprint(f'Warning: End of combat on target: [{target_name}], but that name not in tracking list')

    #
    #
    def process_line(self, line: str) -> None:
        """
        Check the current line for damage related items

        Args:
            line: complete line from the EQ logfile
        """

        # cut off the leading date-time stamp info
        trunc_line = line[27:]

        #
        # check for toggling the parse on/off
        #
        target = r'^\.ct '
        m = re.match(target, trunc_line)
        if m:

            # the relevant section and key value from the ini configfile
            section = 'DamageParser'
            key = 'parse'
            setting = config.config_data.getboolean(section, key)

            if setting:
                config.config_data[section][key] = 'False'
                onoff = 'Off'
            else:
                config.config_data[section][key] = 'True'
                onoff = 'On'

            # save the updated ini logfile
            config.save()

            starprint(f'Combat Parsing: {onoff}')

        #
        # report the current value of combat timeout
        #
        target = r'^\.cto '
        m = re.match(target, trunc_line)
        if m:
            cto = config.config_data.getint('DamageParser', 'combat_timeout_sec')
            starprint(f'DamageParser Combat timeout (CTO) = {cto}')

        #
        # only do the rest if user is parsing combat damage
        #
        if config.config_data.getboolean('DamageParser', 'parse'):

            #
            # watch for non-melee messages
            #
            non_melee_regexp = r'^(?P<target_name>[\w` ]+) was hit by (?P<dmg_type>[\w`\- ]+) for (?P<damage>[\d]+) point(s)? of damage'
            m = re.match(non_melee_regexp, trunc_line)
            if m:
                # extract RE data
                target_name = m.group('target_name')
                dmg_type = m.group('dmg_type')
                damage = int(m.group('damage'))

                # don't parse events vs eyes of zomm
                if not DamageParser.is_zomm(target_name):

                    # set the attacker name
                    # will usually be player name, unless, this message is from a
                    #   pet lt_proc, or
                    #   mage fire pet DS, or
                    #   mage fire/water pet proc
                    attacker_name = config.the_valet.char_name
                    the_pet: PetParser.Pet = config.the_valet.pet_parser.current_pet

                    # if this is a lifetap, assign the attacker as the pet
                    if the_pet and the_pet.lifetap_pending:
                        if the_pet.my_PetLevel and the_pet.my_PetLevel.lifetap_proc == damage:
                            attacker_name = config.the_valet.pet_parser.pet_name()
                            dmg_type = 'Lifetap'

                    # if this is a damage shield, assign the attacker as the pet
                    if the_pet and the_pet.damage_shield_pending:
                        if the_pet.my_PetLevel and the_pet.my_PetLevel.damage_shield == damage:
                            attacker_name = config.the_valet.pet_parser.pet_name()
                            dmg_type = 'Damage Shield'

                    # any damage event indicates we are in combat
                    the_target = self.get_target(target_name)
                    if not the_target.in_combat:
                        the_target.start_combat(line)
                        starprint(f'Combat begun: [{target_name}]', '^', '-')
                        starprint(f'(non-melee event)', '^')

                    # if there is a spell pending, and this isn't a lt_proc, then assume that this event represents the DD component of that spell
                    if self.spell_pending:
                        if not (the_pet and the_pet.lifetap_pending and the_pet.my_PetLevel and the_pet.my_PetLevel.lifetap_proc == damage):
                            dmg_type = self.spell_pending.damage_type()

                    # add the DamageEvent
                    dde = DiscreteDamageEvent(attacker_name, target_name, line, dmg_type, damage)
                    the_target.add_incoming_damage_event(dde)

                    # save this for possible use later if we encounter a mage fire/water pet proc
                    # self.prev_dde = copy.copy(dde)
                    self.prev_dde = dde
                    self.prev_target = the_target

            #
            # did we have a mage fire/water pet proc?
            # this is kind of messy, since by the time we get the proc message, the proc DDE has already been added
            # to the Target under the wrong attacker, with damage type 'non-melee'
            the_pet: PetParser.Pet = config.the_valet.pet_parser.current_pet
            if the_pet and the_pet.procced:

                # make a copy of the old DDE, then correct the attacker and dmg type, and add it back to the target
                redo_dde = copy.copy(self.prev_dde)
                redo_dde.attacker_name = config.the_valet.pet_parser.pet_name()
                redo_dde.dmg_type = 'proc'
                self.prev_target.add_incoming_damage_event(redo_dde)

                # now zero out the damage of the DDE that already got added
                self.prev_dde.dmg_amount = 0

            #
            # watch for conditions indicating combat is finished
            #
            if len(self.active_target_dict) > 0:

                # target is slain by pet or anyone else
                slain_regexp = r'^(?P<target_name>[\w` ]+) has been slain'
                m = re.match(slain_regexp, trunc_line)
                if m:
                    # extract RE data
                    target_name = m.group('target_name')
                    # ensure slain target was not a player and was not a pet
                    if (target_name not in config.the_valet.player_names_set) and (target_name not in self.pet_names_set):
                        # save for exp message comparison
                        self.slain_datetime = datetime.strptime(line[0:26], '[%a %b %d %H:%M:%S %Y]')
                        self.end_combat(target_name, line)

                # target is slain by player
                you_slain_regexp = r'^You have slain (?P<target_name>[\w` ]+)'
                m = re.match(you_slain_regexp, trunc_line)
                if m:
                    # extract RE data
                    target_name = m.group('target_name')
                    if target_name not in config.the_valet.player_names_set:
                        # save for exp message comparison
                        self.slain_datetime = datetime.strptime(line[0:26], '[%a %b %d %H:%M:%S %Y]')
                        self.end_combat(target_name, line)

                # exp message
                exp_regexp = r'^(You gain experience|You gain party experience)'
                m = re.match(exp_regexp, trunc_line)
                if m:
                    # EQ can put out multiple indications that combat has ended for a single target
                    #   - a 'slain' message
                    #   - an 'exp' message
                    # if that happens they will have same date/time stamp, so only react to this exp message
                    # if it hasn't already been processed by a 'slain' message
                    now = datetime.strptime(line[0:26], '[%a %b %d %H:%M:%S %Y]')
                    if now != self.slain_datetime:
                        # have to guess which target just died
                        the_target = self.get_likely_target()
                        if the_target:
                            self.end_combat(the_target.target_name, line)
                        else:
                            starprint('Error:  Exp message received, but no Target identified')

                # combat timeout - have to make a copy because the call to end_combat will modify the dictionary,
                # which would break the for loop
                for target_name in copy.deepcopy(self.active_target_dict):
                    the_target = self.get_target(target_name)
                    if the_target.combat_timeout_seconds(line) > config.config_data.getint('DamageParser', 'combat_timeout_sec'):
                        # ...then the combat timer has time out
                        starprint(f'Combat vs {target_name}: Timed out')
                        self.end_combat(target_name, line)

                # zoning
                zoning_regexp = 'LOADING, PLEASE WAIT'
                m = re.match(zoning_regexp, trunc_line)
                if m:
                    starprint('Player Zoned')
                    # close all open targets
                    for target_name in copy.deepcopy(self.active_target_dict):
                        self.end_combat(target_name, line)

            #
            # check for timeout on spell landed messages
            #
            if self.spell_pending:

                # get current time and check for timeout
                now = datetime.strptime(line[0:26], '[%a %b %d %H:%M:%S %Y]')
                elapsed_seconds = (now - self.spell_pending.event_datetime)
                if elapsed_seconds.total_seconds() > config.config_data.getint('DamageParser', 'spell_pending_timeout_sec'):
                    # ...then this spell pending is expired
                    starprint(f'Spell ({self.spell_pending.spell_name}) no longer pending: Timed out')
                    self.spell_pending = None

            #
            # watch for landed messages
            #
            if self.spell_pending:

                # get the landed message for the spell that is pending
                pending_regexp = self.spell_pending.landed_message
                m = re.match(pending_regexp, trunc_line)
                if m:

                    # extract RE data
                    target_name = m.group('target_name')

                    # don't parse events vs eyes of zomm
                    if not DamageParser.is_zomm(target_name):

                        # set the attacker name to the player name
                        attacker_name = config.the_valet.char_name

                        # any damage event indicates we are in combat
                        the_target = self.get_target(target_name)
                        if not the_target.in_combat:
                            the_target.start_combat(line)
                            starprint(f'Combat begun: [{target_name}]', '^', '-')
                            starprint(f'(spell landed)', '^')

                        # is this spell already in the DE list for the player, and still ticking?
                        # if so, close the existing, and add the new one
                        de_list = the_target.incoming_damage_events_dict.get(attacker_name)
                        # for each event in the player's DE list
                        if de_list:
                            for de in de_list:
                                if de.is_ticking():
                                    if self.spell_pending.spell_name == de.spell_name:
                                        de.set_end_time(line)
                                        starprint(f'{de.spell_name} overwritten with new')

                        # add the DamageEvent
                        de = copy.deepcopy(self.spell_pending)
                        de.set_instance_data(attacker_name, target_name, line)
                        the_target.add_incoming_damage_event(de)

                        # reset the spell pending flag
                        if not self.spell_pending.is_aoe():
                            self.spell_pending = None

            #
            # watch for spell faded conditions -only check DamageEvents that are not closed, i.e. still ticking
            #
            for targ in self.active_target_dict.values():
                if targ.in_combat:
                    attacker_name = config.the_valet.char_name
                    de_list = targ.incoming_damage_events_dict.get(attacker_name)
                    # for each event in the player's DE list
                    if de_list:
                        for de in de_list:
                            if de.is_ticking():
                                faded_target = de.faded_message
                                m = re.match(faded_target, trunc_line)
                                if m:
                                    de.set_end_time(line)
                                    starprint(f'{de.spell_name} faded')

            #
            # watch for casting messages
            #
            casting_regexp = r'^You begin casting (?P<spell_name>[\w`\' ]+)\.'
            m = re.match(casting_regexp, trunc_line)
            if m:

                # fetch the spell name
                spell_name = m.group('spell_name')

                # does the spell name match one of the spells we know about?
                if spell_name in self.spell_dict:
                    self.spell_pending = self.spell_dict[spell_name]
                    self.spell_pending.event_datetime = datetime.strptime(line[0:26], '[%a %b %d %H:%M:%S %Y]')


            #
            # watch for melee misses by me
            #
            my_miss_regexp = r'^You try to (?P<dmg_type>(hit|slash|pierce|crush|claw|bite|sting|maul|gore|punch|kick|backstab|bash|slice)) ' \
                             r'(?P<target_name>[\w` ]+), but miss!'
            m = re.match(my_miss_regexp, trunc_line)
            if m:
                # extract RE data
                target_name = m.group('target_name')

                # don't parse events vs eyes of zomm
                if not DamageParser.is_zomm(target_name):

                    # any damage event indicates we are in combat
                    the_target = self.get_target(target_name)
                    if not the_target.in_combat:
                        the_target.start_combat(line)
                        starprint(f'Combat begun: [{target_name}]', '^', '-')
                        starprint(f'(melee miss by you)', '^')

            #
            # watch for melee messages by me
            #
            my_hit_regexp = r'^You (?P<dmg_type>(hit|slash|pierce|crush|claw|bite|sting|maul|gore|punch|kick|backstab|bash|slice)) ' \
                            r'(?P<target_name>[\w` ]+) for (?P<damage>[\d]+) point(s)? of damage'
            m = re.match(my_hit_regexp, trunc_line)
            if m:

                # extract RE data
                attacker_name = config.the_valet.char_name
                dmg_type = m.group('dmg_type')
                target_name = m.group('target_name')
                damage = int(m.group('damage'))

                # don't parse events vs eyes of zomm
                if not DamageParser.is_zomm(target_name):

                    # any damage event indicates we are in combat
                    the_target = self.get_target(target_name)
                    if not the_target.in_combat:
                        the_target.start_combat(line)
                        starprint(f'Combat begun: [{target_name}]', '^', '-')
                        starprint(f'(melee hit by you)', '^')

                    # add the DamageEvent
                    dde = DiscreteDamageEvent(attacker_name, target_name, line, dmg_type, damage)
                    the_target.add_incoming_damage_event(dde)

            #
            # watch for melee messages
            #
            melee_regexp = r'^(?P<attacker_name>[\w` ]+) ' \
                           r'(?P<dmg_type>(hits|slashes|pierces|crushes|claws|bites|stings|mauls|gores|punches|kicks|backstabs|bashes|slices)) ' \
                           r'(?P<target_name>[\w` ]+) for (?P<damage>[\d]+) point(s)? of damage'
            m = re.match(melee_regexp, trunc_line)
            if m:

                # extract RE data
                attacker_name = m.group('attacker_name')
                dmg_type = m.group('dmg_type')
                target_name = m.group('target_name')
                damage = int(m.group('damage'))

                # don't parse events vs eyes of zomm
                if not DamageParser.is_zomm(target_name):

                    # the case where the Mob is attacking YOU, or a Player, or any pet
                    if (target_name == 'YOU') or (target_name in config.the_valet.player_names_set) or (target_name in self.pet_names_set):

                        # any damage event indicates we are in combat
                        the_target = self.get_target(attacker_name)
                        if not the_target.in_combat:
                            the_target.start_combat(line)
                            starprint(f'Combat begun: [{attacker_name}]', '^', '-')
                            starprint(f'(melee event vs you, or Player, or Pet)', '^')

                        the_target.check_max_melee(damage)

                        # add the DamageEvent
                        dde = DiscreteDamageEvent(attacker_name, target_name, line, dmg_type, damage)
                        the_target.add_outgoing_damage_event(dde)

                    # the case where a Player is attacking the Mob
                    else:
                        # any damage event indicates we are in combat
                        the_target = self.get_target(target_name)
                        if not the_target.in_combat:
                            the_target.start_combat(line)
                            starprint(f'Combat begun: [{target_name}]', '^', '-')
                            starprint(f'(melee event vs mob)', '^')

                        # add the DamageEvent
                        dde = DiscreteDamageEvent(attacker_name, target_name, line, dmg_type, damage)
                        the_target.add_incoming_damage_event(dde)

    #
    #
    @staticmethod
    def is_zomm(target_name: str) -> bool:
        """
        Use this to screen out parsing on events where players are smacking eyes of zomm

        Args:
            target_name: target name

        Returns:
            bool: True if this target name begins with the string 'Eye of '
        """
        zomm_target = 'Eye of '
        return zomm_target == target_name[:7]

    #
    #
    def read_pet_names(self) -> None:
        """
        Create a complete set of allowable pet names.
        Source:  p99 forums
        """
        self.pet_names_set = {'Gabab', 'Gabanab', 'Gabaner', 'Gabann', 'Gabantik', 'Gabarab', 'Gabarer', 'Gabarn', 'Gabartik', 'Gabekab',
                              'Gabeker', 'Gabekn', 'Gaber', 'Gabn', 'Gabobab', 'Gabober', 'Gabobn', 'Gabobtik', 'Gabtik', 'Ganab',
                              'Ganer', 'Gann', 'Gantik', 'Garab', 'Garanab', 'Garaner', 'Garann', 'Garantik', 'Gararab', 'Gararer',
                              'Gararn', 'Garartik', 'Garekab', 'Gareker', 'Garekn', 'Garer', 'Garn', 'Garobab', 'Garober', 'Garobn',
                              'Garobtik', 'Gartik', 'Gasab', 'Gasanab', 'Gasaner', 'Gasann', 'Gasantik', 'Gasarab', 'Gasarer', 'Gasarn',
                              'Gasartik', 'Gasekab', 'Gaseker', 'Gasekn', 'Gaser', 'Gasn', 'Gasobab', 'Gasober', 'Gasobn', 'Gasobtik',
                              'Gastik', 'Gebab', 'Gebanab', 'Gebaner', 'Gebann', 'Gebantik', 'Gebarab', 'Gebarer', 'Gebarn', 'Gebartik',
                              'Gebekab', 'Gebeker', 'Gebekn', 'Geber', 'Gebn', 'Gebobab', 'Gebober', 'Gebobn', 'Gebobtik', 'Gebtik',
                              'Gekab', 'Geker', 'Gekn', 'Genab', 'Genanab', 'Genaner', 'Genann', 'Genantik', 'Genarab', 'Genarer',
                              'Genarn', 'Genartik', 'Genekab', 'Geneker', 'Genekn', 'Gener', 'Genn', 'Genobab', 'Genober', 'Genobn',
                              'Genobtik', 'Gentik', 'Gibab', 'Gibanab', 'Gibaner', 'Gibann', 'Gibantik', 'Gibarab', 'Gibarer', 'Gibarn',
                              'Gibartik', 'Gibekab', 'Gibeker', 'Gibekn', 'Giber', 'Gibn', 'Gibobab', 'Gibober', 'Gibobn', 'Gibobtik',
                              'Gibtik', 'Gobab', 'Gobanab', 'Gobaner', 'Gobann', 'Gobantik', 'Gobarab', 'Gobarer', 'Gobarn', 'Gobartik',
                              'Gobekab', 'Gobeker', 'Gobekn', 'Gober', 'Gobn', 'Gobobab', 'Gobober', 'Gobobn', 'Gobobtik', 'Gobtik',
                              'Gonab', 'Gonanab', 'Gonaner', 'Gonann', 'Gonantik', 'Gonarab', 'Gonarer', 'Gonarn', 'Gonartik', 'Gonekab',
                              'Goneker', 'Gonekn', 'Goner', 'Gonn', 'Gonobab', 'Gonober', 'Gonobn', 'Gonobtik', 'Gontik', 'Jabab',
                              'Jabanab', 'Jabaner', 'Jabann', 'Jabantik', 'Jabarab', 'Jabarer', 'Jabarn', 'Jabartik', 'Jabekab', 'Jabeker',
                              'Jabekn', 'Jaber', 'Jabn', 'Jabobab', 'Jabober', 'Jabobn', 'Jabobtik', 'Jabtik', 'Janab', 'Janer',
                              'Jann', 'Jantik', 'Jarab', 'Jaranab', 'Jaraner', 'Jarann', 'Jarantik', 'Jararab', 'Jararer', 'Jararn',
                              'Jarartik', 'Jarekab', 'Jareker', 'Jarekn', 'Jarer', 'Jarn', 'Jarobab', 'Jarober', 'Jarobn', 'Jarobtik',
                              'Jartik', 'Jasab', 'Jasanab', 'Jasaner', 'Jasann', 'Jasantik', 'Jasarab', 'Jasarer', 'Jasarn', 'Jasartik',
                              'Jasekab', 'Jaseker', 'Jasekn', 'Jaser', 'Jasn', 'Jasobab', 'Jasober', 'Jasobn', 'Jasobtik', 'Jastik',
                              'Jebab', 'Jebanab', 'Jebaner', 'Jebann', 'Jebantik', 'Jebarab', 'Jebarer', 'Jebarn', 'Jebartik', 'Jebekab',
                              'Jebeker', 'Jebekn', 'Jeber', 'Jebn', 'Jebobab', 'Jebober', 'Jebobn', 'Jebobtik', 'Jebtik', 'Jekab',
                              'Jeker', 'Jekn', 'Jenab', 'Jenanab', 'Jenaner', 'Jenann', 'Jenantik', 'Jenarab', 'Jenarer', 'Jenarn',
                              'Jenartik', 'Jenekab', 'Jeneker', 'Jenekn', 'Jener', 'Jenn', 'Jenobab', 'Jenober', 'Jenobn', 'Jenobtik',
                              'Jentik', 'Jibab', 'Jibanab', 'Jibaner', 'Jibann', 'Jibantik', 'Jibarab', 'Jibarer', 'Jibarn', 'Jibartik',
                              'Jibekab', 'Jibeker', 'Jibekn', 'Jiber', 'Jibn', 'Jibobab', 'Jibober', 'Jibobn', 'Jibobtik', 'Jibtik',
                              'Jobab', 'Jobanab', 'Jobaner', 'Jobann', 'Jobantik', 'Jobarab', 'Jobarer', 'Jobarn', 'Jobartik', 'Jobekab',
                              'Jobeker', 'Jobekn', 'Jober', 'Jobn', 'Jobobab', 'Jobober', 'Jobobn', 'Jobobtik', 'Jobtik', 'Jonab',
                              'Jonanab', 'Jonaner', 'Jonann', 'Jonantik', 'Jonarab', 'Jonarer', 'Jonarn', 'Jonartik', 'Jonekab', 'Joneker',
                              'Jonekn', 'Joner', 'Jonn', 'Jonobab', 'Jonober', 'Jonobn', 'Jonobtik', 'Jontik', 'Kabab', 'Kabanab',
                              'Kabaner', 'Kabann', 'Kabantik', 'Kabarab', 'Kabarer', 'Kabarn', 'Kabartik', 'Kabekab', 'Kabeker', 'Kabekn',
                              'Kaber', 'Kabn', 'Kabobab', 'Kabober', 'Kabobn', 'Kabobtik', 'Kabtik', 'Kanab', 'Kaner', 'Kann',
                              'Kantik', 'Karab', 'Karanab', 'Karaner', 'Karann', 'Karantik', 'Kararab', 'Kararer', 'Kararn', 'Karartik',
                              'Karekab', 'Kareker', 'Karekn', 'Karer', 'Karn', 'Karobab', 'Karober', 'Karobn', 'Karobtik', 'Kartik',
                              'Kasab', 'Kasanab', 'Kasaner', 'Kasann', 'Kasantik', 'Kasarab', 'Kasarer', 'Kasarn', 'Kasartik', 'Kasekab',
                              'Kaseker', 'Kasekn', 'Kaser', 'Kasn', 'Kasobab', 'Kasober', 'Kasobn', 'Kasobtik', 'Kastik', 'Kebab',
                              'Kebanab', 'Kebaner', 'Kebann', 'Kebantik', 'Kebarab', 'Kebarer', 'Kebarn', 'Kebartik', 'Kebekab', 'Kebeker',
                              'Kebekn', 'Keber', 'Kebn', 'Kebobab', 'Kebober', 'Kebobn', 'Kebobtik', 'Kebtik', 'Kekab', 'Keker',
                              'Kekn', 'Kenab', 'Kenanab', 'Kenaner', 'Kenann', 'Kenantik', 'Kenarab', 'Kenarer', 'Kenarn', 'Kenartik',
                              'Kenekab', 'Keneker', 'Kenekn', 'Kener', 'Kenn', 'Kenobab', 'Kenober', 'Kenobn', 'Kenobtik', 'Kentik',
                              'Kibab', 'Kibanab', 'Kibaner', 'Kibann', 'Kibantik', 'Kibarab', 'Kibarer', 'Kibarn', 'Kibartik', 'Kibekab',
                              'Kibeker', 'Kibekn', 'Kiber', 'Kibn', 'Kibobab', 'Kibober', 'Kibobn', 'Kibobtik', 'Kibtik', 'Kobab',
                              'Kobanab', 'Kobaner', 'Kobann', 'Kobantik', 'Kobarab', 'Kobarer', 'Kobarn', 'Kobartik', 'Kobekab', 'Kobeker',
                              'Kobekn', 'Kober', 'Kobn', 'Kobobab', 'Kobober', 'Kobobn', 'Kobobtik', 'Kobtik', 'Konab', 'Konanab',
                              'Konaner', 'Konann', 'Konantik', 'Konarab', 'Konarer', 'Konarn', 'Konartik', 'Konekab', 'Koneker', 'Konekn',
                              'Koner', 'Konn', 'Konobab', 'Konober', 'Konobn', 'Konobtik', 'Kontik', 'Labab', 'Labanab', 'Labaner',
                              'Labann', 'Labantik', 'Labarab', 'Labarer', 'Labarn', 'Labartik', 'Labekab', 'Labeker', 'Labekn', 'Laber',
                              'Labn', 'Labobab', 'Labober', 'Labobn', 'Labobtik', 'Labtik', 'Lanab', 'Laner', 'Lann', 'Lantik',
                              'Larab', 'Laranab', 'Laraner', 'Larann', 'Larantik', 'Lararab', 'Lararer', 'Lararn', 'Larartik', 'Larekab',
                              'Lareker', 'Larekn', 'Larer', 'Larn', 'Larobab', 'Larober', 'Larobn', 'Larobtik', 'Lartik', 'Lasab',
                              'Lasanab', 'Lasaner', 'Lasann', 'Lasantik', 'Lasarab', 'Lasarer', 'Lasarn', 'Lasartik', 'Lasekab', 'Laseker',
                              'Lasekn', 'Laser', 'Lasn', 'Lasobab', 'Lasober', 'Lasobn', 'Lasobtik', 'Lastik', 'Lebab', 'Lebanab',
                              'Lebaner', 'Lebann', 'Lebantik', 'Lebarab', 'Lebarer', 'Lebarn', 'Lebartik', 'Lebekab', 'Lebeker', 'Lebekn',
                              'Leber', 'Lebn', 'Lebobab', 'Lebober', 'Lebobn', 'Lebobtik', 'Lebtik', 'Lekab', 'Leker', 'Lekn',
                              'Lenab', 'Lenanab', 'Lenaner', 'Lenann', 'Lenantik', 'Lenarab', 'Lenarer', 'Lenarn', 'Lenartik', 'Lenekab',
                              'Leneker', 'Lenekn', 'Lener', 'Lenn', 'Lenobab', 'Lenober', 'Lenobn', 'Lenobtik', 'Lentik', 'Libab',
                              'Libanab', 'Libaner', 'Libann', 'Libantik', 'Libarab', 'Libarer', 'Libarn', 'Libartik', 'Libekab', 'Libeker',
                              'Libekn', 'Liber', 'Libn', 'Libobab', 'Libober', 'Libobn', 'Libobtik', 'Libtik', 'Lobab', 'Lobanab',
                              'Lobaner', 'Lobann', 'Lobantik', 'Lobarab', 'Lobarer', 'Lobarn', 'Lobartik', 'Lobekab', 'Lobeker', 'Lobekn',
                              'Lober', 'Lobn', 'Lobobab', 'Lobober', 'Lobobn', 'Lobobtik', 'Lobtik', 'Lonab', 'Lonanab', 'Lonaner',
                              'Lonann', 'Lonantik', 'Lonarab', 'Lonarer', 'Lonarn', 'Lonartik', 'Lonekab', 'Loneker', 'Lonekn', 'Loner',
                              'Lonn', 'Lonobab', 'Lonober', 'Lonobn', 'Lonobtik', 'Lontik', 'Vabab', 'Vabanab', 'Vabaner', 'Vabann',
                              'Vabantik', 'Vabarab', 'Vabarer', 'Vabarn', 'Vabartik', 'Vabekab', 'Vabeker', 'Vabekn', 'Vaber', 'Vabn',
                              'Vabobab', 'Vabober', 'Vabobn', 'Vabobtik', 'Vabtik', 'Vanab', 'Vaner', 'Vann', 'Vantik', 'Varab',
                              'Varanab', 'Varaner', 'Varann', 'Varantik', 'Vararab', 'Vararer', 'Vararn', 'Varartik', 'Varekab', 'Vareker',
                              'Varekn', 'Varer', 'Varn', 'Varobab', 'Varober', 'Varobn', 'Varobtik', 'Vartik', 'Vasab', 'Vasanab',
                              'Vasaner', 'Vasann', 'Vasantik', 'Vasarab', 'Vasarer', 'Vasarn', 'Vasartik', 'Vasekab', 'Vaseker', 'Vasekn',
                              'Vaser', 'Vasn', 'Vasobab', 'Vasober', 'Vasobn', 'Vasobtik', 'Vastik', 'Vebab', 'Vebanab', 'Vebaner',
                              'Vebann', 'Vebantik', 'Vebarab', 'Vebarer', 'Vebarn', 'Vebartik', 'Vebekab', 'Vebeker', 'Vebekn', 'Veber',
                              'Vebn', 'Vebobab', 'Vebober', 'Vebobn', 'Vebobtik', 'Vebtik', 'Vekab', 'Veker', 'Vekn', 'Venab',
                              'Venanab', 'Venaner', 'Venann', 'Venantik', 'Venarab', 'Venarer', 'Venarn', 'Venartik', 'Venekab', 'Veneker',
                              'Venekn', 'Vener', 'Venn', 'Venobab', 'Venober', 'Venobn', 'Venobtik', 'Ventik', 'Vibab', 'Vibanab',
                              'Vibaner', 'Vibann', 'Vibantik', 'Vibarab', 'Vibarer', 'Vibarn', 'Vibartik', 'Vibekab', 'Vibeker', 'Vibekn',
                              'Viber', 'Vibn', 'Vibobab', 'Vibober', 'Vibobn', 'Vibobtik', 'Vibtik', 'Vobab', 'Vobanab', 'Vobaner',
                              'Vobann', 'Vobantik', 'Vobarab', 'Vobarer', 'Vobarn', 'Vobartik', 'Vobekab', 'Vobeker', 'Vobekn', 'Vober',
                              'Vobn', 'Vobobab', 'Vobober', 'Vobobn', 'Vobobtik', 'Vobtik', 'Vonab', 'Vonanab', 'Vonaner', 'Vonann',
                              'Vonantik', 'Vonarab', 'Vonarer', 'Vonarn', 'Vonartik', 'Vonekab', 'Voneker', 'Vonekn', 'Voner', 'Vonn',
                              'Vonobab', 'Vonober', 'Vonobn', 'Vonobtik', 'Vontik', 'Vtik', 'Xabab', 'Xabanab', 'Xabaner', 'Xabann',
                              'Xabantik', 'Xabarab', 'Xabarer', 'Xabarn', 'Xabartik', 'Xabekab', 'Xabeker', 'Xabekn', 'Xaber', 'Xabn',
                              'Xabobab', 'Xabober', 'Xabobn', 'Xabobtik', 'Xabtik', 'Xanab', 'Xaner', 'Xann', 'Xantik', 'Xarab',
                              'Xaranab', 'Xaraner', 'Xarann', 'Xarantik', 'Xararab', 'Xararer', 'Xararn', 'Xarartik', 'Xarekab', 'Xareker',
                              'Xarekn', 'Xarer', 'Xarn', 'Xarobab', 'Xarober', 'Xarobn', 'Xarobtik', 'Xartik', 'Xasab', 'Xasanab',
                              'Xasaner', 'Xasann', 'Xasantik', 'Xasarab', 'Xasarer', 'Xasarn', 'Xasartik', 'Xasekab', 'Xaseker', 'Xasekn',
                              'Xaser', 'Xasn', 'Xasobab', 'Xasober', 'Xasobn', 'Xasobtik', 'Xastik', 'Xebab', 'Xebanab', 'Xebaner',
                              'Xebann', 'Xebantik', 'Xebarab', 'Xebarer', 'Xebarn', 'Xebartik', 'Xebekab', 'Xebeker', 'Xebekn', 'Xeber',
                              'Xebn', 'Xebobab', 'Xebober', 'Xebobn', 'Xebobtik', 'Xebtik', 'Xekab', 'Xeker', 'Xekn', 'Xenab',
                              'Xenanab', 'Xenaner', 'Xenann', 'Xenantik', 'Xenarab', 'Xenarer', 'Xenarn', 'Xenartik', 'Xenekab', 'Xeneker',
                              'Xenekn', 'Xener', 'Xenn', 'Xenobab', 'Xenober', 'Xenobn', 'Xenobtik', 'Xentik', 'Xibab', 'Xibanab',
                              'Xibaner', 'Xibann', 'Xibantik', 'Xibarab', 'Xibarer', 'Xibarn', 'Xibartik', 'Xibekab', 'Xibeker', 'Xibekn',
                              'Xiber', 'Xibn', 'Xibobab', 'Xibober', 'Xibobn', 'Xibobtik', 'Xibtik', 'Xobab', 'Xobanab', 'Xobaner',
                              'Xobann', 'Xobantik', 'Xobarab', 'Xobarer', 'Xobarn', 'Xobartik', 'Xobekab', 'Xobeker', 'Xobekn', 'Xober',
                              'Xobn', 'Xobobab', 'Xobober', 'Xobobn', 'Xobobtik', 'Xobtik', 'Xonab', 'Xonanab', 'Xonaner', 'Xonann',
                              'Xonantik', 'Xonarab', 'Xonarer', 'Xonarn', 'Xonartik', 'Xonekab', 'Xoneker', 'Xonekn', 'Xoner', 'Xonn',
                              'Xonobab', 'Xonober', 'Xonobn', 'Xonobtik', 'Xontik', 'Xtik', 'Zabab', 'Zabanab', 'Zabaner', 'Zabann',
                              'Zabantik', 'Zabarab', 'Zabarer', 'Zabarn', 'Zabartik', 'Zabekab', 'Zabeker', 'Zabekn', 'Zaber', 'Zabn',
                              'Zabobab', 'Zabober', 'Zabobn', 'Zabobtik', 'Zabtik', 'Zanab', 'Zaner', 'Zann', 'Zantik', 'Zarab',
                              'Zaranab', 'Zaraner', 'Zarann', 'Zarantik', 'Zararab', 'Zararer', 'Zararn', 'Zarartik', 'Zarekab', 'Zareker',
                              'Zarekn', 'Zarer', 'Zarn', 'Zarobab', 'Zarober', 'Zarobn', 'Zarobtik', 'Zartik', 'Zasab', 'Zasanab',
                              'Zasaner', 'Zasann', 'Zasantik', 'Zasarab', 'Zasarer', 'Zasarn', 'Zasartik', 'Zasekab', 'Zaseker', 'Zasekn',
                              'Zaser', 'Zasn', 'Zasobab', 'Zasober', 'Zasobn', 'Zasobtik', 'Zastik', 'Zebab', 'Zebanab', 'Zebaner',
                              'Zebann', 'Zebantik', 'Zebarab', 'Zebarer', 'Zebarn', 'Zebartik', 'Zebekab', 'Zebeker', 'Zebekn', 'Zeber',
                              'Zebn', 'Zebobab', 'Zebober', 'Zebobn', 'Zebobtik', 'Zebtik', 'Zekab', 'Zeker', 'Zekn', 'Zenab',
                              'Zenanab', 'Zenaner', 'Zenann', 'Zenantik', 'Zenarab', 'Zenarer', 'Zenarn', 'Zenartik', 'Zenekab', 'Zeneker',
                              'Zenekn', 'Zener', 'Zenn', 'Zenobab', 'Zenober', 'Zenobn', 'Zenobtik', 'Zentik', 'Zibab', 'Zibanab',
                              'Zibaner', 'Zibann', 'Zibantik', 'Zibarab', 'Zibarer', 'Zibarn', 'Zibartik', 'Zibekab', 'Zibeker', 'Zibekn',
                              'Ziber', 'Zibn', 'Zibobab', 'Zibober', 'Zibobn', 'Zibobtik', 'Zibtik', 'Zobab', 'Zobanab', 'Zobaner',
                              'Zobann', 'Zobantik', 'Zobarab', 'Zobarer', 'Zobarn', 'Zobartik', 'Zobekab', 'Zobeker', 'Zobekn', 'Zober',
                              'Zobn', 'Zobobab', 'Zobober', 'Zobobn', 'Zobobtik', 'Zobtik', 'Zonab', 'Zonanab', 'Zonaner', 'Zonann',
                              'Zonantik', 'Zonarab', 'Zonarer', 'Zonarn', 'Zonartik', 'Zonekab', 'Zoneker', 'Zonekn', 'Zoner', 'Zonn',
                              'Zonobab', 'Zonober', 'Zonobn', 'Zonobtik', 'Zontik', 'Ztik'}

    #
    #
    def load_spell_dict(self) -> None:
        """
        Create the dictionary of pet spells, with all pet spell info for each
        """

        #
        # enchanter DD spells
        #
        spell_name = 'Chaotic Feedback'
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+)\'s brain begins to smolder')
        self.spell_dict[spell_name] = sp

        spell_name = 'Sanity Warp'
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+) looks delirious')
        self.spell_dict[spell_name] = sp

        spell_name = 'Chaos Flux'
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+) is surrounded by fluxing strands of chaos')
        self.spell_dict[spell_name] = sp

        spell_name = 'Anarchy'
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+)\'s world dissolves into anarchy')
        self.spell_dict[spell_name] = sp

        spell_name = 'Gravity Flux'
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+) rises chaotically into the air')
        self.spell_dict[spell_name] = sp

        spell_name = 'Discordant Mind'
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+)\'s brain begins to melt')
        self.spell_dict[spell_name] = sp

        spell_name = 'Dementia'
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+)\'s mind warps')
        self.spell_dict[spell_name] = sp

        #
        # enchanter DOT spells
        #
        spell_name = 'Shallow Breath'
        sp = LinearDotSpell(spell_name, 18, 5, 0, r'^(?P<target_name>[\w` ]+) begins to choke')
        self.spell_dict[spell_name] = sp

        spell_name = 'Suffocating Sphere'
        sp = LinearDotSpell(spell_name, 18, 10, 8, r'^(?P<target_name>[\w` ]+) gasps for breath')
        self.spell_dict[spell_name] = sp

        spell_name = 'Choke'
        sp = LinearDotSpell(spell_name, 36, 20, 12, r'^(?P<target_name>[\w` ]+) begins to choke')
        self.spell_dict[spell_name] = sp

        spell_name = 'Suffocate'
        sp = LinearDotSpell(spell_name, 108, 65, 11, r'^(?P<target_name>[\w` ]+) begins to choke')
        self.spell_dict[spell_name] = sp

        spell_name = 'Gasping Embrace'
        sp = LinearDotSpell(spell_name, 120, 50, 33, r'^(?P<target_name>[\w` ]+) begins to choke')
        self.spell_dict[spell_name] = sp

        spell_name = 'Torment of Argli'
        sp = LinearDotSpell(spell_name, 120, 0, 28, r'^(?P<target_name>[\w` ]+) screams from the Torment of Argli')
        self.spell_dict[spell_name] = sp

        spell_name = 'Asphyxiate'
        sp = LinearDotSpell(spell_name, 120, 50, 45, r'^(?P<target_name>[\w` ]+) begins to choke')
        self.spell_dict[spell_name] = sp

        #
        # necro DD spells
        #
        spell_name = 'Lifetap'
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+) staggers')
        self.spell_dict[spell_name] = sp

        spell_name = 'Lifespike'
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+) staggers')
        self.spell_dict[spell_name] = sp

        spell_name = 'Vampiric Embrace'
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+) staggers')
        self.spell_dict[spell_name] = sp

        spell_name = 'Lifedraw'
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+) staggers')
        self.spell_dict[spell_name] = sp

        spell_name = 'Siphon Life'
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+) staggers')
        self.spell_dict[spell_name] = sp

        spell_name = 'Spirit Tap'
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+) staggers')
        self.spell_dict[spell_name] = sp

        spell_name = 'Drain Spirit'
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+) staggers')
        self.spell_dict[spell_name] = sp

        spell_name = 'Deflux'
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+) staggers')
        self.spell_dict[spell_name] = sp

        spell_name = 'Touch of Night'
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+) staggers')
        self.spell_dict[spell_name] = sp

        spell_name = 'Gangrenous Touch of Zum`uul'
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+) staggers')
        self.spell_dict[spell_name] = sp

        spell_name = 'Shock of Poison'
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+) screams in agony')
        self.spell_dict[spell_name] = sp

        spell_name = 'Ignite Bones'
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+)\'s skin burns away')
        self.spell_dict[spell_name] = sp

        spell_name = 'Incinerate Bones'
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+) shrieks as their bones are set ablaze')
        self.spell_dict[spell_name] = sp

        spell_name = 'Chill Bones'
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+)\'s skin freezes and cracks off')
        self.spell_dict[spell_name] = sp

        spell_name = 'Conglaciation of Bones'
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+)\'s bones freezes and crack')
        self.spell_dict[spell_name] = sp

        #
        # necro DOT spells
        #
        spell_name = 'Disease Cloud'
        sp = LinearDotSpell(spell_name, 360, 5, 1, r'^(?P<target_name>[\w` ]+) doubles over in pain')
        self.spell_dict[spell_name] = sp

        spell_name = 'Clinging Darkness'
        sp = LinearDotSpell(spell_name, 36, 0, 5, r'^(?P<target_name>[\w` ]+) is surrounded by darkness')
        self.spell_dict[spell_name] = sp

        spell_name = 'Poison Bolt'
        sp = LinearDotSpell(spell_name, 42, 6, 5, r'^(?P<target_name>[\w` ]+) has been poisoned')
        self.spell_dict[spell_name] = sp

        spell_name = 'Engulfing Darkness'
        sp = LinearDotSpell(spell_name, 66, 0, 11, r'^(?P<target_name>[\w` ]+) is engulfed in darkness')
        self.spell_dict[spell_name] = sp

        spell_name = 'Heat Blood'
        sp = LinearDotSpell(spell_name, 60, 0, 17, r'^(?P<target_name>[\w` ]+)\'s blood simmers')
        self.spell_dict[spell_name] = sp

        spell_name = 'Leach'
        sp = LinearDotSpell(spell_name, 54, 0, 8, r'^(?P<target_name>[\w` ]+) pales')
        self.spell_dict[spell_name] = sp

        spell_name = 'Heart Flutter'
        sp = LinearDotSpell(spell_name, 72, 0, 12, r'^(?P<target_name>[\w` ]+) clutches their chest')
        self.spell_dict[spell_name] = sp

        spell_name = 'Infectious Cloud'
        sp = LinearDotSpell(spell_name, 126, 20, 5, r'^(?P<target_name>[\w` ]+) starts to wretch')
        self.spell_dict[spell_name] = sp

        spell_name = 'Boil Blood'
        sp = LinearDotSpell(spell_name, 126, 0, 24, r'^(?P<target_name>[\w` ]+)\'s blood boils')
        self.spell_dict[spell_name] = sp

        spell_name = 'Dooming Darkness'
        sp = LinearDotSpell(spell_name, 96, 0, 20, r'^(?P<target_name>[\w` ]+) is engulfed in darkness')
        self.spell_dict[spell_name] = sp

        spell_name = 'Vampiric Curse'
        sp = LinearDotSpell(spell_name, 54, 0, 21, r'^(?P<target_name>[\w` ]+) pales')
        self.spell_dict[spell_name] = sp

        spell_name = 'Venom of the Snake'
        sp = LinearDotSpell(spell_name, 48, 40, 59, r'^(?P<target_name>[\w` ]+) has been poisoned')
        self.spell_dict[spell_name] = sp

        spell_name = 'Scourge'
        sp = LinearDotSpell(spell_name, 126, 40, 24, r'^(?P<target_name>[\w` ]+) sweats and shivers, looking feverish')
        self.spell_dict[spell_name] = sp

        spell_name = 'Chilling Embrace'
        sp = LinearDotSpell(spell_name, 96, 0, 40, r'^(?P<target_name>[\w` ]+) is wracked by chilling poison')
        self.spell_dict[spell_name] = sp

        spell_name = 'Asystole'
        sp = LinearDotSpell(spell_name, 60, 0, 69, r'^(?P<target_name>[\w` ]+) clutches their chest')
        self.spell_dict[spell_name] = sp

        spell_name = 'Bond of Death'
        sp = LinearDotSpell(spell_name, 54, 0, 80, r'^(?P<target_name>[\w` ]+) staggers')
        self.spell_dict[spell_name] = sp

        spell_name = 'Cascading Darkness'
        sp = LinearDotSpell(spell_name, 96, 0, 72, r'^(?P<target_name>[\w` ]+) is engulfed in darkness')
        self.spell_dict[spell_name] = sp

        spell_name = 'Ignite Blood'
        sp = LinearDotSpell(spell_name, 126, 0, 56, r'^(?P<target_name>[\w` ]+)\'s blood ignites')
        self.spell_dict[spell_name] = sp

        spell_name = 'Envenomed Bolt'
        sp = LinearDotSpell(spell_name, 48, 110, 146, r'^(?P<target_name>[\w` ]+) has been poisoned')
        self.spell_dict[spell_name] = sp

        spell_name = 'Plague'
        sp = LinearDotSpell(spell_name, 132, 60, 55, r'^(?P<target_name>[\w` ]+) sweats and shivers, looking feverish')
        self.spell_dict[spell_name] = sp

        spell_name = 'Cessation of Cor'
        sp = LinearDotSpell(spell_name, 60, 100, 100, r'^(?P<target_name>[\w` ]+)\'s blood stills within their veins')
        self.spell_dict[spell_name] = sp

        spell_name = 'Vexing Mordinia'
        sp = LinearDotSpell(spell_name, 54, 0, 122, r'^(?P<target_name>[\w` ]+) staggers under the curse of Vexing Mordinia')
        self.spell_dict[spell_name] = sp

        spell_name = 'Pyrocruor'
        sp = LinearDotSpell(spell_name, 114, 0, 111, r'^(?P<target_name>[\w` ]+)\'s blood ignites')
        self.spell_dict[spell_name] = sp

        spell_name = 'Devouring Darkness'
        sp = LinearDotSpell(spell_name, 78, 0, 107, r'^(?P<target_name>[\w` ]+) is engulfed in devouring darkness')
        self.spell_dict[spell_name] = sp

        spell_name = 'Torment of Shadows'
        sp = LinearDotSpell(spell_name, 96, 0, 75, r'^(?P<target_name>[\w` ]+) is gripped by shadows of fear and terror')
        self.spell_dict[spell_name] = sp

        # necro non-linear dot spell
        spell_name = 'Splurt'
        sp = SplurtSpell(spell_name, 102, r'^(?P<target_name>[\w` ]+)\'s body begins to splurt')
        self.spell_dict[spell_name] = sp

        # necro non-linear dot spell from VP staff clicky
        spell_name = 'Soul Well'
        sp = SplurtSpell(spell_name, 60, r'^(?P<target_name>[\w` ]+) staggers')
        self.spell_dict[spell_name] = sp


        #
        # shaman DD spells
        #
        spell_name = 'Burst of Flame'   # level 1
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+) singes as the Burst of Flame hits them')
        self.spell_dict[spell_name] = sp

        spell_name = 'Frost Rift'   # level 5
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+) is struck by the frost rift')
        self.spell_dict[spell_name] = sp

        spell_name = 'Spirit Strike'    # level 14
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+) staggers as spirits of frost slam against them')
        self.spell_dict[spell_name] = sp

        spell_name = 'Frost Strike'    # level 24
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+) staggers as spirits of frost slam against them')
        self.spell_dict[spell_name] = sp

        spell_name = 'Poison Storm'      # level 24, rain spell, 3x waves of 60 each
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+)\'s skin blisters', aoe=True)
        self.spell_dict[spell_name] = sp

        spell_name = 'Shock of the Tainted'      # level 34
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+) screams in pain')
        self.spell_dict[spell_name] = sp

        spell_name = 'Winter\'s Roar'      # level 34
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+) staggers as spirits of frost slam against them')
        self.spell_dict[spell_name] = sp

        spell_name = 'Gale of Poison'      # level 39, rain spell, 3x waves of 122 each
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+)\'s skin blisters', aoe=True)
        self.spell_dict[spell_name] = sp

        spell_name = 'Blast of Poison'      # level 44
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+) screams in pain')
        self.spell_dict[spell_name] = sp

        spell_name = 'Blizzard Blast'       # level 44
        sp = DirectDamageSpell(spell_name, r'^(?P<target_name>[\w` ]+) staggers as spirits of frost slam against them')
        self.spell_dict[spell_name] = sp

        #
        # shaman DOT spells
        #
        spell_name = 'Sicken'   # level 5
        sp = LinearDotSpell(spell_name, 126, 8, 2, r'^(?P<target_name>[\w` ]+) sweats and shivers, looking feverish')
        self.spell_dict[spell_name] = sp

        spell_name = 'Tainted Breath'   # level 9
        sp = LinearDotSpell(spell_name, 42, 10, 8, r'^(?P<target_name>[\w` ]+) has been poisoned')
        self.spell_dict[spell_name] = sp

        spell_name = 'Affliction'   # level 19
        sp = LinearDotSpell(spell_name, 126, 30, 6, r'^(?P<target_name>[\w` ]+) sweats and shivers, looking feverish')
        self.spell_dict[spell_name] = sp

        spell_name = 'Infectious Cloud'   # level 19, Targeted AOE
        sp = LinearDotSpell(spell_name, 126, 20, 5, r'^(?P<target_name>[\w` ]+) starts to wretch', aoe=True)
        self.spell_dict[spell_name] = sp

        spell_name = 'Envenomed Breath'   # level 24
        sp = LinearDotSpell(spell_name, 42, 30, 27, r'^(?P<target_name>[\w` ]+) has been poisoned')
        self.spell_dict[spell_name] = sp

        # note that 34 spell Scourge is already loaded with the necro spells
        # note that 39 spell Venom of the Snake is already loaded with the necro spells
        # note that 49 spell Envenomed Breath is already loaded with the necro spells
        # note that 49 spell Plague is already loaded with the necro spells

        # shaman non-linear dot spell - epic click
        spell_name = 'Curse of the Spirits'
        sp = SplurtSpell(spell_name, 90, r'^(?P<target_name>[\w` ]+) is consumed by the raging spirits of the land')
        self.spell_dict[spell_name] = sp

    # overload funciton to allow object to print() to screen in sensible manner, for debugging with print()
    def __repr__(self) -> str:
        return '({}'.format(self.spell_dict)


def main():
    # sec = 17.999
    # print('ticks = {}'.format(sec/6.0))
    # print('ticks = {}'.format(int(sec/6.0)))

    line1 = '[Thu Oct 28 15:24:13 2021] A frost giant captain is engulfed in darkness.'
    line2 = '[Thu Oct 28 15:28:13 2021] A frost giant captain is engulfed in darkness.'
    #
    # ds1 = LinearDOT_Spell(None, None, None, 'Cascading Darkness', 96, 0, 72, 'A frost giant captain is engulfed in darkness')
    # print(ds1)
    # ds1.set_start_time(line1)
    # ds1.set_end_time(line2)
    # print(ds1)
    #
    # print(ds1.elapsed_ticks())
    # print(ds1.damage_dealt())

    # ds2 = LinearDOT_Spell('Envenomed Bolt', 48, 110, 146, 'landed message')
    # ds22 = copy.copy(ds2)
    #
    # ds22.set_instance_data('Attakker', 'TheTarget', line1)
    # ds22.set_end_time(line2)
    #
    # print(ds2)
    # print(ds22)
    #
    # print(ds2.damage_dealt())
    # print(ds22.damage_dealt())

    target_name = 'a stingtooth piranha'
    the_target = Target()
    the_target.target_name = target_name
    #
    # ds2 = LinearDOT_Spell('Envenomed Bolt', 48, 110, 146, 'landed message')
    # ds22 = copy.copy(ds2)
    #
    # ds22.set_instance_data('Xytl', target_name, line1)
    # ds22.set_end_time(line2)
    # the_target.add_damage_event(ds22)

    ds3 = SplurtSpell('Splurt', 102, r'^(?P<target_name>[\w` ]+)\'s body begins to splurt')
    ds33 = copy.copy(ds3)

    ds33.set_instance_data('Xytl', target_name, line1)
    ds33.set_end_time(line2)
    the_target.add_incoming_damage_event(ds33)

    print(ds3)
    print(ds3.damage_dealt())

    print(ds33)
    print(ds33.damage_dealt())
    #
    #
    #
    #
    # line3 = '[Mon Sep 06 14:01:09 2021] Zarobab hits a stingtooth piranha for 26 points of damage.'
    # line4 = '[Mon Sep 06 14:01:11 2021] Goliathette slashes a stingtooth piranha for 25 points of damage.'
    # line44 = '[Mon Sep 06 14:01:11 2021] Goliathette slashes a stingtooth piranha for 125 points of damage.'
    # line45 = '[Mon Sep 06 14:01:11 2021] Goliathette hits a stingtooth piranha for 99 points of damage.'
    # melee_target = prr'^(?P<attacker_name>[\w` ]+) \
    #                (?P<dmg_type>(hits|slashes|pierces|crushes|claws|bites|stings|mauls|gores|punches|kicks|backstabs)) \
    #                (?P<target_name>[\w` ]+) for (?P<damage>[\d]+) point(s)? of damage'
    #
    # m = re.match(melee_target, line3[27:], re.IGNORECASE)
    # if m:
    #     attacker_name   = m.group('attacker_name')
    #     dmg_type        = m.group('dmg_type')
    #     target_name     = m.group('target_name')
    #     dmg             = m.group('damage')
    #     # print('Melee: Attacker / Type / Target / Damage: {}, {}, {}, {}'.format(attacker_name, dmg_type, target_name, dmg))
    #     dde             = DiscreteDamageEvent(attacker_name, target_name, line3, dmg_type, dmg)
    #     # print(dde)
    #
    #     the_target.add_damage_event(dde)
    #
    #
    # m = re.match(melee_target, line4[27:], re.IGNORECASE)
    # if m:
    #     attacker_name   = m.group('attacker_name')
    #     dmg_type        = m.group('dmg_type')
    #     target_name     = m.group('target_name')
    #     dmg             = m.group('damage')
    #     # print('Melee: Attacker / Type / Target / Damage: {}, {}, {}, {}'.format(attacker_name, dmg_type, target_name, dmg))
    #     dde             = DiscreteDamageEvent(attacker_name, target_name, line4, dmg_type, dmg)
    #     # print(dde)
    #
    #     the_target.add_damage_event(dde)
    #
    #
    # m = re.match(melee_target, line44[27:], re.IGNORECASE)
    # if m:
    #     attacker_name   = m.group('attacker_name')
    #     dmg_type        = m.group('dmg_type')
    #     target_name     = m.group('target_name')
    #     dmg             = m.group('damage')
    #     # print('Melee: Attacker / Type / Target / Damage: {}, {}, {}, {}'.format(attacker_name, dmg_type, target_name, dmg))
    #     dde             = DiscreteDamageEvent(attacker_name, target_name, line44, dmg_type, dmg)
    #     # print(dde)
    #
    #     the_target.add_damage_event(dde)
    #
    # m = re.match(melee_target, line45[27:], re.IGNORECASE)
    # if m:
    #     attacker_name   = m.group('attacker_name')
    #     dmg_type        = m.group('dmg_type')
    #     target_name     = m.group('target_name')
    #     dmg             = m.group('damage')
    #     # print('Melee: Attacker / Type / Target / Damage: {}, {}, {}, {}'.format(attacker_name, dmg_type, target_name, dmg))
    #     dde             = DiscreteDamageEvent(attacker_name, target_name, line45, dmg_type, dmg)
    #     # print(dde)
    #
    #     the_target.add_damage_event(dde)
    #
    #
    #
    #
    #
    # line5 = '[Wed Dec 01 21:08:15 2021] a stingtooth piranha was hit by non-melee for 315 points of damage.'
    # non_melee_target = prr'^(?P<target_name>[\w` ]+) was hit by (?P<dmg_type>[\w`\- ]+) for (?P<damage>[\d]+) points of damage'
    #
    # m = re.match(non_melee_target, line5[27:], re.IGNORECASE)
    # if m:
    #     attacker_name = 'Xytl'
    #     target_name = m.group('target_name')
    #     dmg_type        = m.group('dmg_type')
    #     dmg = m.group('damage')
    #     # print('Non-Melee: Type / Target / Damage: {}, {}, {}'.format(dmg_type, target_name, dmg))
    #     dde = DiscreteDamageEvent(attacker_name, target_name, line5, dmg_type, dmg)
    #     print(dde)
    #
    #     the_target.add_damage_event(dde)
    #
    #
    # the_target.damage_report()
    #
    # print(the_target.incoming_damage_events_dict)
    # the_target.clear()
    # print(the_target.incoming_damage_events_dict)


if __name__ == '__main__':
    main()
