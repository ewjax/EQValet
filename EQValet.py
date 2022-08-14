import re
import asyncio

# import the global config data
import config

import EverquestLogFile
import DamageParser
import PetParser
import RandomParser
from util import starprint


#################################################################################################

class EQValet(EverquestLogFile.EverquestLogFile):

    # ctor
    def __init__(self) -> None:

        # force global data to load from ini file
        config.load()

        # parent ctor
        base_dir = config.config_data.get('Everquest', 'base_directory')
        logs_dir = config.config_data.get('Everquest', 'logs_directory')
        heartbeat = config.config_data.getint('Everquest', 'heartbeat')
        super().__init__(base_dir, logs_dir, heartbeat)

        # use a RandomParser class to deal with all things random numbers and rolls
        self.random_parser = RandomParser.RandomParser()

        # use a DamageParser class to keep track of total damage dealt by spells and by pets
        self.damage_parser = DamageParser.DamageParser()

        # use a PetParser class to deal with all things pets
        self.pet_parser = PetParser.PetParser()

    # process each line
    async def process_line(self, line):
        # call parent to edit every line, the default behavior
        # super().process_line(line)

        #
        # check for general commands
        #
        # cut off the leading date-time stamp info
        trunc_line = line[27:]

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

        # check for .status command
        target = r'^\.status'
        m = re.match(target, trunc_line)
        if m:
            if self.is_parsing():
                starprint(f'Parsing character log for:    [{self.char_name}]')
                starprint(f'Log filename:                 [{self.filename}]')
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

            # save the updated ini file
            config.save()

            starprint(f'Bell tone notification: {onoff}')

        # check for a random
        self.random_parser.process_line(line)

        # check for damage-related content
        self.damage_parser.process_line(line)

        # check for pet-related content
        self.pet_parser.process_line(line)

    @staticmethod
    def help_message():
        starprint('')
        starprint('', '^', '*')
        starprint('')
        starprint('EQValet:  Help', '^')
        starprint('')
        starprint('User commands are accomplished by sending a tell to the below fictitious player names:')
        starprint('')
        starprint('General')
        starprint('  .help          : This message')
        starprint('  .bt            : Toggle bell tone on/off.  Summary results can optionally be accompanied with a notification bell tone')
        starprint('  .w or .who     : Show list of all names currently stored player names database')
        starprint('                 : Note that the database is updated every time an in-game /who occurs')
        starprint('Pets')
        starprint('  .pet           : Show information about current pet')
        starprint('  .pt            : Toggle pet tracking on/off')
        starprint('Combat')
        starprint('  .ct            : Toggle combat damage tracking on/off')
        starprint('  .cto           : Show current value for how many seconds until combat times out')
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
    # print a startup message
    starprint('')
    starprint('-------------------------------------------------')
    starprint('EQValet')
    starprint('-------------------------------------------------')
    starprint('')

    # create and start the EQValet parser
    config.the_valet = EQValet()
    config.the_valet.go()

    starprint('EQValet running')

    # while True followed by pass seems to block asyncio coroutines, so give the asyncio task a chance to break out
    while True:
        # sleep for 100 msec
        await asyncio.sleep(0.1)


if __name__ == '__main__':
    asyncio.run(main())
