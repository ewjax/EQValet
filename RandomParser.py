import re
# import the datetime class from the datetime module
from datetime import datetime

# import the global config data
import config

import util
from util import starprint


class PlayerRandomRoll:
    """class for a single random roll by a particular player

    keeps track of
        player names,
        the random range (low, high),
        the actual random roll value,
        and the timestamp of the roll
    """

    #
    # ctor
    def __init__(self, player_name: str, random_value: int, low: int, high: int, eq_timestamp: str) -> None:
        """
        ctor

        Args:
            player_name: Name of the player
            random_value: The value of this particular random roll
            low: The low value of the random range
            high: The high value of the random range
            eq_timestamp: EQ timestamp, e.g. '[Thu Oct 28 15:24:13 2021]' (or the whole line)
        """

        self.player_name = player_name
        self.random_value = int(random_value)
        self.low = int(low)
        self.high = int(high)

        # create a datetime object, using the very capable strptime() parsing function built into the datetime module
        self.time_stamp = datetime.strptime(eq_timestamp[0:26], '[%a %b %d %H:%M:%S %Y]')

    #
    #
    def __repr__(self):
        """
        Overload function to allow object to print() to screen in sensible manner, for debugging with print()
        """
        return (
            '({}, {}, {}, {}, {})'.format(self.player_name, self.random_value, self.low, self.high, self.time_stamp))

    #
    #
    def report(self, you_name: str = '', high_list: list = None, first_timestamp: datetime = None) -> str:
        """
        To make bold text in a Discord message, surround it with double asterisks, i.e. **Example**
        For terminal window, simply append on ' <-- You' indicator

        Args:
            you_name: Name of this character
            high_list: a list of PlayerRandomRoll objects, representing the high roll(s) so far in a RandomGroup
            first_timestamp: datetime object for the timestamp of the first random roll in a RandomGroup

        Returns:
            str: The full report buffer
        """

        rv = ''
        if self.player_name.casefold() == you_name.casefold():
            # discord indicates emphasis with 2x leading and trailing stars
            # rv += '**'
            # for a terminal window, we will simply append on an additional '<-- You' marker
            # rv += '['
            pass

        rv += f'{self.player_name:>15} | Value: {self.random_value:>5} | Range: [{self.low:>5}-{self.high:>5}] | {self.time_stamp} |'

        # if the first timestamp parameter is passed
        if first_timestamp:
            elapsed_seconds = self.time_stamp - first_timestamp
            minutes = int(elapsed_seconds.total_seconds() // 60)
            seconds = int(elapsed_seconds.total_seconds() % 60)
            rv += f' {minutes:>02}:{seconds:>02} |'

        if high_list:
            # if self.player_roll(prr.player_name) is None:
            for prr in high_list:
                if self.player_name == prr.player_name:
                    rv += ' *HIGH*'

        if self.player_name.casefold() == you_name.casefold():
            # discord indicates emphasis with 2x leading and trailing stars
            # rv += '**'
            # for a terminal window, we will simply append on an additional '<-- You' marker
            rv += ' <--You'

        rv += '\n'

        return rv


class RandomGroup:
    """
    Class for many random rolls, to find random winners etc

    every roll in the list must:
      - have same range (low, high) (if low_significant and high_significant parameters are True)
      - must be within the delta_seconds time span
      - presumption is that rolls are added in time-sequential order, so the first roll to be added is assumed to be the
        starting time, and all other rolls must occur within the (starting time + delta_seconds) window
      - players can only random once.  any subsequent random will not be added to the RandomList
    """

    #
    # ctor
    def __init__(self, low: int, high: int, delta_seconds: int, low_significant: bool = True, high_significant: bool = True) -> None:
        """
        Class for a particular set of random rolls (PlayerRandomRoll objects)

        Args:
            low: The low value of the random range
            high: The high value of the random range
            delta_seconds: How many seconds to aggregate PlayerRandomRoll's together
            low_significant: Yes/No whether the low value is significant in the grouping logic
            high_significant: Yes/No whether the high value is significant in the grouping logic
        """
        self.low = int(low)
        self.low_significant = low_significant
        self.high = int(high)
        self.high_significant = high_significant
        self.delta_seconds = int(delta_seconds)

        # list of player random rolls
        self.rolls = list()
        self.start_time_stamp = None

        # flag to indicate whether this list is open for adding rolls
        self.expired = False

    #
    #
    def report_header(self, ndx: int = -1) -> str:
        """
        Class to generate the header of a report

        Args:
            ndx: Which random out of the list of RandomGroups

        Returns:
            Report buffer with header information
        """

        # example header
        # Index[24]..........................................................................................
        # Range: [150 - 999] | Rolls: 1 | Start Time: 2022 - 01 - 1500: 14:35 | Delta(seconds): 60

        width = util.REPORT_WIDTH
        fill = '.'

        rv = '\n'
        leader = f'Group Index: [{ndx}]'
        rv += f'{leader:{fill}<{width}}\n'

        ll = '?'
        if self.low_significant:
            ll = str(self.low)
        hh = '?'
        if self.high_significant:
            hh = str(self.high)
        rv += f'Range: [{ll}-{hh}] | Rolls: {len(self.rolls)} | Start Time: {self.start_time_stamp} | Delta (seconds): {self.delta_seconds}\n'
        return rv

    #
    #
    def report_winner(self, you_name: str = '') -> str:
        """
        Add the random winner(s) to the report

        Args:
            you_name: Name of this player

        Returns:
            Report buffer containing winner(s) info
        """

        # example of the winner report
        # Winner(s):
        # Ceit | Roll: 627 | Range: [0 - 999] | 2022 - 01 - 1500: 14:38 * HIGH *
        
        rv = f'Winner(s):\n'
        prr: PlayerRandomRoll
        high_list: list[PlayerRandomRoll] = self.high_roll_list()
        for prr in high_list:
            rv += f'{prr.report(you_name, high_list)}'
        return rv

    #
    #
    def report_summary(self, ndx: int = -1, you_name: str = '') -> str:
        """
        Provide a report summary, consisting of
            - header report
            - winner report

        Args:
            ndx: index of which RandomGroup is to be edited
            you_name: Name of this player

        Returns:
            Report buffer containing the summary report
        """

        rv = self.report_header(ndx)
        rv += self.report_winner(you_name)
        return rv

    #
    #
    def report_detail(self, ndx: int, you_name: str = '') -> str:
        """
        Provide a detailed report, consisting of
            - header report
            - one line for each PLayerRandomRoll
            - winner report

        Args:
            ndx: index of which RandomGroup is to be edited
            you_name: Name of this player

        Returns:
            Report buffer containing the detail report
        """

        rv = ''

        # add the header report
        rv += self.report_header(ndx)

        # add all the individual PlayerRandomRolls
        prr: PlayerRandomRoll
        high_list: list[PlayerRandomRoll] = self.high_roll_list()

        # the prev line sorted the list in descending random order, to find the winner list
        # re-sort the list back into ascending timestamp order
        self.sort_ascending_timestamps()

        # get timestamp of first roll
        first_timestamp = self.rolls[0].time_stamp

        # add each individual PlayerRandomRoll report
        for prr in self.rolls:
            rv += prr.report(you_name, high_list, first_timestamp)

        # add the winner report
        rv += self.report_winner(you_name)

        # return complete report
        return rv

    #
    # overload function to allow object to print() to screen in sensible manner, for debugging with print()
    def __repr__(self) -> str:
        """
        Overload function to allow object to print() to screen in sensible manner, for debugging with print()

        Returns:
            string representation of this RandomGroup
        """
        rv = self.report_header()
        for r in self.rolls:
            rv += r.report()
        return rv

    # does this list need to expire?  check timestamp of the passed line vs the delta window of this RandomGroup
    # returns True if this list toggles from NotExpired to Expired
    def check_expiration(self, line: str) -> bool:
        """
        Does this list need to expire?  check timestamp of the passed line vs the delta window of this RandomGroup

        Args:
            line: line containing the EQ timestamp to use for expiration calculation

        Returns:
            Returns True if this list toggles from NotExpired to Expired
        """
        rv = False

        # currently not expired...
        if not self.expired:
            # ...and there is at least 1 roll in the list...
            if len(self.rolls) > 0:
                # ...and the time stamp of the passed line parameter is outside the RandomGroup window duration...
                try:
                    check_time = datetime.strptime(line[0:26], '[%a %b %d %H:%M:%S %Y]')
                    elapsed_seconds = check_time - self.start_time_stamp
                    if elapsed_seconds.total_seconds() > self.delta_seconds:
                        # ...then this RandomGroup is expired
                        self.expired = True
                        self.sort_descending_randoms()
                        rv = True
                except ValueError:
                    return False

        # return
        return rv

    #
    # add a roll to the list
    # return True if roll is added, False if not added
    def add_roll(self, prr: PlayerRandomRoll) -> bool:
        """
        Add a roll to the list, assuming
            - high and low values match (if high/low are significant)
            - that the timestamp of this roll is within the RandomGroup window

        Args:
            prr: PlayerRandomRoll to be added

        Returns:
            Return True if roll is added, False if not added
        """
        rv = False

        # check if the random low and high limits match
        if ((not self.low_significant) or (prr.low == self.low)) and \
                ((not self.high_significant) or (prr.high == self.high)):

            # the assumption is these will be loaded in sequential, time-increasing order,
            # i.e. the first one is the starting time for the random window
            if len(self.rolls) == 0:
                self.start_time_stamp = prr.time_stamp

            # check if the timestamp to be added is in range
            elapsed_seconds = prr.time_stamp - self.start_time_stamp
            if elapsed_seconds.total_seconds() <= self.delta_seconds:

                # check that this person hasn't already randomed
                if self.player_roll(prr.player_name) is None:
                    self.rolls.append(prr)

                    # print out a running list of the winner(s)
                    high_list: list[PlayerRandomRoll] = self.high_roll_list()
                    rr: PlayerRandomRoll
                    for rr in high_list:
                        starprint(f'({self.low}-{self.high}): {rr.player_name}/{rr.random_value}', '>')

                    rv = True

        # true if added, false otherwise
        return rv

    #
    # sort the rolls in descending order, so high roll(s) is at start of list
    def sort_descending_randoms(self) -> None:
        """
        Sort the rolls in descending order, so high roll(s) is at start of list
        """
        self.rolls.sort(key=lambda x: x.random_value, reverse=True)

    #
    # sort the rolls in ascending time order
    def sort_ascending_timestamps(self) -> None:
        """
        Sort the rolls in ascending time order
        """
        self.rolls.sort(key=lambda x: x.time_stamp)

    #
    # return high roll(s) in a list()
    def high_roll_list(self) -> list[PlayerRandomRoll]:
        """
        Returns:
            Return high roll(s) in a list()
        """
        # get high roll to start of list and save the value
        self.sort_descending_randoms()
        high_roll = self.rolls[0].random_value

        # since there could be ties, add all high rolls to a list
        rv: list[PlayerRandomRoll] = list()
        elem: PlayerRandomRoll
        for elem in self.rolls:
            if elem.random_value == high_roll:
                rv.append(elem)

        # return list of high roll(s)
        return rv

    # walk the list and return the roll for a particular player
    # not particularly efficient since it just brute force visits every member in the list,
    # but the number of rollers is really never that high,
    # so in this case, simplicity wins over a very slight inefficiency
    def player_roll(self, player: str) -> PlayerRandomRoll:
        """
        Walk the list and return the roll for a particular player.
        Not particularly efficient since it just brute force visits every member in the list,
        but the number of rollers is really never that high, so in this case, simplicity
        wins over a very slight inefficiency

        Args:
            player: Name of the player

        Returns:
            The PlayerRandomRoll for this particular player
        """
        rv = None
        r: PlayerRandomRoll
        for r in self.rolls:
            if player == r.player_name:
                rv = r
        return rv


#
# Class to do all the random tracking work
#
class RandomParser:
    """
    Class to do all the random tracking work
    """

    #
    # ctor
    def __init__(self):
        """
        RandomParser ctor
        """
        # list of all random rolls, and all RandomEvents
        self.all_rolls = list()
        self.all_random_groups = list()

    #
    # check if a random is occurring
    def process_line(self, line: str) -> None:
        """
        This function does all the parsing work for the RandomParser class

        Args:
            line: current line from the EQ logfile being parsed
        """

        # begin by checking if any of the RandomEvents is due to expire
        rg: RandomGroup
        for (ndx, rg) in enumerate(self.all_random_groups):
            if not rg.expired:
                toggled = rg.check_expiration(line)
                if toggled:
                    # bell sound
                    if config.config_data.getboolean('EQValet', 'bell'):
                        print('\a')
                    print(f'{rg.report_summary(ndx, config.the_valet.char_name)}')

        #
        # cut off the leading date-time stamp info
        trunc_line = line[27:]

        #
        # check for toggling the parse on/off
        #
        target = r'^\.rt '
        m = re.match(target, trunc_line)
        if m:

            # the relevant section and key value from the ini configfile
            section = 'RandomParser'
            key = 'parse'
            setting = config.config_data.getboolean(section, key)

            if setting:
                config.config_data[section][key] = 'False'
                onoff = 'Off'
            else:
                config.config_data[section][key] = 'True'
                onoff = 'On'

            # save the updated ini file
            config.save()

            starprint(f'Random Parsing: {onoff}')

        #
        # report the current value of window
        #
        target = r'^\.win '
        m = re.match(target, trunc_line)
        if m:
            win = config.config_data.getint('RandomParser', 'default_window')
            starprint(f'RandomParser default grouping window: {win} seconds')

        #
        # change grouping window
        #
        target = r'^\.win\.(?P<new_win>[0-9]+) '
        m = re.match(target, trunc_line)
        if m:
            new_win = int(m.group('new_win'))
            config.config_data['RandomParser']['grouping_window'] = new_win

            # save the updated ini file
            config.save()

            starprint(f'RandomParser new grouping window: {new_win} seconds')

        #
        # only do everything else if parsing is true
        #
        if config.config_data.getboolean('RandomParser', 'parse'):

            #
            # show a summary of all randomevents
            #
            target = r'^\.rolls '
            m = re.match(target, trunc_line)
            if m:
                self.all_randoms_report()

            #
            # show a detailed report of one particular randomevent
            #
            target = r'^\.roll\.(?P<ndx>[0-9]+) '
            m = re.match(target, trunc_line)
            if m:
                ndx = int(m.group('ndx'))
                self.random_report(ndx)

            #
            # show the last randomevent
            #
            target = r'^\.roll '
            m = re.match(target, trunc_line)
            if m:
                ndx = len(self.all_random_groups) - 1
                self.random_report(ndx)

            #
            # regroup RandomGroup N with new window W
            #
            target = r'^\.win\.(?P<ndx>[0-9]+)\.(?P<new_win>[0-9]+) '
            m = re.match(target, trunc_line)
            if m:
                ndx = int(m.group('ndx'))
                new_win = int(m.group('new_win'))

                # is ndx in range
                if len(self.all_random_groups) == 0:
                    starprint(f'Error:  No RandomGroups to regroup!')

                elif (ndx < 0) or (ndx >= len(self.all_random_groups)):
                    starprint(f'Error:  Requested ndx value = {ndx}.  Value for ndx must be between 0 and {len(self.all_random_groups) - 1}')

                elif new_win <= 0:
                    starprint(f'Error:  Requested new_window value = {new_win}.  Value for new_window must be > 0')

                else:
                    starprint(f'Changing group [{ndx}] to new grouping window of [{new_win}], and rearranging groups as needed')
                    self.regroup(ndx, new_win)

            #
            # check for a random roll
            #
            target1 = '\\*\\*A Magic Die is rolled by (?P<playername>[\\w ]+)\\.'
            target2 = '\\*\\*It could have been any number from (?P<low>[0-9]+) to (?P<high>[0-9]+), ' \
                      'but this time it turned up a (?P<value>[0-9]+)\\.'

            # return value m is either None of an object with information about the RE search
            m = re.match(target1, trunc_line)
            if m:

                # fetch the player name
                player = m.group('playername')

                # get next line
                line = config.the_valet.readline()
                # print(line, end='')
                trunc_line = line[27:]

                # fetch the low, high, and value numbers
                m = re.match(target2, trunc_line)
                if m:
                    low = m.group('low')
                    high = m.group('high')
                    value = m.group('value')

                    # create the roll object
                    roll = PlayerRandomRoll(player, value, low, high, line)
                    starprint(f'Random: {roll.report("")}')

                    # add it to the list of all rolls
                    self.all_rolls.append(roll)

                    added = False
                    # add it to the appropriate RandomGroup - walk the list and try to add the roll to any open randomevents
                    for rg in self.all_random_groups:
                        if not rg.expired:
                            if rg.add_roll(roll):
                                added = True
                                break

                    # if the roll wasn't added, create a new RandomGroup to hold this one
                    if not added:
                        win = config.config_data['RandomParser']['grouping_window']
                        rg = RandomGroup(low, high, win)
                        rg.add_roll(roll)
                        self.all_random_groups.append(rg)

    #
    # regroup random groups with a new, different window than what the random events currently have
    def regroup(self, ndx: int = -1, new_window: int = 0, low_significant: bool = True, high_significant: bool = True) -> None:
        """
        Regroup random events with a new, different window than what the random events currently have

        Args:
            ndx: Which RandomGroup to regroup
            new_window: New window
            low_significant: Boolean to indicate if low value is significant in the grouping process
            high_significant: Boolean to indicate if the high value is significant in the grouping process
        """
        # is ndx in range
        if len(self.all_random_groups) == 0:
            starprint(f'Error:  No RandomGroups to regroup!')

        elif (ndx < 0) or (ndx >= len(self.all_random_groups)):
            starprint(f'Error:  Requested ndx value = {ndx}.  Value for ndx must be between 0 and {len(self.all_random_groups) - 1}')
        elif new_window <= 0:
            starprint(f'Error:  Requested new_window value = {new_window}.  Value for new_window must be > 0')

        else:
            # grab the requested random group, and restore it to time-ascending order
            old_rev: RandomGroup = self.all_random_groups.pop(ndx)

            low = old_rev.low
            high = old_rev.high
            rolls = old_rev.rolls

            # is the new, larger window overlapping into the next random group(s)?
            if new_window >= old_rev.delta_seconds:
                while ndx < len(self.all_random_groups):
                    next_rev = self.all_random_groups[ndx]
                    # get delta t
                    delta_seconds = next_rev.start_time_stamp - old_rev.start_time_stamp
                    delta = delta_seconds.total_seconds()
                    # does next random group and is within new time window?
                    # if ((low == next_rev.low) and (high == next_rev.high) and (delta <= new_window)):
                    if (not low_significant or low == next_rev.low) and \
                            (not high_significant or high == next_rev.high) and \
                            (delta <= new_window):
                        # add the next randomm group rolls to the list of rolls to be sorted / re-added
                        rolls += next_rev.rolls
                        self.all_random_groups.pop(ndx)
                    else:
                        ndx += 1

            # sort the list of all rolls in time-ascenting order
            rolls.sort(key=lambda x: x.time_stamp)

            # get all the rolls from the old random group(s)
            for r in rolls:

                added = False
                # add it to the appropriate RandomGroup - walk the list and try to add the roll to any open randomgroups
                rg: RandomGroup
                for rg in self.all_random_groups:
                    if not rg.expired:
                        rg.low_significant = low_significant
                        rg.high_significant = high_significant
                        if rg.add_roll(r):
                            added = True
                            break

                # if the roll wasn't added, create a new RandomGroup to hold this one
                if not added:
                    rg = RandomGroup(r.low, r.high, new_window, low_significant, high_significant)
                    rg.add_roll(r)
                    self.all_random_groups.append(rg)

            # sort the event list to restore it to time-ascending order
            self.all_random_groups.sort(key=lambda x: x.start_time_stamp)

            # if not expired yet, these are the random events just added, so close them, sort them, report them
            for (n, rg) in enumerate(self.all_random_groups):
                if not rg.expired:
                    rg.expired = True
                    rg.sort_descending_randoms()
                    print(f'{rg.report_summary(n, config.the_valet.char_name)}')

    #
    # show a report for one specific randomgroup
    def random_report(self, ndx: int) -> None:
        """
        Show a report for all random rolls in one specific randomgroup

        Args:
            ndx: Index into the array of all randomgroups
        """
        
        # is ndx in range
        if (ndx >= 0) and (ndx < len(self.all_random_groups)):

            # get the RandomGroup at ndx
            rg: RandomGroup = self.all_random_groups[ndx]
            reportbuffer = rg.report_detail(ndx, config.the_valet.char_name)
            print(f'{reportbuffer}')

        else:
            starprint(f'Requested ndx value = {ndx}.  Value for ndx must be between 0 and {len(self.all_random_groups) - 1}')

    #
    # show a report of all randomevents
    def all_randoms_report(self) -> None:
        """
        Show a report of all randomevents
        """

        width = util.REPORT_WIDTH
        fill1 = '-'
        fill2 = '='

        reportbuffer = f'{"":{fill2}^{width}}\n'
        reportbuffer += f'{"Summary of all randoms":^{width}}'
        reportbuffer += f'\n'

        reportbuffer += f'Total Rolls = {len(self.all_rolls)}\n'
        reportbuffer += f'Total Random Groups = {len(self.all_random_groups)}\n'

        # add the list of random events
        rg: RandomGroup
        for (ndx, rg) in enumerate(self.all_random_groups):
            reportbuffer += f'{rg.report_summary(ndx, config.the_valet.char_name)}'

        reportbuffer += f'{"":{fill1}^{width}}\n'

        print(f'{reportbuffer}')


def main():
    print()
    print('Try list operations')
    print()

    print('list of integers')
    ll = list()
    ll.append(5)
    ll.append(1)
    ll.append(3)
    ll.append(2)
    print(ll)

    ll.sort()
    print(ll)
    print()

    print('list of tuples')
    mm = list()
    mm.append(('Susan', 33))
    mm.append(('Hank', 47))
    mm.append(('John', 22))
    mm.append(('John', 99))
    mm.append(('Jimmy', 12))
    print(mm)
    mm.sort(key=lambda roll: roll[1])
    print(mm)

    print()

    print('using dictionary')
    dd = dict()
    dd['Susan'] = (33, 0, 1000)
    dd['Hank'] = (47, 0, 1000)
    dd['John'] = (22, 0, 1000)
    dd['John'] = (99, 0, 1000)
    dd['Jimmy'] = (12, 0, 1000)
    print(dd)
    sorted_dd = sorted(dd.items(), key=lambda x: x[1], reverse=True)
    print(sorted_dd)
    print()

    print('list of PlayerRandomRolls')

    rr = list()

    line1 = '[Tue Jul 13 00:30:05 2021]'
    line2 = '[Tue Jul 13 00:30:06 2021]'
    line3 = '[Tue Jul 13 00:30:07 2021]'
    line4 = '[Tue Jul 13 00:30:35 2021]'
    line5 = '[Tue Jul 13 00:30:47 2021]'

    r = PlayerRandomRoll('Susan', 33, 0, 1000, line1)
    rr.append(r)
    r = PlayerRandomRoll('Hank', 47, 0, 1000, line2)
    rr.append(r)
    r = PlayerRandomRoll('John', 22, 0, 1000, line3)
    rr.append(r)
    r = PlayerRandomRoll('John', 99, 0, 1000, line3)
    rr.append(r)
    r = PlayerRandomRoll('Jimmy', 12, 0, 1000, line4)
    rr.append(r)
    print(rr)

    rr.sort(key=lambda x: x.random_value)
    print(rr)

    rr.sort(key=lambda x: x.random_value, reverse=True)
    print(rr)
    print()

    print('use RandomGroup class')
    rl = RandomGroup(0, 1000, 30)
    r = PlayerRandomRoll('FirstRoll', 33, 0, 1000, line1)
    print(rl.add_roll(r))
    r = PlayerRandomRoll('HighRoller', 47, 0, 1000, line2)
    print(rl.add_roll(r))
    r = PlayerRandomRoll('TieRoller', 47, 0, 1000, line2)
    print(rl.add_roll(r))
    r = PlayerRandomRoll('DoubleRoller', 22, 0, 1000, line3)
    print(rl.add_roll(r))
    r = PlayerRandomRoll('DoubleRoller', 99, 0, 1000, line3)
    print(rl.add_roll(r))
    r = PlayerRandomRoll('AlmostLateRoller', 12, 0, 1000, line4)
    print(rl.add_roll(r))
    r = PlayerRandomRoll('LateRoller', 12, 0, 1000, line5)
    print(rl.add_roll(r))

    print('roll list as entered')
    print(rl)
    print('roll list sorted')
    rl.sort_descending_randoms()
    print(rl)
    print()

    print('roll winner')
    print(rl.high_roll_list())
    print()

    print('DoubleRoller roll')
    print(rl.player_roll('DoubleRoller'))
    print()

    print('LateRoller roll')
    print(rl.player_roll('LateRoller'))
    print()

    print('Exiting main()')


if __name__ == '__main__':
    main()
