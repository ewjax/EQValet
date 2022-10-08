import logging
import logging.handlers

import Parser
from util import starprint
from LogEvent import *


# list of rsyslog (host, port) information
remote_list = [
    ('192.168.1.127', 514),
    ('ec2-3-133-158-247.us-east-2.compute.amazonaws.com', 22514),
]


# create a global list of parsers
# this global list is used to toggle parsing on/off for the particular parser in the ini file
log_event_list = [
    VesselDrozlin_Event(),
    VerinaTomb_Event(),
    MasterYael_Event(),
    DainFrostreaverIV_Event(),
    Severilous_Event(),
    CazicThule_Event(),
    FTE_Event(),
    PlayerSlain_Event(),
    Earthquake_Event(),
    Random_Event(),
    AnythingButComms_Event(),
    Gratss_Event(),
    TOD_LowFidelity_Event(),
    GMOTD_Event(),
    TOD_HighFidelity_Event
]


#################################################################################################
#
# class to do all the LogEvent work
#
class LogEventParser(Parser.Parser):

    # ctor
    def __init__(self):
        super().__init__()

        # set up a custom logger to use for rsyslog comms
        self.logger_list = []
        for (host, port) in remote_list:
            eq_logger = logging.getLogger(f'{host}:{port}')
            eq_logger.setLevel(logging.INFO)

            # create a handler for the rsyslog communications, with level INFO
            log_handler = logging.handlers.SysLogHandler(address=(host, port))
            # log_handler.setLevel(logging.INFO)
            eq_logger.addHandler(log_handler)

            # create a handler for console, and set level to 100 to ensure it is silent
            # console_handler = logging.StreamHandler(sys.stdout)
            # console_handler.setLevel(100)
            # eq_logger.addHandler(console_handler)

            self.logger_list.append(eq_logger)

    def set_char_name(self, name: str) -> None:
        """
        override base class setter function to also sweep through list of parse targets
        and set their parsing player names

        Args:
            name: player whose log file is being parsed
        """
        global log_event_list
        for log_event in log_event_list:
            log_event.parsing_player = name

    #
    # process each line
    async def process_line(self, line: str) -> None:
        """
        Check the current line for damage related items

        Args:
            line: complete line from the EQ logfile
        """
        await super().process_line(line)

        # the global list of log_events
        global log_event_list

        # cut off the leading date-time stamp info
        trunc_line = line[27:]

        # watch for .lep command
        target = r'^(\.log )'
        m = re.match(target, trunc_line)
        if m:
            starprint(f"    {'LogEvent':30}  {'Parse?'}")
            starprint(f"    {'-':-<30} {'-------'}")
            for log_event in log_event_list:
                starprint(f'    {log_event.__class__.__name__:30}:  {log_event.parse}')
            starprint('To change the Parse True/False settings, edit the .ini file, then reload with the .ini command')

        # check current line for matches in any of the list of Parser objects
        # if we find a match, then send the event report to the remote aggregator
        for log_event in log_event_list:
            if log_event.matches(line):
                report_str = log_event.report()
                # print(report_str, end='')

                # send the info to the remote log aggregator
                for logger in self.logger_list:
                    logger.info(report_str)
