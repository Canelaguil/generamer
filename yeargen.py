import json
import copy
import networkx as nx
from graphviz import Digraph, Graph
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
family_tree = Digraph('Families', filename='families.gv',
            node_attr={'color': 'lightblue2', 'style': 'filled'})
relations = Graph('Relations', filename='community.gv')

# Population control
alive = {}
dead = {}
people = {}
active_couples = {}
people_alive = 0

# Match.com
bachelors = []
bachelorettes = []

class Event:
    def __init__(self, secrecy, description, year, ongoing=False):
        """
        Class that defines an event in terms of people involved and the 
        level of secrecy. 
        """
        # Who is this about?
        self.concerns = []

        # Who was also involved but not condemned by it?
        self.involved = []

        # How secret is this event? [0 - 5]
        self.secrecy = secrecy

        # Which sins / virtues does this relate to? [optional]
        self.meaning = {}

        # When did this take place and is it still taking place?
        self.year = year
        self.ongoing = ongoing
        
        # Description of event
        self.description = description

    def jsonify(self):
        event = {}
        event["concerns"] = self.concerns
        event["involved"] = self.involved
        event["secrecy"] = self.secrecy
        event["meaning"] = self.meaning
        event["when"] = [self.year, self.ongoing]
        event["description"] = self.description
        return event


class Person:
    def __init__(self, mother, father, key, age=0, sex='r', married=False, surname='r'):
        global s_names, w_names, m_names
        global alive, dead, people
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
        self.mother = mother
        self.father = father
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
        self.events = {}

        self.init_person()

    def init_person(self):
        global people_alive
        people_alive += 1
        alive[self.key] = self
        people[self.key] = self
        family_tree.node(self.key, label=self.name)
        relations.node(self.key, label=self.name)

    def die(self):
        global people_alive
        people_alive -= 1
        alive.pop(self.key)
        self.alive = False
        dead[self.key] = self
        family_tree.node(self.key, label=self.name, color='orange')

    def get_personality(self):
        """
        Returns random personality traits based on the
        7 sins and virtues.

        TODO:
        - Actually implement genetics
        """
        random.seed()
        sins = {}
        virtues = {}
        lower = 0
        upper = 5

        # LUCIFER Hoogmoed - ijdelheid
        sins["superbia"] = random.randint(lower, upper)
        # MAMMON Hebzucht - gierigheid
        sins["avaritia"] = random.randint(lower, upper)
        # ASMODEUS Onkuisheid - lust
        sins["luxuria"] = random.randint(lower, upper)
        # LEVIATHAN Jaloezie - afgunst
        sins["invidia"] = random.randint(lower, upper)
        # BEELZEBUB Onmatigheid - vraatzucht
        sins["gula"] = random.randint(lower, upper)
        # SATAN Woede- wraak
        sins["ira"] = random.randint(lower, upper)
        # BELFAGOR gemakzucht - luiheid
        sins["acedia"] = random.randint(lower, upper)

        # Voorzichtigheid - wijsheid
        virtues["prudentia"] = random.randint(lower, upper)
        # Rechtvaardigheid - rechtschapenheid
        virtues["iustitia"] = random.randint(lower, upper)
        # Gematigdheid - Zelfbeheersing
        virtues["temperantia"] = random.randint(lower, upper)
        # Moed - focus - sterkte
        virtues["fortitudo"] = random.randint(lower, upper)
        # Geloof
        virtues["fides"] = random.randint(lower, upper)
        # Hoop
        virtues["spes"] = random.randint(lower, upper)
        # Naastenliefde - liefdadigheid
        virtues["caritas"] = random.randint(lower, upper)

        return {"sins": sins, "virtues": virtues}

    def get_appearance(self):
        """
        Returns appearance based on genetics.

        TODO:
        - Come up with actual appearance traits
        - Genetics stuff
        """
        hair_colors = ['light ash blonde', 'light blonde', 'light golden blond', 'medium champagne', 'dark champagne', 'cool brown', 'light brown',
                    'light golden brown', 'ginger', 'light auburn', 'medium auburn', 'chocolate brown', 'dark golden brown', 'medium ash brown', 'espresso']
        return random.choice(hair_colors)

    def get_health(self):
        # if no parents, return random health
        if self.father == 1:
            return random.uniform(0.6, 1.)
        
        # else, genetically generate health
        parent = self.mother if random.random() < 0.6 else self.father
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

    def add_event(self, event):
        try:
            self.events[event.secrecy].append(event)
        except:
            self.events[event.secrecy] = []
            self.events[event.secrecy].append(event)

    def personal_events(self):
        self.age += 1

        # chance of marrying
        if not self.married:
            if random.random() < self.chance_of_marrying():
                if self.sex == 'f':
                    bachelorettes.append(self.key)
                elif self.sex == 'm':
                    bachelors.append(self.key)

        # chance of dying
        if random.random() < self.chance_of_dying('age'):
            self.die()

    def chance_of_dying(self, trigger):
        # giving birth to a child
        if trigger == 'childbirth':
            return 1 - (self.health - 0.02)
        # being born
        elif trigger == 'birth':
            return 1 - (self.health - 0.1)
        # age related issues
        elif trigger == 'age':
            if self.age < 12:
                return 0.01
            elif self.age > 60:
                return 0.75
            elif self.age > 45:
                return (60 - self.age) / 15
        # general medieval circumstances
        return (1 - self.health) * 0.05

    def chance_of_marrying(self):
        chance = 0

        if self.age > 12:
            chance = 0.6
            if self.sex == 'f':
                if self.age > 41:
                    chance = 0.05
                elif self.age > 36:
                    chance = 0.4
                elif self.age > 25:
                    chance = 0.5
            else:
                if self.age < 18:
                    chance = 0.3
                elif age > 45:
                    chance = 0.4

        if self.sexuality == 'gay':
            chance *= 0.7
        
        return chance


    def jsonify(self):
        person = {}
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
        person["genetics"] = {
            # "mother" : self.mother.key,
            # "father" : self.father.key,
            "health" : self.health
        }
        person["personality"] = self.personality
        person["appearance"] = self.appearance
        person["procedural"] = {
            "age" : self.age,
            "status" : self.married,
            "events" : self.events
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
        if cause == 'woman_died':
            if self.active:
                self.active = False
            if self.married:
                self.man.married = False
        elif cause == 'man_died':
            if self.active:
                self.active = False
            if self.married:
                self.woman.married = False
        elif cause == 'separated':
            self.active = False

        active_couples.pop(self.key)
                
    def add_child(self):
        self.no_children += 1
        child_key = f"{self.key}c{self.no_children}"
        child = Person(self.woman, self.man, child_key)
        self.children.append(child)

        # add to networks
        family_tree.node(child_key)
        relations.node(child_key)
        family_tree.edge(self.key, child_key)

        # chance of child dying in childbirth
        if random.random() < child.chance_of_dying('birth'):
            child.die()
        
        # chance of mother dying in childbirth
        if random.random() < self.woman.chance_of_dying('childbirth'):
            self.woman.die()

    def yearly_chance_of_pregnancy(self):
        chance = 0.6
        if self.woman.age > 41:
            chance = 0.05
        elif self.woman.age > 36:
            chance = 0.4
        elif self.woman.age > 25:
            chance = 0.5
        return chance

    def relationship_events(self, year):
        if random.random() < self.yearly_chance_of_pregnancy():
            self.add_child()

            # If child is out of wedlock, add event
            if not self.married:
                out_of_wedlock = Event(4, "Had a child out of wedlock", year, True)
                out_of_wedlock.concerns.append(self.woman.key)
                out_of_wedlock.concerns.append(self.man.key)


class Community:
    def __init__(self, start_year, seed_couples, end_year=1354):
        # World initiation
        global s_names, w_names, m_names
        global family_tree, relations
        global alive, dead, people, active_couples
        global people_alive, bachelorettes, bachelors

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
            wife = Person(1, 1, w, sex='f', age=wife_age, married=True)
            husband = Person(1, 1, h, sex='m', age=husband_age, married=True)

            # marry husband and wife
            self.marry(wife, husband)

    def marry(self, wife, husband):
        # also serves as key for the relationship
        self.total_marriages += 1
        key = f"{self.total_marriages}"

        # create relationship and add to inventory
        Relationship(husband, wife, key)
        
    def community_events(self):
        pass
    
    def print_stats(self):
        print("---------------------------------")
        print(f"Marriages: {self.total_marriages}")
        print(f"People alive: {people_alive}")
        print(f"People died: {len(dead)}")

    def output_people(self, mode="all"):
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
        while self.year < self.end_year:
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

        self.output_people()
        family_tree.format = 'svg'
        family_tree.view()
        
c = Community(1340, 4)