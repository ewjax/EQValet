# eqvalet

A discord bot that provides several helper functions for Everquest:
  - tracks random rolls
  - tracks pets by their max hit damage output, and reports the associated pet ranks
  - melee and DOT dps tracker.  The main use is intended to allow the soloing pet class to determine if their pet is doing more or less than 50% of the total damage.
      o Tracks melee damage explicitly via damage messages, and 
      o Tracks DOT damage implicitly, by watching for spell landed messages and doing the math to report how much DOT damage was done
      
 
