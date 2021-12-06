import json 
import matplotlib.pyplot as plt
import os
import glob
import pprint

first_year_found = False
first_year = 1370
span = 30
path = 'people'
frequencies = {}
yearly_freq = {}
event_ys = {}

for fn in glob.glob(os.path.join(path, '*json')):
    with open(fn, encoding='utf-8', mode='r') as cf:
        person = cf.read().replace('\n', '')
        events = json.loads(person)['events']

        for year, happenings in events.items(): 
            # if not first_year_found:
            #     first_year = True
            #     first_year = int(year)
            if year not in yearly_freq:
                yearly_freq[year] = {}
            
            for key, _  in happenings:
                if key not in frequencies: 
                    frequencies[key] = 0
                frequencies[key] += 1

                if key not in event_ys:
                    event_ys[key] = [0] * span
                event_ys[key][int(year) - first_year] += 1

                if key not in yearly_freq[year]:
                    yearly_freq[year][key] = 0
                yearly_freq[year][key] += 1

# pprint.pprint(event_ys)
xs = list(range(first_year, first_year + span))
for key, ys in event_ys.items():
    plt.plot(xs, ys, label=key)

plt.legend(loc="upper right")
plt.show()