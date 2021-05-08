import pickle
import numpy as np
import csv
import math
print('al')
from simulation import Street

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

def read_cityfiles():
        buurten = {}
        strbr = {}
        with open('sources/Buurten.csv', 'r') as bfile:
            csvreader = csv.reader(bfile)
            for row in csvreader:
                strbr[row[1]] = row[0]
                if row[0] not in buurten:
                    buurten[row[0]] = []
                buurten[row[0]].append(row[1])

        streets = {}
        with open('sources/SectionStreets.csv', 'r') as cfile:
            csvreader = csv.reader(cfile)
            for row in csvreader:
                streets[row[0]] = Street(row[0], row)

        return buurten, streets

a, b, c, d = read_files()
e, f = read_cityfiles()
pickle.dump([a, b, c, d], open('sources.p', 'wb'))
print(e)
pickle.dump([e, f], open('city.p', 'wb'))