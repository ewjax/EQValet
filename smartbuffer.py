
#################################################################################################

#
# a class to help manage long streams of text being sent to Discord
# There is apparently a limit of 2000 characters on any message, anything over that throws an 
# exception
# 
# this class works by just creating a list of buffers, none of which is over the 2K limit
# Note that when using this, it is important to access the list of buffers using the get_bufflist()
# method, to ensure any remaining content currently stored in the working_buffer is added to the list
#
class SmartBuffer:
    # ctor
    def __init__(self):

#        self._bufflist           = list()
        self._bufflist          = []
        self._working_buffer    = ''

    def add(self, string):
        # would the new string make the buffer too long?
        if ( len(self._working_buffer) + len(string) ) > 1950:
             self._bufflist.append(self._working_buffer)
             self._working_buffer = ''

        self._working_buffer += string

    def get_bufflist(self):
        # add any content currently in the working buffer to the list
        if self._working_buffer != '':
            self._bufflist.append(self._working_buffer)

        # return the list of buffers
        return self._bufflist



