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
    traits = ['superbia', 'avaritia', 'luxuria', 'invidia', 'gula', 'ira', 'acedia', 'prudentia', 'iustitia', 'temperantia', 'fortitudo', 'fides', 'spes', 'caritas']
    trait_modifiers = {}
    for tr in traits:
        trait_modifiers[tr] = {}
        for t in traits:
            trait_modifiers[tr][t] = np.zeros((4, 4), dtype=int)

    csv_modi = np.genfromtxt('sources/relation_modifiers.csv', delimiter=',', dtype=int)
    for row_nr, row in enumerate(csv_modi):
        row_trait = traits[math.floor(row_nr / 4)]
        vertical_index = row_nr % 4
        trait_index, row_index, sub_index = 0, 0, 0
        while row_index < 56:
            column_trait = traits[trait_index]
            trait_modifiers[row_trait][column_trait][sub_index][vertical_index] = row[row_index]
            row_index += 1
            sub_index += 1
            if sub_index == 4:
                sub_index = 0
                trait_index += 1
    return m_names, w_names, s_names, trait_modifiers


# Varaiables
m_names, w_names, s_names, trait_modifiers = read_files()

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

# Global functions
def connect(key_a, key_b, nature='outsider'):
    """
    NATURE:
    - outsider
    - family
    - sibling
    - parent
    """
    A = people[key_a]
    B = people[key_b]

    # Determine index modifier
    for sin in ['superbia', 'avaritia', 'luxuria', 'invidia', 'gula', 'ira', 'acedia']:
        value_a, importance_a = A.personality['sins'][sin]
        value_b, importance_b = B.personality['sins'][sin]

    for virtue in ['prudentia', 'iustitia', 'temperantia', 'fortitudo', 'fides', 'spes', 'caritas']:
        value_a, importance_a = A.personality['virtues'][virtue]
        value_b, importance_b = B.personality['virtues'][virtue]

    index_mod = 0

    # Determine init relationshiplevel
    if nature=='parent':
        rel = random.randint(10, 40)
    elif nature=='sibling':
        rel = random.randint(5, 25)
    elif nature=='family':
        rel = random.randint(0, 15)
    else:
        rel = random.randint(-10, 10)

    network.add_edge(key_a, key_b, weight=rel, index_mod=index_mod)


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
    def __init__(self, parents, key, age=0, sex='r', married=False, surname='r'):
        global s_names, w_names, m_names
        global alive, dead, people
        global births, deads
        global family_tree, network
        global people_alive, bachelors, bachelorettes

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
        self.appearance = self.get_appearance()
        try:
            self.personality = self.get_personality()
        except:
            print("one of the gets went wrong")

        # names
        if surname == 'r':
            self.surname = self.generate_surname()
        else:
            self.surname = surname
        self.name = self.generate_name()

        # progressive variables
        self.age = age
        self.married = married
        self.children = 0
        self.relationships = [] 
        self.bits = {}

        self.init_person()

    def init_person(self):
        global people_alive, births
        births += 1
        people_alive += 1
        alive[self.key] = self
        people[self.key] = self
        family_tree.node(self.key, label=self.name)
        network.add_node(self.key, label=self.name)
        self.init_network()

    def init_network(self):
        global network
        # forge network with siblings
        if not self.parents:
            return
        
        for sibling in self.parents.children:
            connect(sibling.key, self.key, 'sibling')
            for relationship in sibling.relationships:
                if relationship.active:
                    if sibling.sex == 'm':
                        partner = relationship.woman
                    else:
                        partner = relationship.man
                    
                    if relationship.married:
                        connect(partner.key, self.key, 'family')
                        for cousin in relationship.children:
                            if cousin.alive:
                                connect(cousin.key, self.key, 'family')
                    else:
                        if random.random() < 0.6:
                            connect(partner.key, self.key, 'outsider')

        # forge network with parents' family
        for parent in [self.parents.man, self.parents.woman]:
            if parent.parents != None:
                for unclaunt in parent.parents.children:
                    if unclaunt.alive:
                        connect(self.key, unclaunt.key, 'family')

    def die(self):
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
        self.add_bit(0, f"Died at age {self.age}.")
        cause = 'woman_died' if self.sex == 'f' else 'man_died'

        # end relationships
        for relation in self.relationships:
            relation.end_relationship(cause)

        # update parents' relationship
        self.parents.relationship_trigger('dead child', (self.name, self.age))

    def get_personalityvalue(self, kind, values, weight):
        sinmoods = ['happy', 'not happy']
        virtuemoods = ['important', 'not important']
        if kind == 'sin':
            sin = int(np.random.choice(values, p=weight))
            if sin > 2 and sin < 6:
                return (sin, 'happy')
            else:
                return (sin, random.choice(sinmoods))
        elif kind == 'virtue':
            virtue = int(np.random.choice(values, p=weight))
            if virtue < 4:
                return (virtue, random.choice(virtuemoods))
            elif virtue > 5:
                return (virtue, np.random.choice(virtuemoods, p=[0.7, 0.3]))
            else:
                return (virtue, np.random.choice(virtuemoods, p=[0.6, 0.4]))
            
    def influence_personality(self, kind, trait, influence, source):
        tup = self.personality[kind][trait]
        value, importance = tup
        # if influence < 0:
        #     measure = 'decrease'
        # else:
        #     measure = 'increase'

        value += influence
        self.personality[kind][trait] = (value, importance)
        # self.add_bit(2, f'Was influenced by {source} to {measure} {trait}.')

    def get_personality(self, adjusted_sins=[], adjusted_virtues=[]):
        """
        Returns random personality traits based on the
        7 sins and virtues.
        """
        # return "nice"
        random.seed()
        sins = {}
        virtues = {}
        personality_values = [1, 2, 3, 4, 5, 6, 7]
        sins_weight = [1/28, 4/28, 6/28, 6/28, 6/28, 4/28, 1/28] if adjusted_sins == [] else adjusted_sins
        virtues_weight = [1/28, 4/28, 6/28, 6/28, 6/28, 4/28, 1/28] if adjusted_virtues == [] else adjusted_virtues

        # LUCIFER Hoogmoed - ijdelheid
        sins["superbia"] = self.get_personalityvalue('sin', personality_values, sins_weight)
        # MAMMON Hebzucht - gierigheid
        sins["avaritia"] = self.get_personalityvalue('sin', personality_values, sins_weight)
        # ASMODEUS Onkuisheid - lust
        sins["luxuria"] = self.get_personalityvalue('sin', personality_values, sins_weight)
        # LEVIATHAN Jaloezie - afgunst
        sins["invidia"] = self.get_personalityvalue('sin', personality_values, sins_weight)
        # BEELZEBUB Onmatigheid - vraatzucht
        sins["gula"] = self.get_personalityvalue('sin', personality_values, sins_weight)
        # SATAN Woede- wraak
        sins["ira"] = self.get_personalityvalue('sin', personality_values, sins_weight)
        # BELFAGOR gemakzucht - luiheid
        sins["acedia"] = self.get_personalityvalue('sin', personality_values, sins_weight)

        # Voorzichtigheid - wijsheid
        virtues["prudentia"] = self.get_personalityvalue('virtue', personality_values, virtues_weight)
        # Rechtvaardigheid - rechtschapenheid
        virtues["iustitia"] = self.get_personalityvalue('virtue', personality_values, virtues_weight)
        # Gematigdheid - Zelfbeheersing
        virtues["temperantia"] = self.get_personalityvalue('virtue', personality_values, virtues_weight)
        # Moed - focus - sterkte
        virtues["fortitudo"] = self.get_personalityvalue('virtue', personality_values, virtues_weight)
        # Geloof
        virtues["fides"] = self.get_personalityvalue('virtue', personality_values, virtues_weight)
        # Hoop
        virtues["spes"] = self.get_personalityvalue('virtue', personality_values, virtues_weight)
        # Naastenliefde - liefdadigheid
        virtues["caritas"] = self.get_personalityvalue('virtue', personality_values, virtues_weight)

        return {"sins": sins, "virtues": virtues}
        
    def get_appearance(self):
        """
        Returns appearance based on genetics.
        """
        # return "good looking"
        hair_colors = ['black', 'brown', 'red', 'blonde', 'strawberry blonde']
        eye_colors = ['brown', 'green', 'blue']

        # hair color
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
                print(f"{self.key}: hair problem")
        else:
            hair_weights = [0.15, 0.3, 0.1, 0.2, 0.25]

        # eye color
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
                print(f"{self.key}: eye_color problem")
        else:
            eye_weights = [0.3, 0.15, 0.55]
        
        # hair type
        if self.parents != None:
            father_hair = random.choice(self.parents.man.appearance['hair_type'])
            mother_hair = random.choice(self.parents.woman.appearance['hair_type'])
            hair_type = [father_hair, mother_hair]
        else:
            random_hair = ['C', 'S', 'S', 'S']
            hair_type = [random.choice(random_hair), random.choice(random_hair)]
        
        eye_color = np.random.choice(eye_colors, p=eye_weights)
        hair_color = np.random.choice(hair_colors, p=hair_weights)

        return {"eye_color": eye_color, "hair_color": hair_color, "hair_type": hair_type}
        # return "normal"

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
        # return 0.5

    def get_birthday(self):
        months = ["Ianuarius", "Februarius", "Martius", "Aprilis", "Maius", "Iunius", "Iulius", "Augustus", "Septembris", "Octobris", "Novembris", "Decembris"]
        return (random.choice(months), random.randint(1, 29))

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

    def generate_surname(self):
        # return "martens avila"
        global s_names
        if random.random() < 0.4:
            try:
                return random.choice(s_names)
            except:
                print("no name")
                return "No-name"

        if self.parents != None and random.random() < 0.7:
            try:
                if self.sex == 'f':
                    return f"{self.parents.man.name}sdochter"
                if self.sex == 'm':
                    return f"{self.parents.man.name}szoon"
            except:
                return "bobbie"
        return ""

    def add_bit(self, secrecy, description, ongoing=False):
        bit = Bit(secrecy, description, self.age, ongoing)
        try:
            self.bits[secrecy].append(bit)
        except:
            self.bits[secrecy] = []
            self.bits[secrecy].append(bit)

    def add_bit_premade(self, bit):
        try:
            self.bits[bit.secrecy].append(bit)
        except:
            self.bits[bit.secrecy] = []
            self.bits[bit.secrecy].append(bit)
        
    def personal_events(self):
        global bachelorettes, bachelors
        self.age += 1

        # chance of dying
        if random.random() < self.chance_of_dying('age'):
            self.die()
            # if self.age < 12:
            #     print("a child died")
        # chance of marrying
        else:
            if not self.married and self.parents != None:
                if random.random() < self.chance_of_marrying():
                    if self.sex == 'f':
                        bachelorettes.append(self.key)
                    elif self.sex == 'm':
                        bachelors.append(self.key)

    def trigger(self, trigger, param=None):
        """
        Triggers:
        - virtue_influence, param=(virtue, value, source)
        - sin_influence, param=(sin, value, source)
        """
        if trigger == 'virtue_influence':
            virtue, value, source = param
            own_value, own_importance = self.personality['virtues'][virtue]
            if own_importance == 'important':
                chance = 0.2
            else:
                chance = 0.4
            
            # by how much is the value changed?
            if own_value < value:
                change = 1
            else:
                change = -1
            
            if random.random() < chance:
                self.influence_personality('virtues', virtue, change, source)
                
            return
        elif trigger == 'sin_influence':
            sin, value, source = param
            own_value, own_importance = self.personality['sins'][sin]
            if own_importance == 'happy':
                chance = 0.2
            else:
                chance = 0.6
            
            if own_value < value:
                change = 1
            else:
                change = -1
            
            if random.random() < chance:
                self.influence_personality('sins', virtue, change, source)
            return

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

        if self.age > 12:
            chance = 0.7
            if self.sex == 'f':
                if self.age > 41:
                    chance = 0.05
                elif self.age > 36:
                    chance = 0.4
                elif self.age > 25:
                    chance = 0.6
            else:
                if self.age < 18:
                    chance = 0.3
                elif self.age > 45:
                    chance = 0.5

        if self.sexuality == 'gay':
            chance *= 0.5
        
        return chance

    def jsonify(self):
        person = {}
        bits = []
        for l in self.bits.values():
            for el in l:
                bits.append(el.description)

        rs = []
        for r in self.relationships:
            rs.append(r.key)

        person["key"] = self.key
        person["alive"] = self.alive
        person["names"] = {
            "name" : self.name,
            "surname" : self.surname
        }
        person["biological"] = {
            "sex" : self.sex,
            "sexuality" : self.sexuality
        }

        if self.parents:
            parents = f"{self.parents.man.name} and {self.parents.woman.name}"
        else:
            parents = "ancestors"
        person["genetics"] = {
            "parents" : parents,
            "health" : self.health,
            "birthday": self.birthday
        }
        person["personality"] = self.personality
        person["appearance"] = self.appearance
        person["procedural"] = {
            "age" : self.age,
            "married" : self.married,
            'no_children' : self.children,
            'relationships' : rs,
            "events" : bits
        }

        return person


class Relationship:
    def __init__(self, man, woman, key, married=True):
        global s_names, w_names, m_names
        global family_tree, network
        global dead, alive, active_couples

        self.key = key
        self.man = man
        self.woman = woman
        self.married = married
        self.active = True
        self.no_children = 0
        self.dead_children = 0
        self.still_births = 0
        self.children = []

        # sins, virtues
        self.family_values = [[], []]

        self.init_relationship()

    def init_relationship(self):
        self.man.relationships.append(self)
        self.woman.relationships.append(self)
        active_couples[self.key] = self

        if self.married:
            # change surname of wife
            if random.random() < 0.6:
                self.woman.surname = f"van {self.man.name}"
            self.man.add_bit(0, f"Got married at {self.man.age} to {self.woman.name}.")
            self.woman.add_bit(0, f"Got married at {self.woman.age} to {self.man.name}.")
            self.woman.married = True
            self.man.married = True

            # make households

        # set family values
        for partner in [self.man, self.woman]:
            for virtue, score in partner.personality['virtues'].items():
                value, importance = score
                if (value > 5 or value < 3) and importance == 'important':
                    self.family_values[1].append((virtue, value))
            for sin, score in partner.personality['sins'].items():
                value, importance = score
                if value > 5:
                    self.family_values[0].append((sin, value))

        # represent in family network
        family_tree.node(self.key, shape="diamond")
        family_tree.edge(self.woman.key, self.key, weight='12')
        family_tree.edge(self.man.key, self.key, weight='12')

    def end_relationship(self, cause):
        """
        Possible causes:
        - woman_died
        - man_died 
        - separated
        """
        if self.active:
            self.active = False
        if cause == 'woman_died':
            if self.married:
                self.man.married = False
                if self.man.alive:
                    self.man.add_bit(1, f"Became a widower at {self.man.age}.")
                for child in self.children:
                    if child.alive:
                        child.add_bit(2, f"Lost mother at the age of {child.age}")
        elif cause == 'man_died':
            if self.married:
                self.woman.married = False
                if self.woman.alive:
                    self.woman.add_bit(1, f"Became a widow at {self.woman.age}.")
                for child in self.children:
                    if child.alive:
                        child.add_bit(2, f"Lost father at the age of {child.age}")
        elif cause == 'separated':
            self.active = False

        active_couples.pop(self.key)
                
    def add_child(self):
        global network, family_tree
        self.no_children += 1
        self.man.children += 1
        self.woman.children += 1
        child_key = f"{self.key}c{self.no_children}"
        try:
            child = Person(self, child_key)
        except:
            print(f"couldnt init child {self.no_children} of {self.key}")
        self.children.append(child)

        # add to networks
        family_tree.edge(self.key, child_key, weight='6')

        connect(self.woman.key, child_key, 'parent')
        if self.man.alive:
            connect(self.man.key, child_key, 'parent')                      

        # chance of child dying in childbirth
        self.stillbirthbit = False
        if random.random() < child.chance_of_dying('birth'):
            child.die()
            self.dead_children += 1
            self.still_births +=1
            if self.dead_children == 1 and self.children == 1:
                self.man.add_bit(2, f"Lost first child with {self.woman.name} in childbirth.")
                self.woman.add_bit(2, f"Lost first child with {self.man.name} in childbirth.")
            elif self.still_births > 1 and not self.stillbirthbit:
                self.man.add_bit(2, f"{self.woman.name} had several miscarriages when they tried to conceive.")
                self.woman.add_bit(2, f"Had several misscariages when trying to conceive with {self.man.name}.")
                self.stillbirthbit = True

        # chance of mother dying in childbirth
        if random.random() < self.woman.chance_of_dying('childbirth'):
            self.woman.die()
            if self.married:
                self.man.add_bit(2, f"Lost wife {self.woman.name} when she gave birth to {child.name}.")

    def yearly_chance_of_pregnancy(self):
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
        
        return chance

    def relationship_events(self, year):
        random.seed()

        # having a child
        child_chance = self.yearly_chance_of_pregnancy()
        if random.random() < child_chance:
            self.add_child()

        # influence children
        sins, virtues = self.family_values
        for sin in sins:
            s, v = sin
            for child in self.children:
                if child.alive:
                    if random.random() < 0.5:
                        child.trigger('sin_influence', (s, v, 'parents'))
                        # print(f"{self.key} influenced sin")
        
        for virtue in virtues:
            vir, val = virtue
            for child in self.children:
                if child.alive and child.age > 3:
                    if random.random() < 0.5:
                        child.trigger('virtue_influence', (vir, val, 'parents'))
                        # print(f"{self.key} influenced virtue")    

    def relationship_trigger(self, trigger, param=None):
        """
        dead child: param tuple of (name_child, age_child)
        """
        if trigger == 'dead child':
            self.dead_children += 1
            name_child, age_child = param

            # parents
            if self.man.alive:
                self.man.add_bit(2, f"Lost their child {name_child} when {name_child} was {age_child} years old.")
            if self.woman.alive:
                self.woman.add_bit(2, f"Lost their child {name_child} when {name_child} was {age_child} years old.")
            
            # children
            for child in self.children:
                if child.alive:
                    child.add_bit(2, f"Lost their sibling {name_child} when {child.name} was {child.age} and {name_child} was {age_child}.")


class Community:
    def __init__(self, start_year, seed_couples, end_year=1354):
        # World initiation
        global s_names, w_names, m_names
        global family_tree, network
        global alive, dead, people, active_couples
        global people_alive, bachelorettes, bachelors
        global births, deads

        self.seed_town = seed_couples
        self.year = start_year
        self.end_year =  end_year

        # Stat variables
        self.new_people = 0
        self.dead_people = 0
        self.new_marriages = 0
        self.total_marriages = 0

        # Start running simulation
        self.init_town()
        self.time()

    def init_town(self):
        """
        Init town with seed couples and seed friendships. 
        """
        for i in range(1, self.seed_town + 1):
            random.seed()

            # ages
            wife_age = random.randrange(12, 28)
            husband_age = random.randrange(18, 38)

            # keys
            w, h = f"{i}a", f"{i}b"

            # create people
            wife = Person(None, w, sex='f', age=wife_age, married=True)
            husband = Person(None, h, sex='m', age=husband_age, married=True)

            # marry husband and wife
            self.marry(wife, husband)

    def marry(self, wife, husband):
        # also serves as key for the relationship
        self.total_marriages += 1
        key = f"{self.total_marriages}"

        # create relationship and add to inventory
        Relationship(husband, wife, key)
    
    def match_com(self):
        """
        Matches bachelors and bachelorettes. 
        """
        global bachelors, bachelorettes
        for bachelor in bachelors:
            if bachelorettes == []:
                return
            options = copy.deepcopy(bachelorettes)
            while True:
                if options == []:
                    break

                try:
                    groom = alive[bachelor]
                    match_id = random.choice(options)
                    match = alive[match_id]
                except:
                    print("one of them dead")

                if match.parents.key != groom.parents.key:
                    bachelorettes.remove(match_id)
                    self.marry(match, groom)
                    break
                else:
                    options.remove(match_id)

    def all_in_this_together(self):
        """
        Forges new connections between people.
        """
        pass

    def community_events(self):
        self.match_com()
        self.all_in_this_together()

    def draw_community(self):
        global network
        edges = network.edges()
        # edgecolors = [network[u][v]['color'] for u, v in edges]
        color_map = []
        for _, n in network.nodes.data():
            # if n["node"] == "relation":
            #     color_map.append('red')
            # else:
            color_map.append('yellow')
        nx.draw_spring(network, edges=edges, with_labels=True, node_color=color_map)
                 # node_color=color_map, edge_color=edgecolors)
        plt.show()
        # plt.savefig('network.png')

    def print_stats(self):
        print("---------------------------------")
        print(f"| {self.year} | +{births} -{deads}")
        print(f"Marriages: {self.total_marriages}")
        print(f"Currently alive: {people_alive}")
        print(f"Total died: {len(dead)}")

    def output_people(self, mode="all"):
        global alive, people, dead

        if mode == 'all':
            database = people
        elif mode == 'alive':
            database = alive
        elif mode == 'dead':
            database = dead 

        if os.path.exists('people'):
        #     os.rmdir('people')
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
        global bachelors, bachelorettes, deads, births
        while self.year < self.end_year:
            deads, births = 0, 0
            for r in list(active_couples):
                try:
                    active_couples[r].relationship_events(self.year)
                except:
                    pass
            
            for p in list(alive):
                try:
                    alive[p].personal_events()
                except:
                    pass

            self.community_events()

            self.print_stats()
            self.year += 1
            bachelors, bachelorettes = [], []

        self.output_people()
        self.draw_community()
        family_tree.format = 'pdf'
        family_tree.view()
        
c = Community(1350, 1)