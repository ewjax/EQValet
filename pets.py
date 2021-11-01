
import re



class PetStats:

    def __init__(self, rank, pet_level, max_melee, max_bashkick, max_backstab, lifetap):

        self.rank           = rank
        self.pet_level      = pet_level
        self.max_melee      = max_melee
        self.max_bashkick   = max_bashkick
        self.max_backstab   = max_backstab
        self.lifetap        = lifetap


    # overload funciton to allow object to print() to screen in sensible manner, for debugging with print()
    def __repr__(self):

        return '({}, {}, {}, {}, {}, {})\n'.format(self.rank,
                                                   self.pet_level,
                                                   self.max_melee,
                                                   self.max_bashkick,
                                                   self.max_backstab,
                                                   self.lifetap)




#
# class for a Pet spell
#
class PetTemplate:

    # ctor
    def __init__(self, spell_name, eq_class, caster_level, pet_stats_list):

        self.spell_name     = spell_name
        self.eq_class       = eq_class
        self.caster_level   = caster_level
        self.pet_stats_list = pet_stats_list


    # overload funciton to allow object to print() to screen in sensible manner, for debugging with print()
    def __repr__(self):

        return '({}, {}, {}, \n{})'.format(self.spell_name,
                                           self.eq_class,
                                           self.caster_level,
                                           self.pet_stats_list)

#
# class for an actual pet
#
class Pet:

    # ctor
    def __init__(self, pet_template):

        self.pet_name           = None
        self.name_pending       = True

        # keep track of the pet and what level it is
        self.pet_template       = pet_template
        self.max_melee          = 0
        self.pet_rank           = 0
        self.pet_level          = 0

    def created_report(self):
        rv = 'Pet created: {}'.format(self.pet_name)
        if self.pet_template:
            rv += ' ({})'.format(self.pet_template.spell_name)

        return rv

    def __repr__(self):
        rv = 'Pet: {}, Level: {}, Max Melee: {}, Rank (1-{}): {}'.format(self.pet_name, self.pet_level, self.max_melee, len(self.pet_template.pet_stats_list), self.pet_rank)
        if self.pet_template:
            rv += ' ({})'.format(self.pet_template.spell_name)
        return rv


#
# class to do all the pet tracking work
class PetTracker:

    # ctor
    def __init__(self, client):

        # pointer to the discord client for comms
        self.client         = client

        self.current_pet    = None


        # list of all pets
#        self.all_pets       = list()
        self.all_pets       = []


        # set up the templates for the pets
        self.pet_dict       = {}
#        pet_stat_list = list()
        pet_stat_list       = []
        pet_stat_list.append(PetStats(rank = 1, pet_level = 6, max_melee = 8, max_bashkick = 8, max_backstab = 0, lifetap = 0))
        pet_stat_list.append(PetStats(rank = 2, pet_level = 7, max_melee = 10, max_bashkick = 10, max_backstab = 0, lifetap = 0))
        pet_stat_list.append(PetStats(rank = 3, pet_level = 8, max_melee = 12, max_bashkick = 12, max_backstab = 0, lifetap = 0))
        pet_stat_list.append(PetStats(rank = 4, pet_level = 9, max_melee = 14, max_bashkick = 13, max_backstab = 0, lifetap = 0))
        pet_template = PetTemplate('Bone Walk', 'Necro', caster_level = 8, pet_stats_list = pet_stat_list.copy())
        self.pet_dict['Bone Walk'] = pet_template

        pet_stat_list       = []
        pet_stat_list.append(PetStats(rank = 1, pet_level = 37, max_melee = 47, max_bashkick = 22, max_backstab = 0, lifetap = 38))
        pet_stat_list.append(PetStats(rank = 2, pet_level = 38, max_melee = 49, max_bashkick = 23, max_backstab = 0, lifetap = 39))
        pet_stat_list.append(PetStats(rank = 3, pet_level = 39, max_melee = 51, max_bashkick = 23, max_backstab = 0, lifetap = 40))
        pet_stat_list.append(PetStats(rank = 4, pet_level = 40, max_melee = 52, max_bashkick = 24, max_backstab = 0, lifetap = 41))
        pet_stat_list.append(PetStats(rank = 5, pet_level = 41, max_melee = 55, max_bashkick = 24, max_backstab = 0, lifetap = 42))
        pet_template = PetTemplate('Invoke Death', 'Necro', caster_level = 49, pet_stats_list = pet_stat_list.copy())
        self.pet_dict['Invoke Death'] = pet_template

        pet_stat_list.clear()
        pet_stat_list.append(PetStats(rank = 1, pet_level = 40, max_melee = 49, max_bashkick = 0, max_backstab = 147, lifetap = 40))
        pet_stat_list.append(PetStats(rank = 2, pet_level = 41, max_melee = 51, max_bashkick = 0, max_backstab = 153, lifetap = 41))
        pet_stat_list.append(PetStats(rank = 3, pet_level = 42, max_melee = 52, max_bashkick = 0, max_backstab = 159, lifetap = 42))
        pet_stat_list.append(PetStats(rank = 4, pet_level = 43, max_melee = 55, max_bashkick = 0, max_backstab = 165, lifetap = 43))
        pet_stat_list.append(PetStats(rank = 5, pet_level = 44, max_melee = 56, max_bashkick = 0, max_backstab = 171, lifetap = 44))
        pet_template = PetTemplate('Minion of Shadows', 'Necro', caster_level = 53, pet_stats_list = pet_stat_list.copy())
        self.pet_dict['Minion of Shadows'] = pet_template

        pet_stat_list.clear()
        pet_stat_list.append(PetStats(rank = 1, pet_level = 44, max_melee = 49, max_bashkick = 23, max_backstab = 0, lifetap = 0))
        pet_stat_list.append(PetStats(rank = 2, pet_level = 45, max_melee = 51, max_bashkick = 23, max_backstab = 0, lifetap = 0))
        pet_stat_list.append(PetStats(rank = 3, pet_level = 46, max_melee = 52, max_bashkick = 24, max_backstab = 0, lifetap = 0))
        pet_stat_list.append(PetStats(rank = 4, pet_level = 47, max_melee = 55, max_bashkick = 24, max_backstab = 0, lifetap = 0))
        pet_stat_list.append(PetStats(rank = 5, pet_level = 48, max_melee = 56, max_bashkick = 25, max_backstab = 0, lifetap = 0))
        pet_template = PetTemplate('Zumaik`s Animation', 'Enchanter', caster_level = 55, pet_stats_list = pet_stat_list.copy())
        self.pet_dict['Zumaik`s Animation'] = pet_template

        pet_stat_list.clear()
        pet_stat_list.append(PetStats(rank = 0, pet_level = 0, max_melee = 0, max_bashkick = 0, max_backstab = 0, lifetap = 0))
        pet_template = PetTemplate('CharmPet', 'UnknownClass', caster_level = 0, pet_stats_list = pet_stat_list.copy())
        self.pet_dict['CharmPet'] = pet_template


#        print(self.pet_dict)



    # check for pet related items
    async def process_line(self, line):

        # cut off the leading date-time stamp info
        trunc_line = line[27:]


        # check for a few ways in which the pet can be lost
        if self.current_pet:

            # zoning?
            target = '^LOADING, PLEASE WAIT'
            m1 = re.match(target, trunc_line)

            # pet reclaimed?
            target = '^{} disperses'.format(self.current_pet.pet_name)
            m2 = re.match(target, trunc_line)

            # pet died?
            target = '^{} says, \'Sorry to have failed you, oh Great One'.format(self.current_pet.pet_name)
            m3 = re.match(target, trunc_line)

            # somehow pet is gone
            target = r'^You don\'t have a pet to command!'
            m4 = re.match(target, trunc_line)

            if (m1 or m2 or m3 or m4):
                await self.client.send('Pet {} died'.format(self.current_pet.pet_name))
                self.current_pet = None


        # search for cast message
        target = r'^You begin casting (?P<spell_name>[\w` ]+)\.'

        # return value m is either None of an object with information about the RE search
        m = re.match(target, trunc_line)
        if m:

            # fetch the spell name
            spell_name = m.group('spell_name')
#            print(spell_name)

            # does the spell name match one of the pets we know about?
            if spell_name in self.pet_dict:
                pet_template = self.pet_dict[spell_name]
                self.current_pet = Pet(pet_template)
                await self.client.send('*Pet being created from spell ({}), name TBD*'.format(spell_name))


        # if the flag is set that we have a pet and don't know the name yet, search for pet name
        if ((self.current_pet) and (self.current_pet.name_pending)):
            target = r'^(?P<pet_name>[\w ]+) says \'At your service Master.'

            # return value m is either None of an object with information about the RE search
            m = re.match(target, trunc_line)
            if m:

                # fetch the pet name
                pet_name = m.group('pet_name')
                self.current_pet.pet_name = pet_name
                self.current_pet.name_pending = False

                self.all_pets.append(self.current_pet)
                await self.client.send(self.current_pet.created_report())


        # if we have a pet, scan for the max melee hit value, and search for lifetaps
        if self.current_pet:

            # look for max melee
            target = r'^{} (hits|slashes|pierces|crushes|claws|bites) (?P<target_name>[\w` ]+) for (?P<damage>[\d]+) points of damage'.format(self.current_pet.pet_name)
            # return value m is either None of an object with information about the RE search
            m = re.match(target, trunc_line)
            if m:
                # fetch the damage
                damage = int(m.group('damage'))

                # is this new max?
                if damage > self.current_pet.max_melee:
                    self.current_pet.max_melee = damage

                    # find the new rank
                    for petstat in self.current_pet.pet_template.pet_stats_list:
                        if petstat.max_melee == damage:
                            self.current_pet.pet_rank   = petstat.rank
                            self.current_pet.pet_level  = petstat.pet_level

                    # announce the pet rank
                    await self.client.send(self.current_pet)
                    await self.client.send('*Identified via max melee damage*')

            # look for lifetap
            target = r'^{} beams a smile at (?P<target_name>[\w` ]+)'.format(self.current_pet.pet_name)
            m = re.match(target, trunc_line)
            if m:
                # read the next line for the damage message
                next_line = self.client.elf.readline()
                next_trunc_line = next_line[27:]
                next_target = r'^(?P<target_name>[\w` ]+) was hit by non-melee for (?P<damage>[\d]+) points of damage'

                next_m = re.match(next_target, next_trunc_line)
                if next_m:
                    # fetch the damage
                    lifetap_damage = int(next_m.group('damage'))

                    # find the pet rank
                    for petstat in self.current_pet.pet_template.pet_stats_list:
                        if (petstat.lifetap == lifetap_damage) and (self.current_pet.pet_rank != petstat.rank):
                            self.current_pet.pet_rank   = petstat.rank
                            self.current_pet.pet_level  = petstat.pet_level

                            # announce the pet rank
                            await self.client.send(self.current_pet)
                            await self.client.send('*Identified via lifetap signature*')


        # watch for pet leader commands, and check that our pet name matches
        # this is useful if somehow our pet name is goofed up
        target = r'^(?P<pet_name>[\w` ]+) says \'My leader is (?P<char_name>[\w` ]+)'
        m = re.match(target, trunc_line)
        if m:
            pet_name    = m.group('pet_name')
            char_name   = m.group('char_name')

            # if a pet just declared our character as the leader...
            if (char_name == self.client.elf.char_name):

                # announce the pet name
                await self.client.send('Pet name = {}'.format(pet_name))

                # no pet known to EQValet?
                if self.current_pet is None:

                    # then we probably have a charmed pet
                    spell_name = 'CharmPet'

                    # does the spell name match one of the pets we know about?
                    if spell_name in self.pet_dict:
                        pet_template = self.pet_dict[spell_name]
                        self.current_pet = Pet(pet_template)
                        self.current_pet.pet_name = pet_name
                        self.current_pet.name_pending = False
                        self.current_pet.pet_rank       = 0
                        self.current_pet.max_melee      = 0
                        self.pet_rank       = 0
                        self.max_melee      = 0

                        self.all_pets.append(self.current_pet)
                        await self.client.send(self.current_pet.created_report())

                # ok somehow EQValet thinks we have a pet, but the name is goofed up, so just reset the max_melee and pet_rank fields and let them get
                # determined again
                elif (self.current_pet.pet_name != pet_name):
                    self.current_pet.pet_name       = pet_name
                    self.current_pet.name_pending   = False
                    self.current_pet.pet_rank       = 0
                    self.current_pet.max_melee      = 0
                    self.pet_rank       = 0
                    self.max_melee      = 0
                    await self.client.send(self.current_pet.created_report())



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

                # no pet known to EQValet?
                if self.current_pet is None:

                    # then we probably have a charmed pet
                    spell_name = 'CharmPet'

                    # does the spell name match one of the pets we know about?
                    if spell_name in self.pet_dict:
                        pet_template = self.pet_dict[spell_name]
                        self.current_pet = Pet(pet_template)
                        self.current_pet.pet_name = pet_name
                        self.current_pet.name_pending = False

                        self.all_pets.append(self.current_pet)
                        await self.client.send(self.current_pet.created_report())

                # ok somehow EQValet thinks we have a pet, but the name is goofed up, so just reset the max_melee and pet_rank fields and let them get
                # determined again
                else:
                    self.current_pet.pet_name       = pet_name
                    self.current_pet.name_pending   = False
                    self.current_pet.pet_rank       = 0
                    self.current_pet.max_melee      = 0
                    self.pet_rank       = 0
                    self.max_melee      = 0
                    await self.client.send(self.current_pet.created_report())





def main():

    petdict = {}
    petlist = []

    pet_stat_list = list()
    pet_stat_list.append(PetStats(rank = 5, pet_level = 37, max_melee = 47, max_bashkick = 22, max_backstab = 0, lifetap = 38))
    pet_stat_list.append(PetStats(rank = 4, pet_level = 38, max_melee = 49, max_bashkick = 23, max_backstab = 0, lifetap = 39))
    pet_stat_list.append(PetStats(rank = 3, pet_level = 39, max_melee = 51, max_bashkick = 23, max_backstab = 0, lifetap = 40))
    pet_stat_list.append(PetStats(rank = 2, pet_level = 40, max_melee = 52, max_bashkick = 24, max_backstab = 0, lifetap = 41))
    pet_stat_list.append(PetStats(rank = 1, pet_level = 41, max_melee = 55, max_bashkick = 24, max_backstab = 0, lifetap = 42))

    pet_template = PetTemplate('Invoke Death', 'Necro', caster_level = 49, pet_stats_list = pet_stat_list)
    petdict['Invoke Death'] = pet_template
    petlist.append(pet_template)

#    print(pet_template)
#    print(pets)


    pet_stat_list.clear()
    pet_stat_list.append(PetStats(rank = 5, pet_level = 40, max_melee = 49, max_bashkick = 0, max_backstab = 147, lifetap = 40))
    pet_stat_list.append(PetStats(rank = 4, pet_level = 41, max_melee = 51, max_bashkick = 0, max_backstab = 153, lifetap = 41))
    pet_stat_list.append(PetStats(rank = 3, pet_level = 42, max_melee = 52, max_bashkick = 0, max_backstab = 159, lifetap = 42))
    pet_stat_list.append(PetStats(rank = 2, pet_level = 43, max_melee = 55, max_bashkick = 0, max_backstab = 165, lifetap = 43))
    pet_stat_list.append(PetStats(rank = 1, pet_level = 44, max_melee = 56, max_bashkick = 0, max_backstab = 171, lifetap = 44))

    pet_template = PetTemplate('Minion of Shadows', 'Necro', caster_level = 53, pet_stats_list = pet_stat_list)
    petdict['Minion of Shadows'] = pet_template
    petlist.append(pet_template)


#    print(pet_template)


    pet_stat_list.clear()
    pet_stat_list.append(PetStats(rank = 5, pet_level = 44, max_melee = 49, max_bashkick = 23, max_backstab = 0, lifetap = 0))
    pet_stat_list.append(PetStats(rank = 4, pet_level = 45, max_melee = 51, max_bashkick = 23, max_backstab = 0, lifetap = 0))
    pet_stat_list.append(PetStats(rank = 3, pet_level = 46, max_melee = 52, max_bashkick = 24, max_backstab = 0, lifetap = 0))
    pet_stat_list.append(PetStats(rank = 2, pet_level = 47, max_melee = 55, max_bashkick = 24, max_backstab = 0, lifetap = 0))
    pet_stat_list.append(PetStats(rank = 1, pet_level = 48, max_melee = 56, max_bashkick = 25, max_backstab = 0, lifetap = 0))

    pet_template = PetTemplate('Zumaik`s Animation', 'Enchanter', caster_level = 55, pet_stats_list = pet_stat_list)
    petdict['Zumaik`s Animation'] = pet_template
    petlist.append(pet_template)


#    print(pet_template)

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


