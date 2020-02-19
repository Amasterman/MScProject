from math import sqrt
from decimal import *
from grobot import *


class EmbodiedRobot(NewRobot):

    def __init__(self, rname="anon", posx=1, posy=1, colour="red", rshape="None", temp=0.37, energy=0.5, thirst=0.5,
                 pain=0, stress=0.5, libido=1):
        NewRobot.__init__(self, rname, posx, posy, colour, rshape)

        # Homeostatic variables
        self.temp = temp
        self.energy = energy
        self.thirst = thirst
        self.pain = pain
        self.stress = stress
        self.libido = libido

        # Homeostatic thresholds
        self.tempThresh = 0, 1
        self.energyThresh = 0, 1
        self.thirstThresh = 0, 1
        self.painThresh = None, 1
        self.stressThresh = None, 1

        # List of the homeostatic variables that affect well being/viability
        self.homeostaticList = ("temp", "energy", "thirst", "pain", "stress")

        # Keep record of mean viability In a tuple of mean and amount of vanities checked
        self.meanViability = 0, 0

        # Keep record of variance In a tuple of mean and amount of vanities checked
        self.variance = 0, 0

    # ------------------------    Homeostatic Variables manipulation     ----------------------------------

    # Set temp value to temp - delta
    def setTemp(self, deltaTemp):
        self.temp -= deltaTemp

    # Set energy value to energy - delta
    def setEnergy(self, deltaEnergy):
        self.energy -= deltaEnergy

    # Set pain value to pain - delta
    def setPain(self, deltaPain):
        self.pain -= deltaPain

    # Set thirst value to thirst - delta
    def setThirst(self, deltaThirst):
        self.thirst -= deltaThirst

    # Set Libido value to libido - delta
    def setLibido(self, deltaLibido):
        self.libido -= deltaLibido

    # -------------------------------- Error and Wellness calculations -----------------------------------

    # Take in value and limits and test the error / death
    def calclError(self, testVar, lowLim=None, upLim=None):

        # If two limits
        if upLim is not None and lowLim is not None:

            # If passed value is within the limits
            if lowLim < testVar < upLim:

                # Return the maximum difference between the absolute differences
                return max(abs(lowLim - testVar), abs(upLim - testVar))

            # If passed value out of range
            else:
                # Return dead
                return "Dead"

        # If no upper death limit
        elif upLim is None:

            # If passed value is within the limit
            if lowLim < testVar:

                # Return the absolute difference
                return abs(lowLim - testVar)

            # If passed value out of range
            else:
                # Return dead
                return "Dead"

        # If no lower death limit
        else:

            # If passed value is within the limit
            if testVar < upLim:

                # Return the absolute difference
                return abs(upLim - testVar)

            # If passed value out of range
            else:
                # Return dead
                return "Dead"

    # Take the sum of all error and compute viability
    def calcViability(self):
        errorSum = 0

        # Iterate thorough all homeostatic variables
        for variables in self.homeostaticList:

            # Save the upper and lower threshold limits
            lowLim, upLim = getattr(self, variables + "Thresh")

            try:

                # Calculate the error of the variable and add it to the total sum
                errorSum += self.calclError(getattr(self, variables), lowLim, upLim)

            # If any of the error calc return a string (Ie Dead) Return viability 0
            except TypeError as exception:

                return 0

        # Return (a decimal) 1 - (sum of error / Max possible error)
        return Decimal(1 - (errorSum / len(self.homeostaticList)))

    # Take a new Viability value return the mean of Viability and an increment count
    def calcMeanViability(self, newViability):

        # Get current saved mean
        currentMean, count = self.meanViability

        # Prevent division by zero
        if count == 0:
            return newViability, 1

        else:
            # Take the current mean times it by the count to get current sum of viability then compute mean and
            # Increase count
            return ((currentMean * count) + Decimal(newViability)) / (count + 1), count + 1

    # Calculate variance of of the viability
    def calcVariance(self, newViability, mean):

        # Get current variance
        variance, count = self.variance

        # Avoid divide by zero
        if count == 0:
            return 0, 1

        else:
            # Take the current variance times it by the count to get current sum of variance squared then compute mean
            # plus the new value squared and Increase count
            return ((variance * count) + ((mean - newViability) ** 2)) / (count + 1), count + 1

    # Calculate the current standard deviation
    def calcStandardDeviation(self, variance):
        return sqrt(variance)

# ------------------------------------------ Additional TCP queries ----------------------------------------------------

    # Ask simulator for current number of ticks
    def getTicks(self):
        msg = NewRobot._send("TI " + NewRobot.rname)
        print(msg)
        return eval(msg)


def demo():
    hank = EmbodiedRobot("hank", 1, 1)


if __name__ == "__main__":
    demo()
    print("Finished")
