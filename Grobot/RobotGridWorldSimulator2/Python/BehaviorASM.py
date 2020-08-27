# Python 2 and 3 compatibility
from __future__ import absolute_import, division, print_function

from decimal import Decimal

import numpy

from Grobot.RobotGridWorldSimulator2.Python.APIs import EmbodiedRobot

try:
    input = raw_input  # Python 3 style input()
except:
    pass

hostname = "localhost"  # Set to Tutors PC IP address to shown on Projector etc?
port = 9001  # Possibility of various clients running own robots

flee = 0.1
nest = 0.1
energyConversion = 0.1
sweat = 0.1
enemy = 0.1
eat = 0.1
drink = 0.1
mate = 0.1

behaviorList = ['Thirst', 'Hunger', 'Fatigue', 'Confusion', 'Excitement', 'OverMoisture', 'OverNutrition', 'Repair',
                'SelfProtection', 'Libido']

externalStimuli = ['Food', 'Water', 'Mate', 'Enemy']


def externalStimulus(robot):
    stimuliList = []
    rX, rY = robot.getOwnXY()

    for stimuli in externalStimuli:

        try:
            tX, tY = robot.nearest(stimuli)

            sumDiff = (abs(rX - tX) + abs(rY - tY)) / 1000

            stimDiff = 0.1 - sumDiff

        except:

            stimDiff = 0

        stimuliList.append((stimDiff, stimuli))

    return stimuliList


def getError(robot):
    errors = []

    # Iterate thorough all homeostatic variables
    for variables in behaviorList:

        try:

            errors.append(robot.motivationManager(variables))
        # If any of the error calc return a string (Ie Dead) Return 0
        except TypeError as exception:

            return 0

    return errors


def motivationSums(errors, robot):
    stimVal = externalStimulus(robot)

    for val in stimVal:
        value, name = val
        if name == "Enemy":
            enemyStim = value

        elif name == "Water":
            waterStim = value

        elif name == "Mate":
            mateStim = value

        elif name == "Food":
            foodStim = value

    for elements in errors:
        if elements[2] == "Flee":
            errors[errors.index(elements)] = (elements[0] + Decimal(flee), elements[1], elements[2])

        elif elements[2] == "Nest":
            errors[errors.index(elements)] = (elements[0] + Decimal(nest), elements[1], elements[2])

        elif elements[2] == "EnergyConversion":
            errors[errors.index(elements)] = (elements[0] + Decimal(energyConversion), elements[1], elements[2])

        elif elements[2] == "Sweat":
            errors[errors.index(elements)] = (elements[0] + Decimal(sweat), elements[1], elements[2])

        elif elements[2] == "Enemy":
            errors[errors.index(elements)] = (
                elements[0] + Decimal(enemy) + Decimal(enemyStim), elements[1], elements[2])

        elif elements[2] == "Eat":
            errors[errors.index(elements)] = (elements[0] + Decimal(eat) + Decimal(foodStim), elements[1], elements[2])

        elif elements[2] == "Drink":
            errors[errors.index(elements)] = (
                elements[0] + Decimal(drink) + Decimal(waterStim), elements[1], elements[2])

        elif elements[2] == "Mate":
            errors[errors.index(elements)] = (elements[0] + Decimal(mate) + Decimal(mateStim), elements[1], elements[2])

    return errors


def getWinner(errors, robot):
    maxVal, maxBehavior = 0, ""

    motivationSums(errors, robot)

    for elements in errors:
        value, incOrDec, behavior = elements[0], elements[1], elements[2]
        if Decimal(value) > Decimal(maxVal):
            maxVal, maxBehavior = value, behavior

    return maxBehavior


def getAction(behavior, robot):
    if behavior == "Eat":
        robot.behaviorEat()

    elif behavior == "Drink":
        robot.behaviorDrink()

    elif behavior == "Sweat":
        robot.behaviorSweat()

    elif behavior == "EnergyConversion":
        robot.behaviorEnergyConversion()

    elif behavior == "Nest":
        robot.behaviorNest()

    elif behavior == "Flee":
        robot.behaviorFlee()

    elif behavior == "Mate":
        robot.behaviorMate()


if __name__ == '__main__':
    trinity = EmbodiedRobot("I_WinnerTakesAll", 1, 1, "Blue")
    for i in range(1, 1000):
        error = getWinner(getError(trinity), trinity)
        print(error)
        getAction(error, trinity)
