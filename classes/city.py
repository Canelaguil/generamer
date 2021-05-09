import csv
import copy
import random
from .house import House

class City:
    def __init__(self):
        self.houses = {}
        self.empty_houses = {}
        self.buurten, self.streets = self.read_cityfiles()
        self.community = None

    def read_cityfiles(self):
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
                streets[row[0]] = Street(row[0], row, self)

        return buurten, streets

    def get_houses(self):
        return self.houses.values()
    
    def find_house(self, income_class):
        if income_class in self.empty_houses and self.empty_houses[income_class] != []:
            house_key = random.choice(self.empty_houses[income_class])
            return self.houses[house_key]
        else:
            return None

class Street:
    def __init__(self, name, inputlist, city):
        self.name = name
        self.city = city
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
