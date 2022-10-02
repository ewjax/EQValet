import re
import os
import signal
from datetime import datetime

import Parser
from util import starprint
from util import get_eqgame_pid_list

# import the global config data
import config


#################################################################################################

#
# class to do all the damage tracking work
#
class DeathLoopParser(Parser.Parser):
    """
    Class to do all the damage tracking work
    """

    # ctor
    def __init__(self):
        super().__init__()

        # list of death messages
        # this will function as a scrolling queue, with the oldest message at position 0,
        # newest appended to the other end.  Older messages scroll off the list when more
        # than deathloop_seconds have elapsed.  The list is also flushed any time
        # player activity is detected (i.e. player is not AFK).
        #
        # if/when the length of this list meets or exceeds deathloop_deaths, then
        # the deathloop response is triggered
        self._death_list = list()

        # flag indicating whether the "process killer" gun is armed
        self._kill_armed = True

    #
    #
    def reset(self) -> None:
        """
        Utility function to clear the death_list and reset the armed flag
        """
        self._death_list.clear()
        self._kill_armed = True

    #
    #
    async def process_line(self, line: str) -> None:
        """
        This method gets called by the base class parsing thread once for each parsed line.
        We overload it here to perform our special case parsing tasks.

        Args:
            line: string with a single line from the logfile
        """
        # check for death messages
        # check for indications the player is really not AFK
        # are we death looping?  if so, kill the process
        await super().process_line(line)

        #
        # cut off the leading date-time stamp info
        trunc_line = line[27:]

        #
        # check for toggling the parse on/off
        #
        target = r'^\.dlt '
        m = re.match(target, trunc_line)
        if m:

            # the relevant section and key value from the ini configfile
            section = 'DeathLoopParser'
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

            starprint(f'Deathloop Parsing: {onoff}')

        # report the parameters that define a deathloop
        target = r'^\.dl '
        m = re.match(target, trunc_line)
        if m:
            deaths = config.config_data.getint('DeathLoopParser', 'deaths')
            seconds = config.config_data.getint('DeathLoopParser', 'seconds')
            starprint(f'Deathloop parameters: {deaths} deaths in {seconds} seconds')

        # only do everything else if parsing is true
        if config.config_data.getboolean('DeathLoopParser', 'parse'):
            self.check_for_death(line)
            self.check_not_afk(line)
            self.deathloop_response()

    #
    #
    def check_for_death(self, line: str) -> None:
        """
        check for indications the player just died, and if we find it,
        save the message for later processing

        Args:
            line: string with a single line from the logfile
        """

        # cut off the leading date-time stamp info
        trunc_line = line[27:]

        # does this line contain a death message
        slain_regexp = r'^You have been slain'
        m = re.match(slain_regexp, trunc_line)
        if m:
            # add this message to the list of death messages
            self._death_list.append(line)
            starprint(f'DeathLoopVaccine:  Death count = {len(self._death_list)}')

        # a way to test - send a tell to death_loop
        slain_regexp = r'^\.deathloop'
        m = re.match(slain_regexp, trunc_line)
        if m:
            # add this message to the list of death messages
            # since this is just for testing, disarm the kill-gun
            self._death_list.append(line)
            starprint(f'DeathLoopVaccine:  Death count = {len(self._death_list)}')
            self._kill_armed = False

        # only do the list-purging if there are already some death messages in the list, else skip this
        if len(self._death_list) > 0:

            # create a datetime object for this line, using the very capable datetime.strptime()
            now = datetime.strptime(line[0:26], '[%a %b %d %H:%M:%S %Y]')

            # now purge any death messages that are too old
            done = False
            while not done:
                # if the list is empty, we're done
                if len(self._death_list) == 0:
                    self.reset()
                    done = True
                # if the list is not empty, check if we need to purge some old entries
                else:
                    oldest_line = self._death_list[0]
                    oldest_time = datetime.strptime(oldest_line[0:26], '[%a %b %d %H:%M:%S %Y]')
                    elapsed_seconds = now - oldest_time

                    if elapsed_seconds.total_seconds() > config.config_data.getint('DeathLoopParser', 'seconds'):
                        # that death message is too old, purge it
                        self._death_list.pop(0)
                        starprint(f'DeathLoopVaccine:  Death count = {len(self._death_list)}')
                    else:
                        # the oldest death message is inside the window, so we're done purging
                        done = True

    #
    #
    def check_not_afk(self, line: str) -> None:
        """
        check for "proof of life" indications the player is really not AFK

        Args:
            line: string with a single line from the logfile
        """

        # only do the proof of life checks if there are already some death messages in the list, else skip this
        if len(self._death_list) > 0:

            # check for proof of life, things that indicate the player is not actually AFK
            # begin by assuming the player is AFK
            afk = True

            # cut off the leading date-time stamp info
            trunc_line = line[27:]

            # does this line contain a proof of life - casting
            regexp = r'^You begin casting'
            m = re.match(regexp, trunc_line)
            if m:
                # player is not AFK
                afk = False
                starprint(f'DeathLoopVaccine:  Player Not AFK: {line}')

            # does this line contain a proof of life - communication
            # this captures tells, say, group, auction, and shout channels
            regexp = f'^(You told|You say|You tell|You auction|You shout|{config.the_valet._char_name} ->)'
            m = re.match(regexp, trunc_line)
            if m:
                # player is not AFK
                afk = False
                starprint(f'DeathLoopVaccine:  Player Not AFK: {line}')

            # does this line contain a proof of life - melee
            regexp = r'^You( try to)? (hit|slash|pierce|crush|claw|bite|sting|maul|gore|punch|kick|backstab|bash)'
            m = re.match(regexp, trunc_line)
            if m:
                # player is not AFK
                afk = False
                starprint(f'DeathLoopVaccine:  Player Not AFK: {line}')

            # if they are not AFK, then go ahead and purge any death messages from the list
            if not afk:
                self.reset()

    #
    #
    def deathloop_response(self) -> None:
        """
        are we death looping?  if so, kill the process
        """

        # if the death_list contains more deaths than the limit, then trigger the process kill
        if len(self._death_list) >= config.config_data.getint('DeathLoopParser', 'deaths'):

            starprint('---------------------------------------------------')
            starprint('DeathLoopVaccine - Killing all eqgame.exe processes')
            starprint('---------------------------------------------------')
            starprint('DeathLoopVaccine has detected deathloop symptoms:')

            deaths = config.config_data.getint('DeathLoopParser', 'deaths')
            seconds = config.config_data.getint('DeathLoopParser', 'seconds')
            starprint(f'    {deaths} deaths in less than {seconds} seconds, with no player activity')

            # show all the death messages
            starprint('Death Messages:')
            for line in self._death_list:
                starprint('    ' + line)

            # get the list of eqgame.exe process ID's, and show them
            pid_list = get_eqgame_pid_list()
            starprint(f'eqgame.exe process id list = {pid_list}')

            # kill the eqgame.exe process / processes
            for pid in pid_list:
                starprint(f'Killing process [{pid}]')

                # for testing the actual kill process using simulated player deaths, uncomment the following line
                # self._kill_armed = True
                if self._kill_armed:
                    os.kill(pid, signal.SIGTERM)
                else:
                    starprint('(Note: Process Kill only simulated, since death(s) were simulated)')

            # purge any death messages from the list
            self.reset()
