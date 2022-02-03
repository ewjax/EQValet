# eqvalet

A discord bot that provides several helper functions for Everquest:

**_random rolls_**
  - 
  - all rolls with matching lower and upper values, that occur within a 30 second window (default), are grouped, and winner(s) identified
  - default 30 second window can be adjusted up or down.  This will cause random rolls to be regrouped as necessary.
  - ability to declare either the upper or lower value as "not significant", to allow for schemes where some players get bonuses on their randoms.
    - Example:  Perhaps the standard random for an event/item is 0-1000, and perhaps players are afforded a +100 bonus to their lower value for every time they random on that particular event/item but do not win.
      - /random 0 1000 (for normal odds)
      - /random 100 1000 (for players with one roll bonus)
      - /random 200 1000 (for players with two roll bonuses)

**_pet tracker_**
-
  - determines pet level / rank (max pet, or otherwise) by parsing max melee damage, and/or by the pet's lifetap values

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
      
 
