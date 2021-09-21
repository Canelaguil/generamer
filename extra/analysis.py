import numpy as np
import matplotlib.pyplot as plt

data = np.loadtxt('extra/modifiers.txt',dtype=int)
# plt.hist(data, bins=np.arange(data.min(), data.max()+1)-0.5)
sorted = np.sort(data)
normalized = data 
# plt.hist(normalized, bins=np.arange(normalized.min(), normalized.max()+1)-0.5)


print(data.shape)
print(data.mean())
print(data.std())
print(data.max())
print(data.min())

min_age = lambda x : x / 2 + 7
max_age = lambda x : (x - 7) * 2
friends = lambda x : (x, x / 2 + 7, (x - 7) * 2)
ages = np.arange(0, 70, 1)


for i in range(0, 20):
    print(friends(i))
plt.plot(ages, min_age(ages))
plt.plot(ages, max_age(ages))

plt.show()