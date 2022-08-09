# import asyncio
import asyncio
import time
import re

import discord
from discord.ext import commands

# import the global config data
import config

import EverquestLogFile
import DamageParser
import PetParser
import RandomParser
from util import starprint

# allow for testing, by forcing the bot to read an old log file
# TEST_BOT = False
TEST_BOT = True


#################################################################################################


# define the client instance to interact with the discord bot

class EQValetClient(commands.Bot):

    # ctor
    def __init__(self):

        # force global data to load from ini file
        config.load()

        # call parent ctor
        prefix = config.config_data.get('Discord', 'BOT_COMMAND_PREFIX')
        commands.Bot.__init__(self, command_prefix=prefix)

        # create the EQ log file parser
        config.elf = EverquestLogFile.EverquestLogFile()

        # use a RandomParser class to deal with all things random numbers and rolls
        config.random_tracker = RandomParser.RandomParser()

        # use a DamageParser class to keep track of total damage dealt by spells and by pets
        config.damage_tracker = DamageParser.DamageParser()

        # use a PetParser class to deal with all things pets
        config.pet_tracker = PetParser.PetParser()

    # process each line
    async def process_line(self, line):
        # print(line, end='')

        #
        # check for general commands
        #
        # cut off the leading date-time stamp info
        trunc_line = line[27:]

        #
        # todo - just testing the ability to enter a waypoint, with positive and negative value
        #
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
            starprint('')
            starprint('', '^', '*')
            starprint('')
            starprint('EQValet:  Help', '^')
            starprint('')
            starprint('User commands are accomplished by sending a tell to the below fictitious player names:')
            starprint('')
            starprint('General')
            starprint('  .help          : This message')
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
            starprint('  .win.N.W       : Change the grouping window of group N from the default value to new value W')
            starprint('                 : Note that all rolls are retained, but groups may be split or combined as necessary')
            starprint('Examples:')
            starprint('  /t .rolls      : Summary of all random groups')
            starprint('  /t .roll       : Detailed report for the most recent random group')
            starprint('  /t .roll.12    : Detailed report for random group index [12]')
            starprint('  /t .win.1.20   : Change the grouping window of group 1 from the default value to 20 seconds')
            starprint('')
            starprint('', '^', '*')
            starprint('')

        # check for .status command
        target = r'^\.status'
        m = re.match(target, trunc_line)
        if m:
            if config.elf.is_parsing():
                starprint(f'Parsing character log for:    [{config.elf.char_name}]')
                starprint(f'Log filename:                 [{config.elf.filename}]')
                starprint(f'Heartbeat timeout (seconds):  [{config.elf.heartbeat}]')
            else:
                starprint(f'Not currently parsing')

        # check for a random
        config.random_tracker.process_line(line)

        # check for damage-related content
        config.damage_tracker.process_line(line)

        # check for pet-related content
        config.pet_tracker.process_line(line)

    # sound the alert
    async def alert(self, msg):

        channel_id = config.config_data.getint('Discord', 'PERSONAL_SERVER_ALERTID')
        special_channel = self.get_channel(channel_id)
        await special_channel.send(msg)

    # notify of pop
    async def pop(self, msg):

        channel_id = config.config_data.getint('Discord', 'PERSONAL_SERVER_POPID')
        special_channel = self.get_channel(channel_id)
        await special_channel.send(msg)

    # send message to the special EQValet channel
    async def send(self, msg):

        channel_id = config.config_data.getint('Discord', 'PERSONAL_SERVER_VALETID')
        special_channel = self.get_channel(channel_id)
        await special_channel.send(msg)

    # begin parsing
    async def begin_parsing(self):
        # already parsing?
        if config.elf.is_parsing():
            await self.send('Already parsing character log for: [{}]'.format(config.elf.char_name))

        else:

            # use a back door to force the system to read a test file
            if TEST_BOT:

                # read a sample file for testing
                filename = './data/test/randoms.txt'
                # filename = './data/test/pets.txt'
                # filename = './data/test/pets_long.txt'
                # filename = './data/test/fights.txt'

                # start parsing, but in this case, start reading from the beginning of the file,
                # rather than the end (default)
                rv = config.elf.open(self.user, 'Testing', filename, seek_end=False)

            # open the latest file
            else:
                # open the latest file, and kick off the parsing process
                rv = config.elf.open_latest(self.user)

            # if the log file was successfully opened, then initiate parsing
            if rv:

                # status message
                await self.send('Now parsing character log for: [{}]'.format(config.elf.char_name))

                # create the background processs and kick it off
                self.loop.create_task(parse())

            else:
                await self.send('ERROR: Could not open character log file for: [{}]'.format(config.elf.char_name))
                await self.send('Log filename: [{}]'.format(config.elf.filename))


#################################################################################################

# create the global instance of the client that manages communication to the discord bot
client = EQValetClient()


#
# add decorator event handlers to the client instance
#

# on_ready
@client.event
async def on_ready():
    print('EQ Valet is alive!')
    print('Discord.py version: {}'.format(discord.__version__))

    print('Logged on as {}'.format(client.user))
    print('App ID: {}'.format(client.user.id))

    await client.send('EQ Valet is alive!')
    await client.begin_parsing()


# on_message - catches everything, messages and commands
# note the final line, which ensures any command gets processed as a command, and not just absorbed here as a message
@client.event
async def on_message(message):
    author = message.author
    content = message.content
    channel = message.channel
    print('Content received: [{}] from [{}] in channel [{}]'.format(content, author, channel))
    await client.process_commands(message)


# ping command
@client.command(aliases=['ping'])
async def gen_ping(ctx):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
    await client.send('Latency = {} ms'.format(round(client.latency * 1000)))


# rolls command
# how many randoms have there been
@client.command(aliases=['rolls'])
async def ran_rolls(ctx):
    # print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
    #
    # # create a smart buffer to keep buffers under max size for discord messages (2000)
    # sb = SmartBuffer()
    #
    # # add total rolls, and total random events
    # sb.add('Total Rolls = {}\n'.format(len(config.random_tracker.all_rolls)))
    # sb.add('Total Random Events = {}\n'.format(len(config.random_tracker.all_random_groups)))
    #
    # # add the list of random events
    # for (ndx, rev) in enumerate(config.random_tracker.all_random_groups):
    #     sb.add('{}'.format(rev.report_summary(ndx, config.elf.char_name)))
    #
    # # get the list of buffers and send each to discord
    # bufflist = sb.get_bufflist()
    # for b in bufflist:
    #     await client.send('{}'.format(b))
    pass


# show command
# show all rolls in a specified RandomGroup
@client.command(aliases=['show'])
async def ran_show(ctx, ndx=-1):
    # print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
    #
    # # if the ndx value isn't specified, default to showing the last randomevent
    # if ndx == -1:
    #     ndx = len(config.random_tracker.all_random_groups) - 1
    #
    # # is ndx in range
    # if (ndx >= 0) and (ndx < len(config.random_tracker.all_random_groups)):
    #     rev = config.random_tracker.all_random_groups[ndx]
    #
    #     # create a smart buffer to keep buffers under max size for discord messages (2000)
    #     sb = SmartBuffer()
    #
    #     # add the header
    #     sb.add(rev.report_header(ndx))
    #
    #     # add all the rolls
    #     for prr in rev.rolls:
    #         sb.add(prr.report(config.elf.char_name))
    #
    #     # add the winner
    #     sb.add(rev.report_winner(config.elf.char_name))
    #
    #     # get the list of buffers and send each to discord
    #     bufflist = sb.get_bufflist()
    #     for b in bufflist:
    #         await client.send('{}'.format(b))
    #
    # else:
    #     await client.send('Requested ndx value = {}.  Value for ndx must be between 0 and {}'.format(ndx, len(config.random_tracker.all_random_groups) - 1))
    #     await client.send('Unspecified ndx value = shows most recent random event')
    pass


# regroup command
# allows user to change the delta window on any given RandomGroup
@client.command(aliases=['regroup'])
async def ran_regroup(ctx, ndx=-1, new_window=0, low_significant=True, high_significant=True):
    # print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
    #
    # # is ndx in range
    # if len(config.random_tracker.all_random_groups) == 0:
    #     await client.send('Error:  No RandomEvents to regroup!')
    #
    # elif (ndx < 0) or (ndx >= len(config.random_tracker.all_random_groups)):
    #     await client.send('Error:  Requested ndx value = {}.  Value for ndx must be between 0 and {}'.format(ndx, len(config.random_tracker.all_random_groups) - 1))
    # elif new_window <= 0:
    #     await client.send(
    #         'Error:  Requested new_window value = {}.  Value for new_window must be > 0'.format(new_window))
    #
    # else:
    #     await config.random_tracker.regroup(ndx, new_window, low_significant, high_significant)
    pass


# window command
# change the default window for future RandomEvents
@client.command(aliases=['win', 'window'])
async def ran_window(ctx, new_window=0):
    # print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
    #
    # if new_window < 0:
    #     await client.send(
    #         'Error:  Requested new_window value = {}.  Value for new_window must be > 0'.format(new_window))
    #
    # elif new_window == 0:
    #     await client.send('RandomGroup default window = {}'.format(config.random_tracker.default_window))
    #
    # else:
    #     config.random_tracker.default_window = new_window
    #     await client.send('RandomGroup default window = {}'.format(config.random_tracker.default_window))
    pass


# firedrill command
# test the ability to send a message to the #pop channel
@client.command(aliases=['fd', 'firedrill'])
async def gen_firedrill(ctx):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))

    await client.alert('This is a test.  This is only a test.')
    await client.pop('This is a test.  This is only a test.')
    await client.send('This is a test.  This is only a test.')


# start command
@client.command(aliases=['go', 'start'])
async def gen_start(ctx):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))

    await client.begin_parsing()


# status command
@client.command(aliases=['status'])
async def gen_status(ctx):
    # print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
    #
    # if config.elf.is_parsing():
    #     await client.send('Parsing character log for: [{}]'.format(config.elf.char_name))
    #     await client.send('Log filename: [{}]'.format(config.elf.filename))
    #     await client.send('Parsing initiated by: [{}]'.format(config.elf.author))
    #     await client.send('Heartbeat timeout (seconds): [{}]'.format(config.elf.heartbeat))
    #
    # else:
    #     await client.send('Not currently parsing')
    pass


# pet command
@client.command(aliases=['pet'])
async def pet_pet(ctx):
    # print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
    #
    # if config.pet_tracker.current_pet:
    #     await client.send(config.pet_tracker.current_pet)
    #
    # else:
    #     await client.send('No pet')
    pass


# cto command
# change the combat timeout value
@client.command(aliases=['cto'])
async def com_timeout(ctx, new_cto=0):
    # print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
    #
    # if new_cto < 0:
    #     await client.send('Error:  Requested new_cto value = {}.  Value for new_cto must be > 0'.format(new_cto))
    #
    # elif new_cto == 0:
    #     await client.send('DamageParser combat timeout (CTO) = {}'.format(config.damage_tracker.combat_timeout))
    #
    # else:
    #     config.damage_tracker.combat_timeout = new_cto
    #     await client.send('DamageParser Combat timeout (CTO) = {}'.format(config.damage_tracker.combat_timeout))
    pass


# toggle combat tracking command
@client.command(aliases=['ct'])
async def com_toggle(ctx):
    # print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
    #
    # if client.damage_parse:
    #     client.damage_parse = False
    #     onoff = 'Off'
    # else:
    #     client.damage_parse = True
    #     onoff = 'On'
    #
    # await client.send('Combat Parsing: {}'.format(onoff))
    pass


# list player names
@client.command(aliases=['who', 'w'])
async def com_who(ctx):
    # print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
    #
    # sb = SmartBuffer()
    # sb.add('Sorted list of all player names stored in /who database: {}\n'.format(
    #     config.damage_tracker.player_names_fname))
    #
    # for name in sorted(config.damage_tracker.player_names_set):
    #     sb.add('\t{}\n'.format(name))
    #
    # # get the list of buffers and send each to discord
    # bufflist = sb.get_bufflist()
    # for b in bufflist:
    #     await client.send('{}'.format(b))
    pass


# toggle combat tracking command
@client.command(aliases=['pt'])
async def pet_toggle(ctx):
    # print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
    #
    # if client.pet_parse:
    #     client.pet_parse = False
    #     onoff = 'Off'
    # else:
    #     client.pet_parse = True
    #     onoff = 'On'
    #
    # await client.send('Pet Parsing: {}'.format(onoff))
    pass


# toggle combat tracking command
@client.command(aliases=['rt'])
async def ran_toggle(ctx):
    # print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
    #
    # if client.random_parse:
    #     client.random_parse = False
    #     onoff = 'Off'
    # else:
    #     client.random_parse = True
    #     onoff = 'On'
    #
    # await client.send('Random Parsing: {}'.format(onoff))
    pass

#################################################################################################


# the background process to parse the log files
#
async def parse():
    print('Parsing Started')

    # process the log file lines here
    while config.elf.is_parsing():

        # read a line
        line = config.elf.readline()
        now = time.time()
        if line:
            config.elf.prevtime = now

            # process this line
            await client.process_line(line)

        else:
            # check the heartbeat.  Has our tracker gone silent?
            elapsed_seconds = (now - config.elf.prevtime)

            if elapsed_seconds > config.elf.heartbeat:
                starprint(f'Heartbeat over limit, elapsed seconds = {elapsed_seconds:.2f}', '>')
                config.elf.prevtime = now

                # attempt to open latest log file - returns True if a new logfile is opened
                if config.elf.open_latest(client.user):
                    await client.send('Now parsing character log for: [{}]'.format(config.elf.char_name))

            # if we didn't read a line, pause just for a 100 msec blink
            await asyncio.sleep(0.1)

    print('Parsing Stopped')


# let's go!!
client.run(config.config_data['Discord']['BOT_TOKEN'])
