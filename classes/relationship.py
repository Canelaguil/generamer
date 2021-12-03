import random
import sys
from .person import Person

class Relationship:
    def __init__(self, man, woman, key, married=True, assigned_house=None):
        self.active = True
        self.key = key
        self.married = married
        self.context = man.context
        self.family_values = [[], []]

        # family members
        self.man = man
        self.woman = woman
        self.children = []

        # stats
        self.no_children = 0
        self.dead_children = 0
        self.still_births = 0

        self.init_relationship(assigned_house)

    """
    BEGINNING & ENDING
    """
    def init_relationship(self, assigned_house):
        self.man.relationships.append(self)
        self.woman.relationships.append(self)
        self.context.active_couples[self.key] = self
        self.set_familyvalues()
        if self.married:
            self.man.trigger.marriage(self.woman)
            self.woman.trigger.marriage(self.man)

        # represent in family network
        self.context.family_tree.node(self.key, shape="diamond")
        self.context.family_tree.edge(self.woman.key, self.key, weight='12')
        self.context.family_tree.edge(self.man.key, self.key, weight='12')

        # organize house
        self.init_household(assigned_house)

    def init_household(self, assigned_house):
        random.seed()
        if assigned_house == None and self.married:
            if self.woman.breadwinner and self.woman.house != None and not self.man.breadwinner:
                self.woman.house.add_person(self.man, 'married')
                self.man.house.update_roles(care_candidate=self.man)
                self.man.knowledge.add_bit(
                    3, f"Moved in with wife {self.woman.name} after marriage.", 'movein_w_wife')
                self.woman.knowledge.add_bit(
                    3, f"Had {self.man.name} move in at {self.woman.house.key} after marriage.", 'movein_husband')
                self.man.independent = True
            elif self.man.breadwinner and self.man.independent and self.man.house != None:
                self.man.house.add_person(self.woman, 'married')
                self.man.house.update_roles(care_candidate=self.woman)
                self.woman.knowledge.add_bit(
                    2, f"Moved in with husband {self.man.name} after marriage.", 'movein_w_husband')
                self.man.knowledge.add_bit(
                    2, f"Had {self.woman.name} move in at {self.man.house.key} after marriage.", 'movein_wife')
                self.woman.independent = True
            else:
                # print(f"{self.man.key} moved in with {self.woman.key}")
                new_house = self.context.city.find_house(self.man.income_class)
                if new_house != None:
                    new_house.add_people([self.man, self.woman], 'married')
                    new_house.update_roles(
                        care_candidate=self.woman, bread_candidate=self.man)
                    self.man.independent, self.woman.independent = True, True
                else:
                    # move in with husband family
                    if random.random() < 0.5 and self.man.house != None:
                        self.man.house.add_person(self.woman, 'married')
                        self.man.house.update_roles(care_candidate=self.woman)
                        self.woman.knowledge.add_bit(
                            2, f"Moved in with husband {self.man.name}'s family after marriage.", 'move_to_hfam')
                        self.man.knowledge.add_bit(
                            2, f"Had {self.woman.name} move into family home at {self.man.house.key} after marriage.", 'move_wifeto_fam')
                    else:
                        self.context.outside.move_couple_outoftown(self)
        elif self.married:
            self.man.house.update_roles(
                care_candidate=self.woman, bread_candidate=self.man)

    def set_familyvalues(self):
        pass
        # for partner in [self.man, self.woman]:
        #     for trait, score in partner.personality.jsonify_all().items():
        #         value, importance = score
        #         if (value > 5 or value < 3) and importance == 'important':
        #             self.family_values[1].append((trait, value))

    def end_relationship(self, cause, circumstance=""):
        """
        Possible causes:
        - woman_died
        - man_died 
        - man_left
        - woman_left
        - separated
        """
        if self.active:
            self.active = False

        if cause == 'woman_died':
            if self.married:
                self.man.married = False
                if self.man.alive:
                    self.man.knowledge.add_bit(
                        1, f"Became a widower at {self.man.age}.", 'widower')
            # for child in self.children:
            #     if child.alive:
            #         child.trigger.mother_died(circumstance)

        elif cause == 'man_died':
            if self.married:
                self.woman.married = False
                if self.woman.alive:
                    self.woman.knowledge.add_bit(
                        1, f"Became a widow at {self.man.age}{circumstance}.", 'widow')

        elif cause == 'separated':
            pass

        elif cause == 'man_left':
            if self.married:
                self.man.married = False
                self.woman.married = False
            if self.man.alive:
                self.woman.knowledge.add_bit(2, f"Was left by {self.man.name}{circumstance}.", cause)
        elif cause == 'woman_left':
            if self.married:
                self.man.married = False
                self.woman.married = False
            if self.man.alive:
                self.man.knowledge.add_bit(2, f"Was left by {self.woman.name}{circumstance}.", cause)

        self.context.romance_dies(self.key)

    def add_child(self):
        self.no_children += 1

        # init_child
        child_key = f"{self.key}c{self.no_children}"
        try:
            child = Person(self, child_key, self.context, house=self.woman.house)
            self.children.append(child)
        except:
            print(f"couldnt init child {self.no_children} of {self.key}: {self.woman.key} and {self.man.key}")
            sys.exit()
   
        # order is important for triggers
        child.trigger.birth()
        self.woman.trigger.childbirth()
        self.woman.trigger.had_child(child)
        self.man.trigger.had_child(child)

        # add to family tree
        self.context.family_tree.edge(self.key, child_key, weight='6')

    """
    TRIGGERS & EVENTS
    """

    def relationship_trigger(self, trigger, param=None):
        """
        dead child: param=(child)
        adopt grandchild: param=(child)
        """
        if trigger == 'dead child':
            self.dead_children += 1
            child = param
            # parents
            if self.man.alive:
                self.man.trigger.dead_child(child)
            if self.woman.alive:
                self.woman.trigger.dead_child(child)

            # children
            for sibling in self.children:
                if sibling.alive:
                    sibling.trigger.dead_sibling(child)

        elif trigger == 'adopt grandchild':
            child = param
            if self.man.alive:
                self.man.knowledge.add_bit(1, f"Took grandchild {child.name} in when {child.name} was {child.age}.", 'adopt_grandchild')
                house = self.man.house
            if self.woman.alive:
                self.woman.knowledge.add_bit(1, f"Took grandchild {child.name} in when {child.name} was {child.age}.", 'adopt_grandchild')
                house = self.woman.house
            child.knowledge.add_bit(2, f"Went to live with grandparents at age {child.age}.", 'adopted_by_gparents')
            house.add_person(child, 'adopted')
            
    def relationship_events(self):
        # having a child
        child_chance = self.pregnancy_chance()
        if random.random() < child_chance:
            self.add_child()

    def pregnancy_chance(self):
        chance = 0.7
        if self.woman.age > 41:
            chance = 0.05
        elif self.woman.age > 36:
            chance = 0.5
        elif self.woman.age > 25:
            chance = 0.6

        if self.no_children > 14:
            chance *= 0.05
        elif self.no_children > 9:
            chance *= 0.15

        return chance * self.woman.health


    def get_members(self):
        return (self.man.key, self.woman.key)
