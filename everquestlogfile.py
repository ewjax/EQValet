
import threading
import asyncio
import time
import discord
import random
import os
import re



import myconfig


#################################################################################################


#
# class to encapsulate log file operations
#
class EverquestLogFile():

    #
    # ctor
    #
    def __init__(self, char_name = myconfig.DEFAULT_CHAR_NAME):

        # instance data
        self.base_directory = myconfig.BASE_DIRECTORY
        self.logs_directory = myconfig.LOGS_DIRECTORY
        self.char_name      = char_name
        self.server_name    = myconfig.SERVER_NAME
        self.filename       = ''
        self.file           = None

        self.parsing        = threading.Event()
        self.parsing.clear()

        self.ctx            = None
        self.author         = ''

        self.prevtime       = time.time()
        self.heartbeat      = myconfig.HEARTBEAT

        # timezone string for current computer
        self.current_tzname = time.tzname[time.daylight]


        # build the filename
        self.build_filename()

    # build the file name
    # call this anytime that the filename attributes change
    def build_filename(self):
        self.filename = self.base_directory + self.logs_directory + 'eqlog_' + self.char_name + '_' + self.server_name + '.txt'

    # is the file being actively parsed
    def set_parsing(self):
        self.parsing.set()

    def clear_parsing(self):
        self.parsing.clear()

    def is_parsing(self):
        return self.parsing.is_set()


    # open the file
    # seek file position to end of file if passed parameter 'seek_end' is true
    def open(self, author, seek_end = True):
        try:
            self.file = open(self.filename)
            if seek_end:
                self.file.seek(0, os.SEEK_END)

            self.author = author
            self.set_parsing()
            return True
        except:
            return False

    # close the file
    def close(self):
        self.file.close()
        self.author = ''
        self.clear_parsing()

    # get the next line
    def readline(self):
        if self.is_parsing():
            return self.file.readline()
        else:
            return None


