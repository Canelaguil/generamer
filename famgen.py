import json
import copy
import networkx as nx
import matplotlib.pyplot as plt
import random

class Generations:
    def __init__(self, gens, seed_couples):
        self.m_names, self.w_names, self.s_names = self.read_names()
        self.single_gen = 1
        self.marriages = 0
        self.G = nx.Graph()
        self.init_generation(seed_couples)
        for _ in range(gens - 1):
            self.add_generation()
            self.draw_network()
            self.print_stats()

    def print_stats(self):
        nodes = list(self.G.nodes())
        no_nodes = len(nodes)
        no_people = no_nodes - self.marriages
        print(f"Number of nodes: {no_nodes}")
        print(f"Number of people: {no_people}")
        print(f"Number of marriages: {self.marriages}")

    def read_names(self):
        men_file = open("men.names", "r")
        women_file = open("women.names", "r")
        sur_file = open("genericsur.names", "r")

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

    def draw_network(self):
        edges = self.G.edges()
        colors = colors = [self.G[u][v]['color'] for u,v in edges]
        color_map = []
        for _, n in self.G.nodes.data():
            if n["node"] == "relation":
                color_map.append('red')
            else:
                color_map.append('yellow')

        nx.draw(self.G, node_color=color_map, edges=edges, edge_color=colors, with_labels=True, font_weight='bold')
        plt.show()

    def are_siblings(self, a, b):
        neighbours_a = self.G[a]
        parents_a = ""
        for key, value in neighbours_a.items():
            if value['kind'] == 'parents':
                parents_a = key
        return parents_a in self.G[b].keys()

    def get_person(self, generation, rand=True, sex="r", age=-1, surname="", married=False):
        random.seed()
        person = {}

        if rand:
            sex = "m" if random.random() < 0.6 else "f"
            surname = ""
            if random.random() < 0.4:
                surname = random.choice(self.s_names)

        
        sexuality = "straight" if random.random() < 0.9 else "gay"

        # name 
        if sex == "m":
            name = random.choice(self.m_names)
        else:
            name = random.choice(self.w_names)

        # json creator
        person["names"] = {
            'name': name,
            'surname': surname
        }
        person["general"] = {
            'sex': sex,
            'sexuality': sexuality,
            'status' : married
        }

        person["node"] = "human"
        person["gen"] = generation

        return person

    def init_generation(self, init_couples):
        for i in range(init_couples):
            wife = self.get_person(0, rand=False, sex="f", married=True)
            husband = self.get_person(0, rand=False, sex="m", married=True)
            hn = husband["names"]["name"]
            if wife["names"]["surname"] == "":
                if random.random() < 0.6:
                    wife["names"]["surname"] = f"van {hn}"
            
            # add wife and husband to network
            w, h = f"{i}w", f"{i}h"
            self.G.add_nodes_from([(w, wife), (h, husband)])
            
            # generate offspring
            self.consumate_match(h, w)

    def consumate_match(self, husband, wife):
        hn = self.G.nodes[husband]['names']['name']
        no_children = random.randrange(10)
        rel = {"color" :'r', "node" : "relation", "children" : no_children}
        r = f"{husband}r"
        self.G.add_nodes_from([(r, rel)])
        self.G.add_edge(wife, r, color="r", kind='marriage')
        self.G.add_edge(husband, r, color="r", kind='marriage')

        for j in range(no_children):
            key = f"{r}{j}c"
            child = self.get_person(1)
            if child["general"]["sex"] == 'f':
                child["names"]["surname"] = f"{hn}sdochter"
            else:
                child["names"]["surname"] = f"{hn}szoon"

            self.G.add_nodes_from([(key, child)])
            self.G.add_edge(r, key, color='b', kind='parents')

            with open(f"people/{r}{j}c.json", "w") as output:
                json.dump(child, output)
        
        self.marriages += 1

    def add_generation(self):
        random.seed()
        bachelors, bachelorettes = [], []
        for key, n in self.G.nodes.data():
            if n["node"] == "human":
                if int(n["gen"]) == self.single_gen:
                    if n["general"]["sexuality"] == "gay":
                        if random.random() < 0.4:
                            continue
                    else:
                        if random.random() < 0.05:
                            continue
                    
                    if n["general"]["sex"] == 'm':
                        bachelors.append(key)
                    else:
                        bachelorettes.append(key)
                
        for bachelor in bachelors:
            if bachelorettes == []:
                return
            options = copy.deepcopy(bachelorettes)
            while True:
                if options == []:
                    break
                match = random.choice(options)
                if not self.are_siblings(bachelor, match):
                    bachelorettes.remove(match)
                    break
                else:
                    options.remove(match)
            
            self.consumate_match(bachelor, match)
        self.single_gen += 1

gens = Generations(3, 20)