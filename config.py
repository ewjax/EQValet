import configparser


# global data

# begin by reading in the config data
config = configparser.ConfigParser()


def load() -> None:
    global config

    ini_filename = 'EQValet.ini'
    file_list = config.read(ini_filename)
    if len(file_list) == 0:
        raise ValueError(f'Unable to open ini file [{ini_filename}]')

    # todo - get rid of all these global variables and just use the config object for the data

    global BASE_DIRECTORY
    BASE_DIRECTORY = config.get('Everquest', 'BASE_DIRECTORY', fallback='c:\\Everquest')

    global LOGS_DIRECTORY
    LOGS_DIRECTORY = config.get('Everquest', 'LOGS_DIRECTORY', fallback='\\logs\\')

    global SERVER_NAME
    SERVER_NAME = config.get('Everquest', 'SERVER_NAME', fallback='P1999Green')

    # todo - get rid of this, not needed
    global DEFAULT_CHAR_NAME
    DEFAULT_CHAR_NAME = 'Azleep'

    global HEARTBEAT
    HEARTBEAT = config.getint('Everquest', 'HEARTBEAT', fallback=15)

    global DEFAULT_WINDOW
    DEFAULT_WINDOW = config.getint('RandomTracker', 'DEFAULT_WINDOW', fallback=30)

    global SPELL_PENDING_TIMEOUT_SEC
    SPELL_PENDING_TIMEOUT_SEC = config.getint('DamageTracker', 'SPELL_PENDING_TIMEOUT_SEC', fallback=10)

    global COMBAT_TIMEOUT_SEC
    COMBAT_TIMEOUT_SEC = config.getint('DamageTracker', 'COMBAT_TIMEOUT_SEC', fallback=120)

    global BOT_TOKEN
    BOT_TOKEN = config.get('Discord', 'BOT_TOKEN')

    global BOT_COMMAND_PREFIX
    BOT_COMMAND_PREFIX = config.get('Discord', 'BOT_COMMAND_PREFIX')

    global PERSONAL_SERVER_NAME
    PERSONAL_SERVER_NAME = config.get('Discord', 'PERSONAL_SERVER_NAME')

    global PERSONAL_SERVER_POPID
    PERSONAL_SERVER_POPID = config.getint('Discord', 'PERSONAL_SERVER_POPID')

    global PERSONAL_SERVER_ALERTID
    PERSONAL_SERVER_ALERTID = config.getint('Discord', 'PERSONAL_SERVER_ALERTID')

    global PERSONAL_SERVER_VALETID
    PERSONAL_SERVER_VALETID = config.getint('Discord', 'PERSONAL_SERVER_VALETID')

    print(f'{ini_filename} loaded')

    for section in config.sections():
        print(section)
        for val in config[section]:
            print(f'    {val} = {config[section][val]}')


# todo - get rid of all these global variables and just use the config object for the data

# configure location of the everquest log files
BASE_DIRECTORY = ''
LOGS_DIRECTORY = ''
SERVER_NAME = ''
# todo - get rid of this, not needed
DEFAULT_CHAR_NAME = 'Azleep'

# used in hearbeat test.  Max number of seconds of inactivity before it checks to see if a new file is being written to
HEARTBEAT = 0

# default randomevent window
DEFAULT_WINDOW = 0

# timeout for spell casting pending wait timeout
SPELL_PENDING_TIMEOUT_SEC = 0

# timeout for combat timer
COMBAT_TIMEOUT_SEC = 0

# token corresponds to the bot from discord developer portal
BOT_TOKEN = ''

# change this if you need to have multiple bots with same commands present on a server
BOT_COMMAND_PREFIX = ''

# some server ID's
PERSONAL_SERVER_NAME = ''
PERSONAL_SERVER_POPID = 0
PERSONAL_SERVER_ALERTID = 0
PERSONAL_SERVER_VALETID = 0
