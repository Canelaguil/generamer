class Others:
    def __init__(self, context):
        self.people = {}
        self.couples = {}
        self.context = context
        self.monasteries = {}
        self.orphanage = self.Orphanage(self)
        self.outside_home = None

    def yearly_events(self):
        self.orphanage.yearly_events()

    def move_outoftown(self, person):
        if person.house != None:
            person.house.remove_person(person.key, 'moved_outside')
            person.house = self.outside_home
        
        # try:
        #     alive.pop(person.key)
        # except:
        #     print(person.key)
        #     print("Died before leaving?")
        
        # for r in person.relationships:
        #     if r.active:
        #         r.end_relationship('partner_left')
        self.context.towns_people -= 1
        person.trigger.moved_outoftown()

    def move_couple_outoftown(self, couple):
        self.context.romance_dies(couple.key)
        self.couples[couple.key] = couple
        self.move_outoftown(couple.man)
        self.move_outoftown(couple.woman)

    def move_househould_outoftown(self, house):
        pass

    def send_tomonastery(self):
        pass

    def send_toorphanage(self, child):
        self.orphanage.add_person(child)

    def is_alive(self, key):
        pass

    class Monastery:
        def __init__(self):
            pass

    class Orphanage:
        def __init__(self, outside):
            self.outside = outside
            self.children = []
            self.people = {}
            self.supervisors = []
            self.no_children = 0
            self.income_class = 1

        def yearly_events(self):
            for child in self.children:
                if child.age > 17 and child.alive:
                    self.remove_person(child)
                if not child.alive:
                    self.children = [x for x in self.children if x.key != child.key]

        def adopt(self, child_key=""):
            if child_key == "":
                child = self.children.random.choice()
            else:
                child = self.people[child_key]
            self.children = [x for x in self.children if x.key != child.key]
            child.knowledge.add_bit(2, f"Was taken out of orphanage at age {child.age}.")
            child.trigger.out_orphanage()
            self.no_children -= 1
            return child

        def add_person(self, child):
            child.house = None
            self.children.append(child)
            child.emancipated = True
            child.independent = True
            self.people[child.key] = child
            child.income_class = self.income_class
            child.trigger.in_orphanage()

        def remove_person(self, child):
            self.children = [x for x in self.children if x.key != child.key]
            self.outside.context.find_house_for(child)
            child.trigger.out_orphanage()
            # print(f"{child.key} left orphanage")
            self.no_children -= 1
