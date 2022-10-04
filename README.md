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

**_log event parser_**
  - 
  - parse for a variety of different events (XXX spawn detection, XXX time of death, GRATSS messages, GMOTD messages, random rolls, and more.
  - detection of the event will cause a message to be forwarded to a remove server (via the rsyslog system) for processing
 
####*LogEvent base class concepts*

The events to be parsed for are contained in the file *LogEventParser.py*, where several classes are defined:
  - LogEvent, the base class
  - several classes which derive from LogEvent, each designed to search for one particular event or occurrence
  
The fundamental design is for a standard Everquest log parser to read in each line from the log, and then walk the list of LogEvent objects, calling the LogEvent.matches(line) function on each, and if a match is found, to create a one-line report for each using the LogEvent.report() function:
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
If a match is discovered, it then calls LogEvent._custom_match_hook() for any additional processing which may be needed for that LogEvent.

The intention is that child class constructor functions will set customized _search_list regular expressions for that particular parse target.
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
Example child class _search_list intended to watch for Vessel Drozlin spawn:
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

Examples of possible uses of this function can be seen in the child classes 'FTE_Parser' and 'Random_Parser'.  In particular, FTE_Parser uses this function to capture the player name and target name in the short_description variable, and the Random_Parser class uses this function to add the logic necessary to deal with the fact that Everquest random events actually generate two lines in the log file, rather than one.
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

Fields included in the report:
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
The list, along with their assigned event ID values, is as shown:

```
     1 VesselDrozlin_Event()
     2 VerinaTomb_Event()
     3 MasterYael_Event()
     4 DainFrostreaverIV_Event()
     5 Severilous_Event()
     6 CazicThule_Event()
     7 FTE_Event()
     8 PlayerSlain_Event()
     9 Earthquake_Event()
    10 Random_Event()
    11 AnythingButComms_Event()
    12 Gratss_Event()
    13 TOD_Event()
    14 GMOTD_Event()
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
#     If and when the parser begins parsing a new log file, it is necessary to sweep through whatever list of LogEvent
#     objects are being maintained, and update the self.parsing_player field in each LogEvent object, e.g. something like:
#
#             for log_event in self.log_event_list:
#                 log_event.parsing_player = name
#

```

---
