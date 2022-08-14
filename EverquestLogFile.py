import glob
import os
import re
import asyncio
import time

from util import starprint


# allow for testing, by forcing the bot to read an old log file
TEST_ELF = False
# TEST_ELF = True


class EverquestLogFile:
    """
    class to encapsulate Everquest log file operations.
    This class is intended as a base class for any
    child class that needs log parsing abilities.

    The custom log parsing logic in the child class is accomplished by
    overloading the process_line() method
    """

    def __init__(self, base_directory: str, logs_directory: str, heartbeat: int) -> None:
        """
        ctor

        Args:
            base_directory: Base installation directory for Everquest
            logs_directory: Logs directory, typically '\\logs\\'
            heartbeat: Number of seconds of logfile inactivity before a check is made to re-determine most recent logfile
        """
        # instance data
        self.base_directory = base_directory
        self.logs_directory = logs_directory
        self.char_name = 'Unknown'
        self.server_name = 'Unknown'
        self.filename = self.build_filename(self.char_name, self.server_name)
        self.file = None

        # are we parsing
        self._parsing = False

        self.prevtime = time.time()
        self.heartbeat = heartbeat

    def build_filename(self, charname: str, servername: str) -> str:
        """
        build the file name.
        call this anytime that the filename attributes change

        Args:
            charname: Everquest character log to be parsed
            servername: Name of the server, i.e. 'P1999Green'

        Returns:
            str: complete filename
        """
        rv = self.base_directory + self.logs_directory + 'eqlog_' + charname + '_' + servername + '.txt'
        return rv

    def set_parsing(self) -> None:
        """
        called when parsing is active
        """
        self._parsing = True

    def clear_parsing(self) -> None:
        """
        called when parsing is no longer active
        """
        self._parsing = False

    def is_parsing(self) -> bool:
        """
        Returns:
            object: Is the file being actively parsed
        """
        return self._parsing

    def open_latest(self, seek_end=True) -> bool:
        """
        open the file with most recent mod time (i.e. latest).

        Args:
            seek_end: True if parsing is to begin at the end of the file, False if at the beginning

        Returns:
            object: True if a new file was opened, False otherwise
        """
        # get a list of all log files, and sort on mod time, latest at top
        mask = self.base_directory + self.logs_directory + 'eqlog_*_*' + '.txt'
        files = glob.glob(mask)
        files.sort(key=os.path.getmtime, reverse=True)

        # if no files are found to parse, bail out
        if len(files) == 0:
            starprint(f'ERROR: Unable to open any log files in directory [{self.base_directory}]')
            return False

        latest_file = files[0]

        # extract the character name from the filename
        # note that windows pathnames must use double-backslashes in the pathname
        # note that backslashes in regular expressions are double-double-backslashes
        # this expression replaces double \\ with quadruple \\\\, as well as the filename mask asterisk to a
        # named regular expression
        names_regexp = mask.replace('\\', '\\\\').replace('eqlog_*_*', 'eqlog_(?P<charname>[\\w ]+)_(?P<servername>[\\w]+)')
        m = re.match(names_regexp, latest_file)
        char_name = m.group('charname')
        server_name = m.group('servername')

        rv = False

        # figure out what to do
        # if we are already parsing a file, and it is the latest file - do nothing
        if self.is_parsing() and (self.filename == latest_file):
            # do nothing
            pass

        # if we are already parsing a file, but it is not the latest file, close the old and open the latest
        elif self.is_parsing() and (self.filename != latest_file):
            # stop parsing old and open the new file
            self.close()
            rv = self.open(char_name, server_name, latest_file, seek_end)

        # if we aren't parsing any file, then open latest
        elif not self.is_parsing():
            rv = self.open(char_name, server_name, latest_file, seek_end)

        return rv

    def open(self, charname: str, servername: str, filename: str, seek_end=True) -> bool:
        """
        open the file.
        seek file position to end of file if passed parameter 'seek_end' is true

        Args:
            charname: character name whose log file is to be opened
            servername: Name of the server, i.e. 'P1999Green'
            filename: full log filename
            seek_end: True if parsing is to begin at the end of the file, False if at the beginning

        Returns:
            bool: True if a new file was opened, False otherwise
        """
        try:
            self.file = open(filename, 'r', errors='ignore')
            if seek_end:
                self.file.seek(0, os.SEEK_END)

            self.char_name = charname
            self.server_name = servername
            self.filename = filename
            self.set_parsing()
            return True
        except OSError as err:
            starprint('OS error: {0}'.format(err))
            starprint('Unable to open filename: [{}]'.format(filename))
            return False

    def close(self) -> None:
        """
        close the file
        """
        self.file.close()
        self.clear_parsing()

    def readline(self) -> str or None:
        """
        get the next line

        Returns:
            str or None: a string containing the next line, or None if no new lines to be read
        """
        if self.is_parsing():
            return self.file.readline()
        else:
            return None

    def go(self) -> bool:
        """
        call this method to kick off the parsing thread

        Returns:
            bool: True if file is opened successfully for parsing
        """
        rv = False

        # already parsing?
        if self.is_parsing():
            starprint('Already parsing character log for: [{}]'.format(self.char_name))

        else:

            # use a back door to force the system to read a test file
            if TEST_ELF:

                # read a sample file for testing
                filename = './data/test/randoms.txt'
                # filename = './data/test/pets.txt'
                # filename = './data/test/pets_long.txt'
                # filename = './data/test/fights.txt'

                # start parsing, but in this case, start reading from the beginning of the file,
                # rather than the end (default)
                rv = self.open('Testing', 'Testing', filename, seek_end=False)

            # open the latest file
            else:
                # open the latest file, and kick off the parsing process
                rv = self.open_latest()

            # if the log file was successfully opened, then initiate parsing
            if rv:
                # status message
                starprint('Now parsing character log for: [{}]'.format(self.char_name))

                # create the asyncio coroutine and kick it off
                asyncio.create_task(self.run())

            else:
                starprint('ERROR: Could not open character log file for: [{}]'.format(self.char_name))
                starprint('Log filename: [{}]'.format(self.filename))

        return rv

    def stop_parsing(self) -> None:
        """
        call this function when ready to stop (opposite of go() function)
        """
        self.close()

    async def run(self) -> None:
        """
        this method will execute in its own asynco coroutine
        Note that it calls self.process_line() for each line, so child classes can overload that function
        to perform their particular parsing logic
        """

        # do this while the parsing flag is set, and exit if/when stop_parsing() is called
        while self.is_parsing():

            # read a line
            line = self.readline()
            now = time.time()
            if line:
                self.prevtime = now

                # process this line
                await self.process_line(line)

            else:
                # check the heartbeat.  Has our logfile gone silent?
                elapsed_seconds = (now - self.prevtime)

                if elapsed_seconds > self.heartbeat:
                    starprint(f'[{self.char_name}] heartbeat over limit, elapsed seconds = {elapsed_seconds:.2f}')
                    self.prevtime = now

                    # attempt to open latest log file - returns True if a new logfile is opened
                    if self.open_latest():
                        starprint('Now parsing character log for: [{}]'.format(self.char_name))

                # if we didn't read a line, pause just for a 100 msec blink
                await asyncio.sleep(0.1)

        starprint(f'Stopped parsing character log for: [{self.char_name}]')

    async def process_line(self, line: str) -> None:
        """
        virtual method, to be overridden in derived classes to do whatever specialized
        parsing is required for that application.

        Default behavior is to simply print() the line

        Args:
            line: line from logfile to be processed
        """
        print(line.rstrip())


#
# test driver
#
async def main():

    base_directory = 'c:\\users\\ewjax\\Documents\\Gaming\\Everquest-Project1999'
    logs_directory = '\\logs\\'
    # server_name = 'P1999Green'
    heartbeat = 15

    elf = EverquestLogFile(base_directory, logs_directory, heartbeat)

    print('creating and starting elf, then sleeping for 20')
    elf.go()

    count = 20
    for n in range(count):
        print(f'------------------- tick {n} ---------------------')
        await asyncio.sleep(1)

    # test the ability to stop and restart the parsing
    print('stopping elf, then sleeping for 5')
    elf.stop_parsing()

    count = 5
    for n in range(count):
        print(f'------------------- tick {n} ---------------------')
        await asyncio.sleep(1)

    print('restarting elf, then sleeping for 30')
    elf.go()

    count = 30
    for n in range(count):
        print(f'------------------- tick {n} ---------------------')
        await asyncio.sleep(1)

    print('done done')
    elf.stop_parsing()


if __name__ == '__main__':
    asyncio.run(main())
