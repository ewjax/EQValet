

from collections.abc import MutableMapping


class CaseInsensitiveDict(MutableMapping):
    """
    A dictionary class which uses/allows case-insensitive keys, by inheriting from the
    abstract base class MutableMapping and overriding the member function __getitem__
    """
    def __init__(self, *args, **kwargs):
        self.__dict__.update(*args, **kwargs)

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    # the only method which we need to override
    def __getitem__(self, key):
        for (k, v) in self.__dict__.items():
            if key.casefold() == k.casefold():
                return v
        # if we reach this point without finding a match, this key is not in the dictionary
        raise KeyError(key)

    def __delitem__(self, key):
        del self.__dict__[key]

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
    cid = CaseInsensitiveDict()
    # cid = CIDict()

    cid['aaa'] = '111'
    cid['bbb'] = '222'
    cid['ccc'] = '333'

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
    search = 'aaa'
    print('Search: {}, Value: {}'.format(search, cid[search]))

    search = 'AAA'
    print('Search: {}, Value: {}'.format(search, cid[search]))

    search = 'Aaa'
    print('Search: {}, Value: {}'.format(search, cid[search]))

    search = 'cCc'
    print('Search: {}, Value: {}'.format(search, cid[search]))



    # should throw a KeyError exception
    # search = 'Xxx'
    # print('Search: {}, Value: {}'.format(search, cid[search]))


    try:
        search = 'Xxx'
        print('Search: {}, Value: {}'.format(search, cid[search]))
    except KeyError as ke:
        print('caught KeyError exception: {}'.format(ke))

    # test pop
    print(cid)
    cid.pop('bbb')
    print(cid)


if __name__ == '__main__':
    main()
