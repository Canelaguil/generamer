import random
import json
import os, sys
import copy
import math
import numpy as np
from .information import Knowledge, Bit, Trigger

class Person:
    def __init__(self, parents, key, context, age=0, sex='r', married=False, surname='r', house=None, emancipated=False, independent=False):
        # biological
        if sex == 'r':
            self.sex = 'f' if random.random() < 0.51 else 'm'
        else:
            self.sex = sex
        self.sexuality = "straight" if random.random() < 0.9 else "gay"
        self.characteristics = self.get_characteristics()

        # genetics
        self.context = context # city
        self.parents = parents
        self.health = self.get_health()
        self.appearance = self.Appearance(self.parents)
        self.personality = self.Personality()

        # names
        self.names = self.Names(self.sex, self.parents, context, surname)
        self.name = self.names.name
        self.surname = self.names.surname
        self.nickname = self.names.nickname

        # progressive variables
        self.age = age
        self.married = married
        self.children = 0
        self.marriage = None
        self.relationships = []
        self.knowledge = Knowledge(self)
        self.trigger = Trigger(self)

        # binary
        self.key = key
        self.alive = True
        self.birthday = self.get_birthday()

        # houselife
        self.house = house
        self.emancipated = emancipated # financially stable
        self.independent = independent # moved out of parents house 
        self.caretaker = False
        self.breadwinner = False
        self.income_class = 0

        # start life
        self.connections = self.Connections(self, self.house)
        self.init_existence()

    """
    INITIALISATION
    """
    def get_birthday(self):
        if self.age != 0:
            birth_year = self.context.year-self.age
        else:
            birth_year = self.context.year
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
        characteristics = ['infertile', 'autistic',
                           'down syndrome', 'blind', 'deaf', 'transgender']
        own_ch = []
        if random.random() < 0.1:
            own_ch.append(random.choice(characteristics))
            if random.random() < 0.1:
                own_ch.append(random.choice(characteristics))
        return own_ch

    """
    LIVING & DYING
    """
    def init_existence(self):
        self.context.person_was_born(self)

        if self.house == None:
            if self.parents != None:
                self.house = self.parents.woman.house

            else:
                self.house = self.context.houses['outside']
        if self.age == 0:
            self.house.add_person(self, 'birthed')
        else:
            self.house.add_person(self, 'married')
        self.income_class = self.house.income_class

    def die(self, circumstance=""):
        self.alive = False
        self.context.person_died(self.key, self.name)

        # create bits
        self.knowledge.add_bit(0, f"Died at age {self.age}{circumstance}.")

        # end relationships
        cause = 'woman_died' if self.sex == 'f' else 'man_died'
        for relation in self.relationships:
            if relation.active:
                relation.end_relationship(cause, circumstance)

        # notify family
        if self.parents != None:
            self.parents.relationship_trigger(
                'dead child', self)

        # notify children
        for r in self.relationships:
            for child in r.children:
                if child.alive:
                    if self.sex == 'm':
                        child.trigger.father_died()
                    else:
                        child.trigger.mother_died()

        if self.house != None:
            self.house.remove_person(self.key, 'died')

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
                if self.age < 19:
                    chance = 0.00
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
        if self.age > 29 or self.age < 18:
            return

        random.seed()
        chance = 1.0 / (30 - self.age)

        if random.random() < chance:
            self.emancipated = True

            # set new income class
            try:
                hi = self.house.income_class
            except:
                print(f"{self.jsonify()}")
            in_weights = [0.2, 0.7, 0.1]
            in_values = [hi if hi == 1 else hi-1, hi, hi if hi == 5 else hi+1]
            self.income_class = np.random.choice(in_values, p=in_weights)
            self.knowledge.add_bit(
                2, f'Became financially stable at {self.age}.')

    def personal_events(self):
        self.age += 1

        # if self.age < 13 and not self.parents.man.alive and not self.parents.woman.alive:
            # print(f"{self.key} is an orphan")

        # chance of dying
        if random.random() < self.chance_of_dying('age'):
            self.die()
            return

        # chance of marrying
        if not self.married and self.parents != None:
            if random.random() < self.chance_of_marrying():
                if self.sex == 'f':
                    self.context.bachelorettes.append(self.key)
                elif self.sex == 'm' and self.emancipated:
                    self.context.bachelors.append(self.key)
                elif self.sex == 'm' and not self.emancipated:
                    # broadcast intention to look for lover
                    pass

        self.connections.social_life()

        # emancipation
        if not self.emancipated:
            self.emancipate()

    def jsonify(self):
        children = None # [c.key for c in r.children for r in self.relationships]
        rs = [f"{r.man.key}, {r.woman.key}" for r in self.relationships]
        person = {}
        person["alive"] = self.alive
        person["house"] = None if self.house == None else self.house.key
        person["names"] = self.names.jsonfiy()
        person["biological"] = {
            "parents": self.parents.key if self.parents else "ancestors",
            "sex": self.sex,
            "sexuality": self.sexuality,
            "health": self.health,
            "birthday": self.birthday
        }
        person["appearance"] = self.appearance.jsonify()
        person["parents"] = [f"{self.parents.man.key} and {self.parents.woman.key}" if self.parents else "ancestors",
                             f"{self.parents.man.name} and {self.parents.woman.name}" if self.parents else "ancestors"]
        person["procedural"] = {
            "age": self.age,
            "married": self.married,
            "relationships" : rs,
            'no_children': self.children,
            "children" : children
        }
        person["personality"] = {
            "sins": self.personality.jsonify_sins(),
            "virtues": self.personality.jsonify_virtues()
        }
        person["network"] = self.connections.get_network()
        person["events"] = self.knowledge.get_descriptions()

        return person

    """
    CLASSES
    """
    class Names:
        def __init__(self, sex, parents, context, surname='r', income_class=0):
            self.parents = parents
            self.sex = sex
            self.context = context
            if surname == 'r':
                self.surname = self.generate_surname()
            else:
                self.surname = surname
            self.name = self.generate_name()
            self.nickname = self.generate_nickname()

        def generate_name(self):
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
                return random.choice(self.context.w_names)
            if self.sex == 'm':
                return random.choice(self.context.m_names)
            return "Tarun"

        def generate_nickname(self):
            if random.random() < 0.4:
                return random.choice(self.context.n_names)
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
                "name": self.name,
                "nickname": self.nickname,
                "surname": self.surname
            }

    class Appearance:
        def __init__(self, parents):
            self.parents = parents
            self.hair_color = self.get_haircolor()
            self.hair_type = self.get_hairtype()
            self.eye_color = self.get_eye_color()

        def get_haircolor(self):
            hair_colors = ['black', 'brown', 'red',
                           'blonde', 'strawberry blonde']
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
                "hair_color": self.hair_color,
                "hair_type": self.hair_type,
                "eye_color": self.eye_color
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
            self.all[trait] = (v + influence, i)

        def combine_all(self):
            b = self.jsonify_virtues()
            return dict(self.jsonify_sins(), **b)

        def jsonify_virtues(self):
            return {
                "prudentia": self.prudentia,
                "iustitia": self.iustitia,
                "temperantia": self.temperantia,
                "fortitudo": self.fortitudo,
                "fides": self.fides,
                "spes": self.spes,
                "caritas": self.caritas
            }

        def jsonify_sins(self):
            return {
                "superbia": self.superbia,
                "avaritia": self.avaritia,
                "luxuria": self.luxuria,
                "invidia": self.invidia,
                "gula": self.gula,
                "ira": self.ira,
                "acedia": self.acedia
            }

        def jsonify_all(self):
            return self.combine_all()

        def jsonify(self):
            return {
                "sins": self.jsonify_sins(),
                "virtues": self.jsonify_virtues()
            }

    # Procedural classes
    class Connections:
        def __init__(self, person, house):
            self.person = person
            self.context = self.person.context
            self.own_key = person.key
            self.house = house
            self.dead_connections = []
            self.past_friends = []
            self.current_friends = []

            self.init_network()

        def init_network(self):
            for householdmember in self.house.get_householdmembers():
                other_key = householdmember.key
                self.make_connection(other_key, 'household')

            for sectionmember in self.house.section.get_people():
                other_key = sectionmember.key
                if not self.context.network.has_edge(self.own_key, other_key):
                    self.make_connection(other_key, 'section')

            for streetmember in self.house.street.get_street():
                other_key = streetmember.key
                if not self.context.network.has_edge(self.own_key, other_key):
                    self.make_connection(other_key, 'street')

            # for neighbor in self.house.section.get_people():
            #     other_key = streetmember.key
            #     if not network.has_edge(self.own_key, other_key):
            #         self.make_connection(other_key, 'street')

        def broadcast_intention(self, intent, depth=2):
            """
            INTENT:
            - find_child_friend
            - find_connection
            """
            random.seed()
            edges = self.context.network.edges(self.own_key)
            options = []
            for _, v in edges:
                try:
                    suggestions = people[v].connections.receive_intention(
                        intent, self.own_key, self.own_key, depth, [])
                    options.extend(suggestions)
                except:
                    pass
                    # print(f"Got suggestion {v}")

            if intent == 'find_child_friend':
                rel_mod = random.randint(-20, 30)
            else:
                rel_mod = 0

            for option in options:
                if random.random() < 0.6:
                    self.make_connection(option, 'outsider', rel_mod)

        def receive_intention(self, intent, source, op, depth, suggestions):
            depth -= 1
            if depth < 1:
                return []

            options = []
            for _, v in self.context.network.edges(self.own_key):
                if v != source and v != op and v not in suggestions:
                    options.extend(v)

            if intent == 'find_child_friend':
                return [x for x in options if self.context.people[x].age < 12]
            return options

        def get_indexmodifier(self, other_key):
            A = self.person.personality.jsonify_all()
            B = self.person.personality.jsonify_all()
            traits = ['superbia', 'avaritia', 'luxuria', 'invidia', 'gula', 'ira', 'acedia',
                      'prudentia', 'iustitia', 'temperantia', 'fortitudo', 'fides', 'spes', 'caritas']
            index_mod = 0
            for trait_a in traits:
                for trait_b in traits:
                    M = self.context.trait_modifiers[trait_a][trait_b]
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
            - len 1: household (children/parents/spouses)
            - len 2: section
            - len 3: street
            - len 4: neighborhood
            - len 5: city
            - len 6: outside (not for init)
            """
            edge_length = {'household' : 0, 'section' : 1, 'street' : 2, 
                           'neighborhood' : 3, 'city' : 4, 'outside' : 5}[nature]
            index_mod = self.get_indexmodifier(other_key)

            if nature == 'household':
                rel = random.randint(10, 40)
            else:
                rel = random.randint(-10, 10)

            rel += preset_rel
            self.context.network.add_edge(self.own_key, other_key, weight=rel,
                             index_mod=index_mod, nature=nature, length=edge_length)

        def social_life(self):
            pass
            # random.seed()
            # relations = sorted(network[self.own_key].items(), key=lambda edge: edge[1]['length'])
            # people = [[], [], [], [], [], []]
            # [people[i[1]['length']].append(i[0]) for i in relations]
            # print(relations)
            # maintain relations with
            # for u in relations:
            #     index_mod = copy.deepcopy(
            #         network.get_edge_data(self.own_key, u)['index_mod'])
            #     age_mod = 1.5 if self.person.age < 12 else 1

            #     """
            #     RANGE: -30-30
            #     - < 15 : nothing happens
            #     - 15-20 : small event
            #     - 20-25 : medium event
            #     - 25-30: big event
            #     """
            #     event = random.randint(-30, 30) + index_mod
            #     mod = age_mod if event > 0 else -1 * age_mod

            #     if abs(event) < 22:
            #         points = 0
            #     elif abs(event) < 25:
            #         points = 5
            #     elif abs(event) < 28:
            #         points = 10
            #     else:
            #         points = 20

            #     new_weight = network[self.own_key][u]['weight'] + (mod * points)
            #     network[self.own_key][u]['weight'] = new_weight

        def get_network(self):
            social_network = {'household': {}, 'section': {}, 'street': {},
                              'neighborhood': {}, 'city' : {}, 'outside' : {}}
            edges = self.context.network.edges(self.own_key)
            for u, v in edges:
                data = self.context.network.get_edge_data(u, v)
                social_network[data['nature']][v] = data

            return social_network
