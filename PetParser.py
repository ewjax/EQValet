import re
import copy

import Parser
import config
from util import starprint


#################################################################################################

#
# A summoned pet can have a range of levels and abilities.  This class represents one individual set.
#
class PetLevel:
    """
    A summoned pet can have a range of levels and abilities.  This class represents one individual set.
    """

    def __init__(self, rank: int, pet_level: int, max_melee: int, max_bashkick: int, max_backstab: int,
                 lt_proc: int, ds: int = 0, desc: str = None) -> None:
        """
        Constructor

        Args:
            rank: 1 to N, min pet to max pet
            pet_level: what level is the pet
            max_melee: max melee attack
            max_bashkick: max back or kick
            max_backstab: max backstab
            lt_proc: lifetap or proc
            ds: damage shield
            desc: description
        """
        self.rank = rank
        self.pet_level = pet_level
        self.max_melee = max_melee
        self.max_bashkick = max_bashkick
        self.max_backstab = max_backstab
        self.lifetap_proc = lt_proc
        self.damage_shield = ds
        self.description = desc

    # overload function to allow object to print() to screen in sensible manner, for debugging with print()
    def __repr__(self):
        return '({}, {}, {}, {}, {}, {}, {})\n'.format(self.rank,
                                                       self.pet_level,
                                                       self.max_melee,
                                                       self.max_bashkick,
                                                       self.max_backstab,
                                                       self.lifetap_proc,
                                                       self.damage_shield,
                                                       self.description)


#################################################################################################


#
# class for a Pet spell.  
# Has information about this particular pet spell, as well as a list of PetLevel info records,
# for each possible pet level
#
class PetSpell:
    """
    Class for a Pet spell.
    Has information about this particular pet spell, i.e. spell name, caster class, caster level,
    and a list of PetLevel info records
    """

    # ctor
    def __init__(self, spell_name: str, eq_class: str, caster_level: int, pet_level_list: list[PetLevel], mage_subtype=None) -> None:
        self.spell_name = spell_name
        self.eq_class = eq_class
        self.caster_level = caster_level
        self.pet_level_list = pet_level_list
        self.mage_type = mage_subtype

    # overload function to allow object to print() to screen in sensible manner, for debugging with print()
    def __repr__(self):
        rv = f'({self.spell_name}, {self.mage_type}, {self.eq_class}, {self.caster_level}, \n{self.pet_level_list})'
        return rv

    def get_full_spellname(self):
        rv = f'{self.spell_name}'
        if self.mage_type:
            rv += f': {self.mage_type}'
        return rv


#################################################################################################

#
# class for an actual pet in game
#
class Pet:
    """
    Class for an actual pet in game, its name, level, max melee, etc
    """

    # type declarations
    pet_spell: PetSpell
    my_PetLevel: PetLevel

    # ctor
    def __init__(self, pet_spell: PetSpell) -> None:

        self.pet_name = None
        self.name_pending = True

        # necro pets have a lifetap proc
        self.lifetap_pending = False

        # mage fire pets have a damage shield proc
        self.damage_shield_pending = False

        # mage fire/water pets will proc
        self.procced = False

        # which PetSpell was used to create this pet
        # note that each PetSpell object contains a list of PetLevel objects, one for each possible level of this pet
        self.pet_spell = pet_spell

        # pointer to the correct PetLevel object in the list of PetLevel's contained in the PetSpell
        # this is set during the parse, based on max melee, or lifetap, etc
        self.my_PetLevel = None

        # running metric for this pet's max damage
        self.max_melee = 0

    def created_report(self):
        rv = 'Pet created: {}'.format(self.pet_name)
        if self.pet_spell:
            rv += ' ({})'.format(self.pet_spell.get_full_spellname())

        return rv

    def __repr__(self):

        # return value
        rv = ''

        # bell sound
        if config.config_data.getboolean('EQValet', 'bell'):
            rv += f'\a'

        # initial values
        level = 0
        lifetap_proc = 0
        damage_shield = 0
        rank = 0
        desc = None

        # if we know which PetLevel object is in play, use it populate this report
        if self.my_PetLevel:
            level = self.my_PetLevel.pet_level
            lifetap_proc = self.my_PetLevel.lifetap_proc
            damage_shield = self.my_PetLevel.damage_shield
            rank = self.my_PetLevel.rank
            desc = self.my_PetLevel.description

        rv += f'Pet: **{self.pet_name}**, ' \
              f'Max Melee={self.max_melee}, ' \
              f'Level={level}, ' \
              f'LT/Proc={lifetap_proc}, ' \
              f'DS={damage_shield}, ' \
              f'Rank (1-{len(self.pet_spell.pet_level_list)}): {rank}'

        if self.pet_spell:
            rv += f' ({self.pet_spell.spell_name}'
            if self.pet_spell.mage_type:
                rv += f': {self.pet_spell.mage_type}'
            rv += ')'

        if desc:
            rv += f' ({desc})'

        return rv


#################################################################################################

#
# class to do all the pet tracking work
#
class PetParser(Parser.Parser):
    """
    Class to do all the pet tracking work
    """
    super().__init__()

    # type declaraations
    current_pet: Pet
    all_pets: list[Pet]
    pet_dict: dict[str, PetSpell]

    # ctor
    def __init__(self):
        super().__init__()

        # pointer to current pet
        self.current_pet = None

        # list of all pets
        # not really used for now, but keeping it in case this idea is needed later
        # perhaps for some function that needs to know about all pets, etc
        self.all_pets = []

        # a dictionary of pet spells, keys = Pet Spell Names, values = associated PetSpell objects
        self.pet_dict = {}
        self.load_pet_dict()

        # keep track of the previous non-melee damage amount (for mage fire/watere pet proc messages)
        self.prev_non_melee_damage = 0

    # get pet name
    def pet_name(self) -> str:
        """
        Returns:
            pet name
        """
        rv = 'No Pet'
        if self.current_pet:
            if self.current_pet.pet_name:
                rv = self.current_pet.pet_name
        return rv

    #
    # check for pet related items
    #
    async def process_line(self, line: str) -> None:
        """
        The parse logic for this particular parser.

        :param line: complete line to be parsed, i.e. timestamp and content
        """
        await super().process_line(line)

        # cut off the leading date-time stamp info
        trunc_line = line[27:]

        # check for toggling the parse on/off
        target = r'^\.pt '
        m = re.match(target, trunc_line)
        if m:
            # the relevant section and key value from the ini configfile
            section = 'PetParser'
            key = 'parse'
            setting = config.config_data.getboolean(section, key)

            if setting:
                config.config_data[section][key] = 'False'
                onoff = 'Off'
            else:
                config.config_data[section][key] = 'True'
                onoff = 'On'

            # save the updated ini logfile
            config.save()

            starprint(f'Pet Parsing: {onoff}')

        #
        # only do the rest if pet parsing is turned on
        #
        if config.config_data.getboolean('PetParser', 'parse'):

            #
            # check for user commands
            #
            target = r'^\.pet '
            m = re.match(target, trunc_line)
            if m:
                if self.current_pet:
                    starprint(str(self.current_pet))
                else:
                    starprint('No pet')

            #
            # check for a few ways in which the pet can be lost
            #
            if self.current_pet:

                # zoning?
                target = '^LOADING, PLEASE WAIT'
                m1 = re.match(target, trunc_line)

                # pet reclaimed?
                target = '^{} disperses'.format(self.current_pet.pet_name)
                m2 = re.match(target, trunc_line, re.IGNORECASE)

                # pet died?
                target = '^{} says, \'Sorry to have failed you, oh Great One'.format(self.current_pet.pet_name)
                m3 = re.match(target, trunc_line, re.IGNORECASE)

                # somehow pet is gone
                target = r'^You don\'t have a pet to command!'
                m4 = re.match(target, trunc_line)

                # charm break
                m5 = False
                if self.current_pet.pet_spell.spell_name == 'CharmPet':
                    target = r'^Your charm spell has worn off'
                    m5 = re.match(target, trunc_line)

                # check for any of the pet died messages
                if m1 or m2 or m3 or m4 or m5:
                    starprint(f'Pet {self.current_pet.pet_name} died/lost')
                    self.current_pet = None

            #
            # search for cast message, see if any of the pet spells we know about are being cast
            #
            target = r'^You begin casting (?P<spell_name>[\w`\' ]+)(: (?P<mage_type>(Air|Fire|Water|Earth)))?\.'

            # return value m is either None of an object with information about the RE search
            m = re.match(target, trunc_line)
            if m:

                # fetch the spell name
                spell_name = m.group('spell_name')
                mage_type = m.group('mage_type')

                # does the spell name match one of the pets we know about?
                if spell_name in self.pet_dict:
                    pet_spell: PetSpell = copy.copy(self.pet_dict[spell_name])
                    pet_spell.mage_type = mage_type
                    self.current_pet = Pet(pet_spell)
                    starprint(f'Pet being created from spell ({pet_spell.get_full_spellname()}), name TBD')

            #
            # if the flag is set that we have a pet and don't know the name yet, search for pet name
            #
            if self.current_pet and self.current_pet.name_pending:
                target = r'^(?P<pet_name>[\w ]+) says \'At your service Master.'

                # return value m is either None of an object with information about the RE search
                m = re.match(target, trunc_line)
                if m:
                    # fetch the pet name
                    pet_name = m.group('pet_name')
                    self.current_pet.pet_name = pet_name
                    self.current_pet.name_pending = False

                    self.all_pets.append(self.current_pet)
                    starprint(self.current_pet.created_report())

            #
            # check for lifetaps, procs, and damage shields.  Start by getting the non-melee damage amount for use in all
            #
            # For necro pet lifetaps and mage fire pet damage shields, the order of occurrence in the log file is
            #       first: the particular phrase indicating the occurrence of the lifetap or damage shield event
            #       then: non-melee damage message (usually the very next line, not sure if that is always true)
            #
            #       To parse for those events, we start by setting a 'pending' flag, then watch for the non-melee message
            #
            # For mage fire/water pet procs, the order is reversed
            #       first: non-melee damage message
            #       then: the particular phrase indicating the occurrence of the lifetap or damage shield event
            #             (usually the very next line, not sure if that is always true)
            #
            #       To parse for these events, we set a 'proceed' flag, then remember the previous non-melee event as the proc amount
            #
            non_melee_damage = 0
            if self.current_pet:
                target = r'^(?P<target_name>[\w` ]+) was hit by non-melee for (?P<damage>[\d]+) points of damage'
                m = re.match(target, trunc_line)
                if m:
                    non_melee_damage = int(m.group('damage'))

            #
            # if the flag is set that we have a lifetap_pending...
            if self.current_pet and self.current_pet.lifetap_pending and non_melee_damage > 0:

                # did we have a lifetap that matches the current pet?
                if self.current_pet.my_PetLevel and self.current_pet.my_PetLevel.lifetap_proc == non_melee_damage:
                    self.current_pet.lifetap_pending = False

                # new PetLevel?
                if (self.current_pet.my_PetLevel is None) or \
                   (self.current_pet.my_PetLevel and self.current_pet.my_PetLevel.lifetap_proc != non_melee_damage):

                    # find the new PetLevel
                    for pet_level in self.current_pet.pet_spell.pet_level_list:
                        if pet_level.lifetap_proc == non_melee_damage:
                            self.current_pet.my_PetLevel = pet_level
                            self.current_pet.max_melee = pet_level.max_melee
                            self.current_pet.lifetap_pending = False

                            # announce the pet rank
                            starprint(str(self.current_pet))
                            starprint('  (Identified via lifetap signature)')

            #
            # if the flag is set that we have a damage shield pending...
            if self.current_pet and self.current_pet.damage_shield_pending and non_melee_damage > 0:

                # did we have a DS that matches the current pet?
                if self.current_pet.my_PetLevel and self.current_pet.my_PetLevel.damage_shield == non_melee_damage:
                    self.current_pet.damage_shield_pending = False

                # new PetLevel?
                if (self.current_pet.my_PetLevel is None) or \
                        (self.current_pet.my_PetLevel and self.current_pet.my_PetLevel.damage_shield != non_melee_damage):

                    # find the new PetLevel
                    for pet_level in self.current_pet.pet_spell.pet_level_list:
                        if pet_level.damage_shield == non_melee_damage:
                            self.current_pet.my_PetLevel = pet_level
                            self.current_pet.max_melee = pet_level.max_melee
                            self.current_pet.damage_shield_pending = False

                            # announce the pet rank
                            starprint(str(self.current_pet))
                            starprint('  (Identified via damage shield signature)')

            #
            # if the flag is set that we had a proc event...
            if self.current_pet and self.current_pet.procced:

                # did we have a proc that matches the current pet?
                if self.current_pet.my_PetLevel and self.current_pet.my_PetLevel.lifetap_proc == self.prev_non_melee_damage:
                    self.current_pet.procced = False

                # new PetLevel?
                if (self.current_pet.my_PetLevel is None) or \
                        (self.current_pet.my_PetLevel and self.current_pet.my_PetLevel.lifetap_proc != self.prev_non_melee_damage):

                    # find the new PetLevel
                    for pet_level in self.current_pet.pet_spell.pet_level_list:
                        if pet_level.lifetap_proc == self.prev_non_melee_damage:
                            self.current_pet.my_PetLevel = pet_level
                            self.current_pet.max_melee = pet_level.max_melee
                            self.current_pet.procced = False

                            # announce the pet rank
                            starprint(str(self.current_pet))
                            starprint('  (Identified via proc signature)')

            # save the non-melee damage event for use in next proc
            if non_melee_damage > 0:
                self.prev_non_melee_damage = non_melee_damage

            #
            # if we have a pet, do several scans....
            #
            if self.current_pet:

                #
                # look for lt_proc 'beams a smile' message coming from our pet
                target = f'^{self.current_pet.pet_name} beams a smile at (?P<target_name>[\\w` ]+)'
                m = re.match(target, trunc_line, re.IGNORECASE)
                if m:
                    self.current_pet.lifetap_pending = True

                #
                # look for mage fire pet DS 'was burned' message coming from our pet
                target = f'^(?P<target_name>[\\w` ]+ was burned)'
                m = re.match(target, trunc_line, re.IGNORECASE)
                if m:
                    self.current_pet.damage_shield_pending = True

                #
                # look for the mage fire/water pet proc messages
                target = f'^(?P<target_name>[\\w` ]+ ((is slashed by ice)|(is engulfed by fire)))'
                m = re.match(target, trunc_line, re.IGNORECASE)
                if m:
                    self.current_pet.procced = True

                #
                # look for max melee value
                #
                target = r'^{} (hits|slashes|pierces|crushes|claws|bites|stings|mauls|gores|punches|slices) ' \
                         r'(?P<target_name>[\w` ]+) for (?P<damage>[\d]+) point(s)? of damage'.format(self.current_pet.pet_name)
                # return value m is either None of an object with information about the RE search
                m = re.match(target, trunc_line, re.IGNORECASE)
                if m:
                    # fetch the damage
                    damage = int(m.group('damage'))

                    # is this new max?
                    if damage > self.current_pet.max_melee:
                        self.current_pet.max_melee = damage

                        # find the new rank
                        for pet_level in self.current_pet.pet_spell.pet_level_list:
                            if pet_level.max_melee == damage:
                                self.current_pet.my_PetLevel = pet_level

                        # if charmed pet, determine implied level here
                        if self.current_pet.pet_spell.spell_name == 'CharmPet':
                            if damage <= 60:
                                self.current_pet.pet_level = damage / 2
                            else:
                                self.current_pet.pet_level = (damage + 60) / 4

                        # announce the pet rank
                        starprint(str(self.current_pet))
                        starprint('  (Identified via max melee damage)')

            #
            # do we need to reset our pet name to the parser?
            #
            reset_pet = False

            # reset pet method 1:  use /pet leader
            # watch for pet leader commands, and check that our pet name matches
            # this is useful if somehow our pet name is goofed up
            target = r'^(?P<pet_name>[\w` ]+) says \'My leader is (?P<char_name>[\w` ]+)'
            m = re.match(target, trunc_line)
            pet_name = ''
            if m:
                pet_name = m.group('pet_name')
                char_name = m.group('char_name')

                # if a pet just declared our character as the leader...
                if char_name == config.the_valet.char_name:
                    reset_pet = True

            # reset pet method 2:  direct the pet to attack itself
            # search for the special case where the pet is attacking itself - this
            # how we will communicate to EQValet from within the game regarding the
            # presence of a pet that EQValet currently doesn't know about (most likely
            # a charmed pet).  To generate this message, from within EQ issue these commands:
            #   /pet target
            #   /pet attack
            target = r'^(?P<pet_name>[\w` ]+) tells you, \'Attacking (?P<target_name>[\w` ]+) Master'

            # return value m is either None of an object with information about the RE search
            m = re.match(target, trunc_line)
            if m:
                pet_name = m.group('pet_name')
                target_name = m.group('target_name')

                # is the pet attacking itself?
                if pet_name == target_name:
                    reset_pet = True

            # have we encountered a situation where a pet reset is needed?
            if reset_pet:
                # announce the pet name
                starprint(f'Pet name = {pet_name}')

                # no pet known to EQValet?
                if self.current_pet is None:

                    # then we probably have a charmed pet
                    spell_name = 'CharmPet'

                    # does the spell name match one of the pets we know about?
                    if spell_name in self.pet_dict:
                        pet_spell = self.pet_dict[spell_name]
                        self.current_pet = Pet(pet_spell)
                        self.current_pet.pet_name = pet_name
                        self.current_pet.name_pending = False

                        self.all_pets.append(self.current_pet)
                        starprint(self.current_pet.created_report())

                # ok somehow EQValet thinks we have a pet, but the name is goofed up,
                # so just reset the max_melee and pet_rank fields and let them get determined again
                else:
                    self.current_pet.pet_name = pet_name
                    self.current_pet.name_pending = False
                    self.current_pet.pet_rank = 0
                    self.current_pet.pet_level = 0
                    self.current_pet.max_melee = 0

                    starprint(str(self.current_pet))

    #
    #
    def load_pet_dict(self) -> None:
        """
        Create the dictionary of pet spells, with all pet spell info for each

        Returns:
            None: 
        """
        #
        # Necro pets
        #
        pet_level_list = list()
        pet_level_list.append(PetLevel(rank=1, pet_level=1, max_melee=8, max_bashkick=0, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=2, max_melee=10, max_bashkick=0, max_backstab=0, lt_proc=0))
        pet_spell = PetSpell('Cavorting Bones', 'Necro', caster_level=1, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=3, max_melee=8, max_bashkick=0, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=4, max_melee=10, max_bashkick=0, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=5, max_melee=12, max_bashkick=0, max_backstab=0, lt_proc=0, desc='Max'))
        pet_spell = PetSpell('Leering Corpse', 'Necro', caster_level=4, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=6, max_melee=8, max_bashkick=8, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=7, max_melee=10, max_bashkick=10, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=8, max_melee=12, max_bashkick=12, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=9, max_melee=14, max_bashkick=13, max_backstab=0, lt_proc=0, desc='Max'))
        pet_spell = PetSpell('Bone Walk', 'Necro', caster_level=8, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=8, max_melee=10, max_bashkick=10, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=9, max_melee=12, max_bashkick=12, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=10, max_melee=14, max_bashkick=14, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=11, max_melee=16, max_bashkick=16, max_backstab=0, lt_proc=0, desc='Max'))
        pet_spell = PetSpell('Convoke Shadow', 'Necro', caster_level=12, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=12, max_melee=12, max_bashkick=12, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=13, max_melee=14, max_bashkick=14, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=14, max_melee=16, max_bashkick=15, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=15, max_melee=18, max_bashkick=15, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=16, max_melee=20, max_bashkick=16, max_backstab=0, lt_proc=0, desc='Max'))
        pet_spell = PetSpell('Restless Bones', 'Necro', caster_level=16, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=15, max_melee=14, max_bashkick=14, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=16, max_melee=16, max_bashkick=15, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=17, max_melee=18, max_bashkick=15, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=18, max_melee=20, max_bashkick=16, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=19, max_melee=22, max_bashkick=16, max_backstab=0, lt_proc=0, desc='Max'))
        pet_spell = PetSpell('Animate Dead', 'Necro', caster_level=20, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=18, max_melee=18, max_bashkick=15, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=19, max_melee=20, max_bashkick=16, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=20, max_melee=22, max_bashkick=16, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=21, max_melee=23, max_bashkick=17, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=22, max_melee=26, max_bashkick=17, max_backstab=0, lt_proc=0, desc='Max'))
        pet_spell = PetSpell('Haunting Corpse', 'Necro', caster_level=24, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=22, max_melee=20, max_bashkick=16, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=23, max_melee=22, max_bashkick=16, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=24, max_melee=23, max_bashkick=17, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=25, max_melee=26, max_bashkick=17, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=26, max_melee=28, max_bashkick=18, max_backstab=0, lt_proc=0, desc='Max'))
        pet_spell = PetSpell('Summon Dead', 'Necro', caster_level=29, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=25, max_melee=23, max_bashkick=17, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=26, max_melee=26, max_bashkick=17, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=27, max_melee=28, max_bashkick=18, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=28, max_melee=30, max_bashkick=18, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=29, max_melee=32, max_bashkick=19, max_backstab=0, lt_proc=0, desc='Max'))
        pet_spell = PetSpell('Invoke Shadow', 'Necro', caster_level=34, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=29, max_melee=31, max_bashkick=18, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=30, max_melee=33, max_bashkick=19, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=31, max_melee=35, max_bashkick=19, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=32, max_melee=37, max_bashkick=20, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=33, max_melee=39, max_bashkick=20, max_backstab=0, lt_proc=0, desc='Max'))
        pet_spell = PetSpell('Malignant Dead', 'Necro', caster_level=39, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=33, max_melee=39, max_bashkick=20, max_backstab=0, lt_proc=11))
        pet_level_list.append(PetLevel(rank=2, pet_level=34, max_melee=41, max_bashkick=21, max_backstab=0, lt_proc=11))
        pet_level_list.append(PetLevel(rank=3, pet_level=35, max_melee=43, max_bashkick=21, max_backstab=0, lt_proc=11))
        pet_level_list.append(PetLevel(rank=4, pet_level=36, max_melee=45, max_bashkick=22, max_backstab=0, lt_proc=11))
        pet_level_list.append(PetLevel(rank=5, pet_level=37, max_melee=47, max_bashkick=22, max_backstab=0, lt_proc=11, desc='Max'))
        pet_spell = PetSpell('Cackling Bones', 'Necro', caster_level=44, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=37, max_melee=47, max_bashkick=22, max_backstab=0, lt_proc=38))
        pet_level_list.append(PetLevel(rank=2, pet_level=38, max_melee=49, max_bashkick=23, max_backstab=0, lt_proc=39))
        pet_level_list.append(PetLevel(rank=3, pet_level=39, max_melee=51, max_bashkick=23, max_backstab=0, lt_proc=40))
        pet_level_list.append(PetLevel(rank=4, pet_level=40, max_melee=52, max_bashkick=24, max_backstab=0, lt_proc=41))
        pet_level_list.append(PetLevel(rank=5, pet_level=41, max_melee=55, max_bashkick=24, max_backstab=0, lt_proc=42, desc='Max'))
        pet_level_list.append(PetLevel(rank=6, pet_level=42, max_melee=57, max_bashkick=25, max_backstab=0, lt_proc=43, desc='Max+Focus'))
        pet_spell = PetSpell('Invoke Death', 'Necro', caster_level=49, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=40, max_melee=49, max_bashkick=0, max_backstab=147, lt_proc=40))
        pet_level_list.append(PetLevel(rank=2, pet_level=41, max_melee=51, max_bashkick=0, max_backstab=153, lt_proc=41))
        pet_level_list.append(PetLevel(rank=3, pet_level=42, max_melee=52, max_bashkick=0, max_backstab=159, lt_proc=42))
        pet_level_list.append(PetLevel(rank=4, pet_level=43, max_melee=55, max_bashkick=0, max_backstab=165, lt_proc=43))
        pet_level_list.append(PetLevel(rank=5, pet_level=44, max_melee=56, max_bashkick=0, max_backstab=171, lt_proc=44, desc='Max'))
        pet_level_list.append(PetLevel(rank=6, pet_level=45, max_melee=59, max_bashkick=0, max_backstab=177, lt_proc=45, desc='Max+Focus'))
        pet_spell = PetSpell('Minion of Shadows', 'Necro', caster_level=53, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=40, max_melee=51, max_bashkick=63, max_backstab=0, lt_proc=41))
        pet_level_list.append(PetLevel(rank=2, pet_level=41, max_melee=52, max_bashkick=65, max_backstab=0, lt_proc=42))
        pet_level_list.append(PetLevel(rank=3, pet_level=42, max_melee=55, max_bashkick=66, max_backstab=0, lt_proc=43))
        pet_level_list.append(PetLevel(rank=4, pet_level=43, max_melee=56, max_bashkick=68, max_backstab=0, lt_proc=44))
        pet_level_list.append(PetLevel(rank=5, pet_level=44, max_melee=59, max_bashkick=69, max_backstab=0, lt_proc=45, desc='Max'))
        pet_level_list.append(PetLevel(rank=6, pet_level=45, max_melee=61, max_bashkick=71, max_backstab=0, lt_proc=46, desc='Max+Focus'))
        pet_spell = PetSpell('Servant of Bones', 'Necro', caster_level=56, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=43, max_melee=52, max_bashkick=24, max_backstab=0, lt_proc=44))
        pet_level_list.append(PetLevel(rank=2, pet_level=44, max_melee=55, max_bashkick=24, max_backstab=0, lt_proc=45))
        pet_level_list.append(PetLevel(rank=3, pet_level=45, max_melee=56, max_bashkick=25, max_backstab=0, lt_proc=46))
        pet_level_list.append(PetLevel(rank=4, pet_level=46, max_melee=59, max_bashkick=25, max_backstab=0, lt_proc=47))
        pet_level_list.append(PetLevel(rank=5, pet_level=47, max_melee=61, max_bashkick=26, max_backstab=0, lt_proc=48, desc='Max'))
        pet_level_list.append(PetLevel(rank=6, pet_level=48, max_melee=62, max_bashkick=26, max_backstab=0, lt_proc=49, desc='Max+Focus'))
        pet_spell = PetSpell('Emissary of Thule', 'Necro', caster_level=59, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        #
        # Enchanter pets
        #
        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=1, max_melee=7, max_bashkick=0, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=2, max_melee=9, max_bashkick=0, max_backstab=0, lt_proc=0))
        pet_spell = PetSpell('Pendril\'s Animation', 'Enchanter', caster_level=1, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=3, max_melee=9, max_bashkick=0, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=4, max_melee=10, max_bashkick=0, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=5, max_melee=12, max_bashkick=0, max_backstab=0, lt_proc=0, desc='Max'))
        pet_spell = PetSpell('Juli`s Animation', 'Enchanter', caster_level=4, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=6, max_melee=9, max_bashkick=8, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=7, max_melee=10, max_bashkick=10, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=8, max_melee=12, max_bashkick=12, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=9, max_melee=14, max_bashkick=13, max_backstab=0, lt_proc=0, desc='Max'))
        pet_spell = PetSpell('Mircyl\'s Animation', 'Enchanter', caster_level=8, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=9, max_melee=11, max_bashkick=11, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=10, max_melee=13, max_bashkick=13, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=11, max_melee=15, max_bashkick=14, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=12, max_melee=17, max_bashkick=15, max_backstab=0, lt_proc=0, desc='Max'))
        pet_spell = PetSpell('Kilan`s Animation', 'Enchanter', caster_level=12, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=12, max_melee=12, max_bashkick=12, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=13, max_melee=14, max_bashkick=14, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=14, max_melee=16, max_bashkick=15, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=15, max_melee=18, max_bashkick=15, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=16, max_melee=20, max_bashkick=16, max_backstab=0, lt_proc=0, desc='Max'))
        pet_spell = PetSpell('Shalee`s Animation', 'Enchanter', caster_level=16, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=16, max_melee=14, max_bashkick=14, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=17, max_melee=16, max_bashkick=15, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=18, max_melee=19, max_bashkick=15, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=19, max_melee=20, max_bashkick=16, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=20, max_melee=22, max_bashkick=16, max_backstab=0, lt_proc=0, desc='Max'))
        pet_spell = PetSpell('Sisna`s Animation', 'Enchanter', caster_level=20, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=19, max_melee=18, max_bashkick=15, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=20, max_melee=20, max_bashkick=16, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=21, max_melee=22, max_bashkick=16, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=22, max_melee=23, max_bashkick=17, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=23, max_melee=26, max_bashkick=17, max_backstab=0, lt_proc=0, desc='Max'))
        pet_spell = PetSpell('Sagar`s Animation', 'Enchanter', caster_level=24, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=22, max_melee=20, max_bashkick=16, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=23, max_melee=22, max_bashkick=16, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=24, max_melee=23, max_bashkick=17, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=25, max_melee=26, max_bashkick=17, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=26, max_melee=28, max_bashkick=18, max_backstab=0, lt_proc=0, desc='Max'))
        pet_spell = PetSpell('Uleen`s Animation', 'Enchanter', caster_level=29, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=25, max_melee=26, max_bashkick=17, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=26, max_melee=28, max_bashkick=18, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=27, max_melee=30, max_bashkick=18, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=28, max_melee=32, max_bashkick=19, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=29, max_melee=34, max_bashkick=19, max_backstab=0, lt_proc=0, desc='Max'))
        pet_spell = PetSpell('Boltran`s Animation', 'Enchanter', caster_level=34, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=29, max_melee=32, max_bashkick=19, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=30, max_melee=34, max_bashkick=19, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=31, max_melee=36, max_bashkick=20, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=32, max_melee=38, max_bashkick=20, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=33, max_melee=40, max_bashkick=21, max_backstab=0, lt_proc=0, desc='Max'))
        pet_spell = PetSpell('Aanya\'s Animation', 'Enchanter', caster_level=39, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=33, max_melee=40, max_bashkick=21, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=34, max_melee=42, max_bashkick=21, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=35, max_melee=44, max_bashkick=22, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=36, max_melee=45, max_bashkick=22, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=37, max_melee=48, max_bashkick=23, max_backstab=0, lt_proc=0, desc='Max'))
        pet_spell = PetSpell('Yegoreff`s Animation', 'Enchanter', caster_level=44, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=37, max_melee=45, max_bashkick=22, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=38, max_melee=47, max_bashkick=22, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=39, max_melee=49, max_bashkick=23, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=40, max_melee=51, max_bashkick=23, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=41, max_melee=52, max_bashkick=24, max_backstab=0, lt_proc=0, desc='Max'))
        pet_spell = PetSpell('Kintaz`s Animation', 'Enchanter', caster_level=49, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=44, max_melee=49, max_bashkick=23, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=45, max_melee=51, max_bashkick=23, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=46, max_melee=52, max_bashkick=24, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=47, max_melee=55, max_bashkick=24, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=48, max_melee=56, max_bashkick=25, max_backstab=0, lt_proc=0, desc='Max'))
        pet_spell = PetSpell('Zumaik`s Animation', 'Enchanter', caster_level=55, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        #
        # generic charmed pets
        #
        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=0, pet_level=0, max_melee=0, max_bashkick=0, max_backstab=0, lt_proc=0))
        pet_spell = PetSpell('CharmPet', 'UnknownClass', caster_level=0, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        #
        # Shaman pets
        #
        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=22, max_melee=22, max_bashkick=16, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=23, max_melee=23, max_bashkick=17, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=24, max_melee=26, max_bashkick=17, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=25, max_melee=28, max_bashkick=18, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=26, max_melee=30, max_bashkick=18, max_backstab=0, lt_proc=0, desc='Max'))
        pet_spell = PetSpell('Companion Spirit', 'Shaman', caster_level=34, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=24, max_melee=27, max_bashkick=17, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=25, max_melee=28, max_bashkick=18, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=26, max_melee=31, max_bashkick=18, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=27, max_melee=33, max_bashkick=19, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=28, max_melee=35, max_bashkick=19, max_backstab=0, lt_proc=0, desc='Max'))
        pet_spell = PetSpell('Vigilant Spirit', 'Shaman', caster_level=39, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=28, max_melee=35, max_bashkick=19, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=29, max_melee=37, max_bashkick=20, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=30, max_melee=39, max_bashkick=20, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=31, max_melee=41, max_bashkick=21, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=32, max_melee=43, max_bashkick=21, max_backstab=0, lt_proc=0, desc='Max'))
        pet_spell = PetSpell('Guardian Spirit', 'Shaman', caster_level=44, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=32, max_melee=43, max_bashkick=21, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=33, max_melee=45, max_bashkick=22, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=34, max_melee=47, max_bashkick=22, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=35, max_melee=49, max_bashkick=23, max_backstab=0, lt_proc=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=36, max_melee=51, max_bashkick=23, max_backstab=0, lt_proc=0, desc='Max'))
        pet_spell = PetSpell('Frenzied Spirit', 'Shaman', caster_level=49, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        # todo need shaman 55 pet

        #
        # Mage pets
        #
        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=4, max_melee=8, max_bashkick=0, max_backstab=0, lt_proc=5, ds=6, desc='Min'))
        pet_level_list.append(PetLevel(rank=2, pet_level=5, max_melee=10, max_bashkick=0, max_backstab=0, lt_proc=6, ds=7))
        pet_level_list.append(PetLevel(rank=3, pet_level=6, max_melee=12, max_bashkick=0, max_backstab=0, lt_proc=7, ds=8, desc='Max'))
        pet_spell = PetSpell('Elementalkin', 'Magician', caster_level=4, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=6, max_melee=10, max_bashkick=0, max_backstab=0, lt_proc=7, ds=8, desc='Min'))
        pet_level_list.append(PetLevel(rank=2, pet_level=7, max_melee=12, max_bashkick=0, max_backstab=0, lt_proc=8, ds=9))
        pet_level_list.append(PetLevel(rank=3, pet_level=8, max_melee=14, max_bashkick=0, max_backstab=0, lt_proc=8, ds=10))
        pet_level_list.append(PetLevel(rank=4, pet_level=9, max_melee=16, max_bashkick=0, max_backstab=0, lt_proc=10, ds=11, desc='Max'))
        pet_spell = PetSpell('Elementaling', 'Magician', caster_level=8, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=10, max_melee=12, max_bashkick=0, max_backstab=0, lt_proc=11, ds=12, desc='Min'))
        pet_level_list.append(PetLevel(rank=2, pet_level=11, max_melee=14, max_bashkick=0, max_backstab=0, lt_proc=12, ds=13))
        pet_level_list.append(PetLevel(rank=3, pet_level=12, max_melee=16, max_bashkick=0, max_backstab=0, lt_proc=13, ds=14))
        pet_level_list.append(PetLevel(rank=4, pet_level=13, max_melee=18, max_bashkick=0, max_backstab=0, lt_proc=14, ds=15, desc='Max'))
        pet_spell = PetSpell('Elemental', 'Magician', caster_level=12, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=13, max_melee=12, max_bashkick=0, max_backstab=0, lt_proc=14, ds=15, desc='Min'))
        pet_level_list.append(PetLevel(rank=2, pet_level=14, max_melee=14, max_bashkick=0, max_backstab=0, lt_proc=15, ds=16))
        pet_level_list.append(PetLevel(rank=3, pet_level=15, max_melee=16, max_bashkick=0, max_backstab=0, lt_proc=16, ds=17))
        pet_level_list.append(PetLevel(rank=4, pet_level=16, max_melee=18, max_bashkick=0, max_backstab=0, lt_proc=17, ds=18))
        pet_level_list.append(PetLevel(rank=5, pet_level=17, max_melee=20, max_bashkick=0, max_backstab=0, lt_proc=18, ds=19, desc='Max'))
        pet_spell = PetSpell('Minor Summoning', 'Magician', caster_level=16, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=15, max_melee=14, max_bashkick=14, max_backstab=0, lt_proc=17, ds=18, desc='Min'))
        pet_level_list.append(PetLevel(rank=2, pet_level=16, max_melee=16, max_bashkick=15, max_backstab=0, lt_proc=18, ds=19))
        pet_level_list.append(PetLevel(rank=3, pet_level=17, max_melee=18, max_bashkick=15, max_backstab=0, lt_proc=19, ds=20))
        pet_level_list.append(PetLevel(rank=4, pet_level=18, max_melee=20, max_bashkick=16, max_backstab=0, lt_proc=20, ds=21))
        pet_level_list.append(PetLevel(rank=5, pet_level=19, max_melee=22, max_bashkick=16, max_backstab=0, lt_proc=21, ds=22, desc='Max'))
        pet_spell = PetSpell('Lesser Summoning', 'Magician', caster_level=20, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=19, max_melee=16, max_bashkick=0, max_backstab=0, lt_proc=20, ds=21, desc='Min'))
        pet_level_list.append(PetLevel(rank=2, pet_level=20, max_melee=18, max_bashkick=0, max_backstab=0, lt_proc=21, ds=22))
        pet_level_list.append(PetLevel(rank=3, pet_level=21, max_melee=20, max_bashkick=0, max_backstab=0, lt_proc=22, ds=23))
        pet_level_list.append(PetLevel(rank=4, pet_level=22, max_melee=22, max_bashkick=0, max_backstab=0, lt_proc=23, ds=24))
        pet_level_list.append(PetLevel(rank=5, pet_level=23, max_melee=23, max_bashkick=0, max_backstab=0, lt_proc=24, ds=25, desc='Max'))
        pet_spell = PetSpell('Summoning', 'Magician', caster_level=24, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=22, max_melee=20, max_bashkick=0, max_backstab=0, lt_proc=23, ds=24, desc='Min'))
        pet_level_list.append(PetLevel(rank=2, pet_level=23, max_melee=22, max_bashkick=0, max_backstab=0, lt_proc=24, ds=25))
        pet_level_list.append(PetLevel(rank=3, pet_level=24, max_melee=23, max_bashkick=0, max_backstab=0, lt_proc=25, ds=26))
        pet_level_list.append(PetLevel(rank=4, pet_level=25, max_melee=26, max_bashkick=0, max_backstab=0, lt_proc=26, ds=27))
        pet_level_list.append(PetLevel(rank=5, pet_level=26, max_melee=28, max_bashkick=0, max_backstab=0, lt_proc=27, ds=28, desc='Max'))
        pet_spell = PetSpell('Greater Summoning', 'Magician', caster_level=29, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        # todo missing mage 34+ pets

        # mage epic pet
        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=49, max_melee=67, max_bashkick=27, max_backstab=0, lt_proc=143, ds=50))
        pet_spell = PetSpell('Manifest Elements', 'Magician', caster_level=50, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

#################################################################################################
