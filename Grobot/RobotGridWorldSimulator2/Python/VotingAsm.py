# Python 2 and 3 compatibility
from __future__ import absolute_import, division, print_function

from decimal import Decimal
import random

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

fleeKey = [0, 3, 1, 0, 0, 0, 1, 0]
nestKey = [0, 1, 3, 0, 0, 0, 0, 0]
energyConversionKey = [0, 0, 0, 3, 0, 0, 0]
sweatKey = [0, 0, 0, 0, 2, 0, 0]
enemyKey = [0, 5, 1, 0, 0, 0, 0]
eatKey = [1, 0, 0, 0, 0, 4, 0]
drinkKey = [4, 0, 0, 0, 0, 1, 0]
mateKey = [0, 0, 0, 0, 0, 0, 4]

fleeVote = [0, 0, 0, 0, 0, 0, 0]
nestVote = [0, 0, 0, 0, 0, 0, 0]
energyConversionVote = [0, 0, 0, 0, 0, 0, 0]
sweatVote = [0, 0, 0, 0, 0, 0, 0]
enemyVote = [0, 0, 0, 0, 0, 0, 0]
eatVote = [0, 0, 0, 0, 0, 0, 0]
drinkVote = [0, 0, 0, 0, 0, 0, 0]
mateVote = [0, 0, 0, 0, 0, 0, 0]

voteList = ['Drink', 'Flee', 'Nest', 'EnergyConversion', 'Sweat', 'Eat', 'Mate']

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

    voteCount = 0

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

            voteCount = getVoteCount(elements)

            for i in range(0, 7):
                fleeVote[i] = fleeKey[i] * voteCount

        elif elements[2] == "Nest":
            errors[errors.index(elements)] = (elements[0] + Decimal(nest), elements[1], elements[2])

            voteCount = getVoteCount(elements)

            for i in range(0, 7):
                nestVote[i] = nestKey[i] * voteCount

        elif elements[2] == "EnergyConversion":
            errors[errors.index(elements)] = (elements[0] + Decimal(energyConversion), elements[1], elements[2])

            voteCount = getVoteCount(elements)

            for i in range(0, 7):
                energyConversionVote[i] = energyConversionKey[i] * voteCount

        elif elements[2] == "Sweat":
            errors[errors.index(elements)] = (elements[0] + Decimal(sweat), elements[1], elements[2])

            voteCount = getVoteCount(elements)

            for i in range(0, 7):
                sweatVote[i] = sweatKey[i] * voteCount

        elif elements[2] == "Enemy":
            errors[errors.index(elements)] = (
                elements[0] + Decimal(enemy) + Decimal(enemyStim), elements[1], elements[2])

            voteCount = getVoteCount(elements)

            for i in range(0, 7):
                enemyVote[i] = enemyKey[i] * voteCount

        elif elements[2] == "Eat":
            errors[errors.index(elements)] = (elements[0] + Decimal(eat) + Decimal(foodStim), elements[1], elements[2])

            voteCount = getVoteCount(elements)

            for i in range(0, 7):
                eatVote[i] = eatKey[i] * voteCount

        elif elements[2] == "Drink":
            errors[errors.index(elements)] = (
                elements[0] + Decimal(drink) + Decimal(waterStim), elements[1], elements[2])

            voteCount = getVoteCount(elements)

            for i in range(0, 7):
                drinkVote[i] = drinkKey[i] * voteCount

        elif elements[2] == "Mate":
            errors[errors.index(elements)] = (elements[0] + Decimal(mate) + Decimal(mateStim), elements[1], elements[2])

            voteCount = getVoteCount(elements)

            for i in range(0, 7):
                mateVote[i] = mateKey[i] * voteCount

    return errors


def getVoteCount(errors):
    if 0 <= errors[0] < 0.25:
        return 1

    elif 0.25 <= errors[0] < 0.50:
        return 2

    elif 0.50 <= errors[0] < 0.75:
        return 3

    elif 0.75 <= errors[0]:
        return 4


def clearVotes():
    for i in range(0, 7):
        fleeVote[i] = 0
        nestVote[i] = 0
        energyConversionVote[i] = 0
        sweatVote[i] = 0
        enemyVote[i] = 0
        eatVote[i] = 0
        drinkVote[i] = 0
        mateVote[i] = 0


def getWinner(errors, robot):

    ballotBox = [0, 0, 0, 0, 0, 0, 0]

    motivationSums(errors, robot)

    for i in range(0, 7):

        ballotBox[i] = fleeVote[i] + nestVote[i] + energyConversionVote[i] + sweatVote[i] + enemyVote[i] + eatVote[i] + drinkVote[i] + mateVote[i]

    maxIndex = ballotBox.index(max(ballotBox))

    maxIndex = tiedecide(ballotBox, maxIndex)

    clearVotes()

    return voteList[maxIndex]


def tiedecide(votes, maxIndex):

    tieList = []

    for i in range(0, len(votes)):
        if votes[i] == votes[maxIndex]:
            tieList.append(i)

    if len(tieList) > 1:
        return random.randint(0, len(tieList))

    return maxIndex


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
    marvin = EmbodiedRobot("I_VotingResults", 1, 1, "Blue")
    for i in range(1, 1000):
        error = getWinner(getError(marvin), marvin)
        print(error)
        getAction(error, marvin)
