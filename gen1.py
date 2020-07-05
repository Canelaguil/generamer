import json
import networkx as nx
import random

def generate_people(no_people):
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

    for i in range(no_people):
        random.seed()
        person = {}

        # sex
        sex = "m" if random.random() < 0.6 else "f"
        sexuality = "straight" if random.random() < 0.9 else "gay"
        
        # name 
        if sex == "m":
            name = random.choice(m_names)
        else:
            name = random.choice(w_names)

        surname = ""
        if random.random() < 0.4:
            surname = random.choice(s_names)

        # json creator
        person["names"] = {
            'name': name,
            'surname': surname
        }
        person["general"] = {
            'sex': sex,
            'sexuality': sexuality
        }


        # json dump
        with open(f"people/{name}.json", "w") as output:
            json.dump(person, output)

        print(f"{i}. Created {name} {surname}")

generate_people(3)