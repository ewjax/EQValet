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
import logfile
import randoms




# allow for testing, by forcing the bot to read an old log file for the VT and VD fights
TEST_BOT                = False
#TEST_BOT                = True




# create a global instance of the log file reader class
elf = logfile.EverquestLogFile()



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

        self.bufflist           = list()
        self._working_buffer    = ''

    def add(self, string):
        # would the new string make the buffer too long?
        if ( len(self._working_buffer) + len(string) ) > 1950:
             self.bufflist.append(self._working_buffer)
             self._working_buffer = ''

        self._working_buffer += string

    def get_bufflist(self):
        # add any content currently in the working buffer to the list
        if self._working_buffer != '':
            self.bufflist.append(self._working_buffer)

        # return the list of buffers
        return self.bufflist




#################################################################################################


# define the client instance to interact with the discord bot

class EQValetClient(commands.Bot):

    # ctor
    def __init__(self):

        # call parent ctor
        commands.Bot.__init__(self, command_prefix = myconfig.BOT_COMMAND_PREFIX)

        # save the ctx for later
        self.ctx                = None

        # list of all random rolls, and all RandomEvents
        self.all_rolls          = list()
        self.all_random_events  = list()


    # process each line
    async def process_line(self, line):
        print(line, end = '')

        # check if a random has started
        await self.check4_random(line)

        # do other parsing things here
        pass




    # check if a random is occurring
    async def check4_random(self, line):

        # begin by checking if any of the RandomEvents is due to expire
        for (ndx, rev) in enumerate(self.all_random_events):
            if (rev.expired == False):
                toggled = rev.check_expiration(line)
                if toggled:
                    await self.ctx.send('{}'.format(rev.report_summary(ndx, elf.char_name)))


        # cut off the leading date-time stamp info
        trunc_line = line[27:]
        target1 = '\*\*A Magic Die is rolled by (?P<playername>[\w ]+)\.'
        target2 = '\*\*It could have been any number from (?P<low>[0-9]+) to (?P<high>[0-9]+), but this time it turned up a (?P<value>[0-9]+)\.'

        # return value m is either None of an object with information about the RE search
        m = re.match(target1, trunc_line)
        if (m):

            # fetch the player name
            player = m.group('playername')

            # get next line
            line = elf.readline()
            print(line, end = '')
            trunc_line = line[27:]

            # fetch the low, high, and value numbers
            m = re.match(target2, trunc_line)
            if (m):
                low     = m.group('low')
                high    = m.group('high')
                value   = m.group('value')

                # create the roll object
                roll = randoms.PlayerRandomRoll(player, value, low, high, line)
#                print(roll)

                # add it to the list of all rolls
                self.all_rolls.append(roll)

                added = False
                # add it to the appropriate RandomEvent - walk the list and try to add the roll to any open randomevents
                for rev in self.all_random_events:
                    if (rev.expired == False):
                        if (rev.add_roll(roll)):
                            added = True
                            break

                # if the roll wasn't added, create a new RandomEvent to hold this one
                if (added == False):
                    rev = randoms.RandomEvent(low, high)
                    rev.add_roll(roll)
                    self.all_random_events.append(rev)





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



# create the global instance of the client that manages communication to the discord bot
client = EQValetClient()

#################################################################################################


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
    sb.add('Total Rolls = {}\n'.format(len(client.all_rolls)))
    sb.add('Total Random Events = {}\n'.format(len(client.all_random_events)))

    # add the list of random events
    for (ndx, rev) in enumerate(client.all_random_events):
        sb.add('{}'.format(rev.report_summary(ndx, elf.char_name)))

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
        ndx = len(client.all_random_events) - 1

    # is ndx in range
    if ((ndx >= 0) and (ndx < len(client.all_random_events))):
        rev = client.all_random_events[ndx]

        # create a smart buffer to keep buffers under max size for discord messages (2000)
        sb = SmartBuffer()

        # add the header
        sb.add(rev.report_header(ndx))

        # add all the rolls
        for r in rev.rolls:
            sb.add(r.report(elf.char_name))

        # add the winner
        sb.add(rev.report_winner(elf.char_name))

        # get the list of buffers and send each to discord
        bufflist = sb.get_bufflist()
        for b in bufflist:
            await ctx.send('{}'.format(b))

    else:
        await ctx.send('Requested random event ndx value is out of range.  Must be between 0 and {}'.format(len(client.all_random_events)-1))
        await ctx.send('Unspecified ndx value = shows most recent random event')



# regroup command
# allows user to change the delta window on any given RandomEvent
@client.command()
async def regroup(ctx, ndx = -1, new_window = 0):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))

    # is ndx in range
    if (len(client.all_random_events) == 0):
        await ctx.send('Error:  No RandomEvents to regroup!')

    elif ( (ndx < 0) or (ndx >= len(client.all_random_events)) ):
        await ctx.send('Error:  Requested ndx value = {}.  Value for ndx must be between 0 and {}'.format(ndx, len(client.all_random_events)-1))

    elif (new_window <= 0):
        await ctx.send('Error:  Requested new_window value = {}.  Value for new_window must be > 0'.format(new_window))

    else:
        # grab the requested random event, and restore it to time-ascending order
        old_rev = client.all_random_events.pop(ndx)

        low     = old_rev.low
        high    = old_rev.high
        rolls   = old_rev.rolls

        # is the new, larger window overlapping into the next random event(s)?
        if (new_window > old_rev.delta_seconds):
            processing = True
            while processing:
                processing = False
                if (ndx < len(client.all_random_events)):
                    next_rev = client.all_random_events[ndx]
                    # get delta t
                    delta_seconds = next_rev.start_time_stamp - old_rev.start_time_stamp
                    delta = delta_seconds.total_seconds()
                    # does next random event and is within new time window?
                    if ( (low == next_rev.low) and (high == next_rev.high) and (delta <= new_window) ):
                        # add the next randomm event rolls to the list of rolls to be sorted / readded
                        rolls += next_rev.rolls
                        client.all_random_events.pop(ndx)
                        # we're not done yet
                        processing = True

        # sort the list of all rolls in time-ascenting order
        rolls.sort(key = lambda x: x.time_stamp)

        # get all the rolls from the old random event
        for r in rolls:

            added = False
            # add it to the appropriate RandomEvent - walk the list and try to add the roll to any open randomevents
            for rev in client.all_random_events:
                if (rev.expired == False):
                    if (rev.add_roll(r)):
                        added = True
                        break

            # if the roll wasn't added, create a new RandomEvent to hold this one
            if (added == False):
                rev = randoms.RandomEvent(low, high, new_window)
                rev.add_roll(r)
                client.all_random_events.append(rev)

        # sort the event list to restore it to time-ascending order
        client.all_random_events.sort(key = lambda x: x.start_time_stamp)

        # if not expired yet, these are the random events just added, so close them, sort them, report them
        for (n, ev) in enumerate(client.all_random_events):
            if (ev.expired == False):
                ev.expired = True
                ev.sort_descending_randoms()
                await client.ctx.send('{}'.format(ev.report_summary(n, elf.char_name)))





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
    if elf.is_parsing():
        await ctx.send('Already parsing character log for: [{}]'.format(elf.char_name))
        await ctx.send('Log filename: [{}]'.format(elf.filename))
        await ctx.send('Parsing initiated by: [{}]'.format(elf.author))
        
    else:
        # new log file name get passed?
        if charname:
            elf.char_name = charname
        else:
            elf.char_name = myconfig.DEFAULT_CHAR_NAME
        elf.build_filename()

        # open the log file to be parsed
        # allow for testing, by forcing the bot to read an old log file for the VT and VD fights
        if TEST_BOT == False:
            # start parsing.  The default behavior is to open the log file, and begin reading it from tne end, i.e. only new entries
            rv = elf.open(ctx.message.author)

        else:
            # use a back door to force the system to read files from the beginning that contain VD / VT fights to test with
            elf.filename = 'randoms.txt'

            # start parsing, but in this case, start reading from the beginning of the file, rather than the end (default)
            rv = elf.open(ctx.message.author, seek_end = False)


        # if the log file was successfully opened, then initiate parsing
        if rv:
            # status message
            await ctx.send('Now parsing character log for: [{}]'.format(elf.char_name))
            await ctx.send('Log filename: [{}]'.format(elf.filename))
            await ctx.send('Parsing initiated by: [{}]'.format(elf.author))
            await ctx.send('Heartbeat timeout (minutes): [{}]'.format(elf.heartbeat))

            # create the background processs and kick it off
            client.ctx = ctx
            client.loop.create_task(parse())
        else:
            await ctx.send('ERROR: Could not open character log file for: [{}]'.format(elf.char_name))
            await ctx.send('Log filename: [{}]'.format(elf.filename))



# stop command
@client.command()
async def stop(ctx):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))

    if elf.is_parsing():

        # only the person who started the log can close it
        if elf.author == ctx.message.author:
            # stop parsing
            elf.close()
            await ctx.send('Stopped parsing character log for: [{}]'.format(elf.char_name))
        else:
            await ctx.send('Error: Parsing can only be stopped by the same person who started it.  Starter: [{}], !stop requestor [{}]'.format(elf.author, ctx.message.author))

    else:
        await ctx.send('Not currently parsing')



# status command
@client.command()
async def status(ctx):
    print('Command received: [{}] from [{}]'.format(ctx.message.content, ctx.message.author))

    if elf.is_parsing():
        await ctx.send('Parsing character log for: [{}]'.format(elf.char_name))
        await ctx.send('Log filename: [{}]'.format(elf.filename))
        await ctx.send('Parsing initiated by: [{}]'.format(elf.author))
        await ctx.send('Heartbeat timeout (minutes): [{}]'.format(elf.heartbeat))
    else:
        await ctx.send('Not currently parsing')


#################################################################################################


# the background process to parse the log files
#
async def parse():

    print('Parsing Started')

    # process the log file lines here
    while elf.is_parsing() == True:

        # read a line
        line = elf.readline()
        now = time.time()
        if line:
            elf.prevtime = now

            # process this line
            await client.process_line(line)


        else:
            # check the heartbeat.  Has our tracker gone silent?
            elapsed_minutes = (now - elf.prevtime)/60.0
            if elapsed_minutes > elf.heartbeat:
                elf.prevtime = now
                await client.ctx.send('Heartbeat Warning:  Tracker [{}] logfile has had no new entries in last {} minutes.  Is {} still online?'.format(elf.char_name, elf.heartbeat, elf.char_name))

            await asyncio.sleep(0.1)

    print('Parsing Stopped')




# let's go!!
client.run(myconfig.BOT_TOKEN)




