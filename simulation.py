"""
Distinction between city and simulation.
"""

import json
import os, sys
import copy
import math
import networkx as nx
from graphviz import Digraph, Graph
import numpy as np
import matplotlib.pyplot as plt
import random
import csv
import pickle
from classes.person import Person
from classes.places import Others
from classes.house import House
from classes.relationship import Relationship

class City:
    def __init__(self, start_year, end_year=1400):
        # Lists
        self.houses = {}
        self.empty_houses = {}
        self.alive, self.dead, self.people = {}, {}, {}
        self.active_couples = {}
        self.bachelors, self.bachelorettes = [], []
        self.buurten, self.streets = pickle.load(open('city.p', 'rb'))
        Street.city = self
        self.outside = Others(self)
        self.to_die, self.to_live, self.marriage_gone = [], [], []

        # Stats and basics
        self.year = start_year
        self.start_year, self.end_year = start_year, end_year
        self.births, self.deaths = 0, 0
        self.towns_people, self.total_marriages = 0, 0

        # Networks
        self.family_tree = Digraph('Families', filename='families.dot',
                            node_attr={'color': 'lightblue2', 'style': 'filled'}, engine='sfdp')
        self.family_tree.attr(overlap='false')
        self.network = nx.Graph()

        # Initializations
        self.m_names, self.w_names, self.n_names, self.trait_modifiers = pickle.load(open('sources.p', 'rb'))
        self.init_town()
        self.time()

    """
    CITY INIT
    """

    def init_town(self):
        solo_key = 0
        
        random.seed()
        for home in self.houses.values():
            inhabitants = []
            chance = random.random()

            # matrimony
            if chance < 0.6:
                # ages
                wife_age = random.randrange(14, 28)
                husband_age = random.randrange(18, 38)

                # keys & people
                w, h = f"{self.total_marriages}a", f"{self.total_marriages}b"
                wife = Person(None, w, self, house=home, sex='f',
                              age=wife_age, married=True, emancipated=True, independent=True)
                husband = Person(None, h, self, house=home, sex='m',
                                 age=husband_age, married=True, emancipated=True, independent=True)

                self.marry(wife, husband, assigned_home=home)

            # roommates
            elif chance < 0.8:
                no_inhabitants = random.randint(2, 5)
                age_lowest = random.randrange(15, 50)
                sex = 'f' if random.random() < 0.4 else 'm'
                for _ in range(no_inhabitants):
                    age = random.randint(age_lowest, age_lowest + 10)
                    key = f"{solo_key}s"
                    inhabitant = Person(
                        None, key, self, house=home, sex=sex, age=age)
                    inhabitants.append(inhabitant)
                    solo_key += 1
                home.add_people(inhabitants)
        # self.print_stats()

    """
    COMMUNITY BUILDING
    """

    def marry(self, wife, husband, assigned_home=None):
        # also serves as key for the relationship
        key = f"{self.total_marriages}"

        # create relationship and add to inventory
        Relationship(husband, wife, key, assigned_house=assigned_home)
        husband.emancipated = True
        wife.emancipated = True
        self.total_marriages += 1

    def find_house_for(self, person):
        # TODO: find house through connections
        if person.age < 16:
            if person.parents != None:
                # check if they can live with sibling
                for sibling in person.parents.children:
                    if sibling.key != person.key and sibling.alive and sibling.independent:
                        if sibling.house != None:
                            sibling.house.add_person(person, 'adopted')
                            person.knowledge.add_bit(1, f"Went to live with sibling {sibling.name} at age {person.age}.")
                            print(f"{person.key} adopted")
                            return

                # check if they can live with paternal family
                if person.parents.man.parents != None:
                    if person.parents.man.parents.man.alive or person.parents.man.parents.woman.alive:
                        if person.parents.man.parents.man.house != None:
                            person.parents.man.parents.relationship_trigger('adopt grandchild', person)
                            return
                    for unclaunt in person.parents.man.parents.children:
                        if unclaunt.alive and unclaunt.emancipated and unclaunt.house != None:
                            person.knowledge.add_bit(1, f"Went to live with father's sibling {unclaunt.name} at age {person.age}.")
                            unclaunt.house.add_person(person, 'adopted')
                            print(f"{person.key} adopted")
                            return

                # check if they can live with maternal family
                if person.parents.woman.parents != None:
                    if person.parents.woman.parents.man.alive or person.parents.woman.parents.woman.alive:
                        if person.parents.woman.parents.man.house != None:
                            person.parents.woman.parents.relationship_trigger('adopt grandchild', person)
                        return
                    for unclaunt in person.parents.woman.parents.children:
                        if unclaunt.alive and unclaunt.emancipated and unclaunt.house != None and unclaunt.independent:
                            person.knowledge.add_bit(1, f"Went to live with mother's sibling {unclaunt.name} at age {person.age}.")
                            unclaunt.house.add_person(person, 'adopted')
                            print(f"{person.key} adopted")
                            return
                            
            self.outside.send_toorphanage(person)
            return

        if person.income_class in self.empty_houses and self.empty_houses[person.income_class] != []:
            house_key = random.choice(
                        self.empty_houses[person.income_class])
            new_house = self.houses[house_key]
            new_house.add_person(person, 'moved')
            new_house.update_roles(
                care_candidate=person, bread_candidate=person)
        else:
            self.outside.move_outoftown(person)

    def match_com(self):
        """
        Matches bachelors and bachelorettes. 
        """
        for bachelor in self.bachelors:
            if self.bachelorettes == []:
                return
            options = copy.deepcopy(self.bachelorettes)
            while True:
                if options == []:
                    break

                try:
                    groom = self.alive[bachelor]
                    match_id = random.choice(options)
                    match = self.alive[match_id]
                except:
                    print("one of them dead")
                    break

                if match.parents.key != groom.parents.key and match.income_class == groom.income_class:
                    self.bachelorettes.remove(match_id)
                    self.marry(match, groom)
                    break
                else:
                    options.remove(match_id)

    def community_events(self):
        self.match_com()
        self.outside.yearly_events()

    """
    TIME FLIES WHEN YOU'RE HAVING FUN
    """

    def time(self):
        """
        Runs the time loop 
        """
        while self.year < self.end_year:
            for r in self.active_couples.values():
                r.relationship_events()

            for p in self.alive.values():
                p.personal_events()

            for h in self.houses.values():
                h.house_events()

            self.community_events()

            # Dead & Birth
            for baby in self.to_live:
                self.alive[baby.key] = baby
                self.people[baby.key] = baby

            print(len(self.to_die))
            for corpse in self.to_die:
                self.alive.pop(corpse)

            for break_up in self.marriage_gone:
                self.active_couples.pop(break_up)


            self.print_stats()
            self.year += 1
            self.bachelors, self.bachelorettes = [], []
            self.to_die, self.to_live, self.marriage_gone = [], [], []
            self.deaths, self.births = 0, 0

        # self.output_people()
        # self.output_houses()
        # self.output_people()
        # self.draw_community()
        # self.family_tree.format = 'pdf'
        # self.family_tree.view()

    """
    HELPER FUNCTIONS
    """
    def person_died(self, key, name):
        self.deaths += 1
        self.towns_people -= 1
        self.to_die.append(key)
        self.dead[key] = self

        # process global networks
        self.family_tree.node(key, label=name, color='orange')
        # network.remove_node(self.key)

    def person_was_born(self, person):
        self.births += 1
        self.towns_people += 1

        self.to_live.append(person)

        self.family_tree.node(person.key, label=person.name)
        self.network.add_node(person.key, label=person.name)

    def romance_dies(self, key):
        self.marriage_gone.append(key)

    """
    OUTPUT METHODS
    """

    def output_people(self, mode="all"):
        # print(people)
        if mode == 'all':
            database = self.people
        elif mode == 'alive':
            database = self.alive
        elif mode == 'dead':
            database = self.dead

        if not os.path.exists('people'):
            os.mkdir('people')

        for individual in database.values():
            with open(f"people/{individual.key}.json", "w") as output:
                json.dump(individual.jsonify(), output)

    def output_houses(self):
        if os.path.exists('houses'):
            pass
        else:
            os.mkdir('houses')

        for h in self.houses.values():
            with open(f"houses/{h.key}.json", "w") as output:
                json.dump({"summary": h.household_summary()}, output)

    def print_stats(self):
        print("---------------------------------")
        print(f"| {self.year} | +{self.births} -{self.deaths}")
        print(f"Marriages: {self.total_marriages}")
        print(f"Number of inhabitants: {self.towns_people}")
        print(f"Total died: {len(self.dead)}")


class Street:
    city = 0

    def __init__(self, name, inputlist):
        self.name = name
        self.houses = []
        self.sections = self.init_street(inputlist)

    def init_street(self, row):
        if row == []:
            return
        cols = ['street', 'A', 'class', 'B', 'class',
                'C', 'class', 'D', 'class', 'E', 'class']
        sections = {}
        for i in range(1, 11, 2):
            if row[i] == '' or i >= len(row):
                break
            sections[cols[i]] = self.Section(
                int(row[i]), int(row[i+1]), self, cols[i], self.city)
            self.houses.extend(sections[cols[i]].houses)
        return sections

    def get_houses(self):
        return self.houses

    def street_summary(self):
        summary = {}
        for s in self.sections.values():
            summary[s.relative_key] = s.get_section_summary
        return summary

    def get_street(self):
        street = []
        for h in self.houses:
            street.extend(h.get_householdmembers())
        return street


    class Section:
        def __init__(self, no_houses, income_class, street, key, city):
            self.total_lots = no_houses
            self.empty_lots = copy.deepcopy(self.total_lots)
            self.relative_key = key
            self.in_class = income_class
            self.street = street
            self.city = city
            self.houses = self.init_houses()

        def init_houses(self):
            section = []
            for i in range(self.total_lots):
                section.append(House(self.in_class, self.street, self, i, self.city))
            return section

        def get_section_summary(self):
            summary = {}
            for house in self.houses:
                summary[house.key] = house.household_summary()
            return summary

        def get_people(self):
            people = []
            for house in self.houses:
                people.extend(house.get_householdmembers())
            return people

# City(1370)