import pickle


def main():

    # set of player_name strings
    new_set = set()

    f = open('players.dat', 'rb')
    initial_set = pickle.load(f)
    f.close()

    for n in initial_set:
        if n is not None:
            stripped_n = n.strip()
            new_set.add(stripped_n)
            # print('[{}], [{}]'.format(n, stripped_n))
        else:
            print('found a None')

    # print(initial_set)
    # print(new_set)

    f = open('players.dat', 'wb')
    pickle.dump(new_set, f)
    f.close()

    #
    # self.player_names_count = len(self.player_names_set)
    # print('Read {} player names from [{}]'.format(self.player_names_count, self.player_names_fname))
    #
    # the_set = set()
    #
    # name_list = ['aaa', 'bbb', 'ccc', 'ddd']
    # print(name_list)
    #
    # for n in name_list:
    #     the_set.add(n)
    # print(the_set)
    #
    # test_list = ['xxx', 'bbb', 'yyy', 'ddd']
    # print(test_list)
    #
    #
    #
    #
    # for t in test_list:
    #     if t in the_set:
    #         print(t)
    #

    #
    # name_list = ['aaa ', 'bbb ', 'ccc ', 'ddd ']
    # stripped_name_list = []
    # print(name_list)
    # print(stripped_name_list)
    #
    # for n in name_list:
    #     stripped_name_list.append(n.strip())
    #
    # print(name_list)
    # print(stripped_name_list)
    #

    pass


if __name__ == '__main__':
    main()
