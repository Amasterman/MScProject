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

    # Set stress value to stress - delta
    def setStress(self, deltaStress):

        self.stress -= deltaStress

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
        # Get the threshold for pain
        painLow, painHigh = self.painThresh

        # If the pain value is less than half the max pain value
        if 0 < self.pain < (painHigh / 2):

            # Decrease the stress by one step
            self.setStress(self.stressDeg)

        # If the pain value is more than half the max pain value
        else:

            # Increase the stress
            self.setStress(-self.stressDeg)

        # Get the stress threshold
        stressLow, stressHigh = self.stressThresh

        # If the stress value is less than half the max stress value
        if 0 < self.stress < (stressHigh / 2):

            # Increase the libido
            self.setLibido(-self.libidoDeg)

        # If the stress value is more than half the max stress value
        else:

            # decrease the libido
            self.setLibido(self.libidoDeg)

        # Robot loses amounts based on world parameters

        # Get the threshold values
        tempLow, tempHigh = self.tempThresh

        # calculation to increase/decrease temp based on world temp
        self.setTemp(Decimal(tempHigh/2 - temperature) * self.tempDeg)

        # Get the threshold values
        moistureLow, moistureHigh = self.moistureThresh

        # calculation to increase/decrease moisture based on world humidity
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

    # Ask sim for robots xy coords
    def getOwnXY(self):
        msg = self._send("POS " + self.rname + "")
        # print(msg)
        return eval(msg)

    def getHeading(self):
        msg = self._send("HEAD " + self.rname + "")
        # print(msg)
        return eval(msg)
    # -------------------------------------- Additional Movement -------------------------------------------------------

    def gotToCoord(self, targetX, targetY):


        xCord , yCord = self.getOwnXY()
        heading = self.getHeading()

        while xCord != targetX:
            xCord, yCord = self.getOwnXY()
            heading = self.getHeading()

            if xCord < targetX:

                while heading != 0:
                    self.right()
                    heading = self.getHeading()

                vision = self.look()
                if vision[2] is not None:
                    left, right = self.getFreeLook()

                    while not left and not right:

                        self.moveBack()
                        left, right = self.getFreeLook()

                    if yCord < targetY and left:
                        self.left()
                        self.gotToCoord(xCord, yCord + 1)

                    elif yCord > targetY and right:
                        self.right()
                        self.gotToCoord(xCord, yCord - 1)

                    elif left:
                        self.left()
                        self.gotToCoord(xCord, yCord - 1)

                    else:
                        self.right()
                        self.gotToCoord(xCord, yCord + 1)
                else:
                    self.forward()

            else:

                while heading != 180:
                    self.right()
                    heading = self.getHeading()

                vision = self.look()
                if vision[2] is not None:
                    left, right = self.getFreeLook()

                    while not left and not right:

                        self.moveBack()
                        left, right = self.getFreeLook()

                    if yCord < targetY and right:
                        self.right()
                        self.gotToCoord(xCord, yCord + 1)

                    elif yCord > targetY and left:
                        self.left()
                        self.gotToCoord(xCord, yCord - 1)

                    elif left:
                        self.left()
                        self.gotToCoord(xCord, yCord + 1)

                    else:
                        self.right()
                        self.gotToCoord(xCord, yCord - 1)
                else:
                    self.forward()

            xCord, yCord = self.getOwnXY()
            heading = self.getHeading()

        while yCord != targetY:

            if yCord < targetY:

                while heading != 90:
                    self.right()
                    heading = self.getHeading()

                vision = self.look()
                if vision[2] is not None:
                    left, right = self.getFreeLook()

                    while not left and not right:

                        self.moveBack()
                        left, right = self.getFreeLook()

                    if xCord < targetX and left:
                        self.left()
                        self.gotToCoord(xCord - 1, yCord)

                    elif xCord > targetX and right:
                        self.right()
                        self.gotToCoord(xCord + 1, yCord)

                    elif left:
                        self.left()
                        self.gotToCoord(xCord - 1, yCord)

                    else:
                        self.right()
                        self.gotToCoord(xCord + 1, yCord)
                else:
                    self.forward()

            else:

                while heading != 270:
                    self.right()
                    heading = self.getHeading()

                vision = self.look()
                if vision[2] is not None:
                    left, right = self.getFreeLook()

                    while not left and not right:

                        self.moveBack()
                        left, right = self.getFreeLook()

                    if xCord < targetX and right:
                        self.right()
                        self.gotToCoord(xCord - 1, yCord)

                    elif xCord > targetX and left:
                        self.left()
                        self.gotToCoord(xCord + 1, yCord)

                    elif left:
                        self.left()
                        self.gotToCoord(xCord + 1, yCord)

                    else:
                        self.right()
                        self.gotToCoord(xCord - 1, yCord)
                else:
                    self.forward()

            xCord, yCord = self.getOwnXY()
            heading = self.getHeading()

        if xCord != targetX or yCord != targetY:
            self.gotToCoord(targetX, targetY)

    def moveBack(self):
        self.right()
        self.right()
        self.forward()
        self.right()
        self.right()

    def getFreeLook(self):
        vision = self.look()

        return vision[0] is None, vision[4] is None



def demo():
    hank = EmbodiedRobot("hank", 0, 0)
    hank.updateDrives()
    hank.gotToCoord(20,20)

if __name__ == "__main__":
    demo()
    print("Finished")
