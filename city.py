import json
import os
import copy
import math
import networkx as nx
from graphviz import Digraph, Graph
import numpy as np
import matplotlib.pyplot as plt
import random
import csv

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
total_marriages = 0

# People who need people
houses = {}
empty_houses = {}
bachelors = []
bachelorettes = []


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


class Person:
    def __init__(self, parents, key, age=0, sex='r', married=False, surname='r', house=None):
        # biological
        if sex == 'r':
            self.sex = 'f' if random.random() < 0.51 else 'm'
        else:
            self.sex = sex
        self.sexuality = "straight" if random.random() < 0.9 else "gay"
        self.characteristics = self.get_characteristics()
    
        # genetics
        self.parents = parents
        self.health = self.get_health()
        self.appearance = self.Appearance(self.parents)
        self.personality = self.Personality()

        # names
        self.names = self.Names(self.sex, self.parents, surname)
        self.name = self.names.name
        self.surname = self.names.surname
        self.nickname = self.names.nickname

        # progressive variables
        self.age = age
        self.married = married
        self.children = 0 
        self.marriage = None
        self.relationships = []
        self.knowledge = self.Knowledge(self)

        # binary
        self.key = key
        self.alive = True
        self.birthday = self.get_birthday()

        # houselife
        self.house = house
        self.emancipated = False
        self.caretaker = False
        self.breadwinner = False
        self.income_class = 0

        # start life
        self.connections = self.Connections(self, self.house)
        self.init_existence()

    """
    LIVING & DYING
    """
    def get_birthday(self):
        global year
        if self.age != 0:
            birth_year = year-self.age
        else:
            birth_year = year
        months = ["Ianuarius", "Februarius", "Martius", "Aprilis", "Maius", "Iunius",
                  "Iulius", "Augustus", "Septembris", "Octobris", "Novembris", "Decembris"]
        return (random.choice(months), random.randint(1, 29), birth_year)

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

    def get_characteristics(self):
        characteristics = ['infertile', 'autistic', 'down syndrome', 'blind', 'deaf', 'transgender']
        own_ch = []
        if random.random() < 0.1:
            own_ch.append(random.choice(characteristics))
            if random.random() < 0.1:
                own_ch.append(random.choice(characteristics))
        return own_ch
            
    def init_existence(self):
        global people_alive, births, houses

        births += 1
        people_alive += 1

        alive[self.key] = self
        people[self.key] = self

        family_tree.node(self.key, label=self.name)
        network.add_node(self.key, label=self.name)

        if self.house == None:
            if self.parents != None:
                self.house = self.parents.woman.house
            else:
                self.house = houses['outside']
        self.house.add_person(self, 'birthed')
        self.income_class = self.house.income_class

    def die(self, circumstance=""):
        global people_alive, deads
        deads += 1
        people_alive -= 1
        alive.pop(self.key)
        self.alive = False

        # process global networks
        dead[self.key] = self
        family_tree.node(self.key, label=self.name, color='orange')
        network.remove_node(self.key)

        # create bits
        self.knowledge.add_bit(0, f"Died at age {self.age}{circumstance}.")
        
        # end relationships
        cause = 'woman_died' if self.sex == 'f' else 'man_died'
        for relation in self.relationships:
            if relation.active:
                relation.end_relationship(cause, circumstance)

        self.parents.relationship_trigger('dead_child', (self.name, self.age))
        self.house.remove_person(self.key, 'died')
    
    """
    TRIGGERS & CHANCES
    """
    def trigger(self, trigger, param=None):
        """
        Triggers:
        - trait_influence : param=(trait, value, source), return True / False
        - childbirth : return True / False
        - birth : return True / False
        - mother_died : param=circumstance
        - father_died : param=circumstance
        """
        if trigger == 'virtue_influence':
            trait, value, source = param
            own_value, own_importance = self.personality.get_trait(trait)
            if own_importance == 'important':
                chance = 0.1
            else:
                chance = 0.4

            # by how much is the value changed?
            change = 1 if own_value < value else -1

            if random.random() < chance:
                self.personality.influence_personality(trait, change, source)
                return True
        
        elif trigger == 'childbirth':
            if random.random() < self.chance_of_dying('childbirth'):
                self.die('in childbirth')
                return True 
            self.health -= random.randint(0,20) * 0.005

        elif trigger == 'birth':
            if random.random() < self.chance_of_dying('birth'):
                self.die("days after being born")
                return True

        elif trigger == 'mother_died':
            self.knowledge.add_bit(2, f"Lost mother at the age of {self.age}{param}.")
            return

        elif trigger == 'father_died':
            self.knowledge.add_bit(2, f"Lost father at the age of {self.age}{param}.")
            return

        return False

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
            chance *= 0.2

        return chance

    """
    PROCEDURAL & SOCIAL LIFE
    """
    def emancipate(self):
        """
        Doesn't return anything.
        """
        if self.sex == 'f':
            return
        if self.age > 29 or self.age < 16:
            return 

        random.seed()
        chance = 1.0 / (30 - self.age)

        if random.random() < chance:
            self.emancipated = True

            # set new income class
            hi = self.house.income_class
            in_weights = [0.2, 0.7, 0.1]
            in_values = [hi if hi==1 else hi-1, hi, hi if hi==5 else hi+1]
            self.income_class = np.random.choice(in_values, p=in_weights)

    def personal_events(self):
        global bachelorettes, bachelors

        self.age += 1

        # chance of dying
        if random.random() < self.chance_of_dying('age'):
            self.die()
            return

        # chance of marrying
        if not self.married and self.parents != None:
            if random.random() < self.chance_of_marrying():
                if self.sex == 'f':
                    bachelorettes.append(self.key)
                elif self.sex == 'm' and self.emancipated:
                    bachelors.append(self.key)

        # making friends and connections:
        if random.random() < 0.7:
            if self.age < 13:
                self.connections.broadcast_intention('find_child_friend')
            else: 
                self.connections.broadcast_intention('find_connection')
        
        self.connections.social_life()

        # emancipation
        if not self.emancipated:
            self.emancipate()

    def jsonify(self):
        global network
        person = {}
        person["alive"] = self.alive
        person["house"] = self.house.key
        person["names"] = self.names.jsonfiy()
        person["biological"] = {
            "parents" : self.parents.key if self.parents else "ancestors",
            "sex" : self.sex,
            "sexuality" : self.sexuality,
            "health" : self.health,
            "birthday" : self.birthday
        }
        person["appearance"] = self.appearance.jsonify()
        person["parents"] = [f"{self.parents.man.key} and {self.parents.woman.key}" if self.parents else "ancestors", f"{self.parents.man.name} and {self.parents.woman.name}" if self.parents else "ancestors"]
        person["procedural"] = {
            "age": self.age,
            "married": self.married,
            'no_children': self.children,
            'connections' : self.connections.get_network(),
            "events": self.knowledge.get_descriptions()
        }
        person["personality"] = {
            "sins" : self.personality.jsonify_sins(),
            "virtues" : self.personality.jsonify_virtues()
        }

        return person

    """
    CLASSES
    """
    class Names:
        def __init__(self, sex, parents, surname='r', income_class=0):
            self.parents = parents
            self.sex = sex
            if surname == 'r':
                self.surname = self.generate_surname()
            else:
                self.surname = surname
            self.name = self.generate_name()
            self.nickname = self.generate_nickname()

        def generate_name(self):
            global w_names, m_names

            if self.parents != None:
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

        def update_surname(self, trigger):
            pass

        def jsonfiy(self):
            return {
                "name" : self.name,
                "nickname" : self.nickname,
                "surname" : self.surname
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
                genetic_hair.append(self.parents.man.appearance.hair_color)
                genetic_hair.append(self.parents.woman.appearance.hair_color)
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
                    self.parents.man.appearance.hair_type)
                mother_hair = random.choice(
                    self.parents.woman.appearance.hair_type)
                return [father_hair, mother_hair]
            else:
                random_hair = ['C', 'S', 'S', 'S']
                return [random.choice(random_hair),
                            random.choice(random_hair)]

        def get_eye_color(self):
            eye_colors = ['brown', 'green', 'blue']
            genetic_eyes = []

            if self.parents != None:
                genetic_eyes.append(self.parents.man.appearance.eye_color)
                genetic_eyes.append(self.parents.woman.appearance.eye_color)
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

            self.all = self.combine_all()

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

        def combine_all(self):
            b = self.jsonify_virtues()
            return dict(self.jsonify_sins(), **b)

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

        def jsonify_all(self):
            return self.combine_all()

        def jsonify(self):
            return {
                "sins" : self.jsonify_sins(),
                "virtues" : self.jsonify_virtues()
            }

    class Connections:
        def __init__(self, person, house):
            self.person = person
            self.own_key = person.key
            self.house = house
            self.past_friends = []
            self.current_friends = []

            self.init_family_network()
            # self.init_household_network()

        def init_family_network(self):
            global network

            if not self.person.parents:
                return
            else:
                if self.person.parents.woman.alive:
                    self.make_connection(self.person.parents.woman.key, 'parent')
                if self.person.parents.man.alive:
                    self.make_connection(self.person.parents.man.key, 'parent')
            
            for sibling in self.person.parents.children:
                if sibling.alive:
                    self.make_connection(sibling.key, 'sibling')                

        def init_household_network(self):
            global network
            if self.house:
                # what if roommate is extended family?
                for roommate in self.house.inhabitants:
                    if roommate.key not in network[self.own_key]:
                        self.make_connection(roommate.key, 'other')

        def broadcast_intention(self, intent, depth=2):
            """
            INTENT:
            - find_child_friend
            - find_connection
            """
            global network, people

            random.seed()
            edges = network.edges(self.own_key)
            options = []
            for _, v in edges:
                suggestions = people[v].connections.receive_intention(intent, self.own_key, self.own_key, depth, [])
                options.extend(suggestions)

            if intent == 'find_child_friend':
                rel_mod = random.randint(-20, 30)
            else:
                rel_mod = 0
            
            for option in options:
                if random.random() < 0.6:
                    self.make_connection(option, 'outsider', rel_mod)

        def receive_intention(self, intent, source, op, depth, suggestions):
            global people
            depth -= 1
            if depth < 1:
                return []

            options = []
            for _, v in network.edges(self.own_key):
                if v != source and v != op and v not in suggestions:
                    options.extend(v)
            
            if intent == 'find_child_friend':
                return [x for x in options if people[x].age < 12]
            return options

        def get_indexmodifier(self, other_key):
            global people, trait_modifiers

            A = self.person.personality.jsonify_all()
            B = self.person.personality.jsonify_all()
            traits = ['superbia', 'avaritia', 'luxuria', 'invidia', 'gula', 'ira', 'acedia',
                'prudentia', 'iustitia', 'temperantia', 'fortitudo', 'fides', 'spes', 'caritas']
            index_mod = 0
            for trait_a in traits:
                for trait_b in traits:
                    M = trait_modifiers[trait_a][trait_b]
                    a_value, a_opinion = A[trait_a]
                    b_value, b_opinion = B[trait_b]
                    a_mod = 1 if a_opinion == 'important' or a_opinion == 'happy' else 0
                    b_mod = 1 if b_opinion == 'important' or b_opinion == 'happy' else 0
                    if a_value > 5:
                        index_a = a_mod
                    elif a_value < 3:
                        index_a = 2 + a_mod
                    else:
                        continue
                    if b_value > 5:
                        index_b = b_mod
                    elif b_value < 3:
                        index_b = 2 + b_mod
                    else:
                        continue
                    
                    index_mod += M[index_a][index_b]

            return index_mod

        def make_connection(self, other_key, nature, preset_rel=0):
            """
            INPUT:
            - other_key
            - nature
            - (preset_rel)
            """
            global network

            index_mod = self.get_indexmodifier(other_key)
            if nature == 'parent':
                rel = random.randint(10, 40)
            elif nature == 'sibling':
                rel = random.randint(5, 25)
            elif nature == 'family':
                rel = random.randint(0, 15)
            else:
                rel = random.randint(-10, 10)

            rel += preset_rel
            network.add_edge(self.own_key, other_key, weight=rel,
                            index_mod=index_mod, nature=nature)

        def social_life(self):
            random.seed() 
            edges = network.edges(self.own_key)

            for u, v in edges:
                index_mod = copy.deepcopy(network.get_edge_data(u, v)['index_mod'])
                age_mod = 1.5 if self.person.age < 12 else 1

                """
                RANGE: -30-30
                - < 15 : nothing happens
                - 15-20 : small event
                - 20-25 : medium event
                - 25-30: big event
                """
                event = random.randint(-30, 30) + index_mod
                mod = age_mod if event > 0 else -1 * age_mod

                if abs(event) < 15:
                    points = 0
                elif abs(event) < 20:
                    points = 10
                elif abs(event) < 25:
                    points = 20
                else:
                    points = 30
                
                new_weight = network[u][v]['weight'] + (mod * points)
                network[u][v]['weight'] = new_weight

        def get_network(self):
            global network
            social_network = {'family' : {}, 'outsider' : {}, 'sibling' : {}, 'parent' : {}}
            edges = network.edges(self.own_key)
            for u, v in edges:
                data = network.get_edge_data(u, v)
                social_network[data['nature']][v] = data

            return social_network

    class Knowledge:
        def __init__(self, person):
            self.person = person
            self.bits = {}
            self.knowledge = {}

        def add_bit(self, secrecy, description, ongoing=False):
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

        def get_descriptions(self):
            bits = []
            for l in self.bits.values():
                for el in l:
                    bits.append(el.description)
            return bits


class Relationship:
    def __init__(self, man, woman, key, married=True, assigned_house=None):
        self.active = True
        self.key = key
        self.married = married
        self.family_values = [[], []]
        
        # members
        self.man = man
        self.woman = woman
        self.children = []

        # stats
        self.no_children = 0
        self.dead_children = 0
        self.still_births = 0

        self.init_relationship(assigned_house)

    """
    BEGINNING & ENDING
    """
    def init_relationship(self, assigned_house):
        global empty_houses

        self.man.relationships.append(self)
        self.woman.relationships.append(self)
        active_couples[self.key] = self
        self.set_familyvalues()
        if self.married:
            self.man.marriage = self
            self.woman.marriage = self
            self.woman.names.update_surname('marriage')

        # represent in family network
        family_tree.node(self.key, shape="diamond")
        family_tree.edge(self.woman.key, self.key, weight='12')
        family_tree.edge(self.man.key, self.key, weight='12')

        # organize house 
        if assigned_house == None:
            print("self assigned house")
            if self.married:
                if self.woman.breadwinner:
                    self.woman.house.add_person(self.man, 'married')
                    self.man.house.update_roles(care_candidate=self.man)
                elif self.man.breadwinner:
                    self.man.house.add_person(self.woman, 'married')
                    self.man.house.update_roles(care_candidate=self.woman)
                else:
                    print(f"{self.man.key} moved in with {self.woman.key}")
                    if self.man.income_class in empty_houses and empty_houses[self.man.income_class] != []:
                        new_house = random.choice(empty_houses[self.man.income_class])
                        print(new_house)
                        new_house.add_people([self.man, self.woman])
                        new_house.update_roles(care_candidate=self.woman, bread_candidate=self.man)
                    else:
                        self.man.house.add_person(self.woman, 'married')
                        self.man.house.update_roles(care_candidate=self.woman)

    def set_familyvalues(self):
        for partner in [self.man, self.woman]:
            for trait, score in partner.personality.jsonify_all().items():
                value, importance = score
                if (value > 5 or value < 3) and importance == 'important':
                    self.family_values[1].append((trait, value))

    def end_relationship(self, cause, circumstance=""):
        """
        Possible causes:
        - woman_died
        - man_died 
        - separated
        """
        global active_couples

        if self.active:
            self.active = False
        if cause == 'woman_died':
            if self.married:
                self.man.married = False
                if self.man.alive:
                    self.man.knowledge.add_bit(1, f"Became a widower at {self.man.age}{circumstance}.")
            for child in self.children:
                if child.alive:
                    child.trigger('mother_died', circumstance)
        elif cause == 'man_died':
            if self.married:
                self.woman.married = False
                if self.woman.alive:
                    self.woman.knowledge.add_bit(1, f"Became a widow at {self.man.age}{circumstance}.")
            for child in self.children:
                if child.alive:
                    child.trigger('father_died', circumstance)
        elif cause == 'separated':
            pass

        active_couples.pop(self.key)
                    
    def add_child(self):
        global network, family_tree
        self.no_children += 1
        self.man.children += 1
        self.woman.children += 1

        # init_child
        child_key = f"{self.key}c{self.no_children}"
        try:
            child = Person(self, child_key)
            self.children.append(child)
        except:
            print(f"couldnt init child {self.no_children} of {self.key}")
            print("----------------------")
        child.trigger('birth')

        # add to family tree
        family_tree.edge(self.key, child_key, weight='6')
    
    """
    TRIGGERS & EVENTS
    """
    def relationship_trigger(self, trigger, param=None):
        """
        dead child: param tuple of (name_child, age_child)
        """
        if trigger == 'dead child':
            self.dead_children += 1
            name_child, age_child = param

            # parents
            if self.man.alive:
                self.man.add_bit(
                    2, f"Lost their child {name_child} when {name_child} was {age_child} years old.")
            if self.woman.alive:
                self.woman.add_bit(
                    2, f"Lost their child {name_child} when {name_child} was {age_child} years old.")

            # children
            for child in self.children:
                if child.alive:
                    child.add_bit(
                        2, f"Lost their sibling {name_child} when {child.name} was {child.age} and {name_child} was {age_child}.")

    def relationship_events(self):
        # having a child
        child_chance = self.pregnancy_chance()
        if random.random() < child_chance:
            self.add_child()

    def pregnancy_chance(self):
        chance = 0.7
        if self.woman.age > 41:
            chance = 0.05
        elif self.woman.age > 36:
            chance = 0.5
        elif self.woman.age > 25:
            chance = 0.6

        if self.no_children > 14:
            chance *= 0.05
        elif self.no_children > 9:
            chance *= 0.15

        return chance * self.woman.health


class House:
    def __init__(self, income, street, section, number, function=None, material='wood', key='r'):
        # People
        self.inhabitants = []
        self.inh_count = 0
        self.breadwinners = []
        self.caretakers = []
        
        # Household
        self.income_class = income
        self.street = street
        self.section = section 
        self.number = number
        if key == 'r':
            self.key = f"{self.street.name}.{self.section.relative_key}.{self.number}"
        else:
            self.key=key

        # House
        self.function = function
        self.material = material
        self.init_household()

    def init_household(self):
        """
        Init household
        """
        global empty_houses, houses
        if self.income_class not in empty_houses:
            empty_houses[self.income_class] = []
        empty_houses[self.income_class].append(self.key)

        houses[self.key] = self
            
    def add_person(self, inhabitant, reason):
        """
        REASONS:
        - birthed
        - adopted
        - married
        - moved
        """
        global empty_houses
        if self.inh_count == 0:
            empty_houses[self.income_class].remove(self.key)
        self.inh_count += 1
        inhabitant.knowledge.add_bit(0, f"{inhabitant.name} moved to {self.key} because of {reason}.")
        inhabitant.house = self
        self.inhabitants.append(inhabitant)

    def add_people(self, inhabitants, reason='moved'):
        for i in inhabitants:
            self.add_person(i, reason)

    def remove_person(self, key, reason):
        """
        REASONS:
        - died
        - married
        - moved_city
        - moved_outside
        """
        self.inh_count -= 1
        if self.inh_count == 0:
            if self.income_class not in empty_houses:
                empty_houses[self.income_class] = []
            empty_houses[self.income_class].append(self.key)
        self.inhabitants = [x for x in self.inhabitants if x.key != key]

    def update_roles(self, care_candidate=None, bread_candidate=None):
        if care_candidate != None:
            if len(self.caretakers) < 3:
                care_candidate.caretaker = True
                self.caretakers.append(care_candidate)
        if bread_candidate != None:
            if len(self.breadwinners) < 4:
                bread_candidate.caretaker = True
                self.breadwinners.append(bread_candidate)

    def house_trigger(self, trigger, params=None):
        """
        TRIGGERS:
        - death / person_key
        - 
        """
        pass

    def house_events(self):
        """
        Yearly household events.

        EVENTS:
        - inter household relations
        - 
        """
        pass

    def get_householdmembers(self):
        return self.inhabitants
    
    def household_summary(self):
        return [(x.key, x.name) for x in self.inhabitants]


class Street:
    def __init__(self, name, inputlist):
        self.name = name
        self.sections = self.init_street(inputlist)
        # self.empty_lots = copy.deepcopy(self.total_lots)

    def init_street(self, row):
        if row == []:
            return
        cols = ['street', 'A', 'class', 'B', 'class', 'C', 'class', 'D', 'class', 'E', 'class']
        sections = {}
        for i in range(1, 11, 2):
            if row[i] == '' or i >= len(row):
                break
            sections[cols[i]] = self.Section(int(row[i]), int(row[i+1]), self, cols[i])
        return sections

    def street_summary(self):
        summary = {}
        for s in self.sections.values():
            summary[s.relative_key] = s.get_section_summary
        return summary

    class Section:
        def __init__(self, no_houses, income_class, street, key):
            self.total_lots = no_houses
            self.empty_lots = copy.deepcopy(self.total_lots)
            self.relative_key = key
            self.in_class = income_class
            self.street = street
            self.houses = self.init_houses()

        def init_houses(self):
            section = []
            for i in range(self.total_lots):
                section.append(House(self.in_class, self.street, self, i))
            return section

        def get_section_summary(self):
            summary = {}
            for house in self.houses:
                summary[house.key] =  house.household_summary()
            return summary


class City:
    def __init__(self, start_year, end_year=1400):
        global year, houses
        year = start_year
        self.buurten, self.streets = self.read_cityfiles()
        self.start_year, self.end_year = start_year, end_year
        self.init_town()
        houses['outside'] = House(1, None, None, 0, key='outside')
        self.time()

    def read_cityfiles(self):
        buurten = {}
        strbr = {}
        with open('sources/Buurten.csv', 'r') as bfile:
            csvreader = csv.reader(bfile)
            for row in csvreader:
                strbr[row[1]] = row[0]
                if row[0] not in buurten:
                    buurten[row[0]] = []
                buurten[row[0]].append(row[1])
        
        streets = {}
        with open('sources/SectionStreets.csv', 'r') as cfile:
            csvreader = csv.reader(cfile)
            for row in csvreader:
                streets[row[0]] = Street(row[0], row)

        return buurten, streets

    def marry(self, wife, husband, assigned_home=None):
        global total_marriages

        # also serves as key for the relationship
        key = f"{total_marriages}"

        # create relationship and add to inventory
        Relationship(husband, wife, key, assigned_house=assigned_home)
        total_marriages += 1

    def init_town(self):
        global houses, empty_houses, total_marriages, people_alive
        
        random.seed()
        for home in houses.values():
            inhabitants = []
            chance = random.random()

            # matrimony
            if chance < 0.6:
                # ages
                wife_age = random.randrange(14, 28)
                husband_age = random.randrange(18, 38)

                # keys & people
                w, h = f"{total_marriages}a", f"{total_marriages}b"
                wife = Person(None, w, house=home, sex='f', age=wife_age, married=True)
                husband = Person(None, h, house=home, sex='m', age=husband_age, married=True)
                
                self.marry(wife, husband, assigned_home=home)

            # roommates
            elif chance < 0.8:
                no_inhabitants = random.randint(2, 5)
                age_lowest = random.randrange(15, 50)
                sex = 'f' if random.random() < 0.4 else 'm'
                for _ in range(no_inhabitants):
                    age = random.randint(age_lowest, age_lowest + 10)
                    key = f"{people_alive}"
                    inhabitant = Person(None, key, house=home, sex=sex, age=age)
                    inhabitants.append(inhabitant)
                home.add_people(inhabitants)

        self.output_people()
        self.print_stats()

    def output_people(self, mode="all"):
        global alive, people, dead

        if mode == 'all':
            database = people
        elif mode == 'alive':
            database = alive
        elif mode == 'dead':
            database = dead

        if os.path.exists('people'):
            pass
        else:
            os.mkdir('people')

        for individual in database.values():
            with open(f"people/{individual.key}.json", "w") as output:
                json.dump(individual.jsonify(), output)

    def time(self):
        """
        Runs the time loop 
        """
        global bachelors, bachelorettes, year, deads, births
        while year < self.end_year:
            deads, births = 0, 0
            for r in list(active_couples):
                try:
                    active_couples[r].relationship_events()
                except:
                    pass

            for p in list(alive):
                try:
                    alive[p].personal_events()
                except:
                    pass

            # self.community_events()

            self.print_stats()
            year += 1
            bachelors, bachelorettes = [], []

        self.output_people()
        # self.draw_community()
        family_tree.format = 'pdf'
        family_tree.view()

    def print_stats(self):
        global year, total_marriages, births, deads, dead
        print("---------------------------------")
        print(f"| {year} | +{births} -{deads}")
        print(f"Marriages: {total_marriages}")
        print(f"Currently alive: {people_alive}")
        print(f"Total died: {len(dead)}")


# houses['outside'] = House(1, None, None, 0, key='outside')
# try:
#     Person(None, '2')
# except:
#     print("fail")
City(1390)