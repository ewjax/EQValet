import re
import pickle

import Parser
import EverquestLogFile
from util import starprint

# import the global config data
import config


#
# class to do all the character tracking work
#
class WhoParser(Parser.Parser):
    """
    Class to do all the character tracking work
    """
    # ctor
    def __init__(self, logfile_parser: EverquestLogFile) -> None:
        super().__init__()

        # set of player names
        self.player_names_set = set()
        self.player_names_count = 0
        self.player_names_filename = 'Unknown'

        self.logfile_parser = logfile_parser

    #
    #
    async def process_line(self, line: str) -> None:
        """
        This method gets called by the base class parsing thread once for each parsed line.
        We overload it here to perform our special case parsing tasks.

        Args:
            line: string with a single line from the logfile
        """

        # call base class
        await super().process_line(line)

        #
        # cut off the leading date-time stamp info
        trunc_line = line[27:]

        #
        # check for toggling the parse on/off
        #
        target = r'^\.wt '
        m = re.match(target, trunc_line)
        if m:

            # the relevant section and key value from the ini configfile
            section = 'WhoParser'
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

            starprint(f'Who Parsing: {onoff}')

        # only do everything else if parsing is true
        if config.config_data.getboolean('WhoParser', 'parse'):

            # watch for .who|.w user commands
            target = r'^(\.who )|(\.w )'
            m = re.match(target, trunc_line)
            if m:
                self.who_list()

            # watch for /who in-game commands
            who_regexp = r'^Players (in|on) EverQuest'
            m = re.match(who_regexp, trunc_line)
            if m:
                self.who()

    #
    #
    def who_list(self) -> None:
        """
        Print out a full list of all names in the /who database
        """
        namebuffer = f'Sorted list of all player names stored in /who database: {self.player_names_filename}\n'
        current_firstchar = None

        # walk the sorted list of names
        for name in sorted(self.player_names_set):

            # check first character of current name
            testchar = name[0]

            # new first character detected
            if testchar != current_firstchar:
                # print current with the old first character
                print(namebuffer)

                # now reset the data and get it ready for this character
                current_firstchar = testchar
                namebuffer = f'\n[{current_firstchar}] Names:\n'
                namebuffer += f'{name}, '

            # same first char
            else:
                # just append this name to the namebuffer
                namebuffer += f'{name}, '

        # print the last namebuffer
        print(namebuffer)

    #
    #
    def who(self) -> None:
        """
        Process the list of names from an in-game /who command
        """
        starprint('/who detected, checking for new names to add to database')
        processing_names = True
        player_names_set_modified = False

        # # debugging output
        # [Sun Dec 19 20:33:44 2021] Players on EverQuest:
        # [Sun Dec 19 20:33:44 2021] ---------------------------
        # [Sun Dec 19 20:33:44 2021] [ANONYMOUS] Aijalon
        # [Sun Dec 19 20:33:44 2021] [ANONYMOUS] Yihao
        # [Sun Dec 19 20:33:44 2021] [54 Disciple] Weth (Iksar) <Safe Space>
        # [Sun Dec 19 20:33:44 2021] [54 Disciple] Rcva (Iksar) <Kingdom>
        # [Sun Dec 19 20:33:44 2021] [ANONYMOUS] Yula  <Force of Will>
        # [Sun Dec 19 20:33:44 2021] [57 Master] Twywu (Iksar) <Safe Space>
        # [Sun Dec 19 20:33:44 2021] [ANONYMOUS] Tenedorf  <Safe Space>
        # [Sun Dec 19 20:33:44 2021] [60 Grave Lord] Gratton (Troll) <Force of Will>
        # [Sun Dec 19 20:33:44 2021] [ANONYMOUS] Bloodreign
        # [Sun Dec 19 20:33:44 2021] [60 Phantasmist] Azleep (Elemental) <Force of Will>
        # [Sun Dec 19 20:33:44 2021] There are 10 players in Trakanon's Teeth.

        # get next line - many dashes
        self.logfile_parser.readline()
        # nextline = self.readline()
        # print(nextline, end='')

        # read all the name(s) in the /who report
        while processing_names:

            # get next line
            nextline = self.logfile_parser.readline()
            # print(nextline, end='')
            trunc_line = nextline[27:]

            # as a safety net, just presume this is not the next name on the report
            processing_names = False

            # oddly, sometimes the name lists is preceeded by a completely blank line,
            # usually when a /who all command has been issued
            # this regex allows for a blank line
            name_regexp = r'(^(?: AFK +)?(?:<LINKDEAD>)?\[(?P<player_level>\d+ )?(?P<player_class>[A-z ]+)\] (?P<player_name>[\w]+)|^$)'
            m = re.match(name_regexp, trunc_line)
            if m:
                # since we did successfully find a name, extend the processing for another line
                processing_names = True

                # process the name.  will return None if got here via the empty ^$ line that /who all puts out
                record = ''
                player_name = m.group('player_name')
                if player_name:
                    record += player_name
                    if player_name not in self.player_names_set:
                        self.player_names_set.add(player_name)
                        player_names_set_modified = True

                player_level = m.group('player_level')
                if player_level:
                    record += ' '
                    record += player_level

                player_class = m.group('player_class')
                if player_class:
                    record += ' '
                    record += player_class

                # if record != '':
                #     print(record)

        # done processing /who list
        if player_names_set_modified:
            self.write_player_names()

    #
    #
    def read_player_names(self, servername) -> bool:
        """
        Read player names from the database logfile being maintained

        Returns:
            Boolean indicating read success/failure
        """

        self.player_names_filename = 'data/EQValet-PlayerNames_' + servername + '.dat'

        # throws and exception if logfile doesn't exist
        try:
            f = open(self.player_names_filename, 'rb')
            # discard current names, and reload fresh
            self.player_names_set.clear()
            self.player_names_set = pickle.load(f)
            f.close()

            self.player_names_count = len(self.player_names_set)
            starprint(f'Read {self.player_names_count} player names from [{self.player_names_filename}]')

            return True
        except OSError as err:
            print("OS error: {0}".format(err))
            print('Unable to open logfile_name: [{}]'.format(self.player_names_filename))
            return False

    #
    #
    def write_player_names(self) -> bool:
        """
        Write player names to the database logfile being maintained

        Returns:
            Boolean indicating write success/failure
        """
        try:
            f = open(self.player_names_filename, 'wb')
            pickle.dump(self.player_names_set, f)
            f.close()

            old_count = self.player_names_count
            new_count = len(self.player_names_set)
            self.player_names_count = new_count

            starprint(f'{new_count - old_count} new, {new_count} total player names written to [{self.player_names_filename}]')
            return True

        except OSError as err:
            print("OS error: {0}".format(err))
            print('Unable to open logfile_name: [{}]'.format(self.player_names_filename))
            return False


def main():
    pass


if __name__ == '__main__':
    main()
