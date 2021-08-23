


# class for a single random roll by a particular player
class PlayerRandomRoll:

    def __init__(self, player_name, random_value, low, high, time_stamp):

        self.player_name    = player_name
        self.random_value   = random_value
        self.low            = low
        self.high           = high
        self.time_stamp     = time_stamp

    # overload funciton to allow object to print() to screen in sensible manner, for debugging with print()
    def __repr__(self):
        return ('(Player: {}, Roll: {}, Range: ({}-{}), Time: {})'.format(self.player_name, self.random_value, self.low, self.high, self.time_stamp))






# class for many random rolls, to find random winners etc
class RandomList:

    def __init__(self, low, high, delta_seconds = 30):

        self.low            = low
        self.high           = high
        self.delta_seconds  = delta_seconds

        self.rolls          = list()

    # overload funciton to allow object to print() to screen in sensible manner, for debugging with print()
    def __repr__(self):
        rv = 'Range: ({}-{}), Delta (seconds): {}\n'.format(self.low, self.high, self.delta_seconds)
        for r in self.rolls:
            rv += '(Player: {}, Roll: {}, Time: {})\n'.format(r.player_name, r.random_value, r.time_stamp)
        return rv


    # add a roll to the list
    def add_roll(self, r):

        # check if the random low and high limits match
        if (r.low == self.low) and (r.high == self.high):

            # check if the timestamp is in range
            # TODO
            if True:
                self.rolls.append(r)

    # sort the rolls in descending order
    def sort_descending(self):
        self.rolls.sort(key = lambda x: x.random_value, reverse = True)

    # return high roll
    def winner(self):
        self.sort_descending()
        return self.rolls[0]

    # walk the list and return the roll for a particular player
    # not particularly efficient since it visits every membere, but the number of rollers is really never that high
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
    mm.append(('Jimmy', 12))
    print(mm)
    mm.sort(key = lambda roll: roll[1])
    print(mm)

    print()


    print('dictionary')
    dd = dict()
    dd['Susan'] = 33
    dd['Hank'] = 47
    dd['John'] = 22
    dd['Jimmy'] = 12
    print(dd)
    print()


    print('list of PlayerRandomRolls')

    rr = list()

    r = PlayerRandomRoll('Susan', 33, 0, 1000, '')
    rr.append(r)
    r = PlayerRandomRoll('Hank', 47, 0, 1000, '')
    rr.append(r)
    r = PlayerRandomRoll('John', 22, 0, 1000, '')
    rr.append(r)
    r = PlayerRandomRoll('Jimmy', 12, 0, 1000, '')
    rr.append(r)
    print(rr)

    rr.sort(key = lambda x: x.random_value)
    print(rr)

    rr.sort(key = lambda x: x.random_value, reverse = True)
    print(rr)
    print()

    print('use RandomList class')
    rl = RandomList(0, 1000)
    r = PlayerRandomRoll('Susan', 33, 0, 1000, '')
    rl.add_roll(r)
    r = PlayerRandomRoll('Hank', 47, 0, 1000, '')
    rl.add_roll(r)
    r = PlayerRandomRoll('John', 22, 0, 1000, '')
    rl.add_roll(r)
    r = PlayerRandomRoll('Jimmy', 12, 0, 1000, '')
    rl.add_roll(r)

    print('roll list as entered')
    print(rl)
    print('roll list sorted')
    rl.sort_descending()
    print(rl)
    print()

    print('roll winner')
    print(rl.winner())
    print()

    print('Johns roll')
    print(rl.player_roll('John'))
    print()


    print('Exiting main()')


if __name__ == '__main__':
    main()

