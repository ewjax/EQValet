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
TEST_BOT = False
# TEST_BOT = True


#################################################################################################


# define the client instance to interact with the discord bot

# class EQValetClient(commands.Bot):

class EQValetClient():

    # ctor
    def __init__(self):

        # force global data to load from ini file
        config.load()

        # call parent ctor
        # prefix = config.config_data.get('Discord', 'BOT_COMMAND_PREFIX')
        # commands.Bot.__init__(self, command_prefix=prefix)

        # create the EQ log file parser
        self.elf = EverquestLogFile.EverquestLogFile()

        # use a RandomParser class to deal with all things random numbers and rolls
        self.random_parser = RandomParser.RandomParser()

        # use a DamageParser class to keep track of total damage dealt by spells and by pets
        self.damage_parser = DamageParser.DamageParser()

        # use a PetParser class to deal with all things pets
        self.pet_parser = PetParser.PetParser()

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

        # check for .status command
        target = r'^\.status'
        m = re.match(target, trunc_line)
        if m:
            if self.elf.is_parsing():
                starprint(f'Parsing character log for:    [{self.elf.char_name}]')
                starprint(f'Log filename:                 [{self.elf.filename}]')
                starprint(f'Heartbeat timeout (seconds):  [{self.elf.heartbeat}]')
            else:
                starprint(f'Not currently parsing')

        # check for a random
        self.random_parser.process_line(line)

        # check for damage-related content
        self.damage_parser.process_line(line)

        # check for pet-related content
        self.pet_parser.process_line(line)

    # # sound the alert
    # async def alert(self, msg):
    #
    #     channel_id = config.config_data.getint('Discord', 'PERSONAL_SERVER_ALERTID')
    #     special_channel = self.get_channel(channel_id)
    #     await special_channel.send(msg)
    #
    # # notify of pop
    # async def pop(self, msg):
    #
    #     channel_id = config.config_data.getint('Discord', 'PERSONAL_SERVER_POPID')
    #     special_channel = self.get_channel(channel_id)
    #     await special_channel.send(msg)
    #
    # # send message to the special EQValet channel
    # async def send(self, msg):
    #
    #     channel_id = config.config_data.getint('Discord', 'PERSONAL_SERVER_VALETID')
    #     special_channel = self.get_channel(channel_id)
    #     await special_channel.send(msg)

    # begin parsing
    def begin_parsing(self):
        # already parsing?
        if self.elf.is_parsing():
            print('Already parsing character log for: [{}]'.format(self.elf.char_name))

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
                rv = self.elf.open('Unknownuser', 'Testing', filename, seek_end=False)

            # open the latest file
            else:
                # open the latest file, and kick off the parsing process
                rv = self.elf.open_latest('unknownuser')

            # if the log file was successfully opened, then initiate parsing
            if rv:

                # status message
                print('Now parsing character log for: [{}]'.format(self.elf.char_name))

                # create the background processs and kick it off
                self.loop.create_task(parse())

            else:
                print('ERROR: Could not open character log file for: [{}]'.format(self.elf.char_name))
                print('Log filename: [{}]'.format(self.elf.filename))


#################################################################################################

# create the global instance of the client that manages communication to the discord bot
client = EQValetClient()
config.the_valet = client
client.begin_parsing()


# #
# # add decorator event handlers to the client instance
# #
#
# # on_ready
# @client.event
# async def on_ready():
#     print('EQ Valet is alive!')
#     print('Discord.py version: {}'.format(discord.__version__))
#
#     print('Logged on as {}'.format(client.user))
#     print('App ID: {}'.format(client.user.id))
#
#     await client.send('EQ Valet is alive!')
#     await client.begin_parsing()
#
#
# # on_message - catches everything, messages and commands
# # note the final line, which ensures any command gets processed as a command, and not just absorbed here as a message
# @client.event
# async def on_message(message):
#     author = message.author
#     content = message.content
#     channel = message.channel
#     print('Content received: [{}] from [{}] in channel [{}]'.format(content, author, channel))
#     await client.process_commands(message)
#
#
# # ping command
# @client.command(aliases=['ping'])
# async def gen_ping(ctx):
#     print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
#     await client.send('Latency = {} ms'.format(round(client.latency * 1000)))
#
#
# # rolls command
# # how many randoms have there been
# @client.command(aliases=['rolls'])
# async def ran_rolls(ctx):
#     # print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
#     #
#     # # create a smart buffer to keep buffers under max size for discord messages (2000)
#     # sb = SmartBuffer()
#     #
#     # # add total rolls, and total random events
#     # sb.add('Total Rolls = {}\n'.format(len(self.random_parser.all_rolls)))
#     # sb.add('Total Random Events = {}\n'.format(len(self.random_parser.all_random_groups)))
#     #
#     # # add the list of random events
#     # for (ndx, rev) in enumerate(self.random_parser.all_random_groups):
#     #     sb.add('{}'.format(rev.report_summary(ndx, self.elf.char_name)))
#     #
#     # # get the list of buffers and send each to discord
#     # bufflist = sb.get_bufflist()
#     # for b in bufflist:
#     #     await client.send('{}'.format(b))
#     pass
#
#
# # show command
# # show all rolls in a specified RandomGroup
# @client.command(aliases=['show'])
# async def ran_show(ctx, ndx=-1):
#     # print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
#     #
#     # # if the ndx value isn't specified, default to showing the last randomevent
#     # if ndx == -1:
#     #     ndx = len(self.random_parser.all_random_groups) - 1
#     #
#     # # is ndx in range
#     # if (ndx >= 0) and (ndx < len(self.random_parser.all_random_groups)):
#     #     rev = self.random_parser.all_random_groups[ndx]
#     #
#     #     # create a smart buffer to keep buffers under max size for discord messages (2000)
#     #     sb = SmartBuffer()
#     #
#     #     # add the header
#     #     sb.add(rev.report_header(ndx))
#     #
#     #     # add all the rolls
#     #     for prr in rev.rolls:
#     #         sb.add(prr.report(self.elf.char_name))
#     #
#     #     # add the winner
#     #     sb.add(rev.report_winner(self.elf.char_name))
#     #
#     #     # get the list of buffers and send each to discord
#     #     bufflist = sb.get_bufflist()
#     #     for b in bufflist:
#     #         await client.send('{}'.format(b))
#     #
#     # else:
#     #     await client.send('Requested ndx value = {}.  Value for ndx must be between 0 and {}'.format(ndx, len(self.random_parser.all_random_groups) - 1))
#     #     await client.send('Unspecified ndx value = shows most recent random event')
#     pass
#
#
# # regroup command
# # allows user to change the delta window on any given RandomGroup
# @client.command(aliases=['regroup'])
# async def ran_regroup(ctx, ndx=-1, new_window=0, low_significant=True, high_significant=True):
#     # print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
#     #
#     # # is ndx in range
#     # if len(self.random_parser.all_random_groups) == 0:
#     #     await client.send('Error:  No RandomEvents to regroup!')
#     #
#     # elif (ndx < 0) or (ndx >= len(self.random_parser.all_random_groups)):
#     #     await client.send('Error:  Requested ndx value = {}.  Value for ndx must be between 0 and {}'.format(ndx, len(self.random_parser.all_random_groups) - 1))
#     # elif new_window <= 0:
#     #     await client.send(
#     #         'Error:  Requested new_window value = {}.  Value for new_window must be > 0'.format(new_window))
#     #
#     # else:
#     #     await self.random_parser.regroup(ndx, new_window, low_significant, high_significant)
#     pass
#
#
# # window command
# # change the default window for future RandomEvents
# @client.command(aliases=['win', 'window'])
# async def ran_window(ctx, new_window=0):
#     # print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
#     #
#     # if new_window < 0:
#     #     await client.send(
#     #         'Error:  Requested new_window value = {}.  Value for new_window must be > 0'.format(new_window))
#     #
#     # elif new_window == 0:
#     #     await client.send('RandomGroup default window = {}'.format(self.random_parser.default_window))
#     #
#     # else:
#     #     self.random_parser.default_window = new_window
#     #     await client.send('RandomGroup default window = {}'.format(self.random_parser.default_window))
#     pass
#
#
# # firedrill command
# # test the ability to send a message to the #pop channel
# @client.command(aliases=['fd', 'firedrill'])
# async def gen_firedrill(ctx):
#     print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
#
#     await client.alert('This is a test.  This is only a test.')
#     await client.pop('This is a test.  This is only a test.')
#     await client.send('This is a test.  This is only a test.')
#
#
# # start command
# @client.command(aliases=['go', 'start'])
# async def gen_start(ctx):
#     print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
#
#     await client.begin_parsing()
#
#
# # status command
# @client.command(aliases=['status'])
# async def gen_status(ctx):
#     # print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
#     #
#     # if self.elf.is_parsing():
#     #     await client.send('Parsing character log for: [{}]'.format(self.elf.char_name))
#     #     await client.send('Log filename: [{}]'.format(self.elf.filename))
#     #     await client.send('Parsing initiated by: [{}]'.format(self.elf.author))
#     #     await client.send('Heartbeat timeout (seconds): [{}]'.format(self.elf.heartbeat))
#     #
#     # else:
#     #     await client.send('Not currently parsing')
#     pass
#
#
# # pet command
# @client.command(aliases=['pet'])
# async def pet_pet(ctx):
#     # print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
#     #
#     # if self.pet_parser.current_pet:
#     #     await client.send(self.pet_parser.current_pet)
#     #
#     # else:
#     #     await client.send('No pet')
#     pass
#
#
# # cto command
# # change the combat timeout value
# @client.command(aliases=['cto'])
# async def com_timeout(ctx, new_cto=0):
#     # print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
#     #
#     # if new_cto < 0:
#     #     await client.send('Error:  Requested new_cto value = {}.  Value for new_cto must be > 0'.format(new_cto))
#     #
#     # elif new_cto == 0:
#     #     await client.send('DamageParser combat timeout (CTO) = {}'.format(self.damage_parser.combat_timeout))
#     #
#     # else:
#     #     self.damage_parser.combat_timeout = new_cto
#     #     await client.send('DamageParser Combat timeout (CTO) = {}'.format(self.damage_parser.combat_timeout))
#     pass
#
#
# # toggle combat tracking command
# @client.command(aliases=['ct'])
# async def com_toggle(ctx):
#     # print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
#     #
#     # if client.damage_parse:
#     #     client.damage_parse = False
#     #     onoff = 'Off'
#     # else:
#     #     client.damage_parse = True
#     #     onoff = 'On'
#     #
#     # await client.send('Combat Parsing: {}'.format(onoff))
#     pass
#
#
# # list player names
# @client.command(aliases=['who', 'w'])
# async def com_who(ctx):
#     # print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
#     #
#     # sb = SmartBuffer()
#     # sb.add('Sorted list of all player names stored in /who database: {}\n'.format(
#     #     self.damage_parser.player_names_fname))
#     #
#     # for name in sorted(self.damage_parser.player_names_set):
#     #     sb.add('\t{}\n'.format(name))
#     #
#     # # get the list of buffers and send each to discord
#     # bufflist = sb.get_bufflist()
#     # for b in bufflist:
#     #     await client.send('{}'.format(b))
#     pass
#
#
# # toggle combat tracking command
# @client.command(aliases=['pt'])
# async def pet_toggle(ctx):
#     # print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
#     #
#     # if client.pet_parse:
#     #     client.pet_parse = False
#     #     onoff = 'Off'
#     # else:
#     #     client.pet_parse = True
#     #     onoff = 'On'
#     #
#     # await client.send('Pet Parsing: {}'.format(onoff))
#     pass
#
#
# # toggle combat tracking command
# @client.command(aliases=['rt'])
# async def ran_toggle(ctx):
#     # print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
#     #
#     # if client.random_parse:
#     #     client.random_parse = False
#     #     onoff = 'Off'
#     # else:
#     #     client.random_parse = True
#     #     onoff = 'On'
#     #
#     # await client.send('Random Parsing: {}'.format(onoff))
#     pass
#
# #################################################################################################
#

# the background process to parse the log files
#
async def parse():
    print('Parsing Started')

    # process the log file lines here
    while config.the_valet.elf.is_parsing():

        # read a line
        line = config.the_valet.elf.readline()
        now = time.time()
        if line:
            config.the_valet.elf.prevtime = now

            # process this line
            await client.process_line(line)

        else:
            # check the heartbeat.  Has our tracker gone silent?
            elapsed_seconds = (now - config.the_valet.elf.prevtime)

            if elapsed_seconds > config.the_valet.elf.heartbeat:
                starprint(f'Heartbeat over limit, elapsed seconds = {elapsed_seconds:.2f}', '>')
                config.the_valet.elf.prevtime = now

                # attempt to open latest log file - returns True if a new logfile is opened
                if config.the_valet.elf.open_latest(client.user):
                    await client.send('Now parsing character log for: [{}]'.format(config.the_valet.elf.char_name))

            # if we didn't read a line, pause just for a 100 msec blink
            await asyncio.sleep(0.1)

    print('Parsing Stopped')


# let's go!!
client.run(config.config_data['Discord']['BOT_TOKEN'])
