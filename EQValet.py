import re
import asyncio
import pickle

import pywin32_bootstrap
import win32console

# import the global config data
import ParseTarget
import config
import _version

import EverquestLogFile
import DamageParser
import PetParser
import RandomParser
import DeathLoopParser
import util
from util import starprint


#################################################################################################

class EQValet(EverquestLogFile.EverquestLogFile):

    # ctor
    def __init__(self) -> None:

        # force global data to load from ini logfile
        config.load()

        # move console window to saved position
        x = config.config_data.getint('ConsoleWindowPosition', 'x')
        y = config.config_data.getint('ConsoleWindowPosition', 'y')
        width = config.config_data.getint('ConsoleWindowPosition', 'width')
        height = config.config_data.getint('ConsoleWindowPosition', 'height')
        util.move_window(x, y, width, height)

        # parent ctor
        base_dir = config.config_data.get('Everquest', 'base_directory')
        logs_dir = config.config_data.get('Everquest', 'logs_directory')
        heartbeat = config.config_data.getint('Everquest', 'heartbeat')
        super().__init__(base_dir, logs_dir, heartbeat)

        # set of player names
        self.player_names_set = set()
        self.player_names_count = 0
        self.player_names_filename = 'Unknown'

        # add all but PetParser
        self.parser_list = [
            RandomParser.RandomParser(),
            DamageParser.DamageParser(),
            DeathLoopParser.DeathLoopParser(),
            ParseTarget.ParseTargetParser(),
        ]

        # keep a pointer to the pet parser since we need explicit access to it later
        self.pet_parser = PetParser.PetParser()
        self.parser_list.append(self.pet_parser)

    #
    # process each line
    async def process_line(self, line: str, printline: bool = False) -> None:
        # call parent to edit every line, the default behavior
        await super().process_line(line, printline)

        # cut off the leading date-time stamp info
        trunc_line = line[27:]

        # save console window positioning
        target = r'^\.save '
        m = re.match(target, trunc_line)
        if m:
            (x, y, width, height) = util.get_window_coordinates()

            section = 'ConsoleWindowPosition'
            config.config_data[section]['x'] = f'{x}'
            config.config_data[section]['y'] = f'{y}'
            config.config_data[section]['width'] = f'{width}'
            config.config_data[section]['height'] = f'{height}'

            # save the updated ini logfile
            config.save()
            starprint(f'Console window position saved to .ini file')

        # show current version number
        target = r'^\.ver '
        m = re.match(target, trunc_line)
        if m:
            starprint(f'EQValet {_version.__VERSION__}')

        # todo - just testing the ability to enter a waypoint, with positive and negative value
        target = r'^\.wp\.(?P<eqx>[0-9-]+)\.(?P<eqy>[0-9-]+) '
        m = re.match(target, trunc_line)
        if m:
            eqx = int(m.group('eqx'))
            eqy = int(m.group('eqy'))
            print(f'User asked for waypoint at ({eqx},{eqy})')

        # check for .help command
        target = r'^\.help'
        m = re.match(target, trunc_line)
        if m:
            EQValet.help_message()

        # check for .ini command
        target = r'^\.ini'
        m = re.match(target, trunc_line)
        if m:
            # show the ini file
            config.show()

        # check for .status command
        target = r'^\.status'
        m = re.match(target, trunc_line)
        if m:
            if self.is_parsing():
                starprint(f'Parsing character log for:    [{self._char_name}]')
                starprint(f'Log filename:                 [{self.logfile_name}]')
                starprint(f'Heartbeat timeout (seconds):  [{self.heartbeat}]')
            else:
                starprint(f'Not currently parsing')

        # check for .bt command
        target = r'^\.bt'
        m = re.match(target, trunc_line)
        if m:
            # the relevant section and key from the ini configfile
            section = 'EQValet'
            key = 'bell'
            bell = config.config_data.getboolean(section, key)

            if bell:
                config.config_data[section][key] = 'False'
                onoff = 'Off'
            else:
                config.config_data[section][key] = 'True'
                onoff = 'On'

            # save the updated ini logfile
            config.save()

            starprint(f'Bell tone notification: {onoff}')

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

        # sweep through the list of parsers and have them check the current line
        for parser in self.parser_list:
            await parser.process_line(line)

    def set_char_name(self, name: str) -> None:
        """
        override base class setter function to also sweep through list of parse targets
        and set their parsing player names

        Args:
            name: player whose log file is being parsed
        """
        super().set_char_name(name)

    def set_server_name(self, server_name: str) -> None:
        """
        override base class setter function to open player name database

        Args:
            server_name: server name
        """
        # super().set_server_name(server_name)
        self.read_player_names(server_name)

    #
    #
    def read_player_names(self, servername) -> bool:
        """
        Read player names from the database logfile being maintained

        Returns:
            Boolean indicating read success/failure
        """

        # only read names if the servername has changed
        if self._server_name != servername:

            self._server_name = servername
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
        self.readline()
        # nextline = self.readline()
        # print(nextline, end='')

        # read all the name(s) in the /who report
        while processing_names:

            # get next line
            nextline = self.readline()
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
    @staticmethod
    def help_message() -> None:
        """
        Print out a Help message
        """
        starprint('')
        starprint('', '^', '*')
        starprint('')
        starprint('EQValet:  Help', '^')
        starprint('')
        starprint('User commands are accomplished by sending a tell to the below fictitious player names:')
        starprint('')
        starprint('General')
        starprint('  .help          : This message')
        starprint('  .status        : Show logfile parsing status')
        starprint('  .bt            : Toggle summary reports bell tone on/off')
        starprint('  .w or .who     : Show list of all names currently stored player names database')
        starprint('                 : Note that the database is updated every time an in-game /who occurs')
        starprint('  .save          : Force console window on screen position to be saved/remembered')
        starprint('  .ini           : Display contents of EQValet.ini')
        starprint('  .ver           : Display EQValet current version')
        starprint('Pets')
        starprint('  .pet           : Show information about current pet')
        starprint('  .pt            : Toggle pet tracking on/off')
        starprint('Combat')
        starprint('  .ct            : Toggle combat damage tracking on/off')
        starprint('  .cto           : Show current value for how many seconds until combat times out')
        starprint('Death Loops')
        starprint('  .dlt           : Toggle death loop tracking on/off')
        starprint('  .dl            : Show death loop parameters')
        starprint('  .deathloop     : Simulate a death, for testing')
        starprint('Randoms')
        starprint('  .rt            : Toggle combat damage tracking on/off')
        starprint('  .rolls         : Show a summary of all random groups, including their index values N')
        starprint('  .roll          : Show a detailed list of all rolls from the LAST random group')
        starprint('  .roll.N        : Show a detailed list of all rolls from random event group N')
        starprint('  .win           : Show default window (seconds) for grouping of randoms')
        starprint('  .win.W         : Set the default grouping window to W seconds')
        starprint('  .win.N.W       : Change group N to new grouping window W seconds')
        starprint('                 : All rolls are retained, and groups are combined or split up as necessary')
        starprint('Examples:')
        starprint('  /t .rolls      : Summary of all random groups')
        starprint('  /t .roll       : Detailed report for the most recent random group')
        starprint('  /t .roll.12    : Detailed report for random group index [12]')
        starprint('  /t .win.20     : Change the default grouping window to 20 seconds')
        starprint('  /t .win.8.30   : Change group [8] to new grouping window to 30 seconds')
        starprint('')
        starprint('', '^', '*')
        starprint('')

#################################################################################################


async def main():
    # set console title
    win32console.SetConsoleTitle('EQValet')

    # print a startup message
    starprint('')
    starprint('=', alignment='^', fill='=')
    starprint(f'EQValet {_version.__VERSION__}', alignment='^')
    starprint('=', alignment='^', fill='=')
    starprint('')

    # create and start the EQValet parser
    config.the_valet = EQValet()
    config.the_valet.go()

    starprint('EQValet running')
    config.the_valet.help_message()

    # while True followed by pass seems to block asyncio coroutines, so give the asyncio task a chance to break out
    while True:
        # sleep for 100 msec
        await asyncio.sleep(0.1)


if __name__ == '__main__':
    asyncio.run(main())
