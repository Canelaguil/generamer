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

def get_person(rand=True, sex="r", age=-1, surname=""):
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

    print(f"Created {name} {surname}")
    return person


def init_generation(init_couples):
    G = nx.Graph()
    for i in range(init_couples):
        wife = get_person(rand=False, sex="f")
        husband = get_person(rand=False, sex="m")
        w = f"{i}w"
        h = f"{i}h"
        G.add_nodes_from([(w, wife), (h, husband)])
        G.add_edge(w, h)

        # json dump
        with open(f"people/{i}.json", "w") as output:
            json.dump(wife, output)
            json.dump(husband, output)

    nx.draw(G, with_labels=True, font_weight='bold')
    nx.draw_shell(G)
    plt.show()


        

        

init_generation(2)
