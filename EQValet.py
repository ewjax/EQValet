import re
import asyncio

# import pywin32_bootstrap
import win32console

# import the global config data
import LogEventParser
import config
import _version

import EverquestLogFile
import DamageParser
import PetParser
import RandomParser
import DeathLoopParser
import WhoParser
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

        # add some of the parsers
        self.parser_list = [
            RandomParser.RandomParser(),
            DamageParser.DamageParser(),
            DeathLoopParser.DeathLoopParser(),
        ]

        # now add the rest, the ones we need a pointer to

        # keep a pointer to the pet parser and LogEventParser since we need explicit access to it later
        self.pet_parser = PetParser.PetParser()
        self.parser_list.append(self.pet_parser)

        self.parse_target_parser = LogEventParser.LogEventParser()
        self.parser_list.append(self.parse_target_parser)

        self.who_parser = WhoParser.WhoParser(self)
        self.parser_list.append(self.who_parser)

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
            # reload, then show the ini file
            config.load()

        # check for .status command
        target = r'^\.status'
        m = re.match(target, trunc_line)
        if m:
            if self.is_parsing():
                starprint(f'Parsing character log for:    [{self.get_char_name()}]')
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
        self.parse_target_parser.set_char_name(name)

    def set_server_name(self, server_name: str) -> None:
        """
        override base class setter function to open player name database

        Args:
            server_name: server name
        """
        # do we need to reload the player name database?
        if server_name != self.get_server_name():
            self.who_parser.read_player_names(server_name)
        super().set_server_name(server_name)

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
        starprint('  .save          : Force console window on screen position to be saved/remembered')
        starprint('  .ini           : Reload EQValet.ini settings, and display contents')
        starprint('  .ver           : Display EQValet current version')
        starprint('Who / Character Name Database')
        starprint('  .wt            : Toggle who tracking on/off')
        starprint('  .w or .who     : Show list of all names currently stored player names database')
        starprint('                 : Note that the database is updated every time an in-game /who occurs')
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
        starprint('LogEvent Parsing')
        starprint('  .log           : Show a summary of all LogEvents and their parsing status (True/False)')
        starprint('')
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
