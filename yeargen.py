import json
import copy
import networkx as nx
from graphviz import Digraph, Graph
import matplotlib.pyplot as plt
import random

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
    def __init__(self, mother, father, name, surname, sex, key, age=0, married='unmarried'):
        # binary
        self.key = key
        
        # biological
        self.sex = sex
        self.sexuality = "straight" if random.random() < 0.9 else "gay"

        # genetics
        self.personality = self.get_personality()
        self.appearance = self.get_appearance()
        self.fertility = None

        # names
        self.name = name
        self.surname = surname

        # progressive variables
        self.age = age
        self.status = married
        self.family = []
        self.events = []

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
        return hair_colors

    def personal_events(self):
        pass

class Relationship:
    def __init__(self, man, woman, key, married='married'):
        self.key = key
        self.man = man
        self.woman = woman
        self.no_children = 0
        self.children = []

    def add_child(self, child):
        self.no_children += 1
        self.children.append(child.key)

    def relationship_events(self):
        pass

class Community:
    def __init__(self, start_year, seed_couples, end_year=1354):
        # self.world = world
        self.seed_town = seed_couples

        # Population control
        self.alive = {}
        self.dead = {}
        self.alive_couples = {}

        # Networks
        self.family_tree = Digraph('Families', filename='families.gv',
            node_attr={'color': 'lightblue2', 'style': 'filled'})
        self.relations = Graph('Relations', filename='community.gv')
        
        # Time vars
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

    def read_names(self):
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

    def init_town(self):
        """
        Init town with seed couples. 
        """
        self.m_names, self.w_names, self.s_names = self.read_names()

        for i in range(self.seed_town):
            random.seed()

            # ages
            wife_age = random.randrange(12, 28)
            husband_age = random.randrange(18, 38)

            # names
            wife_name = random.choice(self.w_names)
            husband_name = random.choice(self.m_names)
            
            # surnames
            if random.random() < 0.6:
                wife_surname = f"van {husband_name}"
            else:
                wife_surname = ""

            husband_surname = random.choice(self.s_names)

            # keys
            w, h = f"{i}a", f"{i}b"

            # create people
            wife = Person(1, 1, wife_name, wife_surname, 'f', w, age=wife_age, married='married')
            husband = Person(1, 1, husband_name, husband_surname, 'm', h, age=husband_age, married='married')
            
            self.family_tree.node(w)
            self.relations.node(w)
            self.family_tree.node(h)
            self.relations.node(h)

            # marry husband and wife
            self.marry(wife, husband)

    def marry(self, wife, husband):
        # also serves as key for the relationship
        self.total_marriages += 1
        key = f"{self.total_marriages}"

        # create relationship and add to inventory
        marriage = Relationship(husband, wife, key)
        self.alive_couples[key] = marriage

        # represent in family network
        self.family_tree.node(key, shape="diamond")
        self.family_tree.edge(wife.key, key)
        self.family_tree.edge(husband.key, key)

    def community_events(self):
        pass
    
    def print_stats(self):
        print(f"Marriages: {self.total_marriages}")

    def time(self):
        """
        Runs the time loop 
        """
        while self.year < self.end_year:
            for r in self.alive_couples.values():
                r.relationship_events()
            
            for p in self.alive.values():
                p.personal_events()

            self.community_events()
            self.print_stats()
            self.year += 1

c = Community(1340, 4)