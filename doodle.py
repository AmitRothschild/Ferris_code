import random
import sys
import time
import math
from itertools import count
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from threading import Thread
import csv
import pathlib

def animate(i, path):
    with open(path, newline='') as f:
        reader = csv.reader(f)
        data = list(reader)
        t = [float(item[0]) for item in data]
        x = [float(item[1]) for item in data]
    plt.cla()
    plt.plot(t, x)
    # print(t, x)


index = count()


def create_data(x_lst, t_lst):
    fieldnames = ["t", "x"]
    with open('try.csv', 'w', encoding='UTF8', newline='') as f:
        csv.DictWriter(f, fieldnames=fieldnames)
    while len(x_lst) < 20:
        t_lst.append(round(next(index) * 0.001, 3))
        # x_lst.append(math.sin(20 * t_lst[-1]))
        x_lst.append(random.randint(0, 5))
        info = {'t': t_lst[-1], 'x': x_lst[-1]}
        with open('try.csv', 'a', encoding='UTF8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writerow(info)
        time.sleep(0.25)



def main():
    plt.figure()
    plt.locator_params(nbins=4)
    x = []
    t = []
    path = str(pathlib.Path(__file__).parent.resolve()) + '\\try.csv'
    # print(path)
    data_thread = Thread(target=create_data, args=[x, t])
    data_thread.start()
    ani = FuncAnimation(plt.gcf(), animate, interval=500, fargs=(path,))
    plt.show()
    data_thread.join()
    print(x)


if __name__ == '__main__':
    main()
