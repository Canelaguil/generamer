import json
import networkx as nx
import matplotlib.pyplot as plt
import random

def read_names():
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

def get_person(rand=True, sex="r", age=-1, surname="", married=False):
    random.seed()
    m_names, w_names, s_names = read_names()
    person = {}

    if rand:
        sex = "m" if random.random() < 0.6 else "f"
        surname = ""
        if random.random() < 0.4:
            surname = random.choice(s_names)

    
    sexuality = "straight" if random.random() < 0.9 else "gay"

    # name 
    if sex == "m":
        name = random.choice(m_names)
    else:
        name = random.choice(w_names)

    # json creator
    person["names"] = {
        'name': name,
        'surname': surname
    }
    person["general"] = {
        'sex': sex,
        'sexuality': sexuality
    }

    person["node"] = "human"
    person["status"] = married

    return person


def init_generation(init_couples):
    random.seed()
    G = nx.Graph()

    for i in range(init_couples):
        wife = get_person(rand=False, sex="f", married=True)
        husband = get_person(rand=False, sex="m", married=True)
        hn = husband["names"]["name"]
        if wife["names"]["surname"] == "":
            if random.random() < 0.6:
                wife["names"]["surname"] = f"van {hn}"

        # relationship
        no_children = random.randrange(10)
        rel = {"color" :'r', "node" : "relation", "children" : no_children}

        # add wife and husband to network
        r, w, h = f"{i}r", f"{i}w", f"{i}h"
        G.add_nodes_from([(r, rel), (w, wife), (h, husband)])
        G.add_edge(w, r, color="r")
        G.add_edge(h, r, color="r")

        # create children
        for j in range(no_children):
            key = f"{i}{j}c"
            child = get_person()
            if child["general"]["sex"] == 'f':
                child["names"]["surname"] = f"{hn}sdochter"
            else:
                child["names"]["surname"] = f"{hn}szoon"

            G.add_nodes_from([(key, child)])
            G.add_edge(r, key, color='b')

            with open(f"people/{i}{j}c.json", "w") as output:
                json.dump(child, output)        

        # json dump
        with open(f"people/{i}w.json", "w") as output:
            json.dump(wife, output)

        with open(f"people/{i}h.json", "w") as output:
            json.dump(husband, output)

    print(G.nodes())
    edges = G.edges()
    colors = colors = [G[u][v]['color'] for u,v in edges]
    color_map = []
    for _, n in G.nodes.data():
        if n["node"] == "relation":
            color_map.append('red')
        else:
            color_map.append('yellow')

    nx.draw(G, node_color=color_map, edges=edges, edge_color=colors, with_labels=True, font_weight='bold')
    plt.show()
    return G

G = init_generation(3)
print(G.nodes(node="human"))