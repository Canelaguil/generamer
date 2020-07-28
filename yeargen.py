import json
import copy
import networkx as nx
from graphviz import Digraph, Graph
import numpy as np
import matplotlib.pyplot as plt
import random
import copy

def read_names():
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

        return m_names, w_names, s_names

# Varaiables
m_names, w_names, s_names = read_names()

# Networks
family_tree = Digraph('Families', filename='families.dot',
            node_attr={'color': 'lightblue2', 'style': 'filled'}, engine='sfdp')
family_tree.attr(overlap='false')
relations = Graph('Relations', filename='community.dot')

# Population control
alive = {}
dead = {}
people = {}
active_couples = {}
people_alive = 0
births, deads = 0, 0

# Match.com
bachelors = []
bachelorettes = []

class Bit:
    def __init__(self, secrecy, description, age, ongoing=False):
        """
        Class that defines an bit in terms of people involved and the 
        level of secrecy. 
        """
        # Who is this about?
        self.concerns = []

        # Who was also involved but not condemned by it?
        self.involved = []

        # Who was the source of this bit?
        self.source = None

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
        bit["concerns"] = self.concerns
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
        global family_tree, relations
        global people_alive, bachelors, bachelorettes

        # binary
        self.key = key
        self.alive = True
        
        # biological
        if sex == 'r':
            self.sex = 'f' if random.random() < 0.51 else 'm'
        else:
            self.sex = sex
        self.sexuality = "straight" if random.random() < 0.9 else "gay"

        # genetics
        self.parents = parents
        self.personality = self.get_personality()
        self.appearance = self.get_appearance()
        self.health = self.get_health()

        # names
        self.name = self.generate_name()
        if surname == 'r':
            self.surname = self.generate_surname()
        else:
            self.surname = surname

        # progressive variables
        self.age = age
        self.married = married
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
        relations.node(self.key, label=self.name)

    def die(self):
        global people_alive, deads
        deads += 1
        people_alive -= 1
        alive.pop(self.key)
        self.alive = False
        dead[self.key] = self
        family_tree.node(self.key, label=self.name, color='orange')

        cause = 'woman_died' if self.sex == 'f' else 'man_died'
        for relation in self.relationships:
            relation.end_relationship(cause)

    def get_personality(self, adjusted_sins=[], adjusted_virtues=[]):
        """
        Returns random personality traits based on the
        7 sins and virtues.

        TODO:
        - Actually implement genetics
        """
        random.seed()
        sins = {}
        virtues = {}
        personality_values = [0, 1, 2, 3, 4, 5]
        sins_weight = [0.1, 0.1, 0.15, 0.4, 0.15, 0.1] if adjusted_sins == [] else adjusted_sins
        virtues_weight = [0.1, 0.1, 0.15, 0.4, 0.15, 0.1] if adjusted_virtues == [] else adjusted_virtues

        # LUCIFER Hoogmoed - ijdelheid
        sins["superbia"] = int(np.random.choice(personality_values, p=sins_weight))
        # MAMMON Hebzucht - gierigheid
        sins["avaritia"] = int(np.random.choice(personality_values, p=sins_weight))
        # ASMODEUS Onkuisheid - lust
        sins["luxuria"] = int(np.random.choice(personality_values, p=sins_weight))
        # LEVIATHAN Jaloezie - afgunst
        sins["invidia"] = int(np.random.choice(personality_values, p=sins_weight))
        # BEELZEBUB Onmatigheid - vraatzucht
        sins["gula"] = int(np.random.choice(personality_values, p=sins_weight))
        # SATAN Woede- wraak
        sins["ira"] = int(np.random.choice(personality_values, p=sins_weight))
        # BELFAGOR gemakzucht - luiheid
        sins["acedia"] = int(np.random.choice(personality_values, p=sins_weight))

        # Voorzichtigheid - wijsheid
        virtues["prudentia"] = int(np.random.choice(personality_values, p=virtues_weight))
        # Rechtvaardigheid - rechtschapenheid
        virtues["iustitia"] = int(np.random.choice(personality_values, p=virtues_weight))
        # Gematigdheid - Zelfbeheersing
        virtues["temperantia"] = int(np.random.choice(personality_values, p=virtues_weight))
        # Moed - focus - sterkte
        virtues["fortitudo"] = int(np.random.choice(personality_values, p=virtues_weight))
        # Geloof
        virtues["fides"] = int(np.random.choice(personality_values, p=virtues_weight))
        # Hoop
        virtues["spes"] = int(np.random.choice(personality_values, p=virtues_weight))
        # Naastenliefde - liefdadigheid
        virtues["caritas"] = int(np.random.choice(personality_values, p=virtues_weight))

        return {"sins": sins, "virtues": virtues}

    def get_appearance(self):
        """
        Returns appearance based on genetics.
        """
        hair_colors = ['black', 'brown', 'red', 'blonde', 'strawberry blonde']
        eye_colors = ['brown', 'green', 'blue']

        # hair color
        genetic_hair = []
        if self.parents:
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
                hair_weights = [0.25, 0.5, 0.03, 0.11, 0.12]
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
        if self.parents:
            genetic_eyes.append(self.parents.man.appearance['eye_color'])
            genetic_eyes.append(self.parents.woman.appearance['eye_color'])
            genetic_eyes = set(genetic_eyes)
            if genetic_eyes == set(['brown', 'brown']):
                eye_weights =  [0.75, 0.1875, 0.0625]
            elif genetic_eyes == set(['green', 'green']):
                eye_weights = [0.005, 0.75, 0.245]
            elif genetic_eyes == set(['blue', 'blue']):
                eye_weights = [0, 0.01, 0.99]
            elif genetic_eyes == set('green', 'brown'):
                eye_weights = [0.5, 0.375, 0.125]
            elif genetic_eyes == set('blue', 'brown'):
                eye_weights = set(0.5, 0, 0.5)
            elif genetic_eyes == set('green', 'blue'):
                eye_weights = [0, 0.5, 0.5]
            else:
                print(f"{self.key}: eye_color problem")
        else:
            eye_weights = [0.3, 0.15, 0.55]
        
        # hair type
        if self.parents:
            father_hair = random.choice(self.parents.man.appearance['hair_type'])
            mother_hair = random.choice(self.parents.woman.appearance['hair_type'])
            hair_type = [father_hair, mother_hair]
        else:
            random_hair = ['C', 'C', 'S']
            hair_type = [random.choice(random_hair), random.choice(random_hair)]

        eye_color = np.random.choice(eye_colors, p=eye_weights)
        hair_color = np.random.choice(hair_colors, p=hair_weights)

        return {"eye_color": eye_color, "hair_color": hair_color, "hair_type": hair_type}

    def get_health(self):
        # if no parents, return random health
        if not self.parents:
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

    def generate_name(self):
        if self.sex == 'f':
            return random.choice(w_names)
        if self.sex == 'm':
            return random.choice(m_names)

    def generate_surname(self):
        if random.random() < 0.4:
            return random.choice(s_names)

        if self.parents and random.random() < 0.7:
            if self.sex == 'f':
                return f"{self.parents.father.name}sdochter"
            if self.sex == 'm':
                    return f"{self.parents.father.name}szoon"

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
            if self.age < 12:
                print("a child died")
        # chance of marrying
        else:
            if not self.married and self.parents != None:
                if random.random() < self.chance_of_marrying():
                    if self.sex == 'f':
                        bachelorettes.append(self.key)
                    elif self.sex == 'm':
                        bachelors.append(self.key)

    def chance_of_dying(self, trigger):
        """
        Yearly chance of dying.
        """
        # giving birth to a child
        if trigger == 'childbirth':
            return (1 - self.health) * 0.2
        # being born / misscarriage
        elif trigger == 'birth':
            return (1 - self.health) * 0.25
        # age related issues
        elif trigger == 'age':
            if self.age < 12:
                return (1 - self.health) * 0.1
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
            "health" : self.health
        }
        person["personality"] = self.personality
        person["appearance"] = self.appearance
        person["procedural"] = {
            "age" : self.age,
            "married" : self.married,
            "events" : bits
        }

        return person


class Relationship:
    def __init__(self, man, woman, key, married=True):
        global s_names, w_names, m_names
        global family_tree, relations
        global dead, alive, active_couples

        self.key = key
        self.man = man
        self.woman = woman
        self.married = married
        self.active = True
        self.no_children = 0
        self.dead_children = 0
        self.children = []

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

        # represent in family network
        family_tree.node(self.key, shape="diamond")
        family_tree.edge(self.woman.key, self.key)
        family_tree.edge(self.man.key, self.key)

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
        elif cause == 'man_died':
            if self.married:
                self.woman.married = False
                if self.woman.alive:
                    self.woman.add_bit(1, f"Became a widow at {self.woman.age}.")
        elif cause == 'separated':
            self.active = False

        active_couples.pop(self.key)
                
    def add_child(self):
        self.no_children += 1
        print(f"{self.key}: {self.no_children}")
        child_key = f"{self.key}c{self.no_children}"
        child = Person(self, child_key)
        self.children.append(child)

        # add to networks
        family_tree.node(child_key)
        relations.node(child_key)
        family_tree.edge(self.key, child_key)

        # chance of child dying in childbirth
        if random.random() < child.chance_of_dying('birth'):
            print("baby died")
            child.die()
            self.dead_children += 1
            if self.dead_children == 1 and self.children == 1:
                self.man.add_bit(2, f"Lost first child with {self.woman.name} in childbirth.")
                self.woman.add_bit(2, f"Lost first child with {self.man.name} in childbirth.")
            elif self.dead_children > 1:
                self.man.add_bit(2, f"Lost several children with {self.woman.name}.")
                self.woman.add_bit(2, f"Lost several children with {self.man.name}.")
                print(f"{self.woman.key} lost child {self.no_children} in childbirth")

        # chance of mother dying in childbirth
        if random.random() < self.woman.chance_of_dying('childbirth'):
            self.woman.die()
            if self.married:
                self.man.add_bit(2, f"Lost wife {self.woman.name} when she gave birth to {child.name}.")
            print("mother died in childbirth")

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
        if random.random() < self.yearly_chance_of_pregnancy():
            self.add_child()

        # If child is out of wedlock, add bit
        if not self.married:
            out_of_wedlock = Bit(4, "Had a child out of wedlock", year, True)
            out_of_wedlock.concerns.append(self.woman.key)
            out_of_wedlock.concerns.append(self.man.key)
            self.man.add_bit_premade(out_of_wedlock)
            self.woman.add_bit_premade(out_of_wedlock)
            print(f"{self.man.key} had a child out of wedlock with {self.woman.key}")


class Community:
    def __init__(self, start_year, seed_couples, end_year=1354):
        # World initiation
        global s_names, w_names, m_names
        global family_tree, relations
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
        Init town with seed couples. 
        """
        for i in range(self.seed_town):
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

    def community_events(self):
        self.match_com()
    
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
        family_tree.format = 'pdf'
        family_tree.view()
        
c = Community(1250, 10)