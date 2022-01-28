

from collections.abc import MutableMapping


class CaseInsensitiveDict(MutableMapping):
    """
    A dictionary class which uses/allows case-insensitive keys, by inheriting from the
    abstract base class MutableMapping and overriding the member function __getitem__
    """
    def __init__(self, *args, **kwargs):
        self.__dict__.update(*args, **kwargs)

    def __setitem__(self, key, value):
        for (k, v) in self.__dict__.items():
            if k.casefold() == key.casefold():
                self.__dict__[k] = value
                return
        # if we reach this point without finding a match, this key is not in the dictionary
        self.__dict__[key] = value

    def __getitem__(self, key):
        for (k, v) in self.__dict__.items():
            if k.casefold() == key.casefold():
                return v
        # if we reach this point without finding a match, this key is not in the dictionary
        raise KeyError(key)

    def __delitem__(self, key):
        for (k, v) in self.__dict__.items():
            if k.casefold() == key.casefold():
                del self.__dict__[k]
                break

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    # the final two methods aren't required for the abc, but are convenient/handy
    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return '{}, CaseInsensitiveDict({})'.format(super(CaseInsensitiveDict, self).__repr__(), self.__dict__)


def main():
    rd = dict()
    cid = CaseInsensitiveDict()
    # cid = CIDict()

    cid['aaa'] = '111'
    cid['bbb'] = '222'
    cid['ccc'] = '333'

    rd['aaa'] = '111'
    rd['bbb'] = '222'
    rd['ccc'] = '333'

    # test IN and NOT IN
    search = 'aaa'
    if search in cid:
        print('{} is in'.format(search))
    if search not in cid:
        print('{} is NOT in'.format(search))

    search = 'bbb'
    if search in cid:
        print('{} is in'.format(search))
    if search not in cid:
        print('{} is NOT in'.format(search))

    search = 'Aaa'
    if search in cid:
        print('{} is in'.format(search))
    if search not in cid:
        print('{} is NOT in'.format(search))

    search = 'xxx'
    if search in cid:
        print('{} is in'.format(search))
    if search not in cid:
        print('{} is NOT in'.format(search))

    # test get
    try:
        search = 'aaa'
        print('Search: {}, Value: {}'.format(search, cid[search]))
    except KeyError as ke:
        print('caught KeyError exception: {}'.format(ke))

    try:
        search = 'AAA'
        print('Search: {}, Value: {}'.format(search, cid[search]))
    except KeyError as ke:
        print('caught KeyError exception: {}'.format(ke))

    try:
        search = 'Aaa'
        print('Search: {}, Value: {}'.format(search, cid[search]))
    except KeyError as ke:
        print('caught KeyError exception: {}'.format(ke))

    try:
        search = 'cCc'
        print('Search: {}, Value: {}'.format(search, cid[search]))
    except KeyError as ke:
        print('caught KeyError exception: {}'.format(ke))

    try:
        search = 'Xxx'
        print('Search: {}, Value: {}'.format(search, cid[search]))
    except KeyError as ke:
        print('caught KeyError exception: {}'.format(ke))

    # test pop
    print('cid before pop: {}'.format(cid))
    print('rd  before pop: {}'.format(rd))

    cid.pop('bbb')
    rd.pop('bbb')

    print('cid after pop: {}'.format(cid))
    print('rd  after pop: {}'.format(rd))

    # cid2 = dict()
    cid2 = CaseInsensitiveDict()

    uc = 'A drowned citizen'
    lc = 'a drowned citizen'
    xx = 'a new key'

    cid2[uc] = 1
    cid2[uc] = 11
    cid2[lc] = 2
    cid2[xx] = 3
    print(cid2)

    print('IN tests -------------------')
    if lc in cid2:
        print('lc is IN')
    else:
        print('lc is NOT IN')

    print('pop tests -------------------')
    print(cid2)
    if lc in cid2:
        cid2.pop(lc)
    else:
        print('not in')
    print(cid2)

    if lc in cid2:
        cid2.pop(lc)
    else:
        print('not in')
    print(cid2)

    if lc in cid2:
        cid2.pop(lc)
    else:
        print('not in')
    print(cid2)

    if xx in cid2:
        cid2.pop(xx)
    else:
        print('not in')
    print(cid2)
    x = 3

    print(x)


if __name__ == '__main__':
    main()
