import re

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

    def __init__(self, rank: int, pet_level: int, max_melee: int, max_bashkick: int, max_backstab: int, lifetap: int) -> None:
        self.rank = rank
        self.pet_level = pet_level
        self.max_melee = max_melee
        self.max_bashkick = max_bashkick
        self.max_backstab = max_backstab
        self.lifetap = lifetap

    # overload function to allow object to print() to screen in sensible manner, for debugging with print()
    def __repr__(self):
        return '({}, {}, {}, {}, {}, {})\n'.format(self.rank,
                                                   self.pet_level,
                                                   self.max_melee,
                                                   self.max_bashkick,
                                                   self.max_backstab,
                                                   self.lifetap)


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
    def __init__(self, spell_name: str, eq_class: str, caster_level: int, pet_level_list: list[PetLevel]) -> None:
        self.spell_name = spell_name
        self.eq_class = eq_class
        self.caster_level = caster_level
        self.pet_level_list = pet_level_list

    # overload function to allow object to print() to screen in sensible manner, for debugging with print()
    def __repr__(self):
        return '({}, {}, {}, \n{})'.format(self.spell_name,
                                           self.eq_class,
                                           self.caster_level,
                                           self.pet_level_list)


#################################################################################################

#
# class for an actual pet in game
#
class Pet:
    """
    Class for an actual pet in game, its name, level, max melee, etc
    """

    # ctor
    def __init__(self, pet_spell: PetSpell) -> None:

        self.pet_name = None
        self.name_pending = True
        self.lifetap_pending = False

        # keep track of the pet and what level it is
        self.pet_spell = pet_spell
        self.max_melee = 0
        self.pet_rank = 0
        self.pet_level = 0

    def created_report(self):
        rv = 'Pet created: {}'.format(self.pet_name)
        if self.pet_spell:
            rv += ' ({})'.format(self.pet_spell.spell_name)

        return rv

    def __repr__(self):
        rv = 'Pet: **{}**, Level: {}, Max Melee: {}, Rank (1-{}): {}'.format(self.pet_name, self.pet_level, self.max_melee,
                                                                             len(self.pet_spell.pet_level_list),
                                                                             self.pet_rank)
        if self.pet_spell:
            rv += f' ({self.pet_spell.spell_name})'
        return rv


#################################################################################################

#
# class to do all the pet tracking work
#
class PetParser:
    """
    Class to do all the pet tracking work
    """

    # ctor
    def __init__(self):

        # default is to parse for pet info
        self.parse = True

        # pointer to current pet
        self.current_pet = None

        # list of all pets
        # not really used for now, but keeping it in case this idea is needed later
        # perhaps for some function that needs to know about all pets, etc
        self.all_pets = []

        # a dictionary of pet spells, keys = Pet Spell Names, values = associated PetSpell objects
        self.pet_dict = {}
        self.load_pet_dict()

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
    def process_line(self, line: str) -> None:
        """
        The parse logic for this particular parser.

        :param line: complete line to be parsed, i.e. timestamp and content
        """
        # cut off the leading date-time stamp info
        trunc_line = line[27:]

        # check for toggling the parse on/off
        target = r'^\.pt '
        m = re.match(target, trunc_line)
        if m:
            if self.parse:
                self.parse = False
                onoff = 'Off'
            else:
                self.parse = True
                onoff = 'On'

            starprint(f'Pet Parsing: {onoff}')

        if self.parse:

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

                # check for any of the pet died messages
                if m1 or m2 or m3 or m4:
                    starprint(f'Pet {self.current_pet.pet_name} died/lost')
                    self.current_pet = None

            #
            # search for cast message, see if any of the pet spells we know about are being cast
            #
            target = r'^You begin casting (?P<spell_name>[\w`\' ]+)\.'

            # return value m is either None of an object with information about the RE search
            m = re.match(target, trunc_line)
            if m:

                # fetch the spell name
                spell_name = m.group('spell_name')

                # does the spell name match one of the pets we know about?
                if spell_name in self.pet_dict:
                    pet_spell = self.pet_dict[spell_name]
                    self.current_pet = Pet(pet_spell)
                    starprint(f'Pet being created from spell ({spell_name}), name TBD')

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
            # if the flag is set that we have a lifetap message and don't have the amount yet,
            # search for the non-melee message
            #
            if self.current_pet and self.current_pet.lifetap_pending:

                target = r'^(?P<target_name>[\w` ]+) was hit by non-melee for (?P<damage>[\d]+) points of damage'
                m = re.match(target, trunc_line)
                if m:

                    # fetch the damage, and reset the pending flag
                    dmg = int(m.group('damage'))
                    self.current_pet.lifetap_pending = False

                    # find the pet rank
                    for petstat in self.current_pet.pet_spell.pet_level_list:
                        if (petstat.lifetap == dmg) and (self.current_pet.pet_rank != petstat.rank):
                            self.current_pet.pet_rank = petstat.rank
                            self.current_pet.pet_level = petstat.pet_level

                            # announce the pet rank
                            starprint(self.current_pet)
                            starprint('  (Identified via lifetap signature)')

            #
            # if we have a pet, do several scans....
            #
            if self.current_pet:

                #
                # look for lifetap 'beams a smile' message coming from our pet
                #
                target = r'^{} beams a smile at (?P<target_name>[\w` ]+)'.format(self.current_pet.pet_name)
                m = re.match(target, trunc_line, re.IGNORECASE)
                if m:
                    self.current_pet.lifetap_pending = True

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
                        for petstat in self.current_pet.pet_spell.pet_level_list:
                            if petstat.max_melee == damage:
                                self.current_pet.pet_rank = petstat.rank
                                self.current_pet.pet_level = petstat.pet_level

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
        pet_level_list.append(PetLevel(rank=1, pet_level=6, max_melee=8, max_bashkick=8, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=7, max_melee=10, max_bashkick=10, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=8, max_melee=12, max_bashkick=12, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=9, max_melee=14, max_bashkick=13, max_backstab=0, lifetap=0))
        pet_spell = PetSpell('Bone Walk', 'Necro', caster_level=8, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=8, max_melee=10, max_bashkick=10, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=9, max_melee=12, max_bashkick=12, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=10, max_melee=14, max_bashkick=14, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=11, max_melee=16, max_bashkick=16, max_backstab=0, lifetap=0))
        pet_spell = PetSpell('Convoke Shadow', 'Necro', caster_level=12, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=12, max_melee=12, max_bashkick=12, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=13, max_melee=14, max_bashkick=14, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=14, max_melee=16, max_bashkick=15, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=15, max_melee=18, max_bashkick=15, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=16, max_melee=20, max_bashkick=16, max_backstab=0, lifetap=0))
        pet_spell = PetSpell('Restless Bones', 'Necro', caster_level=16, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=15, max_melee=14, max_bashkick=14, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=16, max_melee=16, max_bashkick=15, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=17, max_melee=18, max_bashkick=15, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=18, max_melee=20, max_bashkick=16, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=19, max_melee=22, max_bashkick=16, max_backstab=0, lifetap=0))
        pet_spell = PetSpell('Animate Dead', 'Necro', caster_level=20, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=18, max_melee=18, max_bashkick=15, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=19, max_melee=20, max_bashkick=16, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=20, max_melee=22, max_bashkick=16, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=21, max_melee=23, max_bashkick=17, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=22, max_melee=26, max_bashkick=17, max_backstab=0, lifetap=0))
        pet_spell = PetSpell('Haunting Corpse', 'Necro', caster_level=24, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=22, max_melee=20, max_bashkick=16, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=23, max_melee=22, max_bashkick=16, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=24, max_melee=23, max_bashkick=17, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=25, max_melee=26, max_bashkick=17, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=26, max_melee=28, max_bashkick=18, max_backstab=0, lifetap=0))
        pet_spell = PetSpell('Summon Dead', 'Necro', caster_level=29, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=25, max_melee=23, max_bashkick=17, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=26, max_melee=26, max_bashkick=17, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=27, max_melee=28, max_bashkick=18, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=28, max_melee=30, max_bashkick=18, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=29, max_melee=32, max_bashkick=19, max_backstab=0, lifetap=0))
        pet_spell = PetSpell('Invoke Shadow', 'Necro', caster_level=34, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=29, max_melee=31, max_bashkick=18, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=30, max_melee=33, max_bashkick=19, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=31, max_melee=35, max_bashkick=19, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=32, max_melee=37, max_bashkick=20, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=33, max_melee=39, max_bashkick=20, max_backstab=0, lifetap=0))
        pet_spell = PetSpell('Malignant Dead', 'Necro', caster_level=39, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=37, max_melee=47, max_bashkick=22, max_backstab=0, lifetap=38))
        pet_level_list.append(PetLevel(rank=2, pet_level=38, max_melee=49, max_bashkick=23, max_backstab=0, lifetap=39))
        pet_level_list.append(PetLevel(rank=3, pet_level=39, max_melee=51, max_bashkick=23, max_backstab=0, lifetap=40))
        pet_level_list.append(PetLevel(rank=4, pet_level=40, max_melee=52, max_bashkick=24, max_backstab=0, lifetap=41))
        pet_level_list.append(PetLevel(rank=5, pet_level=41, max_melee=55, max_bashkick=24, max_backstab=0, lifetap=42))
        pet_level_list.append(PetLevel(rank=6, pet_level=42, max_melee=57, max_bashkick=25, max_backstab=0, lifetap=43))
        pet_spell = PetSpell('Invoke Death', 'Necro', caster_level=49, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=40, max_melee=49, max_bashkick=0, max_backstab=147, lifetap=40))
        pet_level_list.append(PetLevel(rank=2, pet_level=41, max_melee=51, max_bashkick=0, max_backstab=153, lifetap=41))
        pet_level_list.append(PetLevel(rank=3, pet_level=42, max_melee=52, max_bashkick=0, max_backstab=159, lifetap=42))
        pet_level_list.append(PetLevel(rank=4, pet_level=43, max_melee=55, max_bashkick=0, max_backstab=165, lifetap=43))
        pet_level_list.append(PetLevel(rank=5, pet_level=44, max_melee=56, max_bashkick=0, max_backstab=171, lifetap=44))
        pet_level_list.append(PetLevel(rank=6, pet_level=45, max_melee=59, max_bashkick=0, max_backstab=177, lifetap=45))
        pet_spell = PetSpell('Minion of Shadows', 'Necro', caster_level=53, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=40, max_melee=51, max_bashkick=63, max_backstab=0, lifetap=41))
        pet_level_list.append(PetLevel(rank=2, pet_level=41, max_melee=52, max_bashkick=65, max_backstab=0, lifetap=42))
        pet_level_list.append(PetLevel(rank=3, pet_level=42, max_melee=55, max_bashkick=66, max_backstab=0, lifetap=43))
        pet_level_list.append(PetLevel(rank=4, pet_level=43, max_melee=56, max_bashkick=68, max_backstab=0, lifetap=44))
        pet_level_list.append(PetLevel(rank=5, pet_level=44, max_melee=59, max_bashkick=69, max_backstab=0, lifetap=45))
        pet_level_list.append(PetLevel(rank=6, pet_level=45, max_melee=61, max_bashkick=71, max_backstab=0, lifetap=46))
        pet_spell = PetSpell('Servant of Bones', 'Necro', caster_level=56, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=43, max_melee=52, max_bashkick=24, max_backstab=0, lifetap=44))
        pet_level_list.append(PetLevel(rank=2, pet_level=44, max_melee=55, max_bashkick=24, max_backstab=0, lifetap=45))
        pet_level_list.append(PetLevel(rank=3, pet_level=45, max_melee=56, max_bashkick=25, max_backstab=0, lifetap=46))
        pet_level_list.append(PetLevel(rank=4, pet_level=46, max_melee=59, max_bashkick=25, max_backstab=0, lifetap=47))
        pet_level_list.append(PetLevel(rank=5, pet_level=47, max_melee=61, max_bashkick=26, max_backstab=0, lifetap=48))
        pet_level_list.append(PetLevel(rank=6, pet_level=48, max_melee=62, max_bashkick=26, max_backstab=0, lifetap=49))
        pet_spell = PetSpell('Emissary of Thule', 'Necro', caster_level=59, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        #
        # Enchanter pets
        #
        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=1, max_melee=7, max_bashkick=0, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=2, max_melee=9, max_bashkick=0, max_backstab=0, lifetap=0))
        pet_spell = PetSpell('Pendril\'s Animation', 'Enchanter', caster_level=1, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=3, max_melee=9, max_bashkick=0, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=4, max_melee=10, max_bashkick=0, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=5, max_melee=12, max_bashkick=0, max_backstab=0, lifetap=0))
        pet_spell = PetSpell('Juli`s Animation', 'Enchanter', caster_level=4, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=6, max_melee=9, max_bashkick=8, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=7, max_melee=10, max_bashkick=10, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=8, max_melee=12, max_bashkick=12, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=9, max_melee=14, max_bashkick=13, max_backstab=0, lifetap=0))
        pet_spell = PetSpell('Mircyl\'s Animation', 'Enchanter', caster_level=8, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=9, max_melee=11, max_bashkick=11, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=10, max_melee=13, max_bashkick=13, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=11, max_melee=15, max_bashkick=14, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=12, max_melee=17, max_bashkick=15, max_backstab=0, lifetap=0))
        pet_spell = PetSpell('Kilan`s Animation', 'Enchanter', caster_level=12, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=12, max_melee=12, max_bashkick=12, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=13, max_melee=14, max_bashkick=14, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=14, max_melee=16, max_bashkick=15, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=15, max_melee=18, max_bashkick=15, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=16, max_melee=20, max_bashkick=16, max_backstab=0, lifetap=0))
        pet_spell = PetSpell('Shalee`s Animation', 'Enchanter', caster_level=16, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=16, max_melee=14, max_bashkick=14, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=17, max_melee=16, max_bashkick=15, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=18, max_melee=19, max_bashkick=15, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=19, max_melee=20, max_bashkick=16, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=20, max_melee=22, max_bashkick=16, max_backstab=0, lifetap=0))
        pet_spell = PetSpell('Sisna`s Animation', 'Enchanter', caster_level=20, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=19, max_melee=18, max_bashkick=15, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=20, max_melee=20, max_bashkick=16, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=21, max_melee=22, max_bashkick=16, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=22, max_melee=23, max_bashkick=17, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=23, max_melee=26, max_bashkick=17, max_backstab=0, lifetap=0))
        pet_spell = PetSpell('Sagar`s Animation', 'Enchanter', caster_level=24, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=22, max_melee=20, max_bashkick=16, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=23, max_melee=22, max_bashkick=16, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=24, max_melee=23, max_bashkick=17, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=25, max_melee=26, max_bashkick=17, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=26, max_melee=28, max_bashkick=18, max_backstab=0, lifetap=0))
        pet_spell = PetSpell('Uleen`s Animation', 'Enchanter', caster_level=29, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=25, max_melee=26, max_bashkick=17, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=26, max_melee=28, max_bashkick=18, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=27, max_melee=30, max_bashkick=18, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=28, max_melee=32, max_bashkick=19, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=29, max_melee=34, max_bashkick=19, max_backstab=0, lifetap=0))
        pet_spell = PetSpell('Boltran`s Animation', 'Enchanter', caster_level=34, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=29, max_melee=32, max_bashkick=19, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=30, max_melee=34, max_bashkick=19, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=31, max_melee=36, max_bashkick=20, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=32, max_melee=38, max_bashkick=20, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=33, max_melee=40, max_bashkick=21, max_backstab=0, lifetap=0))
        pet_spell = PetSpell('Aanya\'s Animation', 'Enchanter', caster_level=39, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=33, max_melee=40, max_bashkick=21, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=34, max_melee=42, max_bashkick=21, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=35, max_melee=44, max_bashkick=22, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=36, max_melee=45, max_bashkick=22, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=37, max_melee=48, max_bashkick=23, max_backstab=0, lifetap=0))
        pet_spell = PetSpell('Yegoreff`s Animation', 'Enchanter', caster_level=44, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=37, max_melee=45, max_bashkick=22, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=38, max_melee=47, max_bashkick=22, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=39, max_melee=49, max_bashkick=23, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=40, max_melee=51, max_bashkick=23, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=41, max_melee=52, max_bashkick=24, max_backstab=0, lifetap=0))
        pet_spell = PetSpell('Kintaz`s Animation', 'Enchanter', caster_level=49, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=44, max_melee=49, max_bashkick=23, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=45, max_melee=51, max_bashkick=23, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=46, max_melee=52, max_bashkick=24, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=47, max_melee=55, max_bashkick=24, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=48, max_melee=56, max_bashkick=25, max_backstab=0, lifetap=0))
        pet_spell = PetSpell('Zumaik`s Animation', 'Enchanter', caster_level=55, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        #
        # generic charmed pets
        #
        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=0, pet_level=0, max_melee=0, max_bashkick=0, max_backstab=0, lifetap=0))
        pet_spell = PetSpell('CharmPet', 'UnknownClass', caster_level=0, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        #
        # Shaman pets
        #
        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=22, max_melee=22, max_bashkick=16, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=23, max_melee=23, max_bashkick=17, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=24, max_melee=26, max_bashkick=17, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=25, max_melee=28, max_bashkick=18, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=26, max_melee=30, max_bashkick=18, max_backstab=0, lifetap=0))
        pet_spell = PetSpell('Companion Spirit', 'Shaman', caster_level=34, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=24, max_melee=27, max_bashkick=17, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=25, max_melee=28, max_bashkick=18, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=26, max_melee=31, max_bashkick=18, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=27, max_melee=33, max_bashkick=19, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=28, max_melee=35, max_bashkick=19, max_backstab=0, lifetap=0))
        pet_spell = PetSpell('Vigilant Spirit', 'Shaman', caster_level=39, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        pet_level_list.clear()
        pet_level_list.append(PetLevel(rank=1, pet_level=28, max_melee=35, max_bashkick=19, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=2, pet_level=29, max_melee=37, max_bashkick=20, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=3, pet_level=30, max_melee=39, max_bashkick=20, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=4, pet_level=31, max_melee=41, max_bashkick=21, max_backstab=0, lifetap=0))
        pet_level_list.append(PetLevel(rank=5, pet_level=32, max_melee=43, max_bashkick=21, max_backstab=0, lifetap=0))
        pet_spell = PetSpell('Guardian Spirit', 'Shaman', caster_level=44, pet_level_list=pet_level_list.copy())
        self.pet_dict[pet_spell.spell_name] = pet_spell

        # todo need shaman pets for 49, 55

        # todo need all mage pets


#################################################################################################


def main():
    petdict = {}
    petlist = []

    pet_level_list = list()
    pet_level_list.append(PetLevel(rank=5, pet_level=37, max_melee=47, max_bashkick=22, max_backstab=0, lifetap=38))
    pet_level_list.append(PetLevel(rank=4, pet_level=38, max_melee=49, max_bashkick=23, max_backstab=0, lifetap=39))
    pet_level_list.append(PetLevel(rank=3, pet_level=39, max_melee=51, max_bashkick=23, max_backstab=0, lifetap=40))
    pet_level_list.append(PetLevel(rank=2, pet_level=40, max_melee=52, max_bashkick=24, max_backstab=0, lifetap=41))
    pet_level_list.append(PetLevel(rank=1, pet_level=41, max_melee=55, max_bashkick=24, max_backstab=0, lifetap=42))

    pet_spell = PetSpell('Invoke Death', 'Necro', caster_level=49, pet_level_list=pet_level_list)
    petdict['Invoke Death'] = pet_spell
    petlist.append(pet_spell)

    #    print(pet_spell)
    #    print(pets)

    pet_level_list.clear()
    pet_level_list.append(PetLevel(rank=5, pet_level=40, max_melee=49, max_bashkick=0, max_backstab=147, lifetap=40))
    pet_level_list.append(PetLevel(rank=4, pet_level=41, max_melee=51, max_bashkick=0, max_backstab=153, lifetap=41))
    pet_level_list.append(PetLevel(rank=3, pet_level=42, max_melee=52, max_bashkick=0, max_backstab=159, lifetap=42))
    pet_level_list.append(PetLevel(rank=2, pet_level=43, max_melee=55, max_bashkick=0, max_backstab=165, lifetap=43))
    pet_level_list.append(PetLevel(rank=1, pet_level=44, max_melee=56, max_bashkick=0, max_backstab=171, lifetap=44))

    pet_spell = PetSpell('Minion of Shadows', 'Necro', caster_level=53, pet_level_list=pet_level_list)
    petdict['Minion of Shadows'] = pet_spell
    petlist.append(pet_spell)

    #    print(pet_spell)

    pet_level_list.clear()
    pet_level_list.append(PetLevel(rank=5, pet_level=44, max_melee=49, max_bashkick=23, max_backstab=0, lifetap=0))
    pet_level_list.append(PetLevel(rank=4, pet_level=45, max_melee=51, max_bashkick=23, max_backstab=0, lifetap=0))
    pet_level_list.append(PetLevel(rank=3, pet_level=46, max_melee=52, max_bashkick=24, max_backstab=0, lifetap=0))
    pet_level_list.append(PetLevel(rank=2, pet_level=47, max_melee=55, max_bashkick=24, max_backstab=0, lifetap=0))
    pet_level_list.append(PetLevel(rank=1, pet_level=48, max_melee=56, max_bashkick=25, max_backstab=0, lifetap=0))

    pet_spell = PetSpell('Zumaik`s Animation', 'Enchanter', caster_level=55, pet_level_list=pet_level_list)
    petdict['Zumaik`s Animation'] = pet_spell
    petlist.append(pet_spell)

    #    print(pet_spell)

    #    print(petdict)
    #    print(petlist)

    p = petdict['Minion of Shadows']
    print(p)

    bb = ('Nonexistent' in petdict)
    print(bb)


#    p = petdict['Nonexistent']
#    print(p)


if __name__ == '__main__':
    main()
