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
