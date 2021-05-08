import random

class Bit:
    def __init__(self, secrecy, description, age, year, ongoing=False, source='life'):
        """
        Class that defines an bit in terms of people involved and the 
        level of secrecy. 
        """
        # Who is this about?
        self.subject = []
        self.action = ""
        self.object = []
        self.circumstances = []

        # Who was otherwise involved but not condemned by it?
        self.involved = []

        # Who was the source of this bit?
        self.source = source

        # How secret is this bit? [0 - 5]
        self.secrecy = secrecy

        # Which sins / virtues does this relate to? [optional]
        self.meaning = {}

        # When did this take place and is it still taking place?
        self.age = age
        self.year = year
        self.ongoing = ongoing

        # Description of bit
        self.description = description

    def jsonify(self):
        bit = {}
        # bit["concerns"] = self.concerns
        bit["involved"] = self.involved
        bit["source"] = self.source
        bit["secrecy"] = self.secrecy
        bit["meaning"] = self.meaning
        bit["age / ongoing"] = [self.age, self.ongoing]
        bit["description"] = self.description
        return bit

class Knowledge:
    def __init__(self, person):
        self.person = person
        self.context = person.context
        self.bits = {}
        self.all_bits = []
        self.knowledge = {}

    def add_bit(self, secrecy, description, ongoing=False):
        bit = Bit(secrecy, description, self.person.age, self.context.year, ongoing)
        self.add_bit_premade(bit)

    def add_bit_premade(self, bit):
        if bit.secrecy not in self.bits:
            self.bits[bit.secrecy] = []

        self.bits[bit.secrecy].append(bit)
        self.all_bits.append(bit)

    def add_knowledge(self, object_key, bit):
        if object_key not in self.knowledge:
            self.knowledge[object_key] = {}

        if bit.secrecy not in self.knowledge[object_key][bit.secrecy]:
            self.knowledge[object_key][bit.secrecy] = []

        self.knowledge[object_key][bit.secrecy].append(bit)

    def get_descriptions(self):
        bits = {}
        for el in self.all_bits:
            if el.year not in bits:
                bits[el.year] = []
            bits[el.year].append(el.description)
        return bits

class Trigger:
    def __init__(self, person):
        self.person = person
        self.prev_neglect = False
        self.marriages = 0
        self.dead_children = 0
        self.dead_chidren_bit = False
        self.orphanage = False

    def trait_influence(self, trait, value, source):
        random.seed()
        own_value, own_importance = self.person.personality.get_trait(
            trait)
        chance = 0.1 if own_importance == 'important' else 0.4
        change = 1 if own_value < value else -1

        if random.random() < chance:
            self.person.personality.influence_personality(
                trait, change, source)
            return True
        return False

    """
    LIFE
    """

    def birth(self):
        random.seed()
        if random.random() < self.person.chance_of_dying('birth'):
            self.person.die(' days after being born')
            return True
        return False

    def marriage(self, partner):
        self.person.married = True
        self.person.marriage = self
        if self.person.sex == 'f':
            self.person.names.update_surname('marriage')

        times = ['', 'a second time ', 'a third time ', ' a fourth time ',
                    'the fifth time ', 'the sixth time ', 'the seventh time ']
        self.person.knowledge.add_bit(
            1, f"Got married {times[self.marriages]} to {partner.name} at age {self.person.age}.")
        self.marriages += 1
        if self.orphanage:
            self.person.context.outside.orphanage.adopt(self.person.key)
            self.orphanage = False

    def moved_outoftown(self):
        self.person.knowledge.add_bit(2, f"Moved out of town.")
        # Communicate to network
        return True

    def in_orphanage(self):
        self.person.knowledge.add_bit(1, f"Went to live in the orphanage at age {self.person.age}.")
        self.orphanage = True

    def out_orphanage(self):
        self.person.knowledge.add_bit(2, f"Left orphanage at the age of {self.person.age}.")
        self.orphanage = False

    def childbirth(self):
        random.seed()
        if random.random() < self.person.chance_of_dying('childbirth'):
            self.person.die(' in childbirth')
            return True
        self.person.health -= random.randint(0, 20) * 0.005
        return False

    def had_child(self, child):
        if self.person.sex == 'f':
            if child.alive and self.person.alive:
                self.person.knowledge.add_bit(1, f"Gave birth to {child.name} at age {self.person.age}.")
            elif not child.alive and not self.person.alive:
                self.person.knowledge.add_bit(1, f"Died while giving birth to stillborn {child.name} at age {self.person.age}.")
            elif child.alive and not self.person.alive:
                self.person.knowledge.add_bit(1, f"Died while giving birth to {child.name} in at age {self.person.age}.")
            elif not child.alive and self.person.alive:
                self.person.knowledge.add_bit(1, f"Gave birth to stillborn {child.name} at age {self.person.age}.")
        else: 
            child_sex = 'son' if child.sex == 'm' else 'daughter'
            partner = child.parents.woman
            if child.alive and partner.alive:
                self.person.knowledge.add_bit(1, f"Had a {child_sex} with {partner.name}, {child.name}, at age {self.person.age}.")
            elif not child.alive and not partner.alive:
                self.person.knowledge.add_bit(1, f"Lost his wife {partner.name} and their {child_sex} {child.name}  while {partner.name} was giving birth when he was {self.person.age}.")
            elif child.alive and not partner.alive:
                self.person.knowledge.add_bit(1, f"Lost his wife {partner.name} while she was giving birth to {child.name}.")
            elif not child.alive and partner.alive:
                self.person.knowledge.add_bit(1, f"{partner.name} gave birth to their stillborn {child_sex} {child.name}.")
            else:
                self.person.knowledge.add_bit(1, f"Had {child_sex} {child.name} with {partner.name} at age {self.person.age}.")

        self.person.children += 1

    """
    FAMILY
    """
    def neglected(self):
        if not self.prev_neglect:
            self.person.knowledge.add_bit(3, f"Was neglected as a child.")
            self.prev_neglect = True
        return True

    def mother_died(self, param=""):
        self.person.knowledge.add_bit(
            2, f"Lost mother at the age of {self.person.age}{param}.")
        return True

    def father_died(self, param=""):
        self.person.knowledge.add_bit(
            2, f"Lost father at the age of {self.person.age}{param}.")
        return True
    
    def dead_child(self, child, circumstance=""):
        child_sex = 'son' if child.sex == 'm' else 'daughter'
        self.person.knowledge.add_bit(1, f'Lost {child_sex} {child.name} when {child.name} was {child.age} years old{circumstance}.')
        self.dead_children += 1
        if self.dead_children > 2 and not self.dead_chidren_bit:
            self.person.knowledge.add_bit(1, f'Has seen several of their children die.')
            self.dead_chidren_bit = True

    def dead_sibling(self, sibling, param=""):            
        self.person.knowledge.add_bit(
            2, f"Lost sibling {sibling.name} {param} when {sibling.name} was {sibling.age}.")
        return True
