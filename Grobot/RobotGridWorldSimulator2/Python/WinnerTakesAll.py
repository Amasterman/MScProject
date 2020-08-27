# Python 2 and 3 compatibility
from __future__ import absolute_import, division, print_function

from decimal import Decimal

from Grobot.RobotGridWorldSimulator2.Python.APIs import EmbodiedRobot

try:
    input = raw_input  # Python 3 style input()
except:
    pass

hostname = "localhost"  # Set to Tutors PC IP address to shown on Projector etc?
port = 9001  # Possibility of various clients running own robots


def getError(robot):
    errors = []

    # Iterate thorough all homeostatic variables
    for variables in robot.homeostaticList:

        # Save the upper and lower threshold limits
        lowLim, upLim = getattr(robot, variables + "Thresh")

        try:

            errors.append((float(robot.calcError(getattr(robot, variables), lowLim, upLim)), variables))

        # If any of the error calc return a string (Ie Dead) Return 0
        except TypeError as exception:

            return 0

    errors.append(((float(robot.calcError(robot.libido))), "libido"))
    return errors


def getWinner(errors):
    maxVal, maxName = 0, ""

    for elements in errors:
        value, name = elements[0], elements[1]
        if maxVal < value:
            maxVal, maxName = value, name

    return maxName


def getAction(error, robot):

    if error == "glucose":
        robot.behaviorEat()

    elif error == "moisture":
        robot.behaviorDrink()

    elif error == "temp":
        robot.behaviorSweat()

    elif error == "energy":
        robot.behaviorEnergyConversion()

    elif error == "pain" or error == "stress":
        robot.behaviorNest()

    elif error == "damage":
        robot.behaviorFlee()

    elif error == "libido":
        robot.behaviorMate()

if __name__ == '__main__':
    marvin = EmbodiedRobot("Marvin", 1, 1, "Blue")
    for i in range(1, 1000):
        error = getWinner(getError(marvin))
        print(error)
        getAction(error, marvin)
