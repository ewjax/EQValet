import logging.handlers

import Parser
import config
from util import starprint
from LogEvent import *


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
    TOD_HighFidelity_Event(),
]


#################################################################################################
#
# class to do all the LogEvent work
#
class LogEventParser(Parser.Parser):

    # ctor
    def __init__(self):
        super().__init__()

        # set up custom loggers to use for rsyslog comms
        self.logger_dict = {}
        server_list = config.config_data.options('rsyslog servers')
        for server in server_list:
            try:
                host_port_str = config.config_data.get('rsyslog servers', server)
                host_port_list = host_port_str.split(':')
                host = host_port_list[0]
                # this will throw an exception if the port number isn't an integer
                port = int(host_port_list[1])
                # print(f'{host}, {port}')

                # create a handler for the rsyslog communications, with level INFO
                # this will throw an exception if host:port are nonsensical
                log_handler = logging.handlers.SysLogHandler(address=(host, port))

                eq_logger = logging.getLogger(f'{host}:{port}')
                eq_logger.setLevel(logging.INFO)

                # log_handler.setLevel(logging.INFO)
                eq_logger.addHandler(log_handler)

                # create a handler for console, and set level to 100 to ensure it is silent
                # console_handler = logging.StreamHandler(sys.stdout)
                # console_handler.setLevel(100)
                # eq_logger.addHandler(console_handler)
                self.logger_dict[server] = eq_logger

            except ValueError:
                pass

        # print(self.logger_dict)

        # now walk the list of parsers and set their logging parameters
        for log_event in log_event_list:
            log_settings_str = config.config_data.get('LogEventParser', log_event.__class__.__name__)
            log_settings_list = log_settings_str.split(', ')

            # the 0-th element is a true/false parse flag
            if log_settings_list[0].lower() == 'true':
                log_event.parse = True
            else:
                log_event.parse = False

            # index 1 and beyond are rsyslog servers
            for n, elem in enumerate(log_settings_list):
                if n != 0:
                    server = log_settings_list[n]
                    if server in self.logger_dict.keys():
                        log_event.add_logger(self.logger_dict[server])

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

        # watch for .log command
        target = r'^(\.log )'
        m = re.match(target, trunc_line)
        if m:
            starprint(f"    {'LogEvent':30}  {'Parse?'}")
            starprint(f"    {'-':-<30} {'-------'}")
            for log_event in log_event_list:
                # starprint(f'    {log_event.__class__.__name__:30}:  {log_event.parse}: {log_event.logger_list}')
                starprint(f'    {log_event.__class__.__name__:30}:  {log_event.parse}')

        # check current line for matches in any of the list of Parser objects
        # if we find a match, then send the event report to the remote aggregator
        for log_event in log_event_list:
            if log_event.matches(line):
                log_event.log_report()
