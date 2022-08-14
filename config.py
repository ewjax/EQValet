import configparser

from util import starprint
# global data

# begin by reading in the config data
config_data = configparser.ConfigParser()

# global instance of the EQValet class
the_valet = None
ini_filename = 'EQValet.ini'


def load() -> None:
    """
    Utility function to load contents from .ini file into a configparser.ConfigParser object
    """
    global config_data

    file_list = config_data.read(ini_filename)
    if len(file_list) == 0:
        raise ValueError(f'Unable to open ini file [{ini_filename}]')

    # print out the contents
    starprint(f'{ini_filename} loaded')
    for section in config_data.sections():
        starprint(f'[{section}]')
        for key in config_data[section]:
            val = config_data[section][key]
            starprint(f'    {key} = {val}')


def save() -> None:
    """
    Utility function to save contents to .ini file from the configparser.ConfigParser object
    """

    global config_data
    with open(ini_filename, 'wt') as inifile:
        config_data.write(inifile)

    # print out the contents
    starprint(f'{ini_filename} saved')
    for section in config_data.sections():
        starprint(f'[{section}]')
        for key in config_data[section]:
            val = config_data[section][key]
            starprint(f'    {key} = {val}')
