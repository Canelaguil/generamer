import json
import os
import copy
import math
import networkx as nx
from graphviz import Digraph, Graph
import numpy as np
import matplotlib.pyplot as plt
import random

def read_files():
    """
    Reads the different name files and saves them as lists.

    TODO:
    - Make distinction in class between names.
    - Add jobs names. 
    """
    men_file = open("names/men.names", "r")
    women_file = open("names/women.names", "r")
    sur_file = open("names/genericsur.names", "r")

    m_names, w_names, s_names = [], [], []

    for mn in men_file:
        mn = mn.replace("\n", "")
        mn = mn.replace("\r", "")
        m_names.append(mn.strip())

    for wn in women_file:
        wn = wn.replace("\n", "")
        wn = wn.replace("\r", "")
        w_names.append(wn.strip())

    for sn in sur_file:
        sn = sn.replace("\n", "")
        sn = sn.replace("\r", "")
        s_names.append(sn.strip())

    # This whole thing could be a lot neater
    traits = ['superbia', 'avaritia', 'luxuria', 'invidia', 'gula', 'ira', 'acedia',
              'prudentia', 'iustitia', 'temperantia', 'fortitudo', 'fides', 'spes', 'caritas']
    trait_modifiers = {}
    for tr in traits:
        trait_modifiers[tr] = {}
        for t in traits:
            trait_modifiers[tr][t] = np.zeros((4, 4), dtype=int).tolist()

    csv_modi = np.genfromtxt(
        'sources/relation_modifiers.csv', delimiter=',', dtype=int)
    for row_nr, row in enumerate(csv_modi):
        row_trait = traits[math.floor(row_nr / 4)]
        vertical_index = row_nr % 4
        trait_index, row_index, sub_index = 0, 0, 0
        while row_index < 56:
            column_trait = traits[trait_index]
            trait_modifiers[row_trait][column_trait][sub_index][vertical_index] = int(
                row[row_index])
            row_index += 1
            sub_index += 1
            if sub_index == 4:
                sub_index = 0
                trait_index += 1
    return m_names, w_names, s_names, trait_modifiers

# Variables
m_names, w_names, n_names, trait_modifiers = read_files()
year = 0

# Networks
family_tree = Digraph('Families', filename='families.dot',
                      node_attr={'color': 'lightblue2', 'style': 'filled'}, engine='sfdp')
family_tree.attr(overlap='false')
network = nx.Graph()

# Population control
alive = {}
dead = {}
people = {}
active_couples = {}
people_alive = 0
births, deads = 0, 0

# People who need people
bachelors = []
bachelorettes = []

class Personality:
    def __init__(self, adjusted_sins=[], adjusted_virtues=[]):
        # Sins
        self.superbia = self.generate_sin()
        self.avaritia = self.generate_sin()
        self.luxuria = self.generate_sin()
        self.invidia = self.generate_sin()
        self.gula = self.generate_sin()
        self.ira = self.generate_sin()
        self.acedia = self.generate_sin()
        
        # Virtues
        self.prudentia = self.generate_virtue()
        self.iustitia = self.generate_virtue()
        self.temperantia = self.generate_virtue()
        self.fortitudo = self.generate_virtue()
        self.fides = self.generate_virtue()
        self.spes = self.generate_virtue()
        self.caritas = self.generate_virtue()

        self.all = {**self.jsonify_sins(), **self.jsonify_virtues}

    def generate_sin(self):
        values = [1, 2, 3, 4, 5, 6, 7]
        weight = [1/28, 4/28, 6/28, 6/28, 6/28, 4/28, 1/28]
        sinmoods = ['happy', 'not happy']
        sin = int(np.random.choice(values, p=weight))
        if sin > 2 and sin < 6:
            return (sin, 'happy')
        else:
            return (sin, random.choice(sinmoods))
            
    def generate_virtue(self):
        values = [1, 2, 3, 4, 5, 6, 7]
        weight = [1/28, 4/28, 6/28, 6/28, 6/28, 4/28, 1/28]
        virtuemoods = ['important', 'not important']
        virtue = int(np.random.choice(values, p=weight))
        if virtue < 4:
            return (virtue, random.choice(virtuemoods))
        elif virtue > 5:
            return (virtue, np.random.choice(virtuemoods, p=[0.7, 0.3]))
        else:
            return (virtue, np.random.choice(virtuemoods, p=[0.6, 0.4]))

    def get_trait(self, trait):
        return self.all[trait]

    def influence_personality(self, trait, influence, source, bit=False):
        v, i = self.all[trait]
        self.all[trait] = ( v + influence, i)        

    def jsonify_virtues(self):
        return {
            "prudentia" : self.prudentia,
            "iustitia" : self.iustitia,
            "temperantia" : self.temperantia,
            "fortitudo" : self.fortitudo,
            "fides" : self.fides,
            "spes" : self.spes,
            "caritas" : self.caritas
        }

    def jsonify_sins(self):
        return {
            "superbia" : self.superbia,
            "avaritia" : self.avaritia,
            "luxuria" : self.luxuria, 
            "invidia" : self.invidia,
            "gula" : self.gula, 
            "ira" : self.ira,
            "acedia" : self.acedia
        }

    def jsonify(self):
        return {
            "sins" : self.jsonify_sins(),
            "virtues" : self.jsonify_virtues()
        }


class Appearance:
    def __init__(self, parents):
        self.parents = parents
        self.hair_color = self.get_haircolor()
        self.hair_type = self.get_hairtype()
        self.eye_color = self.get_eye_color()

    def get_haircolor(self):
        hair_colors = ['black', 'brown', 'red', 'blonde', 'strawberry blonde']
        genetic_hair = []

        if self.parents != None:
            genetic_hair.append(self.parents.man.appearance['hair_color'])
            genetic_hair.append(self.parents.woman.appearance['hair_color'])
            genetic_hair = set(genetic_hair)
            if genetic_hair == set(["black", "black"]):
                hair_weights = [1, 0, 0, 0, 0]
            elif genetic_hair == set(['black', 'brown']):
                hair_weights = [0.5, 0.5, 0, 0, 0]
            elif genetic_hair == set(['black', 'red']):
                hair_weights = [0, 1, 0, 0, 0]
            elif genetic_hair == set(['black', 'blonde']):
                hair_weights = [0, 1, 0, 0, 0]
            elif genetic_hair == set(['black', 'strawberry blonde']):
                hair_weights = [0, 1, 0, 0, 0]
            elif genetic_hair == set(['brown', 'brown']):
                hair_weights = [0.25, 0.5, 0.02, 0.11, 0.12]
            elif genetic_hair == set(['brown', 'red']):
                hair_weights = [0, 0.5, 0.16, 0.34, 0]
            elif genetic_hair == set(['brown', 'strawberry blonde']):
                hair_weights = [0, 0.5, 0.08, 0.25, 0.17]
            elif genetic_hair == set(['brown', 'blonde']):
                hair_weights = [0, 0.5, 0, 0.16, 0.34]
            elif genetic_hair == set(['red', 'red']):
                hair_weights = [0, 0, 1, 0, 0]
            elif genetic_hair == set(['red', 'strawberry blonde']):
                hair_weights = [0, 0, 0.5, 0.5, 0]
            elif genetic_hair == set(['red', 'blonde']):
                hair_weights = [0, 0, 0, 1, 0]
            elif genetic_hair == set(['strawberry blonde', 'strawberry blonde']):
                hair_weights = [0, 0, 0.25, 0.5, 0.25]
            elif genetic_hair == set(['strawberry blonde', 'blonde']):
                hair_weights = [0, 0, 0, 0.5, 0.5]
            elif genetic_hair == set(['blonde', 'blonde']):
                hair_weights = [0, 0, 0, 0, 1]
            else:
                print(f"{self.parents.key}: hair problem")
        else:
            hair_weights = [0.15, 0.3, 0.1, 0.2, 0.25]
        
        return np.random.choice(hair_colors, p=hair_weights)

    def get_hairtype(self):
        if self.parents != None:
            father_hair = random.choice(
                self.parents.man.appearance['hair_type'])
            mother_hair = random.choice(
                self.parents.woman.appearance['hair_type'])
            return [father_hair, mother_hair]
        else:
            random_hair = ['C', 'S', 'S', 'S']
            return [random.choice(random_hair),
                         random.choice(random_hair)]

    def get_eye_color(self):
        eye_colors = ['brown', 'green', 'blue']
        genetic_eyes = []

        if self.parents != None:
            genetic_eyes.append(self.parents.man.appearance['eye_color'])
            genetic_eyes.append(self.parents.woman.appearance['eye_color'])
            genetic_eyes = set(genetic_eyes)
            if genetic_eyes == set(['brown', 'brown']):
                eye_weights = [0.75, 0.1875, 0.0625]
            elif genetic_eyes == set(['green', 'green']):
                eye_weights = [0.005, 0.75, 0.245]
            elif genetic_eyes == set(['blue', 'blue']):
                eye_weights = [0, 0.01, 0.99]
            elif genetic_eyes == set(['green', 'brown']):
                eye_weights = [0.5, 0.375, 0.125]
            elif genetic_eyes == set(['blue', 'brown']):
                eye_weights = [0.5, 0, 0.5]
            elif genetic_eyes == set(['green', 'blue']):
                eye_weights = [0, 0.5, 0.5]
            else:
                print(f"{self.parents.key}: eye_color problem")
        else:
            eye_weights = [0.3, 0.15, 0.55]

        return np.random.choice(eye_colors, p=eye_weights)

    def jsonify(self):
        return {
            "hair_color" : self.hair_color,
            "hair_type" : self.hair_type,
            "eye_color" : self.eye_color
        }
        

class Bit:
    def __init__(self, secrecy, description, age, ongoing=False, source='life'):
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
        self.bits = {}
        self.knowledge = {}

    def add_bit(self, secrecy, description, ongoing):
        bit = Bit(secrecy, description, self.person.age, ongoing)
        self.add_bit_premade(bit)

    def add_bit_premade(self, bit):
        if bit.secrecy not in self.bits:
            self.bits[bit.secrecy] = []

        self.bits[bit.secrecy].append(bit)

    def add_knowledge(self, object_key, bit):
        if object_key not in self.knowledge:
            self.knowledge[object_key] = {}
        
        if bit.secrecy not in self.knowledge[object_key][bit.secrecy]:
            self.knowledge[object_key][bit.secrecy] = []

        self.knowledge[object_key][bit.secrecy].append(bit)


class Names:
    def __init__(self, sex, parents, surname='r', income_class=0):
        self.parents = parents
        self.sex = sex
        self.name = self.generate_name()
        self.nickname = self.generate_nickname()
        if surname == 'r':
            self.surname = self.generate_surname()
        else:
            self.surname = surname

    def generate_name(self):
        global w_names, m_names
        if self.parents:
            if self.parents.no_children == 1:
                if random.random() < 0.25:
                    if self.surname == "":
                        self.surname = "de Jonge"
                    
                    if self.sex == 'f':
                        return self.parents.woman.name
                    else:
                        return self.parents.man.name
        if self.sex == 'f':
            return random.choice(w_names)
        if self.sex == 'm':
            return random.choice(m_names)
        return "Tarun"

    def generate_nickname(self):
        global n_names
        if random.random() < 0.4:
            return random.choice(n_names)
        return ""

    def generate_surname(self):
        if self.parents != None and random.random() < 0.7:
            if self.sex == 'f':
                return f"{self.parents.man.name}sdochter"
            if self.sex == 'm':
                return f"{self.parents.man.name}szoon"
        return ""


class Person:
    def __init__(self, parents, key, age=0, sex='r', married=False, surname='r'):
        # binary
        self.key = key
        self.alive = True
        self.birthday = self.get_birthday()

        # biological
        if sex == 'r':
            self.sex = 'f' if random.random() < 0.51 else 'm'
        else:
            self.sex = sex
        self.sexuality = "straight" if random.random() < 0.9 else "gay"
    
        # genetics
        self.parents = parents
        self.health = self.get_health()
        self.appearance = Appearance(self.parents)
        self.personality = Personality()

        # names
        self.names = Names(self.sex, self.parents, surname)
        self.name = self.names.name
        self.surname = self.names.surname
        self.nickname = self.names.nickname

        # progressive variables
        self.age = age
        self.married = married
        self.children = 0
        self.relationships = []
        self.knowledge = Knowledge(self)

        # start life
        self.init_existence()
        self.init_network()

    """
    LIVING & DYING
    """
    def get_birthday(self):
        global year
        months = ["Ianuarius", "Februarius", "Martius", "Aprilis", "Maius", "Iunius",
                  "Iulius", "Augustus", "Septembris", "Octobris", "Novembris", "Decembris"]
        return (random.choice(months), random.randint(1, 29), year)

    def get_health(self):
        # if no parents, return random health
        if self.parents == None:
            return random.uniform(0.6, 1.)

        # else, genetically generate health
        parent = self.parents.woman if random.random() < 0.6 else self.parents.man
        genetics = random.uniform(-0.2, 0.2)
        gen_health = parent.health + genetics
        if gen_health > 1.:
            gen_health = 0.9
        elif gen_health < 0.:
            gen_health = 0.1

        return gen_health

    def init_existence(self):
        global people_alive, births
        births += 1
        people_alive += 1
        alive[self.key] = self
        people[self.key] = self
        family_tree.node(self.key, label=self.name)
        network.add_node(self.key, label=self.name)
        self.init_network()

    def die(self):
        pass
    
    """
    TRIGGERS & CHANCES
    """
    def trigger(self, trigger, param=None):
        """
        Triggers:
        - trait_influence, param=(trait, value, source)
        """
        if trigger == 'virtue_influence':
            trait, value, source = param
            own_value, own_importance = self.personality.get_trait(trait)
            if own_importance == 'important':
                chance = 0.1
            else:
                chance = 0.4

            # by how much is the value changed?
            if own_value < value:
                change = 1
            else:
                change = -1

            if random.random() < chance:
                self.personality.influence_personality(trait, change, source)

    def chance_of_dying(self, trigger):
        """
        Yearly chance of dying.
        """
        # giving birth to a child
        if trigger == 'childbirth':
            return (1 - self.health) * 0.2
        # being born / misscarriage
        elif trigger == 'birth':
            return (1 - self.health) * 0.15
        # age related issues
        elif trigger == 'age':
            if self.age < 10:
                return (1 - self.health) * (0.12 - (0.01 * self.age))
            elif self.age > 60:
                return 0.7
            elif self.age > 45:
                return 0.4
        # general medieval circumstances
        return (1 - self.health) * 0.05

    def chance_of_marrying(self):
        chance = 0

        if self.age > 13:
            chance = 0.5
            if self.sex == 'f':
                if self.age > 41:
                    chance = 0.05
                elif self.age > 36:
                    chance = 0.1
                elif self.age > 25:
                    chance = 0.3
            else:
                if self.age < 18:
                    chance = 0.1
                elif self.age > 45:
                    chance = 0.3

        if self.sexuality == 'gay':
            chance *= 0.5

        return chance

    """
    PROCEDURAL & SOCIAL LIFE
    """
    def personal_events(self):
        global bachelorettes, bachelors
        self.age += 1

        # chance of dying
        if random.random() < self.chance_of_dying('age'):
            self.die()

        # chance of marrying
        else:
            if not self.married and self.parents != None:
                if random.random() < self.chance_of_marrying():
                    if self.sex == 'f':
                        bachelorettes.append(self.key)
                    elif self.sex == 'm':
                        bachelors.append(self.key)

        # making childhood friends:
        if self.age < 13:
            if random.random() < 0.7:
                broadcast_intention('find_child_friend',
                                    self.key, age=self.age, gender=self.sex)

        self.social_life()
        
    def init_network(self):
        pass

    def social_life(self):
        global network
        random.seed()
        edges = network.edges(self.key)
      
        for u, v in edges:
            old_weight = copy.deepcopy(network.get_edge_data(u, v)['weight'])
            other = people[v].name
            """
            RANGE: 0-30
            - x < 10 : minor event, 5 points
            - 10 < x < 22 : medium event, 10 points
            - 22 < x < 28 : major event, 20 points
            - 28 < x < 30 : mindblowing event, 30 points
            """
            positive = random.randint(0, 30) + old_weight
            negative = random.randint(0, 30) - old_weight

            if positive < 10:
                points = 5
            elif positive < 22:
                points = 10
            elif positive < 28:
                points = 20
            elif positive < 31:
                points = 30

            if negative < 10:
                _points = 5
            elif negative < 22:
                _points = 10
            elif negative < 28:
                _points = 20
            elif negative < 31:
                _points = 30

            # print('--------')
            # print(network[u][v]['weight'])
            # network[u][v]['weight'] = old_weight + points - _points
            # print(network[u][v]['weight'])

            if network[u][v]['weight'] > 80 and old_weight < 80:
                self.add_bit(1, f'{self.name} and {other} became good friends.')
            elif network[u][v]['weight'] > 50 and old_weight < 80:
                self.add_bit(1, f'{self.name} and {other} became friends.')


class House:
    def __init__(self, income, street, section, number, function=None, material='wood', init=False):
        # People
        self.inhabitants = []
        self.inh_count = 0
        self.breadwinner = []
        self.caretaker = []
        
        # Household
        self.income_class = income
        self.street = street
        self.section = section 
        self.number = number

        # House
        self.function = function
        self.material = material
        self.empty = True

        if init:
            self.init_household()

    def init_household(self):
        """
        Init household
        """
        pass

    def add_person(self, inhabitant, reason):
        """
        REASONS:
        - birthed
        - adopted
        - married
        - moved
        """
        self.inh_count += 1
        pass

    def remove_person(self, key, reason):
        """
        REASONS:
        - died
        - married
        - moved_city
        - moved_outside
        """
        pass

    def house_trigger(self, trigger, params=None):
        """
        TRIGGERS:
        - death / person_key
        - 
        """
        pass

    def yearly_events(self):
        """
        Yearly household events.

        EVENTS:
        - inter household relations
        - 
        """
        pass


