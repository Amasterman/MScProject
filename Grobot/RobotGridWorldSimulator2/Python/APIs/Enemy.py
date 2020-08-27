# Python 2 and 3 compatibility
from __future__ import absolute_import, division, print_function
from pathlib import Path
from decimal import Decimal
from random import *

from Grobot.RobotGridWorldSimulator2.Python.APIs.grobot import NewRobot


class Enemy(NewRobot):
    def __init__(self, rname="Enemy", lowCordX=0, lowCordY=0, highCordX=15, highCordY=15):

        self.lowCrodX = lowCordX
        self.lowCordY = lowCordY
        self.highCordX = highCordX
        self.highCordY = highCordY

        posx = randint(lowCordX, highCordX)
        posy = randint(lowCordY, highCordY)

        NewRobot.__init__(self, rname, posx, posy, "Black", "None")

def demo():
    enemy = Enemy()
    while True:
        rand = randint(0, 4)
        look = enemy.look()
        if rand == 0:
            enemy.left()
        elif rand == 1:
            enemy.right()
        elif rand == 2:
            if look[2] == None:
                enemy.forward()



if __name__ == "__main__":
    demo()
    print("Finished")
