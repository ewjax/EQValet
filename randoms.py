
# import the datetime class from the datetime module
from datetime import datetime


#
# class for a single random roll by a particular player
#
# keep track of player names, the random range (low, high), the actual random roll value, and the timestamp of the roll
#
class PlayerRandomRoll:

    # ctor
    # the eq_timestamp must at least include the leading [0:26] time stamp characters from the log file line, or it can also just be the entire line
    def __init__(self, player_name, random_value, low, high, eq_timestamp):

        self.player_name    = player_name
        self.random_value   = random_value
        self.low            = low
        self.high           = high

        # create a datetime object, using the very capable strptime() parsing function built into the datetime module
        self.time_stamp     = datetime.strptime(eq_timestamp[0:26], '[%a %b %d %H:%M:%S %Y]')

    # overload funciton to allow object to print() to screen in sensible manner, for debugging with print()
    def __repr__(self):
        return ('({}, {}, {}, {}, {})'.format(self.player_name, self.random_value, self.low, self.high, self.time_stamp))
    
    # to make bold text in a Discord message, surround it with double asterisks, i.e. **Example**
    def report(self, boldname = ''):

        rv = ''
        if self.player_name == boldname:
            rv += '**'

        rv += '--Player: {} | Roll: {} | Time: {}\n'.format(self.player_name, self.random_value, self.time_stamp)

        if self.player_name == boldname:
            rv += '**'

        return rv






# class for many random rolls, to find random winners etc
#
# every roll in the list must:
#   - have same range (low, high)
#   - must be within the delta_seconds time span
#   - presumption is that rolls are added in time-sequential order, so the first roll to be added is assumed to be the 
#     starting time, and all other rolls must occur within the (starting time + delta_seconds) window
#   - players can only random once.  any subsequent random will not be added to the RandomList
#
class RandomEvent:

    # ctor
    def __init__(self, low, high, delta_seconds = 30):

        self.low                = low
        self.high               = high
        self.delta_seconds      = delta_seconds

        self.rolls              = list()
        self.start_time_stamp   = None

        # flag to indicate whether this list is open for adding rolls
        self.expired            = False


    def report_header(self, ndx = -1):
        rv = '[Index {}]: ==============================================================\n'.format(ndx)
        rv += 'Range: [{}-{}] | Rolls: {} | Start Time: {} | Delta (seconds): {}\n'.format(self.low, self.high, len(self.rolls), self.start_time_stamp, self.delta_seconds)
        return rv

    def report_winner(self, boldname = ''):
        rv = 'Winner(s):\n'
        for r in self.winner():
            rv += r.report(boldname)
        return rv

    def report_summary(self, ndx = -1, boldname = ''):
        rv = self.report_header(ndx)
        rv += self.report_winner(boldname)
        return rv

    # overload funciton to allow object to print() to screen in sensible manner, for debugging with print()
    def __repr__(self):
        rv = self.report_header()
        for r in self.rolls:
            rv += r.report()
        return rv


    # does this list need to expire?  check timestamp of the passed line vs the delta window of this RandomEvent
    # returns True if this list toggles from NotExpired to Expired
    def check_expiration(self, line):

        rv = False

        # currently not expired...
        if (self.expired == False):
            # ...and there is at least 1 roll in the list...
            if (len(self.rolls) > 0):
                # ...and the time stamp of the passed line parameter is outside the RandomEvent window duration...
                try:
                    check_time = datetime.strptime(line[0:26], '[%a %b %d %H:%M:%S %Y]')
                    elapsed_seconds = check_time - self.start_time_stamp
                    if (elapsed_seconds.total_seconds() > self.delta_seconds):
                        # ...then this RandomEvent is expired
                        self.expired = True
                        self.sort_descending_randoms()
                        rv = True
                except ValueError:
                    return False

        # return
        return rv



    #
    # add a roll to the list
    # return True if roll is added, False if not added
    #
    def add_roll(self, r):

        rv = False

        # check if the random low and high limits match
        if (r.low == self.low) and (r.high == self.high):

            # the assumption is these will be loaded in sequential, time-increasing order, i.e. the first one is the starting time for the random window
            if len(self.rolls) == 0:
                self.start_time_stamp = r.time_stamp

            # check if the timestamp to be added is in range
            elapsed_seconds = r.time_stamp - self.start_time_stamp
            if (elapsed_seconds.total_seconds() <= self.delta_seconds):

                # check that this person hasn't already randomed
                if (self.player_roll(r.player_name) == None):
                    self.rolls.append(r)
                    rv = True

        # true if added, false otherwise
        return rv

    # sort the rolls in descending order, so high roll(s) is at start of list
    def sort_descending_randoms(self):
        self.rolls.sort(key = lambda x: x.random_value, reverse = True)

    # sort the rolls in ascending time order
    def sort_ascending_timestamps(self):
        self.rolls.sort(key = lambda x: x.time_stamp)


    # return high roll(s) in a list()
    def winner(self):
        # get high roll to start of list and save the value
        self.sort_descending_randoms()
        high_roll = self.rolls[0].random_value

        # since there could be ties, add all high rolls to a list
        rv = list()
        for elem in self.rolls:
            if elem.random_value == high_roll:
                rv.append(elem)

        # return list of high roll(s)
        return rv


    # walk the list and return the roll for a particular player
    # not particularly efficient since it just brute force visits every member in the list, but the number of rollers is really never that high,
    # so in this case, simplicity wins over a very slight inefficiency
    def player_roll(self, player):
        rv = None
        for r in self.rolls:
            if player == r.player_name:
                rv = r
        return rv








def main():
    print()
    print('Try list operations')
    print()

    print('list of integers')
    ll = list()
    ll.append(5)
    ll.append(1)
    ll.append(3)
    ll.append(2)
    print(ll)

    ll.sort()
    print(ll)
    print()

    print('list of tuples')
    mm = list()
    mm.append(('Susan', 33))
    mm.append(('Hank', 47))
    mm.append(('John', 22))
    mm.append(('John', 99))
    mm.append(('Jimmy', 12))
    print(mm)
    mm.sort(key = lambda roll: roll[1])
    print(mm)

    print()


    print('using dictionary')
    dd = dict()
    dd['Susan'] = (33, 0, 1000)
    dd['Hank'] = (47, 0, 1000)
    dd['John'] = (22, 0, 1000)
    dd['John'] = (99, 0, 1000)
    dd['Jimmy'] = (12, 0, 1000)
    print(dd)
    sorted_dd = sorted(dd.items(), key = lambda x:x[1], reverse = True)
    print(sorted_dd)
    print()


    print('list of PlayerRandomRolls')

    rr = list()

    line1 = '[Tue Jul 13 00:30:05 2021]'
    line2 = '[Tue Jul 13 00:30:06 2021]'
    line3 = '[Tue Jul 13 00:30:07 2021]'
    line4 = '[Tue Jul 13 00:30:35 2021]'
    line5 = '[Tue Jul 13 00:30:47 2021]'


    r = PlayerRandomRoll('Susan', 33, 0, 1000, line1)
    rr.append(r)
    r = PlayerRandomRoll('Hank', 47, 0, 1000, line2)
    rr.append(r)
    r = PlayerRandomRoll('John', 22, 0, 1000, line3)
    rr.append(r)
    r = PlayerRandomRoll('John', 99, 0, 1000, line3)
    rr.append(r)
    r = PlayerRandomRoll('Jimmy', 12, 0, 1000, line4)
    rr.append(r)
    print(rr)

    rr.sort(key = lambda x: x.random_value)
    print(rr)

    rr.sort(key = lambda x: x.random_value, reverse = True)
    print(rr)
    print()

    print('use RandomEvent class')
    rl = RandomEvent(0, 1000)
    r = PlayerRandomRoll('FirstRoll', 33, 0, 1000, line1)
    print(rl.add_roll(r))
    r = PlayerRandomRoll('HighRoller', 47, 0, 1000, line2)
    print(rl.add_roll(r))
    r = PlayerRandomRoll('TieRoller', 47, 0, 1000, line2)
    print(rl.add_roll(r))
    r = PlayerRandomRoll('DoubleRoller', 22, 0, 1000, line3)
    print(rl.add_roll(r))
    r = PlayerRandomRoll('DoubleRoller', 99, 0, 1000, line3)
    print(rl.add_roll(r))
    r = PlayerRandomRoll('AlmostLateRoller', 12, 0, 1000, line4)
    print(rl.add_roll(r))
    r = PlayerRandomRoll('LateRoller', 12, 0, 1000, line5)
    print(rl.add_roll(r))


    print('roll list as entered')
    print(rl)
    print('roll list sorted')
    rl.sort_descending_randoms()
    print(rl)
    print()

    print('roll winner')
    print(rl.winner())
    print()

    print('DoubleRoller roll')
    print(rl.player_roll('DoubleRoller'))
    print()

    print('LateRoller roll')
    print(rl.player_roll('LateRoller'))
    print()



    print('Exiting main()')


if __name__ == '__main__':
    main()

