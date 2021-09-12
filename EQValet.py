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
import gvar





# allow for testing, by forcing the bot to read an old log file for the VT and VD fights
TEST_BOT                = False
#TEST_BOT                = True







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

        self._bufflist           = list()
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

        # save the ctx for later
        self.ctx                = None

        # use a RandomTracker class to deal with all things random numbers and rolls
        self.random_tracker     = randoms.RandomTracker()


    # process each line
    async def process_line(self, ctx, line):
        print(line, end = '')

        # check if a random has started
        await self.random_tracker.process_line(ctx, line)



        # do other parsing things here
        pass


    # sound the alert
    async def alert(self, ctx, msg):

        # try to find the #alert channels
        if ctx.guild.name == myconfig.PERSONAL_SERVER_NAME:
            special_channel = client.get_channel(myconfig.PERSONAL_SERVER_ALERTID)
            await special_channel.send(msg)

        # if we didn't find the desired channel for whatever reason, just bang it to current channel
        else:
            await ctx.send(msg)


    # notify of pop
    async def pop(self, ctx, msg):

        # try to find the #alert channels
        if ctx.guild.name == myconfig.PERSONAL_SERVER_NAME:
            special_channel = client.get_channel(myconfig.PERSONAL_SERVER_POPID)
            await special_channel.send(msg)


        # if we didn't find the desired channel for whatever reason, just bang it to current channel
        else:
            await ctx.send(msg)




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
    await ctx.send('Latency = {} ms'.format(round(client.latency*1000)))



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
        await ctx.send('{}'.format(b))



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
            await ctx.send('{}'.format(b))

    else:
        await ctx.send('Requested ndx value = {}.  Value for ndx must be between 0 and {}'.format(ndx, len(client.random_tracker.all_random_events)-1))
        await ctx.send('Unspecified ndx value = shows most recent random event')



# regroup command
# allows user to change the delta window on any given RandomEvent
@client.command()
async def regroup(ctx, ndx = -1, new_window = 0):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))

    # is ndx in range
    if (len(client.random_tracker.all_random_events) == 0):
        await ctx.send('Error:  No RandomEvents to regroup!')

    elif ( (ndx < 0) or (ndx >= len(client.random_tracker.all_random_events)) ):
        await ctx.send('Error:  Requested ndx value = {}.  Value for ndx must be between 0 and {}'.format(ndx, len(client.random_tracker.all_random_events)-1))

    elif (new_window <= 0):
        await ctx.send('Error:  Requested new_window value = {}.  Value for new_window must be > 0'.format(new_window))

    else:
        await client.random_tracker.regroup(ctx, ndx, new_window)


# firedrill command
# test the ability to send a message to the #pop channel
@client.command(aliases = ['fd'])
async def firedrill(ctx):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))
    await client.alert(ctx, 'This is a test.  This is only a test.')
    await client.pop(ctx, 'This is a test.  This is only a test.')



# start command
@client.command(aliases = ['go'])
async def start(ctx, charname = None):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))

    # already parsing?
    if gvar.elf.is_parsing():
        await ctx.send('Already parsing character log for: [{}]'.format(gvar.elf.char_name))
        await ctx.send('Log filename: [{}]'.format(gvar.elf.filename))
        await ctx.send('Parsing initiated by: [{}]'.format(gvar.elf.author))
        
    else:
        # new log file name get passed?
        cn = myconfig.DEFAULT_CHAR_NAME
        if charname != None:
            cn = charname


#        if charname:
#            cn = charname
##            gvar.elf.char_name = charname
#        else:
#            cn = myconfig.DEFAULT_CHAR_NAME
##            gvar.elf.char_name = myconfig.DEFAULT_CHAR_NAME

        filename = gvar.elf.build_filename(cn)

        # open the log file to be parsed
        # allow for testing, by forcing the bot to read an old log file for the VT and VD fights
        if TEST_BOT == False:
            # start parsing.  The default behavior is to open the log file, and begin reading it from tne end, i.e. only new entries
            rv = gvar.elf.open(ctx.message.author, cn, filename)

        else:
            # use a back door to force the system to read files from the beginning that contain VD / VT fights to test with
#            gvar.elf.filename = 'randoms.txt'
            filename = 'randoms.txt'

            # start parsing, but in this case, start reading from the beginning of the file, rather than the end (default)
            rv = gvar.elf.open(ctx.message.author, 'Testing', filename, seek_end = False)


        # if the log file was successfully opened, then initiate parsing
        if rv:
            # status message
#            await ctx.send('Now parsing character log for: [{}]'.format(gvar.elf.char_name))
#            await ctx.send('Log filename: [{}]'.format(gvar.elf.filename))
#            await ctx.send('Parsing initiated by: [{}]'.format(gvar.elf.author))
#            await ctx.send('Heartbeat timeout (minutes): [{}]'.format(gvar.elf.heartbeat))

            await client.alert(ctx, 'Now parsing character log for: [{}]'.format(gvar.elf.char_name))
            await client.alert(ctx, 'Log filename: [{}]'.format(gvar.elf.filename))
            await client.alert(ctx, 'Parsing initiated by: [{}]'.format(gvar.elf.author))
            await client.alert(ctx, 'Heartbeat timeout (minutes): [{}]'.format(gvar.elf.heartbeat))


            # create the background processs and kick it off
            client.ctx = ctx
            client.loop.create_task(parse())
        else:
            await ctx.send('ERROR: Could not open character log file for: [{}]'.format(gvar.elf.char_name))
            await ctx.send('Log filename: [{}]'.format(gvar.elf.filename))



# stop command
@client.command()
async def stop(ctx):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))

    if gvar.elf.is_parsing():

        # only the person who started the log can close it
        if gvar.elf.author == ctx.message.author:
            # stop parsing
            gvar.elf.close()
            await ctx.send('Stopped parsing character log for: [{}]'.format(gvar.elf.char_name))
        else:
            await ctx.send('Error: Parsing can only be stopped by the same person who started it.  Starter: [{}], !stop requestor [{}]'.format(gvar.elf.author, ctx.message.author))

    else:
        await ctx.send('Not currently parsing')



# status command
@client.command()
async def status(ctx):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))

    if gvar.elf.is_parsing():
        await ctx.send('Parsing character log for: [{}]'.format(gvar.elf.char_name))
        await ctx.send('Log filename: [{}]'.format(gvar.elf.filename))
        await ctx.send('Parsing initiated by: [{}]'.format(gvar.elf.author))
        await ctx.send('Heartbeat timeout (minutes): [{}]'.format(gvar.elf.heartbeat))
    else:
        await ctx.send('Not currently parsing')


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
            await client.process_line(client.ctx, line)


        else:
            # check the heartbeat.  Has our tracker gone silent?
            elapsed_minutes = (now - gvar.elf.prevtime)/60.0
            if elapsed_minutes > gvar.elf.heartbeat:
                gvar.elf.prevtime = now
                await client.ctx.send('Heartbeat Warning:  Tracker [{}] logfile has had no new entries in last {} minutes.  Is {} still online?'.format(gvar.elf.char_name, gvar.elf.heartbeat, gvar.elf.char_name))

            await asyncio.sleep(0.1)

    print('Parsing Stopped')




# let's go!!
client.run(myconfig.BOT_TOKEN)




