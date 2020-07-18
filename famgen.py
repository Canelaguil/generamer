import json
import copy
import networkx as nx
import matplotlib.pyplot as plt
import random

class Generations:
    def __init__(self, gens, seed_couples, json=False):
        self.m_names, self.w_names, self.s_names = self.read_names()
        # Current unmarried generation
        self.single_gen = 1
        # Number of marriages
        self.marriages = 0

        # Genealogic tree
        self.G = nx.DiGraph()
        # Network of friendships
        self.N = nx.Graph()

        # Generational loop
        self.init_generation(seed_couples)
        for _ in range(gens - 1):
            self.forge_friendships()
            self.add_generation()
            self.draw_network()
            self.print_stats()

        # Print to output
        if json:
            self.jsonify()

    def jsonify(self):
        """
        Prints human nodes to output. 
        """
        for individual in self.G:
            with open(f"people/{individual}c.json", "w") as output:
                json.dump(self.G.nodes[individual], output)

    def print_stats(self):
        """
        Prints the statistics of the current Graph state. 

        TODO:
        - Add N statistiscs 
        """
        nodes = list(self.G.nodes())
        no_nodes = len(nodes)
        no_people = no_nodes - self.marriages
        print("---------------------------------------------")
        print(f"Number of nodes: {no_nodes}")
        print(f"Number of people: {no_people}")
        print(f"Number of marriages: {self.marriages}")

    def read_names(self):
        """
        Reads the different name files and saves them as lists.

        TODO:
        - Make distinction in class between names.
        - Add jobs names. 
        """
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
        """
        Draws network G and N.

        TODO:
        - Draw network N.
        """
        gedges = self.G.edges()
        nedges = self.N.edges()
        gcolors = [self.G[u][v]['color'] for u,v in gedges]
        ncolors = [self.N[u][v]['color'] for u,v in nedges]
        color_map = []
        for _, n in self.G.nodes.data():
            if n["node"] == "relation":
                color_map.append('red')
            else:
                color_map.append('yellow')

        nx.draw(self.G, node_color=color_map, edges=gedges, edge_color=gcolors, with_labels=True)
        nx.draw(self.G, edges=nedges, edge_color=ncolors, with_labels=True)
        plt.show()

    def are_siblings(self, a, b):
        """
        Checks if a and b are siblings. 
        """
        neighbours_a = self.G[a]
        parents_a = ""
        for key, value in neighbours_a.items():
            if value['kind'] == 'parents':
                parents_a = key
        return parents_a in self.G[b].keys()

    def get_personality(self):
        """
        Returns random personality traits based on the
        7 sins and virtues.
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

        return {"sins" : sins, "virtues" : virtues}

    def get_person(self, generation, rand=True, sex="r", age=-1, surname="", married="unmarried"):
        """
        Returns a newly generated person.

        TODO:
        - Personality
        - Look
        - Base look & personality on parents
        - Add family information
        """
        random.seed()
        person = {}

        person["node"] = "human"
        person["gen"] = generation

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

        person["personality"] = self.get_personality()

        return person

    def init_generation(self, init_couples):
        """
        Initializes the "seed couples" and generates their offspring.
        """
        for i in range(init_couples):
            wife = self.get_person(0, rand=False, sex="f", married=True)
            husband = self.get_person(0, rand=False, sex="m", married=True)
            hn = husband["names"]["name"]
            if wife["names"]["surname"] == "":
                if random.random() < 0.6:
                    wife["names"]["surname"] = f"van {hn}"
            
            # add wife and husband to network
            w, h = f"{i * 2}", f"{i  * 2 + 1}"
            self.G.add_nodes_from([(w, wife), (h, husband)])
            
            # generate offspring
            self.consumate_match(h, w)

    def consumate_match(self, husband, wife):
        """
        Generates children of a marriage.
        
        TODO:
        - Naming conventions
        - Twins?
        """
        hn = self.G.nodes[husband]['names']['name']
        self.G.nodes[husband]['general']['status'] = "married"
        self.G.nodes[wife]['general']['status'] = "married"
        no_children = random.randrange(10)
        children = []
        rel = {"color" :'r', "node" : "relation", "children" : no_children}
        r = f"{husband}-{wife}"
        self.G.add_nodes_from([(r, rel)])
        self.G.add_edge(wife, r, color="r", kind='marriage')
        self.G.add_edge(husband, r, color="r", kind='marriage')

        for j in range(no_children):
            key = f"{r}{j}"
            child = self.get_person(1)
            if child["general"]["sex"] == 'f':
                child["names"]["surname"] = f"{hn}sdochter"
            else:
                child["names"]["surname"] = f"{hn}szoon"

            self.G.add_nodes_from([(key, child)])
            self.G.add_edge(r, key, color='b', kind='parents')
            children.append(key)
        
        for child in children:
            # self.N.add_edge(wife, child, color='g')
            # self.N.add_edge(husband, child, color='g')
            children.remove(child)
            for sibling in children:
                self.N.add_edge(sibling, child, color='g', kind='sibling')
        
        self.marriages += 1

    def forge_friendships(self):
        pass

    def add_generation(self):
        """
        Makes matches between the currently unmarried generation and
        generates their children. 

        TODO:
        - Generate bastard children
        - Get outsider brides/grooms for bachelors/bachelorettes
        - Adoption (later stage)
        """
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

gens = Generations(2, 2, json=True)