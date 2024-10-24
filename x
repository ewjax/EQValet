D:\dev\everquest\eqvalet\x
**                                                                                                      **
** ==================================================================================================== **
**                                       EQValet 2.11.0.53-dev.0                                        **
** ==================================================================================================== **
**                                                                                                      **
** ---------------------------------------EQValet.ini contents:---------------------------------------- **
** [EQValet]                                                                                            **
**     bell = True                                                                                      **
** [Everquest]                                                                                          **
**     base_directory = c:\users\ewjax\Documents\Gaming\Everquest-Project1999                           **
**     logs_directory = \logs\                                                                          **
**     heartbeat = 15                                                                                   **
** [RandomParser]                                                                                       **
**     parse = True                                                                                     **
**     grouping_window = 20                                                                             **
** [DamageParser]                                                                                       **
**     parse = True                                                                                     **
**     spell_pending_timeout_sec = 15                                                                   **
**     combat_timeout_sec = 120                                                                         **
** [PetParser]                                                                                          **
**     parse = True                                                                                     **
** [DeathLoopParser]                                                                                    **
**     parse = True                                                                                     **
**     deaths = 4                                                                                       **
**     seconds = 120                                                                                    **
** [rsyslog servers]                                                                                    **
**     server1 = 192.168.1.127:514                                                                      **
**     server2 = ec2-3-133-158-247.us-east-2.compute.amazonaws.com:22514                                **
**     server3 = stanvern-hostname:port                                                                 **
** [LogEventParser]                                                                                     **
**     vesseldrozlin_event = False, server1, server2, server3                                           **
**     verinatomb_event = False, server1, server2, server3                                              **
**     dainfrostreaveriv_event = False, server1, server2, server3                                       **
**     severilous_event = False, server1, server2, server3                                              **
**     cazicthule_event = False, server1, server2, server3                                              **
**     masteryael_event = False, server1, server2, server3                                              **
**     fte_event = False, server1, server2, server3                                                     **
**     playerslain_event = False, server1, server2, server3                                             **
**     earthquake_event = False, server1, server2, server3                                              **
**     random_event = False, server1, server2, server3                                                  **
**     anythingbutcomms_event = False, server3                                                          **
**     gratss_event = False, server1, server2, server3                                                  **
**     tod_event = False, server1, server2, server3                                                     **
**     gmotd_event = False, server1, server2, server3                                                   **
**     tod_lowfidelity_event = False, server1, server2, server3                                         **
**     tod_highfidelity_event = False, server1, server2, server3                                        **
** [ConsoleWindowPosition]                                                                              **
**     x = 2746                                                                                         **
**     y = 144                                                                                          **
**     width = 1098                                                                                     **
**     height = 924                                                                                     **
** [WhoParser]                                                                                          **
**     parse = True                                                                                     **
** .................................................................................................... **
** Now parsing character log for: [Unknown]                                                             **
** EQValet running                                                                                      **
**                                                                                                      **
** **************************************************************************************************** **
**                                                                                                      **
**                                            EQValet:  Help                                            **
**                                                                                                      **
** User commands are accomplished by sending a tell to the below fictitious player names:               **
**                                                                                                      **
** General                                                                                              **
**   .help          : This message                                                                      **
**   .status        : Show logfile parsing status                                                       **
**   .bt            : Toggle summary reports bell tone on/off                                           **
**   .save          : Force console window on screen position to be saved/remembered                    **
**   .ini           : Reload EQValet.ini settings, and display contents                                 **
**   .ver           : Display EQValet current version                                                   **
** Who / Character Name Database                                                                        **
**   .wt            : Toggle who tracking on/off                                                        **
**   .w or .who     : Show list of all names currently stored player names database                     **
**                  : Note that the database is updated every time an in-game /who occurs               **
** Pets                                                                                                 **
**   .pet           : Show information about current pet                                                **
**   .pt            : Toggle pet tracking on/off                                                        **
** Combat                                                                                               **
**   .ct            : Toggle combat damage tracking on/off                                              **
**   .cto           : Show current value for how many seconds until combat times out                    **
** Death Loops                                                                                          **
**   .dlt           : Toggle death loop tracking on/off                                                 **
**   .dl            : Show death loop parameters                                                        **
**   .deathloop     : Simulate a death, for testing                                                     **
** Randoms                                                                                              **
**   .rt            : Toggle combat damage tracking on/off                                              **
**   .rolls         : Show a summary of all random groups, including their index values N               **
**   .roll          : Show a detailed list of all rolls from the LAST random group                      **
**   .roll.N        : Show a detailed list of all rolls from random event group N                       **
**   .win           : Show default window (seconds) for grouping of randoms                             **
**   .win.W         : Set the default grouping window to W seconds                                      **
**   .win.N.W       : Change group N to new grouping window W seconds                                   **
**                  : All rolls are retained, and groups are combined or split up as necessary          **
** LogEvent Parsing                                                                                     **
**   .log           : Show a summary of all LogEvents and their parsing status (True/False)             **
**                                                                                                      **
** Examples:                                                                                            **
**   /t .rolls      : Summary of all random groups                                                      **
**   /t .roll       : Detailed report for the most recent random group                                  **
**   /t .roll.12    : Detailed report for random group index [12]                                       **
**   /t .win.20     : Change the default grouping window to 20 seconds                                  **
**   /t .win.8.30   : Change group [8] to new grouping window to 30 seconds                             **
**                                                                                                      **
** **************************************************************************************************** **
**                                                                                                      **
** ---------------------------------------Combat begun: [Saadez]--------------------------------------- **
**                                         (melee event vs mob)                                         **
** ----------------------------------Combat begun: [myconid warrior]----------------------------------- **
**                                         (melee event vs mob)                                         **
** ----------------------------------------Combat begun: [Fria]---------------------------------------- **
**                                         (melee event vs mob)                                         **
** --------------------------------------Combat begun: [Grendol]--------------------------------------- **
**                                         (melee event vs mob)                                         **
** --------------------------------Combat begun: [froglok krup knight]--------------------------------- **
**                                         (melee event vs mob)                                         **


====================================================================================================
Damage Report, Target: **myconid warrior**
Implied Level: 0.0
Combat Duration (sec): 30
Damage To:

                        Grand Total:     0 (100%) (@0.0 dps)
....................................................................................................
Damage By:
        Froglok krup knight
                               hits:  4107
                             bashes:    72
                              Total:  4179 (36%) (@139.3 dps)
        Mamasan
                          backstabs:  1418
                            pierces:  1064
                            slashes:   427
                              Total:  2909 (25%) (@97.0 dps)
        Grendol
                            slashes:  1526
                            pierces:   247
                              kicks:    32
                            punches:     2
                              Total:  1807 (16%) (@60.2 dps)
        Calyenta
                            pierces:  1184
                          backstabs:   119
                              Total:  1303 (11%) (@43.4 dps)
        Zarobab
                            pierces:  1140
                             bashes:    52
                              Total:  1192 (10%) (@39.7 dps)
        Saadez
                              kicks:   175
                            punches:    58
                              Total:   233 (2%) (@7.8 dps)

                        Grand Total: 11623 (100%) (@387.4 dps)
====================================================================================================

** Random:        Calyenta | Value:    10 | Range: [    0-  222] | 2022-01-14 00:34:05 |                **
**                                                                                 (0-222): Calyenta/10 **
** Random:          Azleep | Value:    61 | Range: [    0-  222] | 2022-01-14 00:34:08 |                **
**                                                                                   (0-222): Azleep/61 **
** Random:            Fria | Value:    26 | Range: [    0-  222] | 2022-01-14 00:34:11 |                **
**                                                                                   (0-222): Azleep/61 **
** Random:         Klearic | Value:   177 | Range: [    0-  222] | 2022-01-14 00:34:25 |                **
**                                                                                 (0-222): Klearic/177 **
** -----------------------------------Combat begun: [myconid adept]------------------------------------ **
**                                         (melee event vs mob)                                         **


Group Index: [0]....................................................................................
Range: [0-222] | Rolls: 4 | Start Time: 2022-01-14 00:34:05 | Delta (seconds): 20
       Calyenta | Value:    10 | Range: [    0-  222] | 2022-01-14 00:34:05 | 00:00 |
         Azleep | Value:    61 | Range: [    0-  222] | 2022-01-14 00:34:08 | 00:03 |
           Fria | Value:    26 | Range: [    0-  222] | 2022-01-14 00:34:11 | 00:06 |
        Klearic | Value:   177 | Range: [    0-  222] | 2022-01-14 00:34:25 | 00:20 | *HIGH*
Winner(s):
        Klearic | Value:   177 | Range: [    0-  222] | 2022-01-14 00:34:25 | *HIGH*



====================================================================================================
Damage Report, Target: **myconid adept**
Implied Level: 0.0
Combat Duration (sec): 42
Damage To:

                        Grand Total:     0 (100%) (@0.0 dps)
....................................................................................................
Damage By:
        Mamasan
                          backstabs:  1727
                            pierces:  1176
                            slashes:   636
                              Total:  3539 (30%) (@84.3 dps)
        Grendol
                            slashes:  1512
                            pierces:   922
                              kicks:    51
                              Total:  2485 (21%) (@59.2 dps)
        Froglok krup knight
                               hits:  2209
                             bashes:    72
                              kicks:    42
                              Total:  2323 (20%) (@55.3 dps)
        Calyenta
                            pierces:  1419
                          backstabs:   523
                              Total:  1942 (17%) (@46.2 dps)
        Zarobab
                            pierces:  1280
                             bashes:    75
                              Total:  1355 (12%) (@32.3 dps)

                        Grand Total: 11644 (100%) (@277.2 dps)
====================================================================================================

** ----------------------------------Combat begun: [myconid warrior]----------------------------------- **
**                                         (melee event vs mob)                                         **
** --------------------------------------Combat begun: [Calyenta]-------------------------------------- **
**                                         (melee event vs mob)                                         **
** Combat vs Fria: Timed out                                                                            **


====================================================================================================
Damage Report, Target: **Fria**
Implied Level: 0.0
Combat Duration (sec): 121
Damage To:

                        Grand Total:     0 (100%) (@0.0 dps)
....................................................................................................
Damage By:
        Myconid warrior
                             bashes:    50
                              Total:    50 (100%) (@0.4 dps)

                        Grand Total:    50 (100%) (@0.4 dps)
====================================================================================================

** --------------------------------------Combat begun: [Klearic]--------------------------------------- **
**                                         (melee event vs mob)                                         **


====================================================================================================
Damage Report, Target: **myconid warrior**
Implied Level: 0.0
Combat Duration (sec): 33
Damage To:

                        Grand Total:     0 (100%) (@0.0 dps)
....................................................................................................
Damage By:
        Froglok krup knight
                               hits:  4224
                              kicks:    44
                             bashes:    44
                              Total:  4312 (36%) (@130.7 dps)
        Mamasan
                            pierces:  1164
                          backstabs:   520
                            slashes:   444
                              Total:  2128 (18%) (@64.5 dps)
        Calyenta
                            pierces:  1320
                          backstabs:   401
                              Total:  1721 (14%) (@52.2 dps)
        Zarobab
                            pierces:  1588
                              kicks:    45
                             bashes:    23
                              Total:  1656 (14%) (@50.2 dps)
        Grendol
                            slashes:   790
                            pierces:   397
                              kicks:    54
                             bashes:    15
                              Total:  1256 (10%) (@38.1 dps)
        Saadez
                            punches:   781
                            crushes:   246
                              Total:  1027 (8%) (@31.1 dps)

                        Grand Total: 12100 (100%) (@366.7 dps)
====================================================================================================

** --------------------------------Combat begun: [froglok ilis knight]--------------------------------- **
**                                         (melee event vs mob)                                         **
** ----------------------------------------Combat begun: [Fria]---------------------------------------- **
**                                         (melee event vs mob)                                         **


====================================================================================================
Damage Report, Target: **froglok ilis knight**
Implied Level: 53.0
Combat Duration (sec): 35
Damage To:
        YOU
                               hits:   152
                             bashes:    48
                              Total:   200 (84%) (@5.7 dps)
        Zarobab
                               hits:    38
                              Total:    38 (16%) (@1.1 dps)

                        Grand Total:   238 (100%) (@6.8 dps)
....................................................................................................
Damage By:
        Froglok krup knight
                               hits:  4473
                             bashes:   121
                              Total:  4594 (38%) (@131.3 dps)
        Grendol
                            slashes:  1404
                            pierces:   650
                              kicks:    49
                              Total:  2103 (17%) (@60.1 dps)
        Mamasan
                          backstabs:   718
                            pierces:   543
                            slashes:   330
                              Total:  1591 (13%) (@45.5 dps)
        Zarobab
                            pierces:  1383
                              kicks:    96
                             bashes:    45
                              Total:  1524 (13%) (@43.5 dps)
        Calyenta
                            pierces:   842
                          backstabs:   413
                              Total:  1255 (10%) (@35.9 dps)
        Saadez
                            punches:   613
                            crushes:   406
                              kicks:    71
                              Total:  1090 (9%) (@31.1 dps)
        Unknown
                          non-melee:    20
                              Total:    20 (0%) (@0.6 dps)

                        Grand Total: 12177 (100%) (@347.9 dps)
====================================================================================================

** -----------------------------------Combat begun: [myconid adept]------------------------------------ **
**                                         (melee event vs mob)                                         **
** --------------------------------------Combat begun: [Mamasan]--------------------------------------- **
**                                         (melee event vs mob)                                         **


====================================================================================================
Damage Report, Target: **myconid adept**
Implied Level: 54.0
Combat Duration (sec): 33
Damage To:
        YOU
                               hits:   272
                              Total:   272 (100%) (@8.2 dps)

                        Grand Total:   272 (100%) (@8.2 dps)
....................................................................................................
Damage By:
        Froglok krup knight
                               hits:  4699
                             bashes:   109
                              kicks:    77
                              Total:  4885 (37%) (@148.0 dps)
        Grendol
                            slashes:  1401
                            pierces:   694
                              kicks:    55
                              Total:  2150 (16%) (@65.2 dps)
        Calyenta
                            pierces:  1309
                          backstabs:   675
                              Total:  1984 (15%) (@60.1 dps)
        Mamasan
                            pierces:  1061
                            slashes:   553
                          backstabs:   345
                              Total:  1959 (15%) (@59.4 dps)
        Zarobab
                            pierces:  1326
                             bashes:    49
                              Total:  1375 (10%) (@41.7 dps)
        Saadez
                            punches:   466
                            crushes:   393
                              kicks:   100
                              Total:   959 (7%) (@29.1 dps)
        Unknown
                          non-melee:    20
                              Total:    20 (0%) (@0.6 dps)

                        Grand Total: 13332 (100%) (@404.0 dps)
====================================================================================================

** Combat vs Klearic: Timed out                                                                         **


====================================================================================================
Damage Report, Target: **Klearic**
Implied Level: 0.0
Combat Duration (sec): 161
Damage To:

                        Grand Total:     0 (100%) (@0.0 dps)
....................................................................................................
Damage By:
        Froglok ilis knight
                               hits:   456
                              Total:   456 (68%) (@2.8 dps)
        Myconid adept
                               hits:   156
                             bashes:    60
                              Total:   216 (32%) (@1.3 dps)

                        Grand Total:   672 (100%) (@4.2 dps)
====================================================================================================

** Combat vs Saadez: Timed out                                                                          **


====================================================================================================
Damage Report, Target: **Saadez**
Implied Level: 0.0
Combat Duration (sec): 307
Damage To:

                        Grand Total:     0 (100%) (@0.0 dps)
....................................................................................................
Damage By:
        Myconid warrior
                               hits:   661
                              Total:   661 (43%) (@2.2 dps)
        Myconid adept
                               hits:   567
                             bashes:    52
                              Total:   619 (40%) (@2.0 dps)
        Froglok ilis knight
                               hits:   226
                             bashes:    43
                              Total:   269 (17%) (@0.9 dps)

                        Grand Total:  1549 (100%) (@5.0 dps)
====================================================================================================

** Combat vs Fria: Timed out                                                                            **


====================================================================================================
Damage Report, Target: **Fria**
Implied Level: 0.0
Combat Duration (sec): 133
Damage To:

                        Grand Total:     0 (100%) (@0.0 dps)
....................................................................................................
Damage By:
        Myconid adept
                               hits:   611
                             bashes:    57
                              Total:   668 (100%) (@5.0 dps)

                        Grand Total:   668 (100%) (@5.0 dps)
====================================================================================================

** -----------------------------------Combat begun: [myconid priest]----------------------------------- **
**                                         (melee event vs mob)                                         **
** Combat vs froglok krup knight: Timed out                                                             **


====================================================================================================
Damage Report, Target: **froglok krup knight**
Implied Level: 51.0
Combat Duration (sec): 277
Damage To:
        YOU
                               hits:  1235
                              kicks:    37
                              Total:  1272 (100%) (@4.6 dps)

                        Grand Total:  1272 (100%) (@4.6 dps)
....................................................................................................
Damage By:
        Froglok ilis knight
                               hits:   232
                              Total:   232 (43%) (@0.8 dps)
        Myconid warrior
                               hits:   188
                              Total:   188 (35%) (@0.7 dps)
        Unknown
                          non-melee:   120
                              Total:   120 (22%) (@0.4 dps)

                        Grand Total:   540 (100%) (@1.9 dps)
====================================================================================================

** Combat vs Mamasan: Timed out                                                                         **


====================================================================================================
Damage Report, Target: **Mamasan**
Implied Level: 0.0
Combat Duration (sec): 125
Damage To:

                        Grand Total:     0 (100%) (@0.0 dps)
....................................................................................................
Damage By:
        Myconid adept
                               hits:   477
                              Total:   477 (100%) (@3.8 dps)

                        Grand Total:   477 (100%) (@3.8 dps)
====================================================================================================

** Combat vs Calyenta: Timed out                                                                        **


====================================================================================================
Damage Report, Target: **Calyenta**
Implied Level: 0.0
Combat Duration (sec): 205
Damage To:

                        Grand Total:     0 (100%) (@0.0 dps)
....................................................................................................
Damage By:
        Myconid adept
                               hits:   111
                             bashes:    59
                              Total:   170 (52%) (@0.8 dps)
        Myconid warrior
                               hits:   156
                              Total:   156 (48%) (@0.8 dps)

                        Grand Total:   326 (100%) (@1.6 dps)
====================================================================================================



====================================================================================================
Damage Report, Target: **myconid priest**
Implied Level: 54.0
Combat Duration (sec): 35
Damage To:
        YOU
                               hits:   482
                             bashes:    55
                              Total:   537 (100%) (@15.3 dps)

                        Grand Total:   537 (100%) (@15.3 dps)
....................................................................................................
Damage By:
        Froglok krup knight
                               hits:  4972
                              kicks:    44
                             bashes:    37
                              Total:  5053 (40%) (@144.4 dps)
        Mamasan
                          backstabs:  1490
                            pierces:   793
                            slashes:   377
                              Total:  2660 (21%) (@76.0 dps)
        Grendol
                            slashes:  1589
                            pierces:   628
                              kicks:    34
                              Total:  2251 (18%) (@64.3 dps)
        Calyenta
                            pierces:  1068
                          backstabs:   363
                              Total:  1431 (11%) (@40.9 dps)
        Zarobab
                            pierces:  1029
                              kicks:    53
                             bashes:    27
                              Total:  1109 (9%) (@31.7 dps)
        Unknown
                          non-melee:    60
                              Total:    60 (0%) (@1.7 dps)

                        Grand Total: 12564 (100%) (@359.0 dps)
====================================================================================================

** ---------------------------------------Combat begun: [Saadez]--------------------------------------- **
**                                         (melee event vs mob)                                         **
** ----------------------------------Combat begun: [myconid warrior]----------------------------------- **
**                                         (melee event vs mob)                                         **
** ----------------------------------------Combat begun: [Fria]---------------------------------------- **
**                                         (melee event vs mob)                                         **
** --------------------------------Combat begun: [froglok krup knight]--------------------------------- **
**                                         (melee event vs mob)                                         **


====================================================================================================
Damage Report, Target: **myconid warrior**
Implied Level: 0.0
Combat Duration (sec): 28
Damage To:

                        Grand Total:     0 (100%) (@0.0 dps)
....................................................................................................
Damage By:
        Froglok krup knight
                               hits:  4024
                             bashes:   116
                              kicks:    38
                              Total:  4178 (40%) (@149.2 dps)
        Grendol
                            slashes:  1261
                            pierces:   591
                              kicks:    53
                              Total:  1905 (18%) (@68.0 dps)
        Zarobab
                            pierces:  1563
                             bashes:    70
                              kicks:    27
                              Total:  1660 (16%) (@59.3 dps)
        Mamasan
                            pierces:   648
                          backstabs:   597
                            slashes:   351
                              Total:  1596 (15%) (@57.0 dps)
        Calyenta
                            pierces:   724
                          backstabs:   156
                              Total:   880 (8%) (@31.4 dps)
        Saadez
                            punches:   172
                            crushes:   130
                              Total:   302 (3%) (@10.8 dps)

                        Grand Total: 10521 (100%) (@375.8 dps)
====================================================================================================

** -----------------------------------Combat begun: [myconid reaver]----------------------------------- **
**                                         (melee event vs mob)                                         **


====================================================================================================
Damage Report, Target: **myconid reaver**
Implied Level: 0.0
Combat Duration (sec): 40
Damage To:

                        Grand Total:     0 (100%) (@0.0 dps)
....................................................................................................
Damage By:
        Froglok krup knight
                               hits:  4460
                             bashes:    81
                              Total:  4541 (35%) (@113.5 dps)
        Mamasan
                          backstabs:  1704
                            pierces:  1000
                            slashes:   605
                              Total:  3309 (25%) (@82.7 dps)
        Grendol
                            slashes:  1577
                            pierces:   681
                              kicks:    29
                              Total:  2287 (18%) (@57.2 dps)
        Calyenta
                            pierces:  1171
                          backstabs:   389
                              Total:  1560 (12%) (@39.0 dps)
        Zarobab
                            pierces:  1119
                              kicks:    54
                             bashes:    27
                              Total:  1200 (9%) (@30.0 dps)
        Saadez
                            punches:    53
                            crushes:    39
                              Total:    92 (1%) (@2.3 dps)

                        Grand Total: 12989 (100%) (@324.7 dps)
====================================================================================================

** ---------------------------------------Combat begun: [Yober]---------------------------------------- **
**                                         (melee event vs mob)                                         **
** -----------------------------------Combat begun: [myconid reaver]----------------------------------- **
**                                         (melee event vs mob)                                         **
** Combat vs Fria: Timed out                                                                            **


====================================================================================================
Damage Report, Target: **Fria**
Implied Level: 0.0
Combat Duration (sec): 121
Damage To:

                        Grand Total:     0 (100%) (@0.0 dps)
....................................................................................................
Damage By:
        Myconid warrior
                               hits:   150
                              Total:   150 (100%) (@1.2 dps)

                        Grand Total:   150 (100%) (@1.2 dps)
====================================================================================================



====================================================================================================
Damage Report, Target: **myconid reaver**
Implied Level: 0.0
Combat Duration (sec): 40
Damage To:

                        Grand Total:     0 (100%) (@0.0 dps)
....................................................................................................
Damage By:
        Froglok krup knight
                               hits:  4130
                              kicks:   116
                             bashes:    81
                              Total:  4327 (32%) (@108.2 dps)
        Mamasan
                          backstabs:  1658
                            pierces:  1043
                            slashes:   534
                              Total:  3235 (24%) (@80.9 dps)
        Grendol
                            slashes:  1363
                            pierces:   539
                              kicks:    35
                              Total:  1937 (14%) (@48.4 dps)
        Zarobab
                            pierces:  1697
                              kicks:   112
                             bashes:    78
                              Total:  1887 (14%) (@47.2 dps)
        Calyenta
                            pierces:  1139
                          backstabs:   214
                              Total:  1353 (10%) (@33.8 dps)
        Saadez
                            punches:   415
                            crushes:   237
                              Total:   652 (5%) (@16.3 dps)

                        Grand Total: 13391 (100%) (@334.8 dps)
====================================================================================================

** Combat vs Saadez: Timed out                                                                          **


====================================================================================================
Damage Report, Target: **Saadez**
Implied Level: 0.0
Combat Duration (sec): 162
Damage To:

                        Grand Total:     0 (100%) (@0.0 dps)
....................................................................................................
Damage By:
        Myconid warrior
                               hits:   136
                              Total:   136 (52%) (@0.8 dps)
        Myconid reaver
                               hits:   126
                              Total:   126 (48%) (@0.8 dps)

                        Grand Total:   262 (100%) (@1.6 dps)
====================================================================================================

** -----------------------------------Combat begun: [myconid reaver]----------------------------------- **
**                                         (melee event vs mob)                                         **
** ---------------------------------------Combat begun: [Saadez]--------------------------------------- **
**                                         (melee event vs mob)                                         **


====================================================================================================
Damage Report, Target: **myconid reaver**
Implied Level: 0.0
Combat Duration (sec): 53
Damage To:

                        Grand Total:     0 (100%) (@0.0 dps)
....................................................................................................
Damage By:
        Mamasan
                            pierces:  1758
                          backstabs:  1738
                            slashes:   647
                              Total:  4143 (30%) (@78.2 dps)
        Froglok krup knight
                               hits:  2689
                              kicks:    41
                             bashes:    36
                              Total:  2766 (20%) (@52.2 dps)
        Calyenta
                            pierces:  1857
                          backstabs:   511
                              Total:  2368 (17%) (@44.7 dps)
        Grendol
                            slashes:  1229
                            pierces:   546
                              kicks:    49
                              Total:  1824 (13%) (@34.4 dps)
        Zarobab
                            pierces:  1244
                              kicks:    22
                             bashes:    20
                              Total:  1286 (9%) (@24.3 dps)
        Saadez
                            punches:   838
                            crushes:   431
                              Total:  1269 (9%) (@23.9 dps)

                        Grand Total: 13656 (100%) (@257.7 dps)
====================================================================================================

** --------------------------------Combat begun: [froglok ilis shaman]--------------------------------- **
**                                         (melee event vs mob)                                         **
** Combat vs Yober: Timed out                                                                           **


====================================================================================================
Damage Report, Target: **Yober**
Implied Level: 0.0
Combat Duration (sec): 121
Damage To:

                        Grand Total:     0 (100%) (@0.0 dps)
....................................................................................................
Damage By:
        Myconid reaver
                               hits:   312
                              Total:   312 (100%) (@2.6 dps)

                        Grand Total:   312 (100%) (@2.6 dps)
====================================================================================================

** --------------------------------------Combat begun: [Klearic]--------------------------------------- **
**                                         (melee event vs mob)                                         **
** ----------------------------------------Combat begun: [Fria]---------------------------------------- **
**                                         (melee event vs mob)                                         **


====================================================================================================
Damage Report, Target: **froglok ilis shaman**
Implied Level: 53.0
Combat Duration (sec): 47
Damage To:
        YOU
                               hits:   152
                              Total:   152 (100%) (@3.2 dps)

                        Grand Total:   152 (100%) (@3.2 dps)
....................................................................................................
Damage By:
        Froglok krup knight
                               hits:  5476
                             bashes:   153
                              Total:  5629 (46%) (@119.8 dps)
        Grendol
                            slashes:  1826
                            pierces:   486
                             bashes:    46
                              kicks:    28
                              Total:  2386 (19%) (@50.8 dps)
        Calyenta
                            pierces:  1393
                          backstabs:   200
                              Total:  1593 (13%) (@33.9 dps)
        Mamasan
                          backstabs:   562
                            pierces:   521
                            slashes:   303
                              Total:  1386 (11%) (@29.5 dps)
        Saadez
                            punches:   749
                            crushes:   406
                              kicks:    77
                              Total:  1232 (10%) (@26.2 dps)
        Unknown
                          non-melee:    10
                              Total:    10 (0%) (@0.2 dps)

                        Grand Total: 12236 (100%) (@260.3 dps)
====================================================================================================

** -----------------------------------Combat begun: [myconid priest]----------------------------------- **
**                                         (melee event vs mob)                                         **


====================================================================================================
Damage Report, Target: **myconid priest**
Implied Level: 0.0
Combat Duration (sec): 35
Damage To:

                        Grand Total:     0 (100%) (@0.0 dps)
....................................................................................................
Damage By:
        Froglok krup knight
                               hits:  4564
                              kicks:    34
                             bashes:    34
                              Total:  4632 (39%) (@132.3 dps)
        Mamasan
                          backstabs:  1563
                            pierces:  1031
                            slashes:   681
                              Total:  3275 (27%) (@93.6 dps)
        Grendol
                            slashes:  1306
                            pierces:   661
                              kicks:    68
                             bashes:     2
                              Total:  2037 (17%) (@58.2 dps)
        Calyenta
                            pierces:   857
                          backstabs:   175
                              Total:  1032 (9%) (@29.5 dps)
        Genann
                               hits:   911
                             bashes:    54
                              kicks:    25
                              Total:   990 (8%) (@28.3 dps)

                        Grand Total: 11966 (100%) (@341.9 dps)
====================================================================================================

** Combat vs froglok krup knight: Timed out                                                             **


====================================================================================================
Damage Report, Target: **froglok krup knight**
Implied Level: 0.0
Combat Duration (sec): 337
Damage To:

                        Grand Total:     0 (100%) (@0.0 dps)
....................................................................................................
Damage By:
        Myconid reaver
                               hits:   757
                              Total:   757 (56%) (@2.2 dps)
        Froglok ilis shaman
                               hits:   384
                              Total:   384 (29%) (@1.1 dps)
        Myconid warrior
                               hits:   200
                              Total:   200 (15%) (@0.6 dps)

                        Grand Total:  1341 (100%) (@4.0 dps)
====================================================================================================

** Combat vs Saadez: Timed out                                                                          **


====================================================================================================
Damage Report, Target: **Saadez**
Implied Level: 0.0
Combat Duration (sec): 181
Damage To:

                        Grand Total:     0 (100%) (@0.0 dps)
....................................................................................................
Damage By:
        Myconid reaver
                               hits:  1356
                              Total:  1356 (74%) (@7.5 dps)
        Froglok ilis shaman
                               hits:   478
                              Total:   478 (26%) (@2.6 dps)

                        Grand Total:  1834 (100%) (@10.1 dps)
====================================================================================================

** Combat vs Klearic: Timed out                                                                         **


====================================================================================================
Damage Report, Target: **Klearic**
Implied Level: 0.0
Combat Duration (sec): 129
Damage To:

                        Grand Total:     0 (100%) (@0.0 dps)
....................................................................................................
Damage By:
        Froglok ilis shaman
                               hits:   304
                              Total:   304 (100%) (@2.4 dps)

                        Grand Total:   304 (100%) (@2.4 dps)
====================================================================================================

** Combat vs Fria: Timed out                                                                            **


====================================================================================================
Damage Report, Target: **Fria**
Implied Level: 0.0
Combat Duration (sec): 123
Damage To:

                        Grand Total:     0 (100%) (@0.0 dps)
....................................................................................................
Damage By:
        Froglok ilis shaman
                               hits:   100
                              Total:   100 (100%) (@0.8 dps)

                        Grand Total:   100 (100%) (@0.8 dps)
====================================================================================================

** -----------------------------------Combat begun: [myconid reaver]----------------------------------- **
**                                         (melee event vs mob)                                         **
** ---------------------------------------Combat begun: [Saadez]--------------------------------------- **
**                                         (melee event vs mob)                                         **
** ----------------------------------------Combat begun: [Fria]---------------------------------------- **
**                                         (melee event vs mob)                                         **


====================================================================================================
Damage Report, Target: **myconid reaver**
Implied Level: 0.0
Combat Duration (sec): 38
Damage To:

                        Grand Total:     0 (100%) (@0.0 dps)
....................................................................................................
Damage By:
        Froglok krup knight
                               hits:  4159
                             bashes:   196
                              kicks:    44
                              Total:  4399 (32%) (@115.8 dps)
        Mamasan
                          backstabs:  1168
                            pierces:   971
                            slashes:   931
                              Total:  3070 (22%) (@80.8 dps)
        Grendol
                            slashes:  1440
                            pierces:   623
                              kicks:    53
                              Total:  2116 (15%) (@55.7 dps)
        Calyenta
                            pierces:  1441
                          backstabs:   541
                              Total:  1982 (14%) (@52.2 dps)
        Genann
                               hits:  1397
                             bashes:    19
                              Total:  1416 (10%) (@37.3 dps)
        Saadez
                            punches:   527
                            crushes:   260
                              Total:   787 (6%) (@20.7 dps)

                        Grand Total: 13770 (100%) (@362.4 dps)
====================================================================================================

** --------------------------------Combat begun: [froglok ilis shaman]--------------------------------- **
**                                         (melee event vs mob)                                         **
** ---------------------------------------Combat begun: [Yober]---------------------------------------- **
**                                         (melee event vs mob)                                         **


====================================================================================================
Damage Report, Target: **froglok ilis shaman**
Implied Level: 0.0
Combat Duration (sec): 34
Damage To:

                        Grand Total:     0 (100%) (@0.0 dps)
....................................................................................................
Damage By:
        Froglok krup knight
                               hits:  4050
                              Total:  4050 (36%) (@119.1 dps)
        Genann
                               hits:  2256
                              kicks:    47
                             bashes:    41
                              Total:  2344 (21%) (@68.9 dps)
        Grendol
                            slashes:  1299
                            pierces:   777
                              kicks:   102
                              Total:  2178 (19%) (@64.1 dps)
        Mamasan
                            pierces:   821
                          backstabs:   470
                            slashes:   459
                              Total:  1750 (16%) (@51.5 dps)
        Calyenta
                            pierces:   810
                          backstabs:    78
                              Total:   888 (8%) (@26.1 dps)

                        Grand Total: 11210 (100%) (@329.7 dps)
====================================================================================================

** --------------------------------Combat begun: [froglok krup knight]--------------------------------- **
**                                          (non-melee event)                                           **
** Player Zoned                                                                                         **


====================================================================================================
Damage Report, Target: **Grendol**
Implied Level: 0.0
Combat Duration (sec): 873
Damage To:

                        Grand Total:     0 (100%) (@0.0 dps)
....................................................................................................
Damage By:
        Myconid reaver
                               hits:  4262
                            crushes:   854
                              kicks:   217
                             bashes:   212
                              Total:  5545 (55%) (@6.4 dps)
        Myconid priest
                               hits:  1478
                             bashes:   224
                              Total:  1702 (17%) (@1.9 dps)
        Myconid warrior
                               hits:  1182
                             bashes:   155
                              Total:  1337 (13%) (@1.5 dps)
        Myconid adept
                               hits:   986
                             bashes:    50
                              Total:  1036 (10%) (@1.2 dps)
        Froglok ilis knight
                               hits:   246
                              Total:   246 (2%) (@0.3 dps)
        Froglok ilis shaman
                               hits:   144
                              Total:   144 (1%) (@0.2 dps)

                        Grand Total: 10010 (100%) (@11.5 dps)
====================================================================================================



====================================================================================================
Damage Report, Target: **Saadez**
Implied Level: 0.0
Combat Duration (sec): 111
Damage To:

                        Grand Total:     0 (100%) (@0.0 dps)
....................................................................................................
Damage By:
        Froglok ilis shaman
                               hits:   152
                              Total:   152 (100%) (@1.4 dps)

                        Grand Total:   152 (100%) (@1.4 dps)
====================================================================================================



====================================================================================================
Damage Report, Target: **Fria**
Implied Level: 0.0
Combat Duration (sec): 105
Damage To:

                        Grand Total:     0 (100%) (@0.0 dps)
....................................................................................................
Damage By:
        Froglok ilis shaman
                               hits:   130
                              Total:   130 (100%) (@1.2 dps)

                        Grand Total:   130 (100%) (@1.2 dps)
====================================================================================================



====================================================================================================
Damage Report, Target: **Yober**
Implied Level: 0.0
Combat Duration (sec): 96
Damage To:

                        Grand Total:     0 (100%) (@0.0 dps)
....................................................................................................
Damage By:
        Froglok ilis shaman
                               hits:   152
                              Total:   152 (100%) (@1.6 dps)

                        Grand Total:   152 (100%) (@1.6 dps)
====================================================================================================



====================================================================================================
Damage Report, Target: **froglok krup knight**
Implied Level: 51.0
Combat Duration (sec): 46
Damage To:
        YOU
                               hits:   899
                              kicks:    37
                              Total:   936 (100%) (@20.3 dps)

                        Grand Total:   936 (100%) (@20.3 dps)
....................................................................................................
Damage By:
        Unknown
                          non-melee:    90
                              Total:    90 (100%) (@2.0 dps)

                        Grand Total:    90 (100%) (@2.0 dps)
====================================================================================================
