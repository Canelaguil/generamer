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
# def connect(key_a, key_b, nature='outsider', preset_rel=0):
#     """
#     NATURE:
#     - outsider
#     - family
#     - sibling
#     - parent
#     """
#     global trait_modifiers

#     A = people[key_a].personality
#     B = people[key_b].personality

#     # Determine index modifier
#     traits = ['superbia', 'avaritia', 'luxuria', 'invidia', 'gula', 'ira', 'acedia',
#               'prudentia', 'iustitia', 'temperantia', 'fortitudo', 'fides', 'spes', 'caritas']

#     index_mod = 0
#     # x_a = 0
    # for trait_a in traits:
    #     x_b = 0
    #     for trait_b in traits:
    #         if x_a < 7:
    #             kind_a = 'sins'
    #         else:
    #             kind_a = 'virtues'

    #         if x_b < 7:
    #             kind_b = 'sins'
    #         else:
    #             kind_b = 'virtues'

    #         M = trait_modifiers[trait_a][trait_b]
    #         a_value, a_opinion = A[kind_a][trait_a]
    #         b_value, b_opinion = B[kind_b][trait_b]

    #         a_mod = 1 if a_opinion == 'important' or a_opinion == 'happy' else 0
    #         b_mod = 1 if b_opinion == 'important' or b_opinion == 'happy' else 0
    #         x_b += 1

    #         if a_value > 5:
    #             index_a = a_mod
    #         elif a_value < 3:
    #             index_a = 2 + a_mod
    #         else:
    #             continue

    #         if b_value > 5:
    #             index_b = b_mod
    #         elif b_value < 3:
    #             index_b = 2 + b_mod
    #         else:
    #             continue

    #         index_mod += M[index_a][index_b]
    #     x_a += 1

    # if index_mod < -10 or index_mod > 10:
    #     print(index_mod)

    # Determine init relationshiplevel
    # if nature == 'parent':
    #     rel = random.randint(10, 40)
    # elif nature == 'sibling':
    #     rel = random.randint(5, 25)
    # elif nature == 'family':
    #     rel = random.randint(0, 15)
    # else:
    #     rel = random.randint(-10, 10)

    # rel += preset_rel
    # network.add_edge(key_a, key_b, weight=rel,
    #                  index_mod=index_mod, nature=nature)

# def broadcast_intention(intent, source_key, depth=2, age=0, gender='r'):
#     """
#     INTENT:
#     - find_child_friend: age, gender
#     - find_connection: age, gender
#     """
#     global network, people

#     edges = network.edges(source_key)
#     options = []
#     random.seed()

#     if intent == 'find_child_friend':
#         for u, v in edges:
#             data = network.get_edge_data(u, v)
#             sublist = network.edges(v)

#             if data['nature'] == 'parent'or data['nature'] == 'sibling':
#                 options.extend(sublist)
#             elif data['weight'] > 20:
#                 options.extend(sublist)
#             elif random.random() < 0.075:
#                 options.extend(sublist)
#         for _, option in options:
#             if random.random() < 0.6:
#                 potential_link = people[option]
#                 if potential_link.key == source_key:
#                     continue
#                 if abs(age - potential_link.age) < 4:
#                     childhood_start = random.randint(0, 20)
#                     connect(source_key, potential_link.key,
#                             preset_rel=childhood_start)


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
        self.personality = self.get_personality()

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

    """
    LIVING & DYING
    """

    # def init_person(self):
    #     global people_alive, births
    #     births += 1
    #     people_alive += 1
    #     alive[self.key] = self
    #     people[self.key] = self
    #     family_tree.node(self.key, label=self.name)
    #     network.add_node(self.key, label=self.name)
    #     self.init_network()

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

    # def die(self):
    #     global people_alive, deads
    #     deads += 1
    #     people_alive -= 1
    #     alive.pop(self.key)
    #     self.alive = False

    #     # process global networks
    #     dead[self.key] = self
    #     family_tree.node(self.key, label=self.name, color='orange')
    #     network.remove_node(self.key)
    #     # create bits
    #     self.add_bit(0, f"Died at age {self.age}.")
    #     cause = 'woman_died' if self.sex == 'f' else 'man_died'

    #     # end relationships
    #     for relation in self.relationships:
    #         relation.end_relationship(cause)

    #     # update parents' relationship
    #     self.parents.relationship_trigger('dead child', (self.name, self.age))

    """
    PROCEDURAL
    """
    # def social_life(self):
    #     random.seed()
    #     edges = network.edges(self.key)
      
    #     for u, v in edges:
    #         old_weight = copy.deepcopy(network.get_edge_data(u, v)['index_mod'])
    #         other = people[v].name
    #         """
    #         RANGE: 0-30
    #         - x < 10 : minor event, 5 points
    #         - 10 < x < 22 : medium event, 10 points
    #         - 22 < x < 28 : major event, 20 points
    #         - 28 < x < 30 : mindblowing event, 30 points
    #         """
    #         positive = random.randint(0, 30) + old_weight
    #         negative = random.randint(0, 30) - old_weight

    #         if positive < 10:
    #             points = 5
    #         elif positive < 22:
    #             points = 10
    #         elif positive < 28:
    #             points = 20
    #         elif positive < 31:
    #             points = 30

    #         if negative < 10:
    #             _points = 5
    #         elif negative < 22:
    #             _points = 10
    #         elif negative < 28:
    #             _points = 20
    #         elif negative < 31:
    #             _points = 30

            # print('--------')
            # print(network[u][v]['weight'])
            # network[u][v]['weight'] = old_weight + points - _points
            # print(network[u][v]['weight'])

            if network[u][v]['weight'] > 80 and old_weight < 80:
                self.add_bit(1, f'{self.name} and {other} became good friends.')
            elif network[u][v]['weight'] > 50 and old_weight < 80:
                self.add_bit(1, f'{self.name} and {other} became friends.')
            
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

    """
    CHANCES
    """

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

    def jsonify(self):
        global network
        person = {}
        bits = []
        for l in self.bits.values():
            for el in l:
                bits.append(el.description)

        rs = []
        for r in self.relationships:
            rs.append(r.key)

        social_network = {'family' : {}, 'outsider' : {}, 'sibling' : {}, 'parent' : {}}
        edges = network.edges(self.key)
        for u, v in edges:
            data = network.get_edge_data(u, v)
            social_network[data['nature']][v] = data

        person["key"] = self.key
        person["alive"] = self.alive
        person["names"] = {
            "name": self.name,
            "surname": self.surname
        }
        person["biological"] = {
            "sex": self.sex,
            "sexuality": self.sexuality
        }

        if self.parents:
            parents = f"{self.parents.man.name} and {self.parents.woman.name}"
        else:
            parents = "ancestors"
        person["genetics"] = {
            "parents": parents,
            "health": self.health,
            "birthday": self.birthday
        }
        person["personality"] = self.personality
        person["appearance"] = self.appearance
        person["social"] = social_network
        person["procedural"] = {
            "age": self.age,
            "married": self.married,
            'no_children': self.children,
            'relationships': rs,
            "events": bits
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
            self.man.add_bit(
                0, f"Got married at {self.man.age} to {self.woman.name}.")
            self.woman.add_bit(
                0, f"Got married at {self.woman.age} to {self.man.name}.")
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

    def end_relationship(self, cause, circumstance=""):
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
                        child.add_bit(
                            2, f"Lost mother at the age of {child.age}")
        elif cause == 'man_died':
            if self.married:
                self.woman.married = False
                if self.woman.alive:
                    self.woman.add_bit(
                        1, f"Became a widow at {self.woman.age}.")
                for child in self.children:
                    if child.alive:
                        child.add_bit(
                            2, f"Lost father at the age of {child.age}")
        elif cause == 'separated':
            self.active = False

        active_couples.pop(self.key)

    def add_child(self):
        # global network, family_tree
        # self.no_children += 1
        # self.man.children += 1
        # self.woman.children += 1
        # child_key = f"{self.key}c{self.no_children}"
        # try:
        #     child = Person(self, child_key)
        # except:
        #     print(f"couldnt init child {self.no_children} of {self.key}")
        # self.children.append(child)

        # # add to networks
        # family_tree.edge(self.key, child_key, weight='6')

        # connect(self.woman.key, child_key, 'parent')
        # if self.man.alive:
        #     connect(self.man.key, child_key, 'parent')

        # chance of child dying in childbirth
        # self.stillbirthbit = False
        # if random.random() < child.chance_of_dying('birth'):
        #     child.die()
        #     self.dead_children += 1
        #     self.still_births += 1
        #     if self.dead_children == 1 and self.children == 1:
        #         self.man.add_bit(
        #             2, f"Lost first child with {self.woman.name} in childbirth.")
        #         self.woman.add_bit(
        #             2, f"Lost first child with {self.man.name} in childbirth.")
        #     elif self.still_births > 1 and not self.stillbirthbit:
        #         self.man.add_bit(
        #             2, f"{self.woman.name} had several miscarriages when they tried to conceive.")
        #         self.woman.add_bit(
        #             2, f"Had several misscariages when trying to conceive with {self.man.name}.")
        #         self.stillbirthbit = True

        # # chance of mother dying in childbirth
        # if random.random() < self.woman.chance_of_dying('childbirth'):
        #     self.woman.die()
        #     if self.married:
        #         self.man.add_bit(
        #             2, f"Lost wife {self.woman.name} when she gave birth to {child.name}.")

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
                        child.trigger('virtue_influence',
                                      (vir, val, 'parents'))
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
        self.end_year = end_year

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
        global active_couples

        # Init towns people and marriages
        for i in range(1, self.seed_town + 1):
            random.seed()

            # ages
            wife_age = random.randrange(14, 28)
            husband_age = random.randrange(18, 38)

            # keys
            w, h = f"{i}a", f"{i}b"

            # create people
            wife = Person(None, w, sex='f', age=wife_age, married=True)
            husband = Person(None, h, sex='m', age=husband_age, married=True)

            # marry husband and wife
            self.marry(wife, husband)

        # forge initial friendships
        for relation in active_couples.values():
            for r in active_couples.values():
                if random.random() < 0.6:
                    if not relation.man.key in network[r.man.key]:
                        if random.random() < 0.7:
                            connect(relation.woman.key, r.woman.key)
                    if not relation.woman.key in network[r.woman.key]:
                        if random.random() < 0.7:
                            connect(relation.woman.key, r.woman.key)

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
        nx.draw_spring(network, edges=edges,
                       with_labels=True, node_color=color_map)
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
        # self.draw_community()
        family_tree.format = 'pdf'
        family_tree.view()


Community(1330, 40)
