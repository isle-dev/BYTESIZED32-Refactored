# refactored boil-water.py
# Success Haonan Wang and Ziang Xiao(Oct 2024)
# Success Haonan(2025.2)

# Task: Create a micro-simulation that models how to boil water.
# Environment: kitchen
# Task-critical Objects: Stove, Pot, Water, Sink
# High-level object classes: Substance (Water), Device (Sink, Stove), Container (Pot)
# Critical properties: maxTemperature (Stove), tempIncreasePerTick (Stove), temperature (Substance), stateOfMatter (Substance), solidName/liquidName/gasName (Substance), meltingPoint/boilingPoint (Substance)
# Actions: look, inventory, examine, take/put objects, open/close containers, turn on/off devices
# Distractor Items: None
# Distractor Actions: None
# High-level solution procedure: put pot into the sink, turn on the sink, put pot on the stove, turn on the stove, wait till the water is boiled


from data.library.GameBasic import *


# A stove, which is a heating device.  It holds things on its surface.  When turned on, it progressively heats things up to some temperature.
class Stove(Container, Device):
    def __init__(self):
        GameObject.__init__(self, "stove")
        Container.__init__(self, "stove")
        Device.__init__(self, "stove")

        self.properties["containerPrefix"] = "on"

        # Set the properties of this object
        self.properties["isOpenable"] = False # A stove is not openable
        self.properties["isMoveable"] = False # A stove is too heavy to move (and doesn't really need to be moved for this simulation)

        # Set critical properties
        self.properties["maxTemperature"] = 500.0 # Maximum temperature of the stove (in degrees Celsius)
        self.properties["tempIncreasePerTick"] = 25.0 # How much the temperature increases per tick (in degrees Celsius)

    # If the stove is on, increase the temperature of anything on the stove, up to the maximum temperature.
    def tick(self):
        # If the stove is on, then increase the temperature of anything on the stove
        if self.properties["isOn"]:
            # Get a list of all objects on the stove
            objectsOnStove = self.getAllContainedObjectsRecursive()

            # Increase the temperature of each object on the stove
            for obj in objectsOnStove:
                # Increase the object's temperature, up to the maximum temperature
                newTemperature = obj.properties["temperature"] + self.properties["tempIncreasePerTick"]
                # Set the object's new temperature
                obj.properties["temperature"] = min(newTemperature, self.properties["maxTemperature"])

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a stove"

        # Check if on/off
        outStr += " that is currently " + ("on" if self.properties["isOn"] else "off")

        # Check if empty
        if len(self.contains) == 0:
            outStr += " and has nothing " + self.properties["containerPrefix"] + " it."
        else:
            if not makeDetailed:
                outStr += " and has one or more items " + self.properties["containerPrefix"] + " it."
            else:
                outStr += " and has the following items " + self.properties["containerPrefix"] + " it:\n"
                for obj in self.contains:
                    outStr += "\t" + obj.makeDescriptionStr() + "\n"

        return outStr


# A pot, which is a container that can hold food (and nominally here, a liquid like water to boil)
class Pot(Container):
    # Constructor.
    def __init__(self):
        GameObject.__init__(self, "pot")
        Container.__init__(self, "pot")  # A pot is not openable

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a pot"
        contents = [obj.makeDescriptionStr() for obj in self.contains]
        if contents:
            outStr += " that looks to have " + ", ".join(
                ("and " + contents[i] if i == len(contents) - 1 and len(contents) > 1 else contents[i]) for i in
                range(len(contents))) + f" {self.properties['containerPrefix']} it"
        else:
            outStr += " that is empty"

        return outStr

# An instance of a substance (here, water)
class Water(Substance):
    def __init__(self):
        Substance.__init__(self, "ice", "water", "steam", boilingPoint=100, meltingPoint=0, currentTemperatureCelsius=20)
        # Also call the tick function to set the initial state of matter
        self.tick()

# A sink
class Sink(Container, Device):
    def __init__(self):
        GameObject.__init__(self, "sink")
        Container.__init__(self, "sink")
        Device.__init__(self, "sink")  # A sink is not openable


    # On each step that the sink is on, add water to any object in the sink that doesn't have water on it
    def tick(self):
        # Get the objects contained in the sink
        containedObjects = self.getAllContainedObjectsRecursive()
        # Check if the sink is on
        if self.properties["isOn"]:
            # Check each container to make sure it contains water
            for obj in containedObjects:
                if isinstance(obj, Container) and not any(isinstance(o, Water) for o in obj.contains):
                    obj.addObject(Water())

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a sink"
        # Check if open
        if len(self.contains) == 0:
            outStr += " that is empty"
        else:
            if not makeDetailed:
                outStr += " that contains one or more items."
            else:
                outStr += " that contains the following items: \n"
                for obj in self.contains:
                    outStr += "\t" + obj.makeDescriptionStr() + "\n"

        return outStr


# (Distractor item) a food item
class Food(GameObject):
    def __init__(self, foodName):
        super().__init__(foodName)
        self.foodName = foodName
        # Set critical properties
        self.properties["isFood"] = True

    def makeDescriptionStr(self, makeDetailed=False):
        return "a " + self.foodName


# The world is the root object of the game object tree.  In single room environments, it's where all the objects are located.
class KitchenWorld(World):
    def __init__(self):
        World.__init__(self, "kitchen")


class BoilWaterGame(TextGame):
    def __init__(self, randomSeed):
        TextGame.__init__(self, randomSeed)

    # Create/initialize the world/environment for this game
    def initializeWorld(self):
        world = KitchenWorld()

        # Add the agent
        world.addObject(self.agent)

        # Add a stove
        stove = Stove()
        world.addObject(stove)

        # Add a sink
        sink = Sink()
        world.addObject(sink)

        # Add a pot
        pot = Pot()
        world.addObject(pot)

        # Distractor items
        # Food names
        foodNames = ["apple", "orange", "banana", "pizza", "peanut butter", "sandwhich", "pasta", "bell pepper"]
        # Shuffle the food names
        self.random.shuffle(foodNames)
        # Add a few random foods
        numFoods = self.random.randint(1, 3)
        for i in range(numFoods):
            food = Food(foodNames[i % len(foodNames)])
            world.addObject(food)


        # Return the world
        return world

    # Get the task description for this game
    def getTaskDescription(self):
        return "Your task is to boil water."

    # Returns a list of valid actions at the current time step
    def generatePossibleActions(self):
        # Get a list of all game objects that could serve as arguments to actions
        allObjects = self.makeNameToObjectDict()

        # Make a dictionary whose keys are possible action strings, and whose values are lists that contain the arguments.
        self.possibleActions = {}
        # Actions with zero arguments
        # (0-arg) Look around the environment and Look at the agent's current inventory
        for action in [("look around", "look around"), ("look", "look around"), ("inventory", "inventory")]:
            self.addAction(action[0], [action[1]])

        # Actions with one object argument
        # (1-arg) Eat, Take, Open/Close, Detailed look/examine, Turn on/Turn off device
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction(f"eat {objReferent}", ["eat", obj])
                self.addAction(f"take {objReferent}", ["take", obj])
                self.addAction(f"take {objReferent} from {obj.parentContainer.getReferents()[0]}", ["take", obj])
                self.addAction(f"open {objReferent}", ["open", obj])
                self.addAction(f"close {objReferent}", ["close", obj])
                self.addAction(f"examine {objReferent}", ["examine", obj])
                self.addAction(f"turn on {objReferent}", ["turn on", obj])
                self.addAction(f"turn off {objReferent}", ["turn off", obj])

        # Actions with two object arguments
        # (2-arg) Put, Use
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if obj1 != obj2:
                            # Put action with containerPrefix
                            containerPrefix = obj2.properties.get("containerPrefix", "in") if obj2.properties.get(
                                "isContainer") else "in"
                            self.addAction(f"put {objReferent1} {containerPrefix} {objReferent2}", ["put", obj1, obj2])
                            # Use action
                            self.addAction(f"use {objReferent1} on {objReferent2}", ["use", obj1, obj2])

        return self.possibleActions
    #
    #   Interpret actions
    #

    # Perform the "eat" action.  Returns an observation string.
    def actionEat(self, obj):
        # Enforce that the object must be in the inventory to do anything with it
        if obj.parentContainer != self.agent:
            return "You don't currently have the " + obj.getReferents()[0] + " in your inventory."

        # Check if the object is food
        if obj.getProperty("isFood"):
            # Try to pick up/take the food
            obsStr, objRef, success = obj.parentContainer.takeObjectFromContainer(obj)
            if not success:
                # If it failed, we were unable to take the food (e.g. it was in a closed container)
                return "You can't see that."

            # Update the game observation
            return "You eat the " + obj.foodName + "."
        else:
            return "You can't eat that."

    # Open a container
    def actionOpen(self, obj):
        # Check if the object is a container
        if obj.getProperty("isContainer"):
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

    ## OMIT, UNUSED (boiling water)
    def actionUse(self, deviceObj, patientObject):
        # Check if the object is a device
        if (deviceObj.getProperty("isDevice") == True):
            # This is handled by the object itself
            obsStr, success = deviceObj.useWithObject(patientObject)
            return obsStr
        else:
            return "You can't use that."

    def actionTurnOn(self, obj):
        # Check if the object is a device
        if obj.getProperty("isDevice"):
            # This is handled by the object itself
            obsStr, success = obj.turnOn()
            return obsStr
        return "You can't turn on that."

    def actionTurnOff(self, obj):
        # Check if the object is a device
        if obj.getProperty("isDevice"):
            # This is handled by the object itself
            obsStr, success = obj.turnOff()
            return obsStr
        return "You can't turn off that."

    # Performs an action in the environment, returns the result (a string observation, the reward, and whether the game is completed).
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

        action_map = {
            "look around": self.rootObject.makeDescriptionStr,  # Look around the environment -- i.e. show the description of the world.
            "inventory": self.actionInventory,  # Display the agent's inventory
            "examine": lambda action: action[1].makeDescriptionStr(makeDetailed=True),  # Examine an object
            "eat": lambda action: self.actionEat(action[1]),  # Eat a food
            "open": lambda action: self.actionOpen(action[1]),  # Open a container
            "close": lambda action: self.actionClose(action[1]),  # Close a container
            "take": lambda action: self.actionTake(action[1]),  # Take an object from a container
            "turn on": lambda action: self.actionTurnOn(action[1]),  # Turn on a device
            "turn off": lambda action: self.actionTurnOff(action[1]),  # Turn off a device
            "put": lambda action: self.actionPut(action[1], action[2]),  # Put an object in a container
            "use": lambda action: self.actionUse(action[1], action[2])  # Use a device on an object
        }

        # Catch-all
        self.observationStr = action_map.get(actionVerb, lambda: "ERROR: Unknown action.")(action)

        # Do one tick of the environment
        self.doWorldTick()

        # Calculate the score
        lastScore = self.score
        self.calculateScore()
        reward = self.score - lastScore

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    def calculateScore(self):
        # Baseline score
        self.score = 0

        # If there is any steam in the environment, then add a point.
        allObjects = self.rootObject.getAllContainedObjectsRecursive()
        if any(obj.name == "steam" for obj in allObjects):
            self.score, self.gameOver, self.gameWon = 1, True, True

if __name__ == "__main__":
    # Set random seed 0 and Create a new game
    main(BoilWaterGame(randomSeed=1))
