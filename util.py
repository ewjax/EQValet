import psutil
from win32gui import FindWindow, GetWindowRect, MoveWindow

MAXBUFFLENGTH = 1950


#
#
class SmartBuffer:
    """
    A class to help manage long streams of text being sent to Discord
    There is apparently a limit of 2000 characters on any message, anything over that throws an
    exception

    this class works by just creating a list of buffers, none of which is over the MAXBUFFLENGTH limit
    Note that when using this, it is important to access the list of buffers using the get_bufflist()
    method, to ensure any remaining content currently stored in the working_buffer is added to the list
    """

    # ctor
    def __init__(self):

        # create a list of strings, each less than MAXBUFFLENGTH in length
        self._bufflist = []
        self._working_buffer = ''

    def add(self, a_string: str) -> None:
        """
        Add the string 'a_string' to the SmartBuffer

        :param a_string: str
        """
        # would the new string make the buffer too long?
        if (len(self._working_buffer) + len(a_string)) > MAXBUFFLENGTH:
            self._bufflist.append(self._working_buffer)
            self._working_buffer = ''

        self._working_buffer += a_string

    def get_bufflist(self) -> list:
        """
        :return: list of strings, each less than MAXBUFFLENTH bytes in length
        """
        # add any content currently in the working buffer to the list
        if self._working_buffer != '':
            self._bufflist.append(self._working_buffer)

        # return the list of buffers
        return self._bufflist


# report width
REPORT_WIDTH = 100


# standalone function to print results to terminal window
def starprint(line: str, alignment: str = '<', fill: str = ' ') -> None:
    """
    utility function to print with leading and trailing ** indicators

    Args:
        line: line to be printed
        alignment: (left, centered, right) are denoted by one of (<, ^, >)
        fill: Character to fill with
    """
    width = REPORT_WIDTH
    print(f'** {line.rstrip():{fill}{alignment}{width}} **')


#
#
def get_eqgame_pid_list() -> list[int]:
    """
    get list of process ID's for eqgame.exe, using psutil module
    returns a list of process ID's (in case multiple versions of eqgame.exe are somehow running)

    :return: list of process ID integers
    """

    pid_list = list()
    for p in psutil.process_iter(['name']):
        if p.info['name'] == 'eqgame.exe':
            pid_list.append(p.pid)
    return pid_list


#
#
def get_window_coordinates() -> (int, int, int, int):
    """
    Get the windows rectangle of the console window

    Returns:
        Tuple of four integers representing the (x, y, width, height) dimensions
    """

    # return value
    rv = (0, 0, 0, 0)

    # use win32gui function
    window_handle = FindWindow(None, 'EQValet')
    if window_handle:
        # use win32gui function
        (upper_left_x, upper_left_y, lower_right_x, lower_right_y) = GetWindowRect(window_handle)
        x = upper_left_x
        y = upper_left_y
        width = lower_right_x - upper_left_x
        height = lower_right_y - upper_left_y
        rv = (x, y, width, height)

    return rv


#
#
def move_window(x: int, y: int, width: int, height: int) -> None:
    """
    Move the console window to the indicated screen location.
    The windows coordinate system has the origin in the upper left corner,
    with positive x dimenstions proceeding left to right, and positive
    y dimensions proceeding top to bottom

    Args:
        x: x position, pixels
        y: y position, pixels
        width: window width, pixels
        height: window height, pixels
    """

    # use win32gui function
    window_handle = FindWindow(None, 'EQValet')
    if window_handle:

        # use win32gui function
        MoveWindow(window_handle, x, y, width, height, True)
