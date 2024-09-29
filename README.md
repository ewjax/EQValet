# eqvalet

An Everquest log parsing utility that provides several helper functions for Everquest.  Output is sent to a console window.

---

**_random rolls_**
  - 
  - all rolls with matching lower and upper values, that occur within a 30 second window (default), are grouped, and winner(s) identified
  - default 30 second window can be adjusted up or down.  This will cause random rolls to be regrouped as necessary.
  - ability to declare either the upper or lower value as "not significant", to allow for schemes where some players get bonuses on their randoms.
    - Example:  Perhaps the standard random for an event/item is 0-1000, and perhaps players are afforded a +100 bonus to their lower value for every time they random on that particular event/item but do not win.
      - /random 0 1000 (for normal odds)
      - /random 100 1000 (for players with one roll bonus)
      - /random 200 1000 (for players with two roll bonuses)

---

**_pet tracker_**
-
  - determines pet level / rank (max pet, or otherwise) by parsing max melee damage, and/or by the pet's lifetap, procs, or damage shield values

---

**_damage parser_**
  - 
  - dps tracker.  The main use is intended to allow the soloing pet class to determine if their pet is doing more or less than 50% of the total damage.
  - melee damage tracked explicitly via damage messages
  - DOT damage tracked implicitly, by watching for spell cast / spell landed messages and doing the math to report how much DOT damage was done
  - Loads a combat summary into the windows clipboard, ready for pasting, at the end of every combat
  - Notes
    - keeps a running database of all known player names, to help distinguish between damage to a friend or enemy
    - also has a database of all allowable pet names, for same purpose
    - Users should ensure the player database is up to date by entering a /who command prior to grouping, to ensure all group members are known to the player database

---

**_death loop parser_**
  - 
  - Watches for "death loop" conditions, and if it detects the presence of a death loop, it will automatically kill the eqgame.exe process and kick the user out of game.
  - Death Loop conditions are defined as
    - N deaths (default 4), in
    - T seconds (default 120), with
    - no evidence of player activity in the interim, such as melee attacks, spell casts, or communications

---

**_log event tracking_**
  - 
  - parse the Everquest log file for a variety of different events (XXX spawn detection, XXX time of death, GRATSS messages, GMOTD messages, random rolls, and more.
  - detection of the event will cause a message to be forwarded to a remove server for processing
  - communication to remote server is via the unix rsyslog service, configured to listen for UDP packets (set up for UDP, rather than TCP, so clients can "fire and forget" and not wait on a server reply)
 
####*LogEvent base class concepts*

The events to be parsed for are contained in the file *LogEventParser.py*, where several classes are defined:
  - LogEvent, the base class
  - several classes which derive from LogEvent, each designed to search for one particular event or occurrence
  
The fundamental design is for a standard Everquest log parser to read in each line from the log, and then walk its list of LogEvent parsing objects, calling the LogEvent.matches(line) function on each, and if a match is found, to create a one-line report for each using the LogEvent.report() function:
```
        # check current line for matches in any of the list of LogEvent objects
        for log_event in self.log_event_list:
            if log_event.matches(line):
                report_str = log_event.report()
                
                # process the match in some manner
                print(report_str, end='')
```               

#### *Base class LogEvent.matches()*

Walks the list of regular expression trigger strings contained in LogEvent._search_list, checking each for a match.  
If a match is discovered, it then calls LogEvent._custom_match_hook() for any additional processing which may be needed for that LogEvent.  Multiple regex strings are allowed, under the theory that there can be more than one way to indicate a certain event (e.g. a desired mob has spawned) has occurred.

The intention is that child class will derive from the base class, and in the child constructor functions will set customized _search_list regular expressions for that particular log event.
Example base class LogEvent._search_list:
```
        self.short_description = 'Generic Target Name spawn!'
        self._search_list = [
            '^Generic Target Name begins to cast a spell',
            '^Generic Target Name engages (?P<playername>[\\w ]+)!',
            '^Generic Target Name has been slain',
            '^Generic Target Name says',
            '^You have been slain by Generic Target Name'
        ]
```
Example child class VesselDrozlin_Event._search_list intended to watch for Vessel Drozlin spawn:
```
        self.short_description = 'Vessel Drozlin spawn!'
        self._search_list = [
            '^Vessel Drozlin begins to cast a spell',
            '^Vessel Drozlin engages (?P<playername>[\\w ]+)!',
            '^Vessel Drozlin has been slain',
            '^Vessel Drozlin says',
            '^You have been slain by Vessel Drozlin'
        ]
```
Example child class _search_list intended to watch for FTE messages:
```
        self.short_description = 'FTE!'
        self._search_list = [
            '^(?P<target_name>[\\w ]+) engages (?P<playername>[\\w ]+)!'
        ]
```

#### *LogEvent._custom_match_hook()*
Once LogEvent.matches() finds a match when checking against the _search_list of regular expression triggers, it then calls LogEvent._custom_match_hook() method.  The default behavior is simply to return True, but the intention is to allow child classes to override this function to provide any additional logic.

Examples of possible uses of this function can be seen in the child classes 'FTE_Event' and 'Random_Event'.  In particular, FTE_Event uses this function to capture the player name and target name in the short_description variable, and the Random_Event class uses this function to add the logic necessary to deal with the fact that Everquest random events actually generate two lines in the log file, rather than one.
```
        self._search_list = [
            '\\*\\*A Magic Die is rolled by (?P<playername>[\\w ]+)\\.',
            '\\*\\*It could have been any number from (?P<low>[0-9]+) to (?P<high>[0-9]+), but this time it turned up a (?P<value>[0-9]+)\\.'
        ]
...
    # override the default base class behavior to add some additional logic
    def _custom_match_hook(self, m: re.Match, line: str) -> bool:
        rv = False
        if m:
            # if m is true, and contains the playername group, this represents the first line of the random dice roll event
            # save the playername for later
            if 'playername' in m.groupdict().keys():
                self.playername = m.group('playername')
            # if m is true but doesn't have the playername group, then this represents the second line of the random dice roll event
            else:
                low = m.group('low')
                high = m.group('high')
                value = m.group('value')
                self.short_description = f'Random roll: {self.playername}, {low}-{high}, Value={value}'
                rv = True

        return rv

```

#### *LogEvent.report()*
The concept is that each match generates a single line report that contains the relevant information for this event, with fields separated by LogEvent.field_separator character (default = '|').

Fields included in the rsyslog report:
1. A standard marker, default 'EQ__', to assist in downstream parsing
2. Player name
3. An integer ID, unique to that particular type of LogEvent,  to assist in downstream sorting and processing
4. Short description
5. UTC timestamp
6. The raw line from the everquest log file

Examples:
```
EQ__|Azleep|1|Vessel Drozlin spawn!|2021-05-31 23:05:42+00:00|[Mon May 31 16:05:42 2021] Vessel Drozlin engages Azleep!
EQ__|Azleep|7|FTE: Vessel Drozlin engages Azleep|2021-05-31 23:05:42+00:00|[Mon May 31 16:05:42 2021] Vessel Drozlin engages Azleep!
EQ__|Azleep|13|TOD (Slain Message): Vessel Drozlin|2021-05-31 23:09:18+00:00|[Mon May 31 16:09:18 2021] Vessel Drozlin has been slain by Crusader Golia!
EQ__|Azleep|12|Gratss|2022-09-18 23:41:50+00:00|[Sun Sep 18 16:41:50 2022] Snoiche tells the guild, 'Crexxus Crown of Narandi  500 Gratss me'
EQ__|Azleep|13|TOD|2021-07-03 08:19:27+00:00|[Sat Jul 03 01:19:27 2021] Jherin tells the guild, 'ToD Harla Dar'
EQ__|Azleep|14|GMOTD|2021-03-20 02:16:48+00:00|[Fri Mar 19 19:16:48 2021] GUILD MOTD: Zalkestna - - What do you call an elf who won't share? -----Elfish----That's your Friday GMOTD!  Have fun and be kind to one another!
```
---

#### *LogEvent child classes*

Several child classes are pre-defined in LogEventParser.py, but the opportunity to create additional classes for other desired parsing targets is limited only by the imagination / need.
The list, along with their assigned event ID values, is as shown below.  Developers should take care to give any newly-developed XXX_Event() parsers a unique ID.

```
# define some ID constants for the derived classes
LOGEVENT_BASE: int = 0
LOGEVENT_VD: int = 1
LOGEVENT_VT: int = 2
LOGEVENT_YAEL: int = 3
LOGEVENT_DAIN: int = 4
LOGEVENT_SEV: int = 5
LOGEVENT_CT: int = 6
LOGEVENT_FTE: int = 7
LOGEVENT_PLAYERSLAIN: int = 8
LOGEVENT_QUAKE: int = 9
LOGEVENT_RANDOM: int = 10
LOGEVENT_ABC: int = 11
LOGEVENT_GRATSS: int = 12
LOGEVENT_TODLO: int = 13
LOGEVENT_GMOTD: int = 14
LOGEVENT_TODHI: int = 15

Example usage, in constructor for VesselDrozlin_Event:

        self.log_event_ID = LOGEVENT_VD

```
Some guidance to the developer for possible future event parsers:

```
#########################################################################################################################
#
# Notes for the developer:
#   - derived classes constructor should correctly populate the following fields, according to whatever event this
#     parser is watching for:
#           self.log_event_ID, a unique integer for each LogEvent class, to help the server side
#           self.short_description, a text description, and
#           self._search_list, a list of regular expression(s) that indicate this event has happened
#   - derived classes can optionally override the _custom_match_hook() method, if special/extra parsing is needed,
#     or if a customized self.short_description is desired.  This method gets called from inside the standard matches()
#     method.  The default base case behavior is to simply return True.
#           see Random_Event() class for a good example, which deals with the fact that Everquest /random events
#           are actually reported in TWO lines of text in the log file
#
#   - See the example derived classes in this file to get a better idea how to set these items up
#
#   - IMPORTANT:  These classes make use of the self.parsing_player field to embed the character name in the report.
#     If and when the logfile parser begins parsing a new log file, it is necessary to sweep through whatever list of LogEvent
#     objects are being maintained, and update the self.parsing_player field in each LogEvent object, e.g. something like:
#
#             for log_event in log_event_list:
#                 log_event.parsing_player = name
#
```

#### *Client-Server Communication*
   
  - On python client:  done via the SysLogHandler built into the logging standard library
  - Uses the UDP interface (rather than TCP), so there is no reply acknowledgement required, the client can "fire and forget"
    - Advantage: speed (no wait for TCP reply)
    - Disadvantage: no confirmation to the client that the messages are being received by the server
  - On the server side
    - the unix rsyslog setup does not typically listen for TCP or UDP packets by default, that will need to be enabled and the service restarted
    - the default port is 514, but can be configured to something else if desired
    - the firewall will likely need that port opened for incoming traffic
    - the default filename to receive the rsyslog messages depends on the flavor of unix being used (usually /var/log/something), but can also be configured 
  - The client can send information to more than one rsyslog server, by adding hostname/IP address and port number to the following list of (host, port) tuples.  This example is sending the logging information to both a raspberry pi on my home network, as well as an Amazon Web Service EC2 virtual machine: 

```
# list of rsyslog (host, port) information
remote_list = [
    ('192.168.1.127', 514),
    ('ec2-3-133-158-247.us-east-2.compute.amazonaws.com', 22514),
]
```

The server should be able to listen / tail the appropriate rsyslog file, and decode it using something like:
```
        # parsing landmarks
        self.field_separator = '\\|'
        self.eqmarker = 'EQ__'

        # does this line contain a EQ report?
        target = f'^.*{self.eqmarker}{self.field_separator}'
        target += f'(?P<charname>.+){self.field_separator}'
        target += f'(?P<log_event_ID>.+){self.field_separator}'
        target += f'(?P<short_desc>.+){self.field_separator}'
        target += f'(?P<utc_timestamp_str>.+){self.field_separator}'
        target += f'(?P<eq_log_line>.+)'
        m = re.match(target, line)
        if m:
            # print(line, end='')
            charname = m.group('charname')
            log_event_ID = m.group('log_event_ID')
            short_desc = m.group('short_desc')
            eq_log_line = m.group('eq_log_line')

            # convert the timestamp string into a datetime object, for use in reporting or de-duping of other reports
            utc_timestamp_datetime = datetime.fromisoformat(m.group('utc_timestamp_str'))

            # todo - do something useful with the received data, e.g. put all spawn messages in this channel, 
            # put all TOD messages in that channel, use the UTC timestamp to de-dupe, etc
            print(f'{charname} --- {log_event_ID} --- {short_desc} --- {utc_timestamp_datetime} --- {eq_log_line}')

```

---
**_Build and Installation Steps:_**
-
EQValet makes use of a virtual python environment, and creates a standalone executable, which can be copied to a local directory for use.

The build process is controlled via a makefile.

Build steps:
```
git clone git@github.com:ewjax/EQValet.git
cd EQValet
make venv
```
Activate the python virtual environment, then continue the build process:
```
(unix): source .ascii-plot.venv/bin/activate
(windows): .ascii-plot.venv\Scripts\activate
make all
Executable will be placed in ./dist subdirectory
```
Cleanup steps:
```
(while still in the python virtual environment): 
make clean
deactivate
make venv.clean
```
