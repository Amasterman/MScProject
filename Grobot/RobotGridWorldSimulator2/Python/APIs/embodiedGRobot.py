from math import sqrt
from decimal import *
from grobot import *


class EmbodiedRobot(NewRobot):

    def __init__(self, rname="anon", posx=1, posy=1, colour="red", rshape="None", temp=0.37, energy=0.5, moisture=0.5,
                 pain=0, glucose=0, stress=0.5, libido=1):
        NewRobot.__init__(self, rname, posx, posy, colour, rshape)

        # Homeostatic variables
        self.temp = Decimal(temp)
        self.energy = Decimal(energy)
        self.moisture = Decimal(moisture)
        self.pain = Decimal(pain)
        self.stress = Decimal(stress)
        self.libido = Decimal(libido)
        self.glucose = Decimal(glucose)

        # Homeostatic thresholds
        self.tempThresh = 0, 1
        self.energyThresh = 0, None
        self.moistureThresh = 0, 1
        self.painThresh = None, 1
        self.stressThresh = None, 1
        self.glucose = None, 1

        # Standard degradation values for each variable that decays per tick
        self.energyDeg = Decimal(.01)
        self.painDeg = Decimal(.01)
        self.moistureDeg = Decimal(.01)
        self.libidoDeg = Decimal(.01)
        self.tempDeg = Decimal(.01)
        self.stressDeg = Decimal(.01)

        # List of the homeostatic variables that affect well being/viability
        self.homeostaticList = ("temp", "energy", "moisture", "pain", "stress", "glucose")

        # Keep record of mean viability In a tuple of mean and amount of vanities checked
        self.meanViability = 0, 0

        # Keep record of variance In a tuple of mean and amount of vanities checked
        self.variance = 0, 0

        # Take the ticks of the simulator at time of initiation
        self.ticks = self.getTicks()

    # ---------------------------------- Homeostatic Variables manipulation --------------------------------------------

    # Set temp value to temp - delta
    def setTemp(self, deltaTemp):

        self.temp -= deltaTemp

    # Set energy value to energy - delta
    def setEnergy(self, deltaEnergy):

        self.energy -= deltaEnergy

    # Set pain value to pain - delta
    def setPain(self, deltaPain):

        self.pain -= deltaPain

    # Set moisture value to moisture - delta
    def setMoisture(self, deltaMoisture):

        self.moisture -= deltaMoisture

    # Set Libido value to libido - delta
    def setLibido(self, deltaLibido):

        self.libido -= deltaLibido

    # Set glucose value to glucose - delta
    def setGlucose(self, deltaGlucose):

        self.glucose -= deltaGlucose

    # Update values based on amount of ticks passed since last update
    def updateDrives(self):

        xCord, yCord = self.getOwnXY()
        temperature, humidity = self.getTempAndHumidity(xCord, yCord)

        # Robot loses preset amounts per tick
        self.setEnergy(self.energyDeg)
        self.setPain(self.painDeg)

        # Robot loses amounts based on other drive variables
        painLow, painHigh = self.painThresh
        if painLow < self.pain < (painHigh / 2):

            self.setStress(self.stressDeg)

        else:

            self.setStress(-self.stressDeg)

        stressLow, stressHigh = self.stressThresh
        if stressLow < self.stress < (stressHigh / 2):

            self.setLibido(-self.libidoDeg)

        else:

            self.setLibido(self.libidoDeg)

        # Robot loses amounts based on world parameters
        tempLow, tempHigh = self.tempThresh
        self.setTemp(Decimal(tempHigh/2 - temperature) * self.tempDeg)

        moistureLow, moistureHigh = self.moistureThresh
        self.setMoisture(Decimal(moistureHigh/2 - humidity) * self.moistureDeg)

    # ------------------------------------------------------ System ----------------------------------------------------

    # Calculate Life span from initial ticks - current ticks
    def getLifeSpan(self):

        return self.getTicks() - self.ticks

    # Return two values for heat and humidity based on x and y cords low = cold and moist, high = dry and hot
    def getTempAndHumidity(self, xCord, yCord):

        mapSize = self.getMapSize()

        # Check coords are in range
        if (0 <= xCord <= mapSize) and (0 <= yCord <= mapSize):

            # temp , moisture
            return (xCord / mapSize), (yCord / mapSize)

        return "Coords outside of map range"

    # ---------------------------------------- Error and Wellness calculations -----------------------------------------

    # Take in value and limits and test the error / death
    def calcError(self, testVar, lowLim=None, upLim=None):

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
                errorSum += self.calcError(getattr(self, variables), lowLim, upLim)

            # If any of the error calc return a string (Ie Dead) Return viability 0
            except TypeError as exception:

                return 0

        # Return (a decimal to prevent floating point errors) 1 - (sum of error / Max possible error)
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

    # -------------------------------------- Additional TCP queries ----------------------------------------------------

    # Ask simulator for current number of ticks
    def getTicks(self):
        msg = self._send("T " + self.rname + "")
        # print(msg)
        return eval(msg)

    # Ask simulator for map size
    def getMapSize(self):
        msg = self._send("M " + self.rname + "")
        # print(msg)
        return eval(msg)

        # Ask simulator for map size

    def getOwnXY(self):
        msg = self._send("POS " + self.rname + "")
        # print(msg)
        return eval(msg)


def demo():
    hank = EmbodiedRobot("hank", 0, 0)
    hank.updateDrives()


if __name__ == "__main__":
    demo()
    print("Finished")
