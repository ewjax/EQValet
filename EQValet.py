import threading
import asyncio
import time
import discord
import random
import os
import re

from discord.ext import commands

# import the customized settings and file locations etc, found in myconfig.py
import myconfig
import randoms
import pets
import damage
import logfile
from smartbuffer import SmartBuffer 





# allow for testing, by forcing the bot to read an old log file
TEST_BOT                = False
#TEST_BOT                = True









#################################################################################################


# define the client instance to interact with the discord bot

class EQValetClient(commands.Bot):

    # ctor
    def __init__(self):

        # call parent ctor
        commands.Bot.__init__(self, command_prefix = myconfig.BOT_COMMAND_PREFIX)

        # create the EQ log file parser
        self.elf                = logfile.EverquestLogFile()

        # use a RandomTracker class to deal with all things random numbers and rolls
        self.random_parse       = True
        self.random_tracker     = randoms.RandomTracker(self)

        # use a DamageTracker class to keep track of total damage dealt by spells and by pets
        self.damage_parse       = True
        self.damage_tracker     = damage.DamageTracker(self)

        # use a PetTracker class to deal with all things pets
        self.pet_parse          = True
        self.pet_tracker        = pets.PetTracker(self)


    # process each line
    async def process_line(self, line):
        print(line, end = '')

        # check for a random
        if self.random_parse:
            await self.random_tracker.process_line(line)

        # check for damage-related content
        if self.damage_parse:
            await self.damage_tracker.process_line(line)

        # check for pet-related content
        if self.pet_parse:
            await self.pet_tracker.process_line(line)


    # sound the alert
    async def alert(self, msg):

        special_channel = self.get_channel(myconfig.PERSONAL_SERVER_ALERTID)
        await special_channel.send(msg)


    # notify of pop
    async def pop(self, msg):

        special_channel = self.get_channel(myconfig.PERSONAL_SERVER_POPID)
        await special_channel.send(msg)


    # send message to the special EQValet channel
    async def send(self, msg):

        special_channel = self.get_channel(myconfig.PERSONAL_SERVER_VALETID)
        await special_channel.send(msg)
        


    # begin parsing
    async def begin_parsing(self):
        # already parsing?
        if self.elf.is_parsing():
            await self.send('Already parsing character log for: [{}]'.format(self.elf.char_name))

        else:

            # use a back door to force the system to read a test file
            if TEST_BOT == True:

                # read a sample file with sample random rolls in it
                filename = 'randoms.txt'
#                filename = 'pets.txt'

                # start parsing, but in this case, start reading from the beginning of the file, rather than the end (default)
                rv = self.elf.open(self.user, 'Testing', filename, seek_end = False)

            # open the latest file
            else:
                # open the latest file, and kick off the parsing process
                rv = self.elf.open_latest(self.user)


            # if the log file was successfully opened, then initiate parsing
            if rv:

                # status message
                await self.send('Now parsing character log for: [{}]'.format(self.elf.char_name))

                # create the background processs and kick it off
                self.loop.create_task(parse())

            else:
                await self.send('ERROR: Could not open character log file for: [{}]'.format(self.elf.char_name))
                await self.send('Log filename: [{}]'.format(self.elf.filename))





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
@client.command(aliases = ['ping'])
async def gen_ping(ctx):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
    await client.send('Latency = {} ms'.format(round(client.latency*1000)))



# rolls command
# how many randoms have there been
@client.command(aliases = ['rolls'])
async def ran_rolls(ctx):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))

    # create a smart buffer to keep buffers under max size for discord messages (2000)
    sb = SmartBuffer()

    # add total rolls, and total random events
    sb.add('Total Rolls = {}\n'.format(len(client.random_tracker.all_rolls)))
    sb.add('Total Random Events = {}\n'.format(len(client.random_tracker.all_random_events)))

    # add the list of random events
    for (ndx, rev) in enumerate(client.random_tracker.all_random_events):
        sb.add('{}'.format(rev.report_summary(ndx, client.elf.char_name)))

    # get the list of buffers and send each to discord
    bufflist = sb.get_bufflist()
    for b in bufflist:
        await client.send('{}'.format(b))


# show command
# show all rolls in a specified RandomEvent
@client.command(aliases = ['show'])
async def ran_show(ctx, ndx = -1):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))

    # if the ndx value isn't specified, default to showing the last randomevent
    if ndx == -1:
        ndx = len(client.random_tracker.all_random_events) - 1

    # is ndx in range
    if ((ndx >= 0) and (ndx < len(client.random_tracker.all_random_events))):
        rev = client.random_tracker.all_random_events[ndx]

        # create a smart buffer to keep buffers under max size for discord messages (2000)
        sb = SmartBuffer()

        # add the header
        sb.add(rev.report_header(ndx))

        # add all the rolls
        for r in rev.rolls:
            sb.add(r.report(client.elf.char_name))

        # add the winner
        sb.add(rev.report_winner(client.elf.char_name))

        # get the list of buffers and send each to discord
        bufflist = sb.get_bufflist()
        for b in bufflist:
            await client.send('{}'.format(b))

    else:
        await client.send('Requested ndx value = {}.  Value for ndx must be between 0 and {}'.format(ndx, len(client.random_tracker.all_random_events)-1))
        await client.send('Unspecified ndx value = shows most recent random event')



# regroup command
# allows user to change the delta window on any given RandomEvent
@client.command(aliases = ['regroup'])
async def ran_regroup(ctx, ndx = -1, new_window = 0):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))

    # is ndx in range
    if (len(client.random_tracker.all_random_events) == 0):
        await client.send('Error:  No RandomEvents to regroup!')

    elif ( (ndx < 0) or (ndx >= len(client.random_tracker.all_random_events)) ):
        await client.send('Error:  Requested ndx value = {}.  Value for ndx must be between 0 and {}'.format(ndx, len(client.random_tracker.all_random_events)-1))

    elif (new_window <= 0):
        await client.send('Error:  Requested new_window value = {}.  Value for new_window must be > 0'.format(new_window))

    else:
        await client.random_tracker.regroup(ndx, new_window)



# window command
# change the default window for future RandomEvents
@client.command(aliases = ['win', 'window'])
async def ran_window(ctx, new_window = 0):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))

    if (new_window < 0):
        await client.send('Error:  Requested new_window value = {}.  Value for new_window must be > 0'.format(new_window))

    elif (new_window == 0):
        await client.send('RandomEvent default window = {}'.format(client.random_tracker.default_window))

    else:
        client.random_tracker.default_window = new_window
        await client.send('RandomEvent default window = {}'.format(client.random_tracker.default_window))




# firedrill command
# test the ability to send a message to the #pop channel
@client.command(aliases = ['fd', 'firedrill'])
async def gen_firedrill(ctx):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))

    await client.alert('This is a test.  This is only a test.')
    await client.pop('This is a test.  This is only a test.')
    await client.send('This is a test.  This is only a test.')



# start command
@client.command(aliases = ['go', 'start'])
async def gen_start(ctx, charname = None):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))

    await client.begin_parsing()



# status command
@client.command(aliases = ['status'])
async def gen_status(ctx):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))

    if client.elf.is_parsing():
        await client.send('Parsing character log for: [{}]'.format(client.elf.char_name))
        await client.send('Log filename: [{}]'.format(client.elf.filename))
        await client.send('Parsing initiated by: [{}]'.format(client.elf.author))
        await client.send('Heartbeat timeout (seconds): [{}]'.format(client.elf.heartbeat))

    else:
        await client.send('Not currently parsing')



# pet command
@client.command(aliases = ['pet'])
async def pet_pet(ctx):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))

    if client.pet_tracker.current_pet:
        await client.send(client.pet_tracker.current_pet)

    else:
        await client.send('No pet')



# cto command
# change the combat timeout value
@client.command(aliases = ['cto'])
async def com_timeout(ctx, new_cto = 0):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))

    if (new_cto < 0):
        await client.send('Error:  Requested new_cto value = {}.  Value for new_cto must be > 0'.format(new_cto))

    elif (new_cto == 0):
        await client.send('DamageTracker combat timeout (CTO) = {}'.format(client.damage_tracker.combat_timeout))

    else:
        client.damage_tracker.combat_timeout = new_cto
        await client.send('DamageTracker Combat timeout (CTO) = {}'.format(client.damage_tracker.combat_timeout))



# toggle combat tracking command
@client.command(aliases = ['ct'])
async def com_toggle(ctx, new_cto = 0):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))

    onoff = 'On'
    if client.damage_parse:
        client.damage_parse = False
        onoff = 'Off'
    else:
        client.damage_parse = True
        onoff = 'On'

    await client.send('Combat Parsing: {}'.format(onoff))


# list player names
@client.command(aliases = ['who'])
async def com_who(ctx):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))

    sb = SmartBuffer()
    sb.add('Sorted list of all player names stored in /who database: {}\n'.format(client.damage_tracker.player_names_fname))

    for name in sorted(client.damage_tracker.player_names_set):
        sb.add('\t{}\n'.format(name))

    # get the list of buffers and send each to discord
    bufflist = sb.get_bufflist()
    for b in bufflist:
        await client.send('{}'.format(b))





# toggle combat tracking command
@client.command(aliases = ['pt'])
async def pet_toggle(ctx, new_cto = 0):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))

    onoff = 'On'
    if client.pet_parse:
        client.pet_parse = False
        onoff = 'Off'
    else:
        client.pet_parse = True
        onoff = 'On'

    await client.send('Pet Parsing: {}'.format(onoff))


# toggle combat tracking command
@client.command(aliases = ['rt'])
async def ran_toggle(ctx, new_cto = 0):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))

    onoff = 'On'
    if client.random_parse:
        client.random_parse = False
        onoff = 'Off'
    else:
        client.random_parse = True
        onoff = 'On'

    await client.send('Random Parsing: {}'.format(onoff))


#################################################################################################


# the background process to parse the log files
#
async def parse():                                      

    print('Parsing Started')

    # process the log file lines here
    while client.elf.is_parsing() == True:

        # read a line
        line = client.elf.readline()
        now = time.time()
        if line:
            client.elf.prevtime = now

            # process this line
            await client.process_line(line)


        else:

            # don't check the heartbeat if we are just testing
            if TEST_BOT == False:

                # check the heartbeat.  Has our tracker gone silent?
                elapsed_seconds = (now - client.elf.prevtime)

                if elapsed_seconds > client.elf.heartbeat:
                    print('Heartbeat over limit, elapsed seconds = {}'.format(elapsed_seconds))
                    client.elf.prevtime = now

                    # attempt to open latest log file - returns True if a new logfile is opened
                    if (client.elf.open_latest(client.user)):
                        await client.send('Now parsing character log for: [{}]'.format(client.elf.char_name))

            # if we didn't read a line, pause just for a 100 msec blink
            await asyncio.sleep(0.1)

    print('Parsing Stopped')




# let's go!!
client.run(myconfig.BOT_TOKEN)




