
class House:
    def __init__(self, income, street, section, number, city, function=None, material='wood', key='r'):
        # People
        self.inhabitants = []
        self.inh_count = 0
        self.breadwinners = []
        self.caretakers = []
        self.care_dependant = []

        # House
        self.city = city
        self.income_class = income
        self.street = street
        self.section = section
        self.number = number
        if key == 'r':
            self.key = f"{self.street.name}.{self.section.relative_key}.{self.number}"
        else:
            self.key = key

        # House
        self.function = function
        self.material = material
        self.init_household()

    def init_household(self):
        """
        Init household
        """
        if self.income_class not in self.city.empty_houses:
            self.city.empty_houses[self.income_class] = []
        self.city.empty_houses[self.income_class].append(self.key)

        self.city.houses[self.key] = self

    """
    PEOPLE MANAGEMENT
    """

    def add_person(self, inhabitant, reason):
        """
        REASONS:
        - birthed
        - adopted
        - married
        - moved
        """
        if self.inh_count == 0:
            self.city.empty_houses[self.income_class].remove(self.key)
        self.inh_count += 1

        if reason == 'birthed':
            text = f"{inhabitant.name} was born in {self.street.name}."
        elif reason == 'adopted':
            text = f"{inhabitant.name} was adopted into the household at {self.key} at age {inhabitant.age}."
        elif reason == 'married':
            text = f"{inhabitant.name} moved to {self.key} after marriage."
        elif reason == 'moved':
            text = f"{inhabitant.name} moved to {self.key} at {inhabitant.age}."
        else:
            text = f"{inhabitant.name} moved to {self.key} at age {inhabitant.age} because of {reason}."
        inhabitant.knowledge.add_bit(0, text)

        inhabitant.house = self
        self.inhabitants.append(inhabitant)
        if inhabitant.age < 13:
            self.care_dependant.append(inhabitant)

    def add_people(self, inhabitants, reason='moved'):
        for i in inhabitants:
            self.add_person(i, reason)

    def remove_person(self, key, reason):
        """
        REASONS:
        - died
        - married
        - orphaned
        - moved_city
        - moved_outside
        """
        self.inh_count -= 1
        if self.inh_count == 0:
            if self.income_class not in self.city.empty_houses:
                self.city.empty_houses[self.income_class] = []
            self.city.empty_houses[self.income_class].append(self.key)

        self.inhabitants = [x for x in self.inhabitants if x.key != key]
        self.care_dependant = [x for x in self.care_dependant if x.key != key]
        self.breadwinners = [x for x in self.breadwinners if x.key != key]
        self.caretakers = [x for x in self.caretakers if x.key != key]

    """
    HOUSEHOLD MANAGEMENT
    """

    def appoint_breadwinner(self, bread_candidate):
        bread_candidate.breadwinner = True
        bread_candidate.knowledge.add_bit(2, f"Became breadwinner of household.")
        self.breadwinners.append(bread_candidate)

    def appoint_caretaker(self, care_candidate):
        care_candidate.caretaker = True
        self.caretakers.append(care_candidate)

        # add knowledge to caretaker and caretakees
        if self.care_dependant != []:
            children = ""
            for ch in self.care_dependant:
                if ch.key != care_candidate.key:
                    ch.knowledge.add_bit(
                        2, f"{care_candidate.name} took care of {ch.name} since {ch.name} was {ch.age}.")
                    children += f"{ch.name}, "
            care_candidate.knowledge.add_bit(
                2, f"Became caretaker of {children[:-2]} at age {care_candidate.age}.")

    def update_roles(self, care_candidate=None, bread_candidate=None):
        if care_candidate != None:
            self.appoint_caretaker(care_candidate)
        if bread_candidate != None:
            self.appoint_breadwinner(bread_candidate)

    def find_breadwinner(self):
        option = None

        for i in self.inhabitants:
            if i.age > 15 or i.emancipated or i.independent or i.breadwinner or i.caretaker:
                if option != None:
                    if option.sex == i.sex:
                        if i.age > option.age:
                            option = i
                    elif option.sex == 'f' and i.sex == 'm':
                        option = i
                    else:
                        option = i
                else:
                    option = i
                
                # print(f"sex: {i.jsonify()['biological']['sex']}")
                # print(f"alive: {i.jsonify()['alive']}")
                # print(f"house: {i.jsonify()['house']}")
                # print(f"age: {i.jsonify()['procedural']['age']}")
                # print(i.jsonify())
                # print("---------------------------")

        if option != None:
            self.appoint_breadwinner(bread_candidate=option)
            return True
        # print(self.inhabitants)
        # for i in self.inhabitants:
        #     if i.age > 15:
        #         sys.exit()
        return False

    def find_caretaker(self):
        option = None

        for i in self.inhabitants:
            if i.age > 11:
                if option != None:
                    if option.sex == 'f' and i.sex == 'f':
                        if i.age > option.age:
                            option = i
                    elif option.sex == 'm' and i.sex == 'f':
                        option = i
                    else:
                        option = i
                else:
                    option = i

        if option != None:
            self.update_roles(care_candidate=option)
            return True
        return False

    def relocate_members(self):
        for i in self.inhabitants:
            i.knowledge.add_bit(4, f"Left {self.key} for lack of a breadwinner.")
            self.remove_person(i.key, 'orphaned')
            self.city.community.find_house_for(i)                 

    """
    EVENTS
    """
    def house_trigger(self, trigger, params=None):
        """
        TRIGGERS:
        - death / person_key
        - 
        """
        pass

    def house_events(self):
        """
        Yearly household events.

        EVENTS:
        - inter household relations
        - 
        """
        if self.inhabitants == []:
            return

        # take children out of care
        for i in self.care_dependant:
            if i.age > 13:
                self.care_dependant.remove(i)        

        # check if there is a caretaker for the children
        if self.care_dependant != [] and self.caretakers == []:
            if not self.find_caretaker():
                for child in self.care_dependant:
                    child.trigger.neglected()

        # check if there is still a breadwinner
        if self.breadwinners == []:
            found_breadwinner = self.find_breadwinner()
            if not found_breadwinner:
                self.relocate_members()

    """
    OUTPUT
    """
    def get_householdmembers(self):
        return self.inhabitants

    def household_summary(self):
        return {
            "income_class" : self.income_class,
            "breadwinners" : [(x.key, x.name) for x in self.breadwinners],
            "caretakers" : [(x.key, x.name) for x in self.caretakers],
            "care dependant" : [(x.key, x.name) for x in self.care_dependant],
            "inhabitants" : [(x.key, x.name) for x in self.inhabitants]
        }
   