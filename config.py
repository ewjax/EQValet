import configparser

# global data

# begin by reading in the config data
config_data = configparser.ConfigParser()

# the EverquestLogFile object
elf = None

# various trackers
random_tracker = None
damage_tracker = None
pet_tracker = None

# report width
REPORT_WIDTH = 100


def load() -> None:
    """
    Utility function to load contents from .ini file into a configparser.ConfigParser object
    """
    global config_data

    ini_filename = 'EQValet.ini'
    file_list = config_data.read(ini_filename)
    if len(file_list) == 0:
        raise ValueError(f'Unable to open ini file [{ini_filename}]')

    # print out the contents
    print(f'{ini_filename} loaded')
    for section in config_data.sections():
        print(f'[{section}]')
        for key in config_data[section]:
            val = config_data[section][key]
            print(f'    {key} = {val}')
