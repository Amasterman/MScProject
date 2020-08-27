import csv
import math
from math import sqrt
from decimal import *
import random
from pathlib import Path

from Grobot.RobotGridWorldSimulator2.Python.APIs.grobot import NewRobot


class EmbodiedRobot(NewRobot):

    def __init__(self, rname="anon", posx=1, posy=1, colour="red", rshape="None", temp=0.5, energy=1, moisture=0.5,
                 pain=0, glucose=0.5, stress=0.2, libido=0):
        NewRobot.__init__(self, rname, posx, posy, colour, rshape)

        # Nest cords = start cords
        self.nest = posx, posy

        # Homeostatic variables
        self.temp = Decimal(temp)
        self.energy = Decimal(energy)
        self.moisture = Decimal(moisture)
        self.pain = Decimal(pain)
        self.stress = Decimal(stress)
        self.libido = Decimal(libido)
        self.glucose = Decimal(glucose)
        self.damage = Decimal(0)

        # Homeostatic thresholds
        self.tempThresh = 0, 1
        self.energyThresh = 0, None
        self.moistureThresh = 0, 1
        self.painThresh = None, 1
        self.stressThresh = None, 1
        self.glucoseThresh = 0, 1
        self.damageThresh = None, 1

        # Standard degradation values for each variable that decays per tick
        self.energyDeg = Decimal(.01)
        self.painDeg = Decimal(.01)
        self.moistureDeg = Decimal(.005)
        self.libidoDeg = Decimal(.01)
        self.tempDeg = Decimal(.005)
        self.stressDeg = Decimal(.01)
        self.damageDeg = Decimal(.01)
        self.glucoseDeg = Decimal(0.005)

        # List of the homeostatic variables that affect well being/viability
        self.homeostaticList = ("temp", "energy", "moisture", "pain", "stress", "glucose", "damage")

        # Viablility with libido
        self.libidoViability = 0

        # Keep record of mean viability In a tuple of mean and amount of vanities checked
        self.meanViability = 0, 0

        # Keep record of variance In a tuple of mean and amount of vanities checked
        self.variance = 0, 0

        # Take the ticks of the simulator at time of initiation
        self.ticks = self.getTicks()

        # path for current file
        self.filePath = self.createFile()

        # Amount of times mated
        self.mateCount = 0

    # ---------------------------------- Homeostatic Variables manipulation --------------------------------------------

    # Set temp value to temp - delta
    def setTemp(self, deltaTemp):

        self.temp += Decimal(deltaTemp)

    # Set energy value to energy - delta
    def setEnergy(self, deltaEnergy):

        self.energy += Decimal(deltaEnergy)

    # Set pain value to pain - delta
    def setPain(self, deltaPain):

        self.pain += Decimal(deltaPain)

    # Set moisture value to moisture - delta
    def setMoisture(self, deltaMoisture):

        self.moisture += Decimal(deltaMoisture)

    # Set Libido value to libido - delta
    def setLibido(self, deltaLibido):

        self.libido += Decimal(deltaLibido)

    # Set stress value to stress - delta
    def setStress(self, deltaStress):

        self.stress += Decimal(deltaStress)

    # Set glucose value to glucose - delta
    def setGlucose(self, deltaGlucose):

        self.glucose += Decimal(deltaGlucose)

    # Set damage to value + delta
    def setDamage(self, deltaDamage):

        self.damage += Decimal(deltaDamage)

    # Update values based on amount of ticks passed since last update
    def updateDrives(self):

        look = self.look()
        xCord, yCord = self.getOwnXY()
        temperature, humidity = self.getTempAndHumidity(xCord, yCord)

        # Robot loses preset amounts per tick
        if 0 < self.energy <= 1:
            self.setEnergy(-self.energyDeg)
        elif 0 > self.energy:
            self.energy = 0
        elif self.energy > 1:
            self.energy = 1

        if 0 < self.pain <= 1:
            self.setPain(-self.painDeg)
        elif 0 > self.pain:
            self.pain = 0
        elif self.pain > 1:
            self.pain = 1

        # Robot loses amounts based on other drive variables
        # Get the threshold for pain
        painLow, painHigh = self.painThresh

        # If the pain value is less than half the max pain value
        if 0 <= self.pain < (painHigh / 2):

            # Decrease the stress by one step
            if 0 < self.stress < 1:
                self.setStress(-self.stressDeg)
            elif 0 > self.stress:
                self.stress = 0
            elif self.stress > 1:
                self.stress = 1

        # If the pain value is more than half the max pain value
        else:

            # Increase the stress
            if 0 < self.stress <= 1:
                self.setStress(self.stressDeg)
            elif 0 > self.stress:
                self.stress = 0
            elif self.stress > 1:
                self.stress = 1

        # Get the stress threshold
        stressLow, stressHigh = self.stressThresh

        # If the stress value is less than half the max stress value
        if 0 <= self.stress < (stressHigh / 2):

            # Increase the libido
            if 0 <= self.libido <= 1:
                self.setLibido(self.libidoDeg)
            elif 0 > self.libido:
                self.libido = 0
            elif self.libido > 1:
                self.libido = 1

        # If the stress value is more than half the max stress value
        else:

            # decrease the libido
            if 0 < self.libido <= 1:
                self.setLibido(-self.libidoDeg)
            elif 0 > self.libido:
                self.libido = 0
            elif self.libido > 1:
                self.libido = 1

        # Robot loses amounts based on world parameters

        # Get the threshold values
        tempLow, tempHigh = self.tempThresh

        # calculation to increase/decrease temp based on world temp
        if 0 < self.temp <= 1:
            self.setTemp(-(temperature * self.tempDeg))
        elif 0 > self.temp:
            self.temp = 0
        elif self.temp > 1:
            self.temp = 1

        if 0.55 <= self.temp or self.temp <= 0.45:
            self.setPain(0.012)

        # Get the threshold values
        moistureLow, moistureHigh = self.moistureThresh

        # calculation to increase/decrease moisture based on world humidity
        if 0 < self.moisture <= 1:
            self.setMoisture(-self.moistureDeg)
        elif 0 > self.moisture:
            self.moisture = 0
        elif self.moisture > 1:
            self.moisture = 1

        # If in nest Decrease Stress and pain
        nestX, nestY = self.nest
        if xCord == nestX and yCord == nestY:
            self.stress = self.stress - self.stressDeg * 2
            self.pain = self.pain - self.painDeg * 2

        if 0 < self.glucose <= 1:
            self.setGlucose(-self.glucoseDeg)
            self.setEnergy(self.glucoseDeg)
        elif 0 > self.glucose:
            self.glucose = 0
        elif self.glucose > 1:
            self.glucose = 1

        if "enemy" in look:
            self.setPain(0.1)

        self.writeToFile()

    # ------------------------------------------------------ System ----------------------------------------------------

    # Return two values for heat and humidity based on x and y cords low = cold and moist, high = dry and hot
    def getTempAndHumidity(self, xCord, yCord):

        mapSize = self.getMapSize()

        # Check coords are in range
        if (0 <= xCord <= mapSize) and (0 <= yCord <= mapSize):

            # temp , moisture
            # print((xCord - math.ceil(mapSize/2))/10000)

            return Decimal((xCord - math.ceil(mapSize / 2)) / 10000), Decimal((yCord - math.ceil(mapSize / 2)) / 10000)

        return "Coords outside of map range"

    def writeToFile(self):

        # Calculate viability, mean viability, variance and standard deviation
        currentViability = self.calcViability()
        self.meanViability = self.calcMeanViability(currentViability)
        meanViability, count = self.meanViability
        self.variance = self.calcVariance(currentViability, meanViability)
        currentVariance, varCount = self.variance
        standardDev = self.calcStandardDeviation(currentVariance)
        self.libidoViability = currentViability + self.calcError(self.libido)

        with open(self.filePath, mode='a') as csv_file:
            fieldnames = ["lifeSpan", "viability", "meanViability", "currentVariance", "standardDeviation",
                          "libidoViability", "temp",
                          "energy", "moisture", "pain", "stress", "libido", "glucose", "damage", "mateCount"]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            writer.writerow({"lifeSpan": self.getLifeSpan(), "viability": currentViability, "meanViability":
                meanViability, "currentVariance": currentVariance, "standardDeviation": standardDev,
                             "libidoViability": self.libidoViability,
                             "temp": self.temp, "energy": self.energy, "moisture": self.moisture, "pain": self.pain,
                             "stress": self.stress, "libido": self.libido, "glucose": self.glucose,
                             "damage": self.damage, "mateCount": self.mateCount})

    def createFile(self):
        created = False
        count = 0
        filePath = "/home/alex/PycharmProjects/MScProject2/Results"

        while not created:
            tempPath = Path(filePath + "/" + self.rname + "results" + str(count) + ".csv")
            if tempPath.exists():
                count += 1
            else:
                open(tempPath, "+w")
                created = True

        with open(tempPath, mode='a') as csv_file:
            fieldnames = ["lifeSpan", "viability", "meanViability", "currentVariance", "standardDeviation",
                          "libidoViability", "temp",
                          "energy", "moisture", "pain", "stress", "libido", "glucose", "damage", "mateCount"]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            writer.writeheader()

        return tempPath

    def getMoveSide(self, coordX, coordY, startX, startY):

        if abs(coordX - startX) >= abs(coordY - startY):

            # Y is closer
            if abs((coordY + 1) - startY) > abs((coordY - 1) - startY):

                return coordX, coordY - 1

            else:

                return coordX, coordY + 1

        else:

            # X is closer
            if abs((coordX + 1) - startX) > abs((coordX - 1) - startX):

                return coordX - 1, coordY

            else:

                return coordX + 1, coordY

    def faceTarget(self, target):

        sight = self.look()
        for i in range(0, 4):

            if sight[2] != target:

                if sight[0] == target:

                    self.left()

                else:

                    self.right()
            sight = self.look()

    def consumeResource(self):
        look = self.look()
        if look[2] is not None:
            if random.randint(0, 9) == 0:
                self.pick()

    # ---------------------------------------- Error and Wellness calculations -----------------------------------------

    # Calculate Life span from initial ticks - current ticks
    def getLifeSpan(self):

        return self.getTicks() - self.ticks

    # Take in value and limits and test the error / death
    def calcError(self, testVar, lowLim=None, upLim=None):

        # If two limits
        if upLim is not None and lowLim is not None:

            # If passed value is within the limits
            if lowLim < testVar < upLim:

                # Return the maximum difference between the absolute differences
                return abs(testVar - Decimal(0.75))
                # return max(abs(lowLim - testVar), abs(upLim - testVar))

            # If passed value out of range
            else:
                # Return dead
                self.die()
                return "Dead" + str(testVar)

        # If no upper death limit
        elif upLim is None and lowLim is not None:

            # If passed value is within the limit
            if lowLim < testVar:

                # Return the absolute difference
                return abs(1 - testVar)

            # If passed value out of range
            elif lowLim >= testVar:
                # Return dead
                self.die()
                return "Dead" + str(testVar)

        # If no lower death limit
        elif lowLim is None and upLim is not None:

            # If passed value is within the limit
            if testVar < upLim:

                # Return the absolute difference
                return abs(0 - testVar)

            # If passed value out of range
            elif testVar >= upLim:
                # Return dead
                self.die()
                return "Dead" + str(testVar)

        else:

            return abs(testVar - 0)

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

    def die(self):
        msg = self._send("Die " + self.rname + "")
        # print(msg)

    # -------------------------------------- Behaviors  ----------------------------------------------------------------

    def behaviorNest(self):

        targetX, targetY = self.nest
        self.gotToCoord(targetX, targetY)
        self.updateDrives()

    def behaviorEat(self):
        look = self.look()

        if look[2] != "Food":

            if not isinstance(self.nearest("Food"), str):

                foodX, foodY = self.nearest("Food")
                selfX, selfY = self.getOwnXY()
                targetX, targetY = self.getMoveSide(foodX, foodY, selfX, selfY)
                self.gotToCoord(targetX, targetY)
                self.faceTarget("Food")

        self.consumeResource()
        self.setGlucose(.2)
        self.setEnergy(0.05)
        self.setMoisture(0.01)
        self.setStress(-0.05)

    def behaviorDrink(self):
        look = self.look()

        if look[2] != "Water":

            if not isinstance(self.nearest("Water"), str):

                waterX, waterY = self.nearest("Water")
                selfX, selfY = self.getOwnXY()
                targetX, targetY = self.getMoveSide(waterX, waterY, selfX, selfY)
                self.gotToCoord(targetX, targetY)
                self.faceTarget("Water")

        self.consumeResource()

        self.setMoisture(0.2)
        self.setGlucose(0.01)
        self.setStress(-0.05)
        self.setTemp(-0.05)

    def behaviorMate(self):

        look = self.look()
        while look[2] != "Drone0":

            if not isinstance(self.nearest("Mate"), str):
                try:
                    startMateX, startMateY = self.nearest("Mate")
                    selfX, selfY = self.getOwnXY()
                    targetX, targetY = self.getMoveSide(startMateX, startMateY, selfX, selfY)
                    self.gotToCoord(targetX, targetY)
                    self.faceTarget("Drone0")

                except:

                    pass

            look = self.look()

        self.libido = 0
        self.setStress(-0.1)
        self.setEnergy(-0.05)
        self.setMoisture(-0.05)

        self.mateCount += 1

    def behaviorFlee(self):

        # Is this the best way to do this?
        self.left()
        self.left()
        self.forward()
        self.behaviorNest()
        self.setPain(-0.1)
        self.setStress(0.1)

    def behaviorEnergyConversion(self):
        if 0 < self.glucose <= 1:
            self.setGlucose(-0.1)
            self.setEnergy(0.075)

    def behaviorSweat(self):
        if 0 < self.moisture <= 1:
            self.setMoisture(-0.2)
            self.setEnergy(-0.01)
            self.temp = Decimal(0.5)

    # -------------------------------------- Motivations ---------------------------------------------------------------

    def motivationManager(self, target):
        if target == "Thirst":
            return self.motivationThirst()
        elif target == "Hunger":
            return self.motivationHunger()
        elif target == "Fatigue":
            return self.motivationFatigue()
        elif target == "Confusion":
            return self.motivationConfusion()
        elif target == "Excitement":
            return self.motivationExcitement()
        elif target == "OverMoisture":
            return self.motivationOverMoisture()
        elif target == "OverNutrition":
            return self.motivationOverNutrition()
        elif target == "Repair":
            return self.motivationRepair()
        elif target == "SelfProtection":
            return self.motivationSelfProtection()
        elif target == "Libido":
            return self.motivationLibido()

    def motivationThirst(self):
        lowLim, upLim = self.moistureThresh
        error = self.calcError(self.moisture, lowLim, upLim)
        return error, "Inc", "Drink"

    def motivationHunger(self):
        lowLim, upLim = self.glucoseThresh
        error = self.calcError(self.glucose, lowLim, upLim)
        return error, "Inc", "Eat"

    def motivationFatigue(self):
        lowLim, upLim = self.energyThresh
        error = self.calcError(self.energy, lowLim, upLim)
        return error, "Inc", "EnergyConversion"

    def motivationConfusion(self):
        lowLim, upLim = self.stressThresh
        error = self.calcError(self.stress, lowLim, upLim)
        return error, "Dec", "Nest"

    def motivationExcitement(self):
        lowLim, upLim = self.energyThresh
        error = self.calcError(self.energy, lowLim, upLim)
        return error, "Dec", "Enemy"

    def motivationOverMoisture(self):
        lowLim, upLim = self.moistureThresh
        error = self.calcError(self.moisture, lowLim, upLim)
        return error, "Dec", "Sweat"

    def motivationOverNutrition(self):
        lowLim, upLim = self.glucoseThresh
        error = self.calcError(self.glucose, lowLim, upLim)
        return error, "Dec", "EnergyConversion"

    def motivationRepair(self):
        lowLim, upLim = self.damageThresh
        error = self.calcError(self.damage, lowLim, upLim)
        return error, "Dec", "Nest"

    def motivationSelfProtection(self):
        lowLim, upLim = self.painThresh
        error = self.calcError(self.pain, lowLim, upLim)
        return error, "Dec", "Flee"

    def motivationLibido(self):
        lowLim, upLim = None, None
        error = self.calcError(self.libido, lowLim, upLim)
        return error, "Dec", "Mate"

    # -------------------------------------- Additional Movement -------------------------------------------------------

    # Go to provided x y cords
    def gotToCoord(self, targetX, targetY):

        # Get initial cords
        xCord, yCord = self.getOwnXY()

        # While not at correct cords
        while xCord != targetX or yCord != targetY:

            # while not at correct x cord
            while xCord != targetX:

                # Move to target x cord
                self.moveToX(xCord, targetX, targetY)

                # Update coords
                xCord, yCord = self.getOwnXY()

            # While not at correct y cord
            while yCord != targetY:

                # Move to target y cord
                self.moveToY(yCord, targetX, targetY)

                # Update cords
                xCord, yCord = self.getOwnXY()

    # Move to correct X cord
    def moveToX(self, xCord, targetX, targetY):

        # Check if target x is left or right
        if xCord < targetX:

            # If higher look left
            self.turnToHeading(0)

        else:

            # If lower look right
            self.turnToHeading(180)

        # Get vision
        vision = self.look()

        # If not looking at nothing
        if vision[2] is not None:

            # Check your left and right
            left, right = self.getFreeLook()

            # Check if in dead end
            xCord, yCord, left, right = self.deadEnd(left, right)

            # If not correct yCord
            if yCord != targetY:

                # Try to move to target Y first
                self.gotToCoord(xCord, targetY)

            # If at correct yCord
            else:

                # Follow wall
                self.followWall(left, right)

        # If clear forward
        else:

            # Move forward
            self.forward()

    # Move to correct y cord
    def moveToY(self, yCord, targetX, targetY):

        # If y higher or lower face correct direction
        if yCord < targetY:

            # If higher look up
            self.turnToHeading(90)

        else:

            # If lower look down
            self.turnToHeading(270)

        # Update vision
        vision = self.look()

        # If facing nothing
        if vision[2] is not None:

            # Check your left and right
            left, right = self.getFreeLook()

            # Check if in dead end
            xCord, yCord, left, right = self.deadEnd(left, right)

            # If not correct xCord
            if xCord != targetX:

                # Try to move to target X first
                self.gotToCoord(targetX, yCord)

            # If at correct xCord
            else:

                # Follow wall
                self.followWall(left, right)

        # If clear forward
        else:

            # Move forward
            self.forward()

    # Turn to target heading
    def turnToHeading(self, targetHeading):

        # Get current heading
        heading = self.getHeading()

        # If heading is not target
        while heading != targetHeading:

            # If needs to turn around
            if abs(targetHeading - heading) == 180:
                # Turn around
                self.right()
                self.right()

            # If need to turn right
            elif heading - targetHeading == 90 or heading - targetHeading == -270:

                # Turn right
                self.right()

            # If need to turn left
            elif heading - targetHeading == -90 or heading - targetHeading == 270:

                # Turn left
                self.left()

            # Update heading
            heading = self.getHeading()

    # Follow wall to left or right
    def followWall(self, left, right):

        # Update look
        vision = self.look()

        # If both left and right are clear choose one at random
        if left and right:

            if random.uniform(0, 1) == 1:

                left = True
                right = False

            else:

                left = False
                right = True

        # If left is clear
        if left:

            # Turn left move forward and turn right back
            while vision[2] is not None:
                self.left()
                self.forward()
                self.right()
                vision = self.look()

        # If right is clear
        elif right:

            # Turn right move forward and turn left back
            while vision[2] is not None:
                self.right()
                self.forward()
                self.left()
                vision = self.look()

    # Check if in dead end and back up if are
    def deadEnd(self, left, right):

        # If in a dead end
        while not left and not right:

            # Move back
            self.moveBack()

            # Update coords and check left and right
            xCord, yCord = self.getOwnXY()
            left, right = self.getFreeLook()

        # Update and return new cords and left and right
        xCord, yCord = self.getOwnXY()
        left, right = self.getFreeLook()
        return xCord, yCord, left, right

    # Turn around, move forward, then face original direction
    def moveBack(self):
        self.right()
        self.right()
        self.forward()
        self.right()
        self.right()

    # Check left and right
    def getFreeLook(self):
        vision = self.look()

        return vision[0] is None, vision[4] is None

    def left(self):
        self.updateDrives()
        NewRobot.left(self)

    def right(self):
        self.updateDrives()
        NewRobot.right(self)

    def forward(self):
        self.updateDrives()
        NewRobot.forward(self)

    def look(self):
        self.writeToFile()
        return NewRobot.look(self)


def demo():
    bill = NewRobot("Bill", 1, 1)
    bill.gotoCoord(20, 20)
    hank = EmbodiedRobot("hank", 0, 0)
    hank.gotToCoord(20, 20)


if __name__ == "__main__":
    demo()
    print("Finished")
