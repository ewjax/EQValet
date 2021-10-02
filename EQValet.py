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
import gvar





# allow for testing, by forcing the bot to read an old log file
#TEST_BOT                = False
TEST_BOT                = True







#################################################################################################

#
# a class to help manage long streams of text being sent to Discord
# There is apparently a limit of 2000 characters on any message, anything over that throws an 
# exception
# 
# this class works by just creating a list of buffers, none of which is over the 2K limit
# Note that when using this, it is important to access the list of buffers using the get_bufflist()
# method, to ensure any remaining content currently stored in the working_buffer is added to the list
#
class SmartBuffer:
    # ctor
    def __init__(self):

#        self._bufflist           = list()
        self._bufflist          = []
        self._working_buffer    = ''

    def add(self, string):
        # would the new string make the buffer too long?
        if ( len(self._working_buffer) + len(string) ) > 1950:
             self._bufflist.append(self._working_buffer)
             self._working_buffer = ''

        self._working_buffer += string

    def get_bufflist(self):
        # add any content currently in the working buffer to the list
        if self._working_buffer != '':
            self._bufflist.append(self._working_buffer)

        # return the list of buffers
        return self._bufflist




#################################################################################################


# define the client instance to interact with the discord bot

class EQValetClient(commands.Bot):

    # ctor
    def __init__(self):

        # call parent ctor
        commands.Bot.__init__(self, command_prefix = myconfig.BOT_COMMAND_PREFIX)

#        # save the ctx for later
#        self.ctx                = None

        # use a RandomTracker class to deal with all things random numbers and rolls
        self.random_tracker     = randoms.RandomTracker(self)

        # use a PetTracker class to deal with all things pets
        self.pet_tracker        = pets.PetTracker(self)


    # process each line
#    async def process_line(self, ctx, line):
    async def process_line(self, line):
        print(line, end = '')

        # check for a random or for a pet
#        await self.random_tracker.process_line(ctx, line)
#        await self.pet_tracker.process_line(ctx, line)

        await self.random_tracker.process_line(line)
        await self.pet_tracker.process_line(line)


        # do other parsing things here
        pass


    # sound the alert
    async def alert(self, msg):

        special_channel = client.get_channel(myconfig.PERSONAL_SERVER_ALERTID)
        await special_channel.send(msg)

#        # try to find the #alert channels
#        if ctx.guild.name == myconfig.PERSONAL_SERVER_NAME:
#            special_channel = client.get_channel(myconfig.PERSONAL_SERVER_ALERTID)
#            await special_channel.send(msg)
#
#        # if we didn't find the desired channel for whatever reason, just bang it to current channel
#        else:
#            await ctx.send(msg)


    # notify of pop
    async def pop(self, msg):

        special_channel = client.get_channel(myconfig.PERSONAL_SERVER_POPID)
        await special_channel.send(msg)


#        # try to find the #alert channels
#        if ctx.guild.name == myconfig.PERSONAL_SERVER_NAME:
#
#
#        # if we didn't find the desired channel for whatever reason, just bang it to current channel
#        else:
#            await ctx.send(msg)

    # send message to the special EQValet channel
    async def send(self, msg):

        special_channel = client.get_channel(myconfig.PERSONAL_SERVER_VALETID)
        await special_channel.send(msg)
        



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

#    special_channel = client.get_channel(myconfig.PERSONAL_SERVER_VALETID)
#    await special_channel.send('EQ Valet is alive!')



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
@client.command()
async def ping(ctx):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
#    await ctx.send('Latency = {} ms'.format(round(client.latency*1000)))
    await client.send('Latency = {} ms'.format(round(client.latency*1000)))



# rolls command
# how many randoms have there been
@client.command()
async def rolls(ctx):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))

    # create a smart buffer to keep buffers under max size for discord messages (2000)
    sb = SmartBuffer()

    # add total rolls, and total random events
    sb.add('Total Rolls = {}\n'.format(len(client.random_tracker.all_rolls)))
    sb.add('Total Random Events = {}\n'.format(len(client.random_tracker.all_random_events)))

    # add the list of random events
    for (ndx, rev) in enumerate(client.random_tracker.all_random_events):
        sb.add('{}'.format(rev.report_summary(ndx, gvar.elf.char_name)))

    # get the list of buffers and send each to discord
    bufflist = sb.get_bufflist()
    for b in bufflist:
#        await ctx.send('{}'.format(b))
        await client.send('{}'.format(b))



# show command
# show all rolls in a specified RandomEvent
@client.command()
async def show(ctx, ndx = -1):
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
            sb.add(r.report(gvar.elf.char_name))

        # add the winner
        sb.add(rev.report_winner(gvar.elf.char_name))

        # get the list of buffers and send each to discord
        bufflist = sb.get_bufflist()
        for b in bufflist:
#            await ctx.send('{}'.format(b))
            await client.send('{}'.format(b))

    else:
#        await ctx.send('Requested ndx value = {}.  Value for ndx must be between 0 and {}'.format(ndx, len(client.random_tracker.all_random_events)-1))
#        await ctx.send('Unspecified ndx value = shows most recent random event')

        await client.send('Requested ndx value = {}.  Value for ndx must be between 0 and {}'.format(ndx, len(client.random_tracker.all_random_events)-1))
        await client.send('Unspecified ndx value = shows most recent random event')



# regroup command
# allows user to change the delta window on any given RandomEvent
@client.command()
async def regroup(ctx, ndx = -1, new_window = 0):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))

    # is ndx in range
    if (len(client.random_tracker.all_random_events) == 0):
#        await ctx.send('Error:  No RandomEvents to regroup!')
        await client.send('Error:  No RandomEvents to regroup!')

    elif ( (ndx < 0) or (ndx >= len(client.random_tracker.all_random_events)) ):
#        await ctx.send('Error:  Requested ndx value = {}.  Value for ndx must be between 0 and {}'.format(ndx, len(client.random_tracker.all_random_events)-1))
        await client.send('Error:  Requested ndx value = {}.  Value for ndx must be between 0 and {}'.format(ndx, len(client.random_tracker.all_random_events)-1))

    elif (new_window <= 0):
#        await ctx.send('Error:  Requested new_window value = {}.  Value for new_window must be > 0'.format(new_window))
        await client.send('Error:  Requested new_window value = {}.  Value for new_window must be > 0'.format(new_window))

    else:
#        await client.random_tracker.regroup(ctx, ndx, new_window)
        await client.random_tracker.regroup(ndx, new_window)



# window command
# change the default window for future RandomEvents
@client.command(aliases = ['win'])
async def window(ctx, new_window = 0):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))

    if (new_window < 0):
#        await ctx.send('Error:  Requested new_window value = {}.  Value for new_window must be > 0'.format(new_window))
        await client.send('Error:  Requested new_window value = {}.  Value for new_window must be > 0'.format(new_window))

    elif (new_window == 0):
#        await ctx.send('RandomEvent default window = {}'.format(client.random_tracker.default_window))
        await client.send('RandomEvent default window = {}'.format(client.random_tracker.default_window))

    else:
        client.random_tracker.default_window = new_window
#        await ctx.send('RandomEvent default window = {}'.format(client.random_tracker.default_window))
        await client.send('RandomEvent default window = {}'.format(client.random_tracker.default_window))




# firedrill command
# test the ability to send a message to the #pop channel
@client.command(aliases = ['fd'])
async def firedrill(ctx):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
#    await client.alert(ctx, 'This is a test.  This is only a test.')
#    await client.pop(ctx, 'This is a test.  This is only a test.')

    await client.alert('This is a test.  This is only a test.')
    await client.pop('This is a test.  This is only a test.')
    await client.send('This is a test.  This is only a test.')



# start command
@client.command(aliases = ['go'])
async def start(ctx, charname = None):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))

    # already parsing?
    if gvar.elf.is_parsing():
#        await ctx.send('Already parsing character log for: [{}]'.format(gvar.elf.char_name))
        await client.send('Already parsing character log for: [{}]'.format(gvar.elf.char_name))
        
    else:

        # use a back door to force the system to read a test file
        if TEST_BOT == True:

            # read a sample file with sample random rolls in it
            filename = 'randoms.txt'
#            filename = 'pets.txt'

            # start parsing, but in this case, start reading from the beginning of the file, rather than the end (default)
#            rv = gvar.elf.open(ctx.message.author, 'Testing', filename, seek_end = False)
            rv = gvar.elf.open(client.user, 'Testing', filename, seek_end = False)

        # open the latest file
        else:
            # open the latest file, and kick off the parsing process
#            rv = gvar.elf.open_latest(ctx.message.author)
            rv = gvar.elf.open_latest(client.user)


        # if the log file was successfully opened, then initiate parsing
        if rv:

            # status message
#            await ctx.send('Now parsing character log for: [{}]'.format(gvar.elf.char_name))
            await client.send('Now parsing character log for: [{}]'.format(gvar.elf.char_name))

            # create the background processs and kick it off
#            client.ctx = ctx
            client.loop.create_task(parse())

        else:
#            await ctx.send('ERROR: Could not open character log file for: [{}]'.format(gvar.elf.char_name))
#            await ctx.send('Log filename: [{}]'.format(gvar.elf.filename))

            await client.send('ERROR: Could not open character log file for: [{}]'.format(gvar.elf.char_name))
            await client.send('Log filename: [{}]'.format(gvar.elf.filename))


#
## stop command
#@client.command()
#async def stop(ctx):
#    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
#




# status command
@client.command()
async def status(ctx):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))

    if gvar.elf.is_parsing():
#        await ctx.send('Parsing character log for: [{}]'.format(gvar.elf.char_name))
#        await ctx.send('Log filename: [{}]'.format(gvar.elf.filename))
#        await ctx.send('Parsing initiated by: [{}]'.format(gvar.elf.author))
#        await ctx.send('Heartbeat timeout (seconds): [{}]'.format(gvar.elf.heartbeat))

        await client.send('Parsing character log for: [{}]'.format(gvar.elf.char_name))
        await client.send('Log filename: [{}]'.format(gvar.elf.filename))
        await client.send('Parsing initiated by: [{}]'.format(gvar.elf.author))
        await client.send('Heartbeat timeout (seconds): [{}]'.format(gvar.elf.heartbeat))

    else:
#        await ctx.send('Not currently parsing')
        await client.send('Not currently parsing')



#        self.pet_tracker        = pets.PetTracker()


# pet command
@client.command()
async def pet(ctx):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))

    if client.pet_tracker.current_pet:
#        await ctx.send(client.pet_tracker.current_pet)
        await client.send(client.pet_tracker.current_pet)

    else:
#        await ctx.send('No pet')
        await client.send('No pet')




#################################################################################################


# the background process to parse the log files
#
async def parse():                                      

    print('Parsing Started')

    # process the log file lines here
    while gvar.elf.is_parsing() == True:

        # read a line
        line = gvar.elf.readline()
        now = time.time()
        if line:
            gvar.elf.prevtime = now

            # process this line
#            await client.process_line(client.ctx, line)
            await client.process_line(line)


        else:

            # don't check the heartbeat if we are just testing
            if TEST_BOT == False:

                # check the heartbeat.  Has our tracker gone silent?
                elapsed_seconds = (now - gvar.elf.prevtime)

                if elapsed_seconds > gvar.elf.heartbeat:
                    print('Heartbeat over limit, elapsed seconds = {}'.format(elapsed_seconds))
                    gvar.elf.prevtime = now

                    # attempt to open latest log file - returns True if a new logfile is opened
#                    if (gvar.elf.open_latest(client.ctx.message.author)):
                    if (gvar.elf.open_latest(client.user)):
#                        await client.ctx.send('Now parsing character log for: [{}]'.format(gvar.elf.char_name))
                        await client.send('Now parsing character log for: [{}]'.format(gvar.elf.char_name))

            # if we didn't read a line, pause just for a 100 msec blink
            await asyncio.sleep(0.1)

    print('Parsing Stopped')




# let's go!!
client.run(myconfig.BOT_TOKEN)




