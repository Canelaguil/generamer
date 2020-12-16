import json
import os, sys
import random


class PlayableCharacter:
    def __init__(self, name, last_name):
        self.name = name
        self.last_name = last_name


class Sarah(PlayableCharacter):
    def __init__(self):
        PlayableCharacter.__init__(self, 'Sarah', 'Thijssen')


class newGame:
    def __init__(self, people_dir="./people"):
        self.people_dir = people_dir
        self.init_loop()

    def out(self, txt):
        output_str = "> " + txt
        print(output_str)

    def user(self, options=['y', 'n']):
        while True:
            ip = input("< ")
            ip = ip.replace("\n", "")
            if ip ==  "":
                continue
            elif ip not in options:
                self.out("Input is invalid.")
                continue
            return ip

    def load_character(self):
        found_candidate = False
        while not found_candidate:
            person_file = random.choice(os.listdir(self.people_dir))
            with open(self.people_dir + "/" + person_file) as json_file:
                self.person = json.load(json_file)
                if self.person['alive'] == True:
                    found_candidate =  True
        self.person_key = person_file[:5]

    def init_loop(self):
        while True:
            self.load_character()
            self.out(f"You found {self.person['names']['name']}, age {self.person['procedural']['age']}.")
            self.out(f"Do you want to talk to {self.person['names']['name']}? [y/n]")
            if self.user() == 'y':
                break
        self.conversation_loop()        

    def conversation_loop(self):
        pass

newGame()