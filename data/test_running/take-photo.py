# refactored take-photo.py

# success junf
from GameBasic import *
import copy


# A manual camera, which is a device for taking photos.
# To make the photo more appealing, one needs to set the appropriate aperture-iso-shutter speed combination.
class Camera(Device):
    def __init__(self, random_seed):
        Device.__init__(self, "camera")
        self.random = random.Random(random_seed)

        # Set the properties of this object
        self.properties["isOn"] = True  # always on
        self.shutter_speed_dial = ["1/4000", "1/2000", "1/1000", "1/500", "1/250",
                                   "1/125", "1/60", "1/30", "1/15", "1/8", "1/4", "1/2", "1", "2", "4", "8"]
        self.iso_dial = ["64", "200", "400", "800", "1600", "3200", "6400"]
        self.aperture_dial = ["1.4", "2", "2.8", "4", "5.6", "8", "11", "16"]
        self.current_shutter_speed = self.random.randint(0, len(self.shutter_speed_dial) - 1)
        self.current_iso = self.random.randint(0, len(self.iso_dial) - 1)
        self.current_aperture = self.random.randint(0, len(self.aperture_dial) - 1)
        self.current_focus = None
        self.photo = None

    def rotate_dial(self, which_dial="aperture", clockwise=True):
        outStr = ""
        diff = 1 if clockwise else -1
        if which_dial == "aperture":
            self.current_aperture = (
                self.current_aperture + len(self.aperture_dial) + diff) % len(self.aperture_dial)
            outStr = "You rotated the aperture dial to %s" % (
                self.aperture_dial[self.current_aperture])
        elif which_dial == "iso":
            self.current_iso = (self.current_iso +
                                len(self.iso_dial) + diff) % len(self.iso_dial)
            outStr = "You rotated the iso dial to %s" % (
                self.iso_dial[self.current_iso])
        elif which_dial == "shutter speed":
            self.current_shutter_speed = (self.current_shutter_speed + len(
                self.shutter_speed_dial) + diff) % len(self.shutter_speed_dial)
            outStr = "You rotated the shutter speed dial to %s" % (
                self.shutter_speed_dial[self.current_shutter_speed])
        return outStr

    def shutter(self):
        current_focus_ = "nothing" if self.current_focus is None else self.current_focus.name
        self.photo = [current_focus_, copy.copy(
            self.current_shutter_speed), copy.copy(self.current_aperture), copy.copy(self.current_iso)]
        outStr = "You took a photo of %s, with shutter speed of %s, aperture of %s, and iso of %s." % (
            self.photo[0], self.shutter_speed_dial[self.photo[1]], self.aperture_dial[self.photo[2]], self.iso_dial[self.photo[3]])
        return outStr

    def focus(self, something):
        if something == self:
            return "You cannot focus on the camera itself."
        else:
            self.current_focus = something
            return f"The camera is now focusing on {something.name}."

    def makeDescriptionStr(self, makeDetailed=False):
        current_focus_ = "nothing" if self.current_focus is None else self.current_focus.name
        outStr = []
        outStr.append("A loaded camera, the current shutter speed, aperture, and iso are %s, %s, and %s, it is currently focusing on %s." % (
            self.shutter_speed_dial[self.current_shutter_speed],
            self.aperture_dial[self.current_aperture],
            self.iso_dial[self.current_iso],
            current_focus_))

        outStr.append(
            "To change the shutter speed, aperture, or iso settings, one can rotate the corresponding dials either clockwise or the opposite direction.")
        outStr.append("The min/max available shutter speed is %s and %s." %
                      (self.shutter_speed_dial[0], self.shutter_speed_dial[-1]))
        outStr.append("The min/max available aperture is %s and %s." %
                      (self.aperture_dial[0], self.aperture_dial[-1]))
        outStr.append("The min/max available iso is %s and %s." %
                      (self.iso_dial[0], self.iso_dial[-1]))

        return "\n".join(outStr)


# (Distractor item) a food item
class Food(GameObject):
    def __init__(self, foodName):
        GameObject.__init__(self, foodName)
        self.foodName = foodName
        # Set critical properties
        self.properties["isFood"] = True

    def makeDescriptionStr(self, makeDetailed=False):
        return "a " + self.foodName


# World Setup
class PhotographyWorld(World):
    def __init__(self):
        super().__init__("kitchen")


# Game Implementation
class TakePhotoGame(TextGame):
    def __init__(self, randomSeed):
        self.randomSeed = randomSeed
        TextGame.__init__(self, randomSeed)
    # Create/initialize the world/environment for this game
    def initializeWorld(self):
        world = PhotographyWorld()

        # Add the agent
        world.addObject(self.agent)

        # Add a camera
        self.camera = Camera(self.randomSeed)
        world.addObject(self.camera)

        # Distractor items
        # Food names
        foodNames = ["apple", "orange", "banana", "pizza",
                     "peanut butter", "sandwhich", "pasta", "bell pepper"]
        # Shuffle the food names
        self.random.shuffle(foodNames)
        # Add a few random foods
        exist_foods = []
        numFoods = self.random.randint(1, 3)
        for i in range(numFoods):
            foodName = foodNames[i % len(foodNames)]
            exist_foods.append(foodName)
            food = Food(foodName=foodName)
            world.addObject(food)

        self.sample_task(exist_foods)
        return world

    def sample_task(self, exist_foods):
        assert len(exist_foods) > 0
        self.target_food = self.random.choice(exist_foods)
        self.target_aperture = self.random.choice(self.camera.aperture_dial)
        self.target_shutter_speed = self.random.choice(self.camera.shutter_speed_dial)
        self.target_iso = self.random.choice(self.camera.iso_dial)

    # Get the task description for this game
    def getTaskDescription(self):
        return "Your task is to take a nice picture of %s, using a camera with shutter speed of %s, aperture of %s, and iso of %s." % (
            self.target_food, self.target_shutter_speed, self.target_aperture, self.target_iso)

    # Returns a list of valid actions at the current time step
    def generatePossibleActions(self):
        # Get a list of all game objects that could serve as arguments to actions
        allObjects = self.makeNameToObjectDict()

        # Make a dictionary whose keys are possible action strings, and whose values are lists that contain the arguments.
        self.possibleActions = {}

        # Add actions that are not provided in the default actions in the super class
        # Zero-argument actions
        for action in [("look around", "look around"), ("press shutter", "press shutter"), ("look", "look around"), ("inventory", "inventory")]:
            self.addAction(action[0], [action[1]])

        # (1-arg) Eat
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction("eat " + objReferent, ["eat", obj])
                self.addAction("take " + objReferent, ["take", obj])
                self.addAction("take " + objReferent + " from " +
                               obj.parentContainer.getReferents()[0], ["take", obj])
                self.addAction("open " + objReferent, ["open", obj])
                self.addAction("close " + objReferent, ["close", obj])
                self.addAction("examine " + objReferent, ["examine", obj])
                self.addAction("focus " + objReferent, ["focus", obj])
                self.addAction("turn on " + objReferent, ["turn on", obj])
                self.addAction("turn off " + objReferent, ["turn off", obj])


        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if (obj1 != obj2):
                            containerPrefix = "in"
                            if obj2.properties["isContainer"]:
                                containerPrefix = obj2.properties["containerPrefix"]
                            self.addAction(
                                "put " + objReferent1 + " " + containerPrefix + " " + objReferent2, ["put", obj1, obj2])
                            self.addAction(
                                "use " + objReferent1 + " on " + objReferent2, ["use", obj1, obj2])

        for dial in ["aperture", "iso", "shutter speed"]:
            for direction in ["clockwise", "anticlockwise"]:
                self.addAction("rotate " + dial + " " + direction, ["rotate", dial, direction])

        return self.possibleActions


    #
    #   Interpret actions
    #

    # Perform the "press shutter" action.
    def actionPressShutter(self):
        if (self.camera.parentContainer != self.agent):
            return "You don't currently have the camera in your inventory."
        else:
            return self.camera.shutter()

    # Perform the "focus" action.  Returns an observation string.
    def actionFocus(self, obj):
        if (self.camera.parentContainer != self.agent):
            return "You don't currently have the camera in your inventory."
        else:
            return self.camera.focus(obj)

        # Perform the "eat" action.  Returns an observation string.

    def actionEat(self, obj):
        # Enforce that the object must be in the inventory to do anything with it
        if (obj.parentContainer != self.agent):
            return "You don't currently have the " + obj.getReferents()[0] + " in your inventory."

        # Check if the object is food
        if (obj.getProperty("isFood") == True):
            # Try to pick up/take the food
            obsStr, objRef, success = obj.parentContainer.takeObjectFromContainer(
                obj)
            if (success == False):
                # If it failed, we were unable to take the food (e.g. it was in a closed container)
                return "You can't see that."

            # Update the game observation
            return "You eat the " + obj.foodName + "."
        else:
            return "You can't eat that."

        # Open a container

    def actionOpen(self, obj):
        # Check if the object is a container
        if (obj.getProperty("isContainer") == True):
            # This is handled by the object itself
            obsStr, success = obj.openContainer()
            return obsStr
        else:
            return "You can't open that."

        # Close a container

    def actionClose(self, obj):
        # Check if the object is a container
        if (obj.getProperty("isContainer") == True):
            # This is handled by the object itself
            obsStr, success = obj.closeContainer()
            return obsStr
        else:
            return "You can't close that."

    # rotate a dial
    def actionRotate(self, which_dial, direction):
        if (self.camera.parentContainer != self.agent):
            return "You don't currently have the camera in your inventory."
        return self.camera.rotate_dial(which_dial=which_dial, clockwise=(direction == "clockwise"))

    def actionTurnOn(self, obj):
        # Check if the object is a device
        if (obj.getProperty("isDevice") == True):
            # This is handled by the object itself
            obsStr, success = obj.turnOn()
            return obsStr
        else:
            return "You can't turn on that."

    def actionTurnOff(self, obj):
        # Check if the object is a device
        if (obj.getProperty("isDevice") == True):
            # This is handled by the object itself
            obsStr, success = obj.turnOff()
            return obsStr
        else:
            return "You can't turn off that."

    # OMIT, UNUSED (boiling water)
    def actionUse(self, deviceObj, patientObject):
        # Check if the object is a device
        if (deviceObj.getProperty("isDevice") == True):
            # This is handled by the object itself
            obsStr, success = deviceObj.useWithObject(patientObject)
            return obsStr
        else:
            return "You can't use that."

    def step(self, actionStr):
        self.observationStr = ""
        reward = 0

        # Check to make sure the action is in the possible actions dictionary
        if actionStr not in self.possibleActions:
            self.observationStr = "I don't understand that."
            return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

        self.numSteps += 1

        # Find the action in the possible actions dictionary
        actions = self.possibleActions[actionStr]
        action = None

        # Check for an ambiguous action (i.e. one that has multiple possible arguments)
        if (len(actions) > 1):
            # If there are multiple possible arguments, for now just choose the first one
            action = actions[0]
        else:
            # Otherwise, also just take the first action in the list of possible actions
            action = actions[0]

        # Interpret the action
        actionVerb = action[0]

        actions = {
            "look around": lambda: self.rootObject.makeDescriptionStr(),
            "inventory": lambda: self.actionInventory(),
            "press shutter": lambda: self.actionPressShutter(),
            "examine": lambda: action[1].makeDescriptionStr(makeDetailed=True),
            "eat": lambda: self.actionEat(action[1]),
            "open": lambda: self.actionOpen(action[1]),
            "close": lambda: self.actionClose(action[1]),
            "take": lambda: self.actionTake(action[1]),
            "turn on": lambda: self.actionTurnOn(action[1]),
            "turn off": lambda: self.actionTurnOff(action[1]),
            "put": lambda: self.actionPut(action[1], action[2]),
            "use": lambda: self.actionUse(action[1], action[2]),
            "focus": lambda: self.actionFocus(action[1]),
            "rotate": lambda: self.actionRotate(action[1], action[2])
        }

        self.observationStr = actions.get(actionVerb, lambda: "ERROR: Unknown action.")()

        # Do one tick of the environment
        self.doWorldTick()

        # Calculate the score
        lastScore = self.score
        self.calculateScore()
        reward = self.score - lastScore

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    def calculateScore(self):
        # Calculate the score
        self.score = 0
        if self.camera.photo is not None and \
                self.camera.photo[0] == self.target_food and \
                self.camera.shutter_speed_dial[self.camera.photo[1]] == self.target_shutter_speed and \
                self.camera.aperture_dial[self.camera.photo[2]] == self.target_aperture and \
                self.camera.iso_dial[self.camera.photo[3]] == self.target_iso:
            self.score = 1
            self.gameOver = True
            self.gameWon = True
        else:
            allObjects = self.makeNameToObjectDict()
            if self.target_food not in allObjects:
                # consumed
                self.score = 0
                self.gameOver = True
                self.gameWon = False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Execute a game command.")
    parser.add_argument("commands", help="The command to execute in the game")
    args = parser.parse_args()

    print("Command received")
    # Random seed
    randomSeed = 0
    # Create a new game
    game = TakePhotoGame(randomSeed=randomSeed)
    main(game, args.commands)