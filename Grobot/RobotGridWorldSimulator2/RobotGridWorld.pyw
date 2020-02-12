#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  RoboGridWorld.py
#
#  Copyright 2015 Mick Walters <Mick Walters> M.L.Walters@herts.ac.uk
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
# Version 0.1 Sept 2015
# Version 1.0 Nov 2015
# Version 1.1 Jan 2016
#   Fixed (Mac) socket, default map load dir. Contributed by Jamie Hollaway
#   Fixed Bug in Look() routine when robot heading east. MLW
# Version 2  March 2016
#   Fixed serious bug in Look()routine. had to change Map.map file format/size
#       Will load V1 maps, but if saved from V2, will load in V1 program
#       Recommend update to V2!

# Python 2 and 3 compatibility
from __future__ import absolute_import, division, print_function

try:
    test = raw_input  # Python 3 style input()

except Exception as e:
    pass

try:
    # Python 3 tkinter
    import tkinter as tk
    import tkinter.filedialog as fd
    import tkinter.messagebox as mb

except Exception as e:
    # Else Python 2 Tkinter
    import Tkinter as Tk
    import tkFileDialog as Fd
    import tkMessageBox as Mb

# Standard imports
import numpy
from numpy.linalg import norm
from threading import Thread
from time import sleep
import turtle as rbt
import pickle
import socket
import atexit


class GridRobotSim(tk.Tk):
    def __init__(self, master=None):

        # Define Size of white canvas in pixels
        self.frameHeight = 600  # Default 622
        self.frameWidth = 600  # Default 622

        # Define map size and grid size
        self.gridSpace = 20
        self.mapSize = 30

        # Define world size and borders
        self.world = [[None] * (self.mapSize + 3) for i in range(self.mapSize + 3)]  # World map

        # print(self.world) #debug

        # Define edit menu variable
        self.showEditMenu = True

        # Define brush variable
        self.brush = ['disabled', 'normal', 'normal', 'normal', 'normal']

        # List of robot names
        self.robots = {}
        # Robot shapes list
        self.shp = []
        # Internal states of the robot
        self.robotStates = {}
        # Trails variable definition
        self.trails = False

        # Initialise frame window and name
        tk.Tk.__init__(self, master)
        tk.Tk.title(self, "RobotGridWorld V3")

        # Initialise drone target array
        self.drone = [[0, 0, 0, 0, True, False]]

        # Initialise drone brush variable
        self.droneBrushState = True
        self.droneBrushStart = (0, 0)

        # Draw frame for canvas to be drawn onto
        self.frame = tk.Frame(master, bg="black", borderwidth=3)
        self.frame.grid(row=0, column=5, columnspan=1, rowspan=1, padx=5, pady=5)

        # Draw canvas with set frame heights and widths
        self.canvas = tk.Canvas(self.frame, height=self.frameHeight, width=self.frameWidth, bg="white")
        self.canvas.grid(row=0, column=5, columnspan=1, rowspan=1, padx=5, pady=5)

        # Error Message
        self.errorLabel = tk.Label(text="")
        self.errorLabel.grid(column=0, row=0, columnspan=5)

        # Buttons under canvas area to the left
        self.newButton = tk.Button(master, text="New Map", command=lambda: self.newWorld())
        self.newButton.grid(column=0, row=1)

        self.loadButton = tk.Button(master, text="Load Map", command=lambda: self.loadWorld())
        self.loadButton.grid(column=1, row=1)

        self.saveButton = tk.Button(master, text="Save Map", command=lambda: self.saveWorld())
        self.saveButton.grid(column=2, row=1)

        self.editButton = tk.Button(master, text="Editor", command=lambda: self.toggleEditMenu())
        self.editButton.grid(column=3, row=1)

        self.trailButton = tk.Button(master, text="Toggle Trails", command=lambda: self.toggleTrails())
        self.trailButton.grid(column=4, row=1)

        # Buttons under canvas area to the right
        self.speedSlider = tk.Scale(master, from_=1, to=10, orient=tk.HORIZONTAL, command=self.simSpeed)
        self.speedSlider.set(5)
        self.speedSlider.grid(column=7, row=1)

        self.speedLabel = tk.Label(text="Speed")
        self.speedLabel.grid(column=8, row=1)

        # Second rank of hidden edit features toggled by editor button
        self.wallBrush = tk.Button(master, text="Wall", state=self.brush[0], command=lambda: self.setBrush(0))
        self.wallBrush.grid_forget()

        self.goalBrush = tk.Button(master, text="Goal", state=self.brush[1], command=lambda: self.setBrush(1))
        self.goalBrush.grid_forget()

        self.foodBrush = tk.Button(master, text="Food", state=self.brush[2], command=lambda: self.setBrush(2))
        self.foodBrush.grid_forget()

        self.waterBrush = tk.Button(master, text="Water", state=self.brush[3], command=lambda: self.setBrush(3))
        self.waterBrush.grid_forget()

        self.droneBrush = tk.Button(master, text="Drone", state=self.brush[4], command=lambda: self.setBrush(4))
        self.droneBrush.grid_forget()

        # Map Size slider that will be hidden
        self.mapSizeSlider = tk.Scale(master, from_=10, to=50, resolution=10, orient=tk.HORIZONTAL,
                                      command=self.setMapSize)
        self.mapSizeSlider.set(30)
        self.mapSizeSlider.grid_forget()

        self.sizeLabel = tk.Label(text="Map Size")
        self.sizeLabel.grid_forget()

        # Add dummy turtle as hidden to set up drawing area
        self.robot1 = rbt.RawTurtle(self.canvas)  # changes canvas coords! (0,0) now in middle
        self.robot1.hideturtle()

        # Handler for mouse clicks
        self.screen = self.robot1.getscreen()
        self.screen.onclick(self.editGrid, btn=1)  # Mouse left button

        # Draw initial state of world on canvas area
        self.drawWorld()

        # Start server for robot programs to connect
        self.tcpTrd = Thread(target=self.tcpServer)
        self.tcpTrd.daemon = True
        self.tcpTrd.start()

        # Start timer for simulation speed
        self.timerTrd = Thread(target=self.simtimer)
        self.timerTrd.daemon = True
        self.timerTrd.start()

    # -------------------------------- Mapping ---------------------------------------------------

    # Take in the desired mapSize and calculate the size of grid need to accommodate
    def calculateGridspace(self, targetMapSize):

        return int(self.frameHeight / targetMapSize)

    # When the slider changes update grid space, map size and world
    def setMapSize(self, event):

        # Only update if there is a change
        if self.mapSizeSlider.get() != self.mapSize:

            # Save a temporary instance of the map
            tempWorld = self.world

            # clear boundary walls that would be in the new world area in the saved copy
            mapSize = len(self.world) - 1
            for n in range(0, mapSize):
                tempWorld[mapSize - 1][n] = "None"
                tempWorld[n][mapSize - 1] = "None"
            tempWorld[mapSize - 1][mapSize - 1] = "None"

            # Calculate the gridspace
            self.gridSpace = self.calculateGridspace(self.mapSizeSlider.get())
            # set mapSize
            self.mapSize = self.mapSizeSlider.get()

            # Make world at new size
            self.world = [[None] * (self.mapSize + 3) for i in range(self.mapSize + 3)]

            # Write the saved map back into original map
            for i in range(1, mapSize - 1):
                for j in range(1, mapSize - 1):
                    # If out of range catch exception and ignore it
                    try:
                        self.world[i][j] = tempWorld[i][j]
                    except Exception as exception:
                        pass

        # Draw new world
        self.drawWorld()

    # Draws the grid and labels XYaxis lines, labels
    def drawWorld(self):

        # Clear canvas and reset count
        self.canvas.delete("all")
        count = 0

        # Vertical lines, With steps = to gridspace
        for i in range(-self.frameHeight // 2, self.frameHeight // 2 - 1, self.gridSpace):

            # Dont draw 0 on vertical to prevent drawing two zeros
            if count != 0:
                self.canvas.create_line(i, self.frameHeight // 2, i, -self.frameWidth // 2, dash=(2, 4))
                self.canvas.create_text(i + 10, self.frameHeight // 2 - 10, text=str(count), font=("courier", 6),
                                        fill="red")
            count += 1

        # Reset count
        count = self.frameHeight // self.gridSpace

        # Horizontal lines With steps = to gridspace
        for i in range(-self.frameWidth // 2, self.frameWidth // 2 - 1, self.gridSpace):
            self.canvas.create_line(-self.frameWidth // 2, i, self.frameHeight // 2, i, dash=(2, 4))
            self.canvas.create_text(-self.frameWidth // 2 + 10, i + 12, text=str(int(count - 1)), font=("courier", 6),
                                    fill="red")

            count -= 1

        # Set boundary walls: 0,0 to mapSize,mapSize
        mapSize = len(self.world) - 1
        for n in range(0, mapSize):
            self.world[0][n] = "Wall"
            self.world[mapSize - 1][n] = "Wall"
            self.world[n][0] = "Wall"
            self.world[n][mapSize - 1] = "Wall"
        self.world[mapSize - 1][mapSize - 1] = "Wall"

        # Draw filled grids square
        for ix in range(0, len(self.world) - 1):
            for iy in range(0, len(self.world[ix]) - 1):

                if self.world[ix + 1][iy + 1] is not None:

                    if self.world[ix + 1][iy + 1] == "Wall":
                        self.fillGridWall(ix, iy)

                    elif self.world[ix + 1][iy + 1] == "Goal":
                        self.fillGridGoal(ix, iy)

                    elif self.world[ix + 1][iy + 1] == "Food":
                        self.fillGridFood(ix, iy)

                    elif self.world[ix + 1][iy + 1] == "Water":
                        self.fillGridWater(ix, iy)

                else:

                    self.clearGrid(ix, iy)

        # Redraw all robots and reinitialise any drones
        for robname in (self.robots.keys()):

            # If the robot is not a drone then remake
            if robname[:5] != "Drone":

                self.newRobot(robname, self.maptoX(self.robots[robname].xcor()),
                              self.maptoY(self.robots[robname].ycor()))

            # If it is a drone then remove it from the world and restart it from its start coords
            # This will not make the drone if the end coords are no longer in the range of the world
            else:

                # Remove "old" drone from World
                self.world[self.maptoX(self.robots[robname].xcor()) + 1][
                    self.maptoY(self.robots[robname].ycor()) + 1] = None

                self.newDrone(self.drone[int(robname[5:])][0], self.drone[int(robname[5:])][1],
                              self.drone[int(robname[5:])][2], self.drone[int(robname[5:])][3], robname)

    # Fill clicked on square based on brush
    def editGrid(self, mousex, mousey):

        # Convert mouse co-ords to grid co-ords
        x = self.maptoX(mousex)
        y = self.maptoY(mousey)

        if self.world[x + 1][y + 1] is None:

            # Make filled square with wall
            if self.brush[0] == 'disabled':
                self.fillGridWall(x, y)
                self.world[x + 1][y + 1] = "Wall"

            # Make filled square with Goal
            elif self.brush[1] == 'disabled':
                self.fillGridGoal(x, y)
                self.world[x + 1][y + 1] = "Goal"

            # Make filled square with Food
            elif self.brush[2] == 'disabled':
                self.fillGridFood(x, y)
                self.world[x + 1][y + 1] = "Food"

            # Make filled square with Water
            elif self.brush[3] == 'disabled':
                self.fillGridWater(x, y)
                self.world[x + 1][y + 1] = "Water"

            # Evaluate the drone inputs
            elif self.brush[4] == 'disabled':
                self.droneBrushHandler(x, y)

        else:
            # Clear grid square
            self.clearGrid(x, y)
            self.world[x + 1][y + 1] = None

    # Decide on actions for drone brush
    def droneBrushHandler(self, x, y):

        # If start co-ords
        if self.droneBrushState:

            # Save start co-ords
            self.droneBrushStart = x, y
            # Change to end co-ords
            self.droneBrushState = False
            # Tell user whats up
            self.displayDroneBrushMsg()

        # If end co-ords
        else:

            # Get start co-ords
            sx, sy = self.droneBrushStart
            # Check if path ok
            if self.checkPath(sx, sy, x, y):

                # If so make new drone
                self.newDrone(sx, sy, x, y)
                # Change to end co-ords
                self.droneBrushState = True
                # Tell user whats up
                self.displayDroneBrushMsg()

            else:

                # Reset start co-ords and tell user
                self.droneBrushStart = 0, 0

                # Change to end co-ords
                self.droneBrushState = True

    # Fill grid areas with scaled size to grid rectangles
    def fillGridWall(self, x, y):

        # Pass correct colour and tg identifier to fillGrid
        self.fillGrid(x, y, "grey", "walls")

    # Fill grid areas with scaled size to grid rectangles
    def fillGridGoal(self, x, y):

        # Pass correct colour and tg identifier to fillGrid
        self.fillGrid(x, y, "green", "goals")

    # Fill grid areas with scaled size to grid rectangles
    def fillGridFood(self, x, y):

        # Pass correct colour and tg identifier to fillGrid
        self.fillGrid(x, y, "orange", "foods")

    # Fill grid areas with scaled size to grid rectangles
    def fillGridWater(self, x, y):

        # Pass correct colour and tg identifier to fillGrid
        self.fillGrid(x, y, "blue", "waters")

    # Add colored rectangles to the grid and add a tag
    def fillGrid(self, x, y, color, tag):

        # Add to the tag string
        tagStr = [str(x) + "u" + str(y), tag]

        # Scale size of box based on grid size
        self.canvas.create_rectangle(self.xtoMap(x) - (self.gridSpace / 2), self.ytoMap(y) - (self.gridSpace / 2) - 1,
                                     self.xtoMap(x) + (self.gridSpace / 2), self.ytoMap(y) + (self.gridSpace / 2) - 1,
                                     fill=color, tag=tagStr)

    # Clear all values from the grid
    def clearGrid(self, x, y):

        tagStr = str(x) + "u" + str(y)
        self.canvas.delete(tagStr)

    # Take x value and map to grid x
    def xtoMap(self, x=0):

        # Find right side edge, Add half to get to the center of the square and then add amount of squares to move to
        # the right
        return int((-self.frameWidth // 2) + (self.gridSpace / 2) + (x * self.gridSpace))

    # Take y value and map to grid y
    def ytoMap(self, y=0):

        # Find bottom side edge, Subtract half to get to the center of the square and then subtract amount of squares to
        # move up
        return int((self.frameHeight // 2) - (self.gridSpace / 2) - (y * self.gridSpace))

    # Take grid x value and map to x
    def maptoX(self, mapx=0):

        # Generate the center of the squares based on half the frame height divide by the gridspace
        return int((mapx + (self.frameWidth // 2)) // self.gridSpace)

    # Take grid y value and map to y
    def maptoY(self, mapy=0):

        # Generate the center of the squares based on half the frame height divide by the gridspace
        return int((mapy + (self.frameHeight // 2)) // self.gridSpace)

    # Reinitialise world as empty world
    def newWorld(self):

        # print("NewMAp")
        self.world = [[None] * (self.mapSize + 3) for i in range(self.mapSize + 3)]  # World map

        # Reset drone values
        self.drone = [[0, 0, 0, 0, True, False]]
        self.robots.clear()

        # Redraw world
        self.drawWorld()

    # ------------------------------ UI Frame ---------------------------------------------------------

    # Change the Brush array to only contain disabled on selected brush
    def setBrush(self, value):

        for i in range(0, len(self.brush)):
            if i != value:

                # reset other entries in the array
                self.brush[i] = 'normal'

            else:

                # Set selected brush to disabled
                self.brush[i] = 'disabled'

        # Update the states of the buttons
        self.disableBrushButton()

        # Update the display message with the drone brush info
        self.displayDroneBrushMsg()

    # If the drone brush is selected show associated massage
    def displayDroneBrushMsg(self):

        # If brush is selected
        if self.brush[4] == 'disabled':

            # Start or end co-ords?
            if self.droneBrushState:

                # Waiting for starting co-ords
                self.setErrorMsg("Choose starting co-ords")

            else:

                # Waiting for the end co=ords
                self.setErrorMsg("Choose end co-ords")
        else:
            # If brush not selected clear message
            self.setErrorMsg(" ")

    # Disable selected brush button
    def disableBrushButton(self):

        # Set the state of each brush button to their corresponding array entry
        self.wallBrush.config(state=self.brush[0])
        self.goalBrush.config(state=self.brush[1])
        self.foodBrush.config(state=self.brush[2])
        self.waterBrush.config(state=self.brush[3])
        self.droneBrush.config(state=self.brush[4])

    # Show or hide edit menu features using grid_forget to retain information
    def toggleEditMenu(self):

        # If Show is true then hide the buttons on the grid
        if self.showEditMenu:

            # Un-hide brush buttons
            self.wallBrush.grid(column=0, row=2)
            self.goalBrush.grid(column=1, row=2)
            self.foodBrush.grid(column=2, row=2)
            self.waterBrush.grid(column=3, row=2)
            self.droneBrush.grid(column=4, row=2)

            # Update selected brush
            self.disableBrushButton()

            # Un-hide world slider
            self.sizeLabel.grid(column=8, row=2)
            self.mapSizeSlider.grid(column=7, row=2)

            # Set show false
            self.showEditMenu = False

        else:

            # Hide brush buttons
            self.wallBrush.grid_forget()
            self.goalBrush.grid_forget()
            self.foodBrush.grid_forget()
            self.waterBrush.grid_forget()
            self.droneBrush.grid_forget()

            # Hide world slider
            self.sizeLabel.grid_forget()
            self.mapSizeSlider.grid_forget()
            self.showEditMenu = True

    # Update the simulation based on the timer
    def simtimer(self):
        while True:
            # Update ticks
            self.wait = True
            sleep(0.3 - self.delay / 50)
            self.wait = False
            sleep(0.05)

            # Update drones
            self.runDrones()

            # Bug fix - Jamie Hollaway
            # Stops window freezing when not in focus
            self.update()
            self.update_idletasks()

    # Set the simulation speed when speed slider changed
    def simSpeed(self, event):

        self.delay = self.speedSlider.get()

    # Toggle Trails following robots based on button
    def toggleTrails(self):

        # For all robots
        for robname in self.robots:

            # If state is true
            if self.trails:

                # Tell robot to pen up
                print("OFF")
                self.robots[robname].penup()
                self.robots[robname].clear()

            # If state is false
            else:

                # Tell robot to put pen down
                print("ON")
                self.robots[robname].pendown()

        # Once all the robots are inline swap state
        if self.trails:

            self.trails = False

        else:

            self.trails = True

    # Dispaly error Message
    def setErrorMsg(self, inputMsg):

        # Display the error label with passed String
        self.errorLabel.config(text=inputMsg)

    # ------------------------- Save Load --------------------------------------------------------

    # Compress list of objects using pickle and save as .map file
    def saveWorld(self):

        # Get user to name file
        filename = fd.asksaveasfilename(filetypes=[("Map Files", "*.map")], initialdir="./Maps/")

        # If valid filename provided
        if filename is not None:

            # remove robots from world!
            for robname in list(self.robots.keys()):
                xpos, ypos = self.getXYpos(robname)
                self.world[xpos + 1][ypos + 1] = None

            # Then save!
            if filename[-4:] != ".map":
                filename += ".map"

            # Create list of objects or values to be pickled and saved
            data = {0: self.world, 1: self.mapSize, 2: self.drone}
            pickle.dump(data, open(filename, 'wb'), 2)  # Protocol 2 for python 2 compatibility

    # Uncompress list of objects previously pickled
    def loadWorld(self):

        # Get user to select file
        filename = fd.askopenfilename(filetypes=[("Map Files", "*.map")], initialdir="./Maps/")

        # If valid file
        if filename is not None:

            # If the file does not have the .map extension add it
            if filename[-4:] != ".map":
                filename += ".map"

            # UnPickel list of saved objects
            newWorld = pickle.load(open(filename, 'rb'))

            # Check object type of second indexed entry, if its an integer then this is a V3 map
            if type(newWorld[1]) == int:

                # Set map size and slider based on loaded data
                self.mapSizeSlider.set(newWorld[1])
                self.setMapSize(newWorld[1])

                # Load drone array from file into local drone variable
                self.drone = newWorld[2]

                try:
                    # Create drones from this array
                    for drone in list(self.drone):
                        self.newDrone(drone[0], drone[1], drone[2], drone[3])

                except Exception as exception:
                    pass

                # Load world from file into local world variable
                self.world = newWorld[0]

            # Else check if its a V1 or V2 map
            else:
                if len(newWorld) < 32:  # V1 or part map
                    # map onto new map
                    self.world = [[None] * (self.mapSize + 3) for i in range(self.mapSize + 3)]  # Clear World map
                    dx = 1
                    for ix in newWorld:
                        dy = 1
                        for iy in ix:
                            # print(dx, dy)#debug
                            self.world[dx][dy] = iy
                            dy += 1
                        dx += 1
                else:
                    # V2 Map
                    self.world = newWorld

            # Draw loaded world
            self.drawWorld()

    # -------------------------------- Robot -----------------------------------------------------

    # Create new robot with a name,x and y co-ords, color and shape
    def newRobot(self, robname="None", posx=1, posy=1, colour="red", rshape="None"):

        # create/use Anonymous robot. Can only do one!
        if robname == "None":
            robname = "anon"

        # If robot with name does not already exist create one
        if robname not in self.robots:

            # Generate a RawTurtle object on the canvas
            self.robots[robname] = rbt.RawTurtle(self.canvas)

        else:

            # Remove "old" robot from World
            self.world[self.maptoX(self.robots[robname].xcor()) + 1][
                self.maptoY(self.robots[robname].ycor()) + 1] = None

        # Robot shape/colour
        if rshape == "None":  # Can provide own shape def

            # Otherwise use standard robot shape
            self.shp.append(rbt.Shape("compound"))

            poly1 = ((0, 0), (10, -5), (0, 10), (-10, -5))
            self.shp[len(self.shp) - 1].addcomponent(poly1, colour, "black")

            poly2 = ((0, 0), (10, -5), (-10, -5))
            self.shp[len(self.shp) - 1].addcomponent(poly2, "black", colour)

            self.screen.register_shape(robname + "shape", self.shp[len(self.shp) - 1])

        else:

            # Can use standard shape  “arrow”, “turtle”, “circle”, “square”, “triangle”, “classic”
            self.robots[robname].shape(rshape)

        # Initalise robot
        self.robotStates[robname] = 0
        self.robots[robname].hideturtle()
        self.robots[robname].pencolor(colour)
        self.robots[robname].clear()
        self.robots[robname].penup()
        self.robots[robname].shape(robname + "shape")
        self.robots[robname].speed(0)
        self.robots[robname].goto(self.xtoMap(posx) - 3, self.ytoMap(self.mapSize - posy - 1) + 2)
        self.robots[robname].setheading(90)
        self.robots[robname].showturtle()

        # If trails are set then
        if self.trails:

            # clear previous trail and put pen down
            self.robots[robname].clear()
            self.robots[robname].pendown()

        # If trail is not set
        else:

            # Pen up and clear trail
            self.robots[robname].penup()
            self.robots[robname].clear()

        # Scale the shape size based on the map size
        self.robots[robname].shapesize(30 / self.mapSize, 30 / self.mapSize)

        self.robots[robname].speed(2)
        self.world[posx + 1][posy + 1] = robname

        return "OK"

    # Getter for robot x and y co-ords
    def getXYpos(self, robname):

        posx = self.maptoX(self.robots[robname].xcor())
        posy = self.maptoY(self.robots[robname].ycor())

        return posx, posy

    # Tell robot with rname to move forward
    def moveForward(self, rName):

        # If the robot exists and is not broken
        if rName in self.robots and self.robotStates[rName] != "Broken":

            # Clear to move in front
            if self.look(rName)[2] is None:

                # Save x and y co-ords
                posx = self.maptoX(self.robots[rName].xcor())
                posy = self.maptoY(self.robots[rName].ycor())

                # Clear robot from world
                self.world[posx + 1][posy + 1] = None

                # move to next grid square
                self.robots[rName].forward(self.gridSpace)

                # Save new x and y co-ords
                posx = self.maptoX(self.robots[rName].xcor())
                posy = self.maptoY(self.robots[rName].ycor())

                # update to world to show robot
                self.world[posx + 1][posy + 1] = rName

                return "OK"
            else:

                # If not clear (None), then collision
                self.robots[rName].shape("circle")
                self.robotStates[rName] = "Broken"  # Out of order!
                return "Bang"

        # If broken then return broken
        elif self.robotStates[rName] != "Broken":
            return "Broken"

        else:

            return "Error"

    # tell robot with rname to turn left
    def turnLeft(self, rName):

        # If robot exists
        if rName in self.robots:

            # And is not broken
            if self.robotStates[rName] != "Broken":

                # Turn left
                self.robots[rName].left(90)

                return "OK"

            # If broken
            else:

                return "Broken"

        return "Robot name not found"

    # tell robot with rname to turn right
    def turnRight(self, rName):

        # If robot exists
        if rName in self.robots:

            # And is not broken
            if self.robotStates[rName] != "Broken":

                # Turn right
                self.robots[rName].right(90)
                return "OK"

            # If broken
            else:

                return "Broken"

        return "Robot name not found"

    # Ask robot with rName to report on what is in front of it
    def look(self, rName):

        # If robot exists
        if rName in self.robots:

            # And is not broken
            if self.robotStates[rName] != "Broken":

                # Get x, y and heading for the robot
                posx = self.maptoX(self.robots[rName].xcor())
                posy = self.maptoY(self.robots[rName].ycor())
                heading = int(self.robots[rName].heading())

                # For each direction return world data in the order:
                # 0:left 1: frontLeft 2: in front 3: frontRight 4: right

                # East
                if heading == 0 and posx < self.mapSize + 1:
                    val = [self.world[posx + 1][posy + 2], self.world[posx + 2][posy + 2],
                           self.world[posx + 2][posy + 1], self.world[posx + 2][posy], self.world[posx + 1][posy]]

                # North
                elif heading == 90 and posy < self.mapSize + 1:
                    val = [self.world[posx][posy + 1], self.world[posx][posy + 2],
                           self.world[posx + 1][posy + 2], self.world[posx + 2][posy + 2],
                           self.world[posx + 2][posy + 1]]

                # West
                elif heading == 180 and posx >= 0:
                    val = [self.world[posx + 1][posy], self.world[posx][posy],
                           self.world[posx][posy + 1], self.world[posx][posy + 2], self.world[posx + 1][posy + 2]]

                # South
                elif heading == 270 and posy >= 0:
                    val = [self.world[posx + 2][posy + 1], self.world[posx + 2][posy],
                           self.world[posx + 1][posy], self.world[posx][posy], self.world[posx][posy + 1]]

                return val

            # If the robot is broken just return a junk broken string
            else:

                return ["Broken", "Broken", "Broken", "Broken", "Broken"]

        return "Robot name not found"

    # If object in front of robot is not none or a wall "Pick" it up by removing it from the world
    def pick(self, rName):
        # If robot exists
        if rName in self.robots:

            # And is not broken
            if self.robotStates[rName] != "Broken":

                # If one of the allowable pick objects (not None or robots)
                if self.look(rName)[2] in ('Goal', 'Food', 'Water', 'Wall'):

                    # Remove graphical and world data in square infront
                    self.clearInfront(self.maptoX(self.robots[rName].xcor()), self.maptoY(self.robots[rName].ycor()),
                                      int(self.robots[rName].heading()))

                    return "OK"

                else:
                    return "Can't pick that up"

            else:

                return "Broken"

        return "Robot name not found"

    # Place in the world a square of specified type
    def place(self, rName, placeType):

        # If robot exists
        if rName in self.robots:

            # And is not broken
            if self.robotStates[rName] != "Broken":

                # Take x y coords and find what posx and posy coords infront of the robot are
                posx, posy = self.findForward(self.maptoX(self.robots[rName].xcor()),
                                              self.maptoY(self.robots[rName].ycor()), int(self.robots[rName].heading()))

                # If it is clear ahead
                if self.world[posx][posy] is None:

                    # If type is food set the graphical and world data to food
                    if placeType == "Food":

                        self.fillGridFood(posx, posy)
                        self.world[posx + 1][posy + 1] = "Food"

                    # If type is water set the graphical and world data to water
                    elif placeType == "Water":

                        self.fillGridWater(posx, posy)
                        self.world[posx + 1][posy + 1] = "Water"

                    # If type is goal set the graphical and world data to goal
                    elif placeType == "Goal":

                        self.fillGridGoal(posx, posy)
                        self.world[posx + 1][posy + 1] = "Goal"

                    # If type is wall set the graphical and world data to wall
                    elif placeType == "Wall":

                        self.fillGridWall(posx, posy)
                        self.world[posx + 1][posy + 1] = "Wall"

                    # If type is not known return that
                    else:
                        return "Unkown object"

                    return "Ok"
                else:
                    return "Cannot place object there"

            else:

                return "Broken"

        return "Robot name not found"

    # Search in an increasing area for specific object
    def nearest(self, robname, target):

        # Get robots x y coords
        x, y = self.maptoX(self.robots[robname].xcor()), self.maptoY(self.robots[robname].ycor())

        # Initialize vars
        nearest = None
        dist = 3
        found = False

        # While nothing is found
        while nearest is None:

            # For each iteration move the start coords to the bottom right
            if (x - 1 > 0) and (y - 1 > 0):
                x, y = x - 1, y - 1
            else:
                x, y = 0, 0

            # Iterate throught the range defined and find any instances of target
            for i in range(0, dist):
                for j in range(0, dist):

                    # Check if square is in world size
                    if 0 <= (x + i) <= self.mapSize and 0 <= (y + i) <= self.mapSize:

                        # Check if square is target
                        print(x + i, y + j)
                        print(self.world[x + i][y + j])

                        # Only check the outermost squares of the area as all the inner squares will have been checked
                        if j == y or j == dist - 1:

                            # If an instance of a target is found set found true
                            if self.world[x + i][j] == target:
                                found = True

                        elif i == x or i == dist - 1:

                            # If an instance of a target is found set found true
                            if self.world[i][y + j] == target:
                                found = True

                        if found:

                            # If nearest has been set
                            if nearest is not None:

                                # If its norm vector distance is smaller set as new nearest
                                if numpy.linalg.norm(nearest) > numpy.linalg.norm([x + i, y + j]):
                                    nearest = x + i - 1, y + j - 1

                            else:

                                # Save coords as nearest
                                nearest = x + i - 1, y + j - 1

            # if x and y hit both edges and haven't been found return not found
            if (x == 0 and x + dist > self.mapSize) and (y == 0 and y + dist > self.mapSize):
                return "Not found"

            # If a nearest has been found return it
            # TODO Possibly return dist x dist y insted
            if nearest is not None:
                return nearest

            # Increment the distance
            dist += 1

    # Take x y and heading coords and find what coords dictate "in front" of it
    def findForward(self, posx, posy, heading):

        # East
        if heading == 0:

            return posx + 1, posy

        # North
        elif heading == 90:

            return posx, posy + 1

        # West
        elif heading == 180:

            return posx - 1, posy

        # South
        elif heading == 270:

            return posx, posy - 1

    # Clear graphical and world data from in front of provided coords and heading
    def clearInfront(self, posx, posy, heading):

        # Find positions for in front of drone
        nposx, nposy = self.findForward(posx, posy, heading)

        # Clear space in front of robot
        self.clearGrid(nposx, nposy)
        self.world[nposx + 1][nposy + 1] = None

    # --------------------------------- Drones -------------------------------------------------

    # Create a robot that moves from provided start to end points in a loop
    def newDrone(self, xpos, ypos, loopx, loopy, robname=None):

        # Check if robot has been provided a name
        if robname is not None:
            name = robname

        else:
            # If the path is clear
            if self.checkPath(xpos, ypos, loopx, loopy):

                # Iterate on drone name and set as name
                name = self.generateDroneName()

                # If array index exists
                try:

                    # Save data
                    self.drone[int(name[5:])][0] = xpos
                    self.drone[int(name[5:])][1] = ypos
                    self.drone[int(name[5:])][2] = loopx
                    self.drone[int(name[5:])][3] = loopy
                    self.drone[int(name[5:])][4] = True
                    self.drone[int(name[5:])][5] = True

                except Exception as exception:

                    # Else append element contains data
                    self.drone.append([xpos, ypos, loopx, loopy, True, True])

        # Create robot with new saved parameters
        self.newRobot(name, self.drone[int(name[5:])][0], self.drone[int(name[5:])][1], "Pink")

    # Make the drones run forward if it is none or they can see themselves
    def droneForward(self, robname):

        # Get x, y and heading for the robot
        posx = self.maptoX(self.robots[robname].xcor())
        posy = self.maptoY(self.robots[robname].ycor())
        heading = int(self.robots[robname].heading())

        # Check the square in front to see if the self named square bug is here (Gotta be a better way to fix this)
        if self.look(robname)[2] is robname:
            self.clearInfront(posx, posy, heading)

        # If clear ahead move forward
        if self.look(robname)[2] is None:
            self.moveForward(robname)

    # Make the drones run a loop from there start to there end coords and back again
    def runDrones(self):

        # Check all robots
        for robname in list(self.robots.keys()):

            # If they are drones
            if robname[:5] == "Drone":

                # get their co-ords
                x, y = self.getXYpos(robname)

                # If they are moving to loop co-ords or back to start
                if self.drone[int(robname[5:])][4]:

                    # If target y is higher and x is same as start
                    if y < self.drone[int(robname[5:])][3] and x == self.drone[int(robname[5:])][0]:

                        # If not facing up turn to face up
                        if self.robots[robname].heading() != 90:

                            self.turnRight(robname)

                        # If facing correct direction move forward
                        else:

                            self.droneForward(robname)

                    # If target y is lower and x is same as start
                    elif y > self.drone[int(robname[5:])][3] and x == self.drone[int(robname[5:])][0]:

                        # If not facing up turn to face down
                        if self.robots[robname].heading() != 270:

                            self.turnRight(robname)

                        # If facing correct direction move forward
                        else:

                            self.droneForward(robname)

                    # If target x is to the left and y is same as start
                    elif y == self.drone[int(robname[5:])][3] and x > self.drone[int(robname[5:])][2]:

                        # If not facing left turn to face left
                        if self.robots[robname].heading() != 180:

                            self.turnRight(robname)

                        else:

                            # If facing correct direction move forward
                            self.droneForward(robname)

                    # If target x is to the right and y is same as start
                    elif y == self.drone[int(robname[5:])][3] and x < self.drone[int(robname[5:])][2]:

                        # If not facing right turn to face right
                        if self.robots[robname].heading() != 0:

                            self.turnRight(robname)

                        else:

                            # If facing correct direction move forward
                            self.droneForward(robname)

                    # else begin move back to start
                    else:
                        self.drone[int(robname[5:])][4] = False

                # If moving back to the start
                else:

                    # If target y is higher and x is same as xloop
                    if y < self.drone[int(robname[5:])][1] and x == self.drone[int(robname[5:])][2]:

                        # If not facing up turn until facing up
                        if self.robots[robname].heading() != 90:

                            self.turnRight(robname)

                        else:

                            # If facing correct direction move forward
                            self.droneForward(robname)

                    # If target y is lower and x is same as xloop
                    elif y > self.drone[int(robname[5:])][1] and x == self.drone[int(robname[5:])][2]:

                        # If not facing down turn until facing down
                        if self.robots[robname].heading() != 270:

                            self.turnRight(robname)

                        else:

                            # If facing direction is correct move forward
                            self.droneForward(robname)

                    # If target x is to the left and y is equal to y loop
                    elif y == self.drone[int(robname[5:])][1] and x > self.drone[int(robname[5:])][0]:

                        # If not facing left turn until facing left
                        if self.robots[robname].heading() != 180:

                            self.turnRight(robname)

                        else:

                            # If facing the direction is correct move forward
                            self.droneForward(robname)

                    # If target x is to the right and y is equal to y loop
                    elif y == self.drone[int(robname[5:])][1] and x < self.drone[int(robname[5:])][0]:

                        # If not facing right turn unitl facing right
                        if self.robots[robname].heading() != 0:

                            self.turnRight(robname)

                        else:

                            # If facing direction is correct move forward
                            self.droneForward(robname)

                    # Else begin heading back to start
                    else:

                        self.drone[int(robname[5:])][4] = True

    # Check for existing drones and iterate drone name based on number found
    def generateDroneName(self):

        count = 0
        # Count number of robots with drone as start of name
        for robname in list(self.robots.keys()):

            if robname[:5] == "Drone":
                count += 1

        return "Drone" + str(count)

    # Take the start and end co-ords for a drone and check if the path is clear
    def checkPath(self, xpos, ypos, loopx, loopy):
        ypos += 1
        loopy += 1
        xpos += 1
        loopx += 1

        # Check x position moves
        for i in range(xpos, loopx):

            if self.world[i][ypos] is not None:
                self.setErrorMsg(("Path not clear: ", self.world[i][ypos], " At: X:", xpos, " Y:", ypos))
                return False

            if self.world[i][loopy] is not None:
                self.setErrorMsg(("Path not clear: ", self.world[i][loopy], " At: X:", xpos, " Y:", ypos))
                return False

        # Check y position moves
        for j in range(ypos, loopy):

            if self.world[xpos][j] is not None:
                self.setErrorMsg(("Path not clear: ", self.world[xpos][j], " At: X:", xpos, " Y:", ypos))
                return False

            if self.world[loopx][j] is not None:
                self.setErrorMsg(("Path not clear: ", self.world[loopx][j], " At: X:", xpos, " Y:", ypos))
                return False

        return True

    # --------------------------------- TCP Server ---------------------------------------------

    def tcpServer(self):
        """
        TCIP server, opens a TC IP socket and passes the message on to be executed and
        waits for input from the TCIP socket and pases it on to despatch() for
        evaluation. If "q" input, ends connection, "Q" input ends server.
        """
        # variables
        msg = ""
        rmsg = ""
        passw = ""
        tcpSock = None
        tcpOk = 0

        try:

            # Create IP socket and wait for customers
            tcpSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        except Exception as exception:

            print("Error creating socket")

        print("Please wait: Binding address to socket")

        # Bug fix for Mac - C ontributed by Jamie Hollaway
        tcpSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.setErrorMsg("Please Wait: Setting up Connection")

        while tcpOk == 0:

            try:

                tcpSock.bind(("localhost", 9001))
                tcpSock.listen(3)
                tcpOk = 1

            except Exception as exception:

                sleep(1.0)  # Keep trying!

        print("Socket ready now")

        self.setErrorMsg("")

        # make sure socket closes at eop
        atexit.register(tcpSock.close)
        atexit.register(tcpSock.shutdown, 1)

        msg = ""

        while tcpOk == 1:

            # when customer calls, service requests
            cli_sock, cli_ipAdd = tcpSock.accept()

            try:

                # python 3
                thrd = Thread(target=self.despatch, args=(cli_sock,))
                thrd.daemon = True
                thrd.start()

            except Exception as exception:

                # raise # debug
                print("Warning TCP/IP Error")  # Just keep on with next request

        # Clean up if this point ever reached
        tcpSock.shutdown(1)
        tcpSock.close()
        print("Server closed")

    def despatch(self, cli_sock):
        msg = ""
        rmsg = ""

        # Recive input and pass to eval
        # print("Connected") # Debug
        msg = cli_sock.recv(50).decode('utf-8')
        print("*" + msg)  # debug

        if msg != "Q":

            msg = msg.split()  # parse
            # for i in msg: print(i) #debug

            # Do robot commands
            try:

                if msg[0] == "N":

                    # print(msg) #debug
                    # New or init robot
                    rmsg = self.newRobot(msg[1], int(msg[2]), int(msg[3]), msg[4], msg[5])

                elif msg[0] == "F":

                    # msg[1] is robot name
                    rmsg = self.moveForward(msg[1])

                elif msg[0] == "R":
                    rmsg = self.turnRight(msg[1])

                elif msg[0] == "L":
                    rmsg = self.turnLeft(msg[1])

                elif msg[0] == "S":
                    rmsg = str(self.look(msg[1]))

                elif msg[0] == "P":
                    rmsg = self.getXYpos(msg[1])

                elif msg[0] == "U":
                    rmsg = self.pick(msg[1])

                elif msg[0] == "HF":
                    rmsg = self.place(msg[1], "Food")

                elif msg[0] == "HWT":
                    rmsg = self.place(msg[1], "Wall")

                elif msg[0] == "HG":
                    rmsg = self.place(msg[1], "Goal")

                elif msg[0] == "HW":
                    rmsg = self.place(msg[1], "Wall")

                elif msg[0] == "DW":
                    rmsg = self.nearest(msg[1], "Wall")

                elif msg[0] == "DF":
                    rmsg = self.nearest(msg[1], "Food")

                elif msg[0] == "DWT":
                    rmsg = self.nearest(msg[1], "Water")

                elif msg[0] == "DG":
                    rmsg = self.nearest(msg[1], "Goal")

                else:
                    rmsg = "Unknown command"

            except Exception as exception:

                # raise #debug. If error just carry on
                rmsg = "Server Error"

            if rmsg is None:

                rmsg == "None"
            # print(rmsg, type(rmsg))# debug

            # Wait here for step timer
            while self.wait:
                sleep(0.01)
            cli_sock.send(str(rmsg).encode('utf-8'))

        # print("Connection Closed")# debug
        cli_sock.close()
        return


if __name__ == '__main__':
    GRSApp = GridRobotSim()
    GRSApp.mainloop()
