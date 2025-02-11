# Refactor refrigerate-food.py
# Process and problem of code generation
# success junf

from GameBasic import *


# A fridge, which is a cooling device. It contains things inside of it. It's always on. When things are inside it, it cools them down to some temperature.
class Fridge(Container, Device):
    def __init__(self):
        GameObject.__init__(self, "fridge")
        Container.__init__(self, "fridge")
        Device.__init__(self, "fridge")

        self.properties["containerPrefix"] = "in"

        # Set critical properties
        self.properties["isOpenable"] = True  # A fridge is openable
        self.properties["isOpen"] = False  # A fridge starts out closed
        self.properties["isMoveable"] = False  # A fridge is too heavy to move
        self.properties["isOn"] = True  # A fridge is always on
        self.properties["isActivatable"] = False  # A fridge is never turned off
        self.properties["minTemperature"] = 4.0  # Min temperature of the fridge
        self.properties["tempDecreasePerTick"] = 5.0  # Temperature decrease per tick

    # Decrease the temperature of anything inside the fridge
    def tick(self):
        # If the fridge is on and closed
        if self.properties["isOn"] and not self.properties["isOpen"]:
            objectsInFridge = self.getAllContainedObjectsRecursive()

            # Decrease the temperature of each object in the fridge
            for obj in objectsInFridge:
                newTemperature = obj.properties["temperature"] - self.properties["tempDecreasePerTick"]
                obj.properties["temperature"] = max(newTemperature, self.properties["minTemperature"])

    def makeDescriptionStr(self, makeDetailed=False):
        # Description based only on its current state (open/closed)
        outStr = "a fridge" + (" that is currently open" if self.properties["isOpen"] else " that is currently closed")

        if self.properties["isOpen"]:
            # If fridge is open, describe contents.
            if self.contains:
                outStr += " that contains:\n"
                for obj in self.contains:
                    outStr += "\t" + obj.makeDescriptionStr() + "\n"
            else:
                outStr += " and is empty."
        return outStr


# A food item, which is a type of object that can be eaten. The food has a certain amount of time before it spoils.
class FoodItem(GameObject):
    def __init__(self, foodPrefix, foodName, spoilTime=20):
        super().__init__(foodName)
        self.properties["foodPrefix"] = foodPrefix

        self.properties["isFood"] = True
        self.properties["spoilTime"] = spoilTime  # How long the food lasts before spoiling
        self.properties["maxTemperature"] = 4.0  # Max temperature before it starts spoiling
        self.properties["timeAboveMaxTemp"] = 0  # Tracks how long it has been at a high temperature
        self.properties["isSpoiled"] = False
        self.properties["isAboveMaxTemp"] = True  # Whether the food item is above the maximum temperature or not (helpful for scoring)

    # Simulate spoilage process per tick
    def tick(self):
        # Check if the food item is above the maximum temperature
        self.properties["isAboveMaxTemp"] = self.properties["temperature"] > self.properties["maxTemperature"]

        # If the food item is above the maximum temperature, increase the time it's been above the max temperature
        if self.properties["isAboveMaxTemp"]:
            self.properties["timeAboveMaxTemp"] += 1

        # If the food item has been above the maximum temperature for too long, it spoils
        if self.properties["timeAboveMaxTemp"] > self.properties["spoilTime"]:
            self.properties["isSpoiled"] = True

    def getReferents(self):
        referents = []
        # Add the food item's potentially spoiled property as a prefix
        if (self.properties["isSpoiled"]):
            referents.append("spoiled " + self.name)
        referents.append(self.name)
        return referents

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = self.properties["foodPrefix"] + " "
        if self.properties["isSpoiled"]:
            outStr += "spoiled "
        outStr += self.name
        return outStr


# A counter, which is a type of container that can be used to put things on
class Counter(Container):
    def __init__(self):
        Container.__init__(self, "counter")
        self.properties["containerPrefix"] = "on"
        self.properties["isOpenable"] = False  # Counter is a flat surface, always open
        self.properties["isMoveable"] = False  # Counter is heavy to move

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a counter"

        effectiveContents = [obj.makeDescriptionStr() for obj in self.contains]

        if effectiveContents:
            outStr += " that looks to have "
            outStr += ", ".join(effectiveContents[:-1])
            if len(effectiveContents) > 1:
                outStr += " and " + effectiveContents[-1]
            outStr += " " + self.properties["containerPrefix"] + " it"
        else:
            outStr += " that is empty"

        return outStr


# World Setup
class KitchenWorld(World):
    def __init__(self):
        super().__init__("kitchen")


# Game Implementation
class RefrigerateFoodGame(TextGame):
    def __init__(self, randomSeed):
        TextGame.__init__(self, randomSeed)

    def initializeWorld(self):
        world = KitchenWorld()

        # Add the agent
        world.addObject(self.agent)

        # Add a fridge
        fridge = Fridge()
        world.addObject(fridge)

        # Add a counter
        counter = Counter()
        world.addObject(counter)

        # Create foods
        possibleFoods = [
            FoodItem("some", "apple sauce", spoilTime=20),
            FoodItem("some", "yogurt", spoilTime=20),
            FoodItem("a bottle of", "orange juice", spoilTime=20),
            FoodItem("a bottle of", "pineapple juice", spoilTime=20),
            FoodItem("a bottle of", "soy milk", spoilTime=20),
            FoodItem("a jar of", "jam", spoilTime=20),
        ]

        # Randomly shuffle and select foods
        self.random.shuffle(possibleFoods)
        numFoods = self.random.randint(1, 3)
        for i in range(numFoods):
            counter.addObject(possibleFoods[i])

        self.numFoodsToPutInFridge = numFoods

        return world

    def getTaskDescription(self):
        return "Your task is to prevent these foods from spoiling."

    def generatePossibleActions(self):
        # Get a list of all game objects that could serve as arguments to actions
        allObjects = self.makeNameToObjectDict()

        # Make a dictionary whose keys are possible action strings, and whose values are lists that contain the arguments.
        self.possibleActions = {}

        # Zero-argument actions
        for action in [("look around", "look around"), ("look", "look around"), ("inventory", "inventory")]:
            self.addAction(action[0], [action[1]])

        # Add specific actions
        # (1-arg) Eat
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction("eat " + objReferent, ["eat", obj])
                self.addAction("take " + objReferent, ["take", obj])
                self.addAction("take " + objReferent + " from " + obj.parentContainer.getReferents()[0], ["take", obj])
                self.addAction("open " + objReferent, ["open", obj])
                self.addAction("close " + objReferent, ["close", obj])
                self.addAction("examine " + objReferent, ["examine", obj])
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
                            self.addAction("put " + objReferent1 + " " + containerPrefix + " " + objReferent2, ["put", obj1, obj2])
                            self.addAction("use " + objReferent1 + " on " + objReferent2, ["use", obj1, obj2])

        return self.possibleActions

    #
    #   Interpret actions
    #

    def actionEat(self, obj):
        if obj.parentContainer != self.agent:
            return "You don't currently have the " + obj.getReferents()[0] + " in your inventory."

        if obj.getProperty("isFood"):
            obsStr, objRef, success = obj.parentContainer.takeObjectFromContainer(obj)
            if not success:
                return "You can't see that."

            return "You eat the " + obj.name + "."
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

        ## OMIT, UNUSED (refridgerate food)

    def actionTurnOn(self, obj):
        # Check if the object is a device
        if (obj.getProperty("isDevice") == True):
            # This is handled by the object itself
            obsStr, success = obj.turnOn()
            return obsStr
        else:
            return "You can't turn on that."

        ## OMIT, UNUSED (refridgerate food)

    def actionTurnOff(self, obj):
        # Check if the object is a device
        if (obj.getProperty("isDevice") == True):
            # This is handled by the object itself
            obsStr, success = obj.turnOff()
            return obsStr
        else:
            return "You can't turn off that."

    ## OMIT, UNUSED (refridgerate food)
    def actionUse(self, deviceObj, patientObject):
        # Check if the object is a device
        if (deviceObj.getProperty("isDevice") == True):
            # This is handled by the object itself
            obsStr, success = deviceObj.useWithObject(patientObject)
            return obsStr
        else:
            return "You can't use that."

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
            "look around": lambda: self.rootObject.makeDescriptionStr(),
            "inventory": lambda: self.actionInventory(),
            "examine": lambda: action[1].makeDescriptionStr(makeDetailed=True),
            "eat": lambda: self.actionEat(action[1]),
            "open": lambda: self.actionOpen(action[1]),
            "close": lambda: self.actionClose(action[1]),
            "take": lambda: self.actionTake(action[1]),
            "turn on": lambda: self.actionTurnOn(action[1]),
            "turn off": lambda: self.actionTurnOff(action[1]),
            "put": lambda: self.actionPut(action[1], action[2]),
            "use": lambda: self.actionUse(action[1], action[2]),
        }

        # Default response for unknown actions
        self.observationStr = action_map.get(actionVerb, lambda: "ERROR: Unknown action.")()

        # Do one tick of the environment
        self.doWorldTick()

        # Calculate the score
        lastScore = self.score
        self.calculateScore()
        reward = self.score - lastScore

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    def calculateScore(self):
        self.score = 0
        numFoodsFound = 0
        numFoodsChanged = 0

        allObjects = self.rootObject.getAllContainedObjectsRecursive()
        for obj in allObjects:
            if isinstance(obj, FoodItem):
                if obj.getProperty("isSpoiled"):
                    self.score -= 1
                    numFoodsChanged += 1
                # Otherwise, check if the food is cooled
                elif not obj.getProperty("isAboveMaxTemp"):
                    self.score += 1
                    numFoodsChanged += 1

                numFoodsFound += 1

        numFoodsMissing = self.numFoodsToPutInFridge - numFoodsFound
        self.score -= numFoodsMissing

        if self.score == self.numFoodsToPutInFridge:
            self.gameOver = True
            self.gameWon = True
        elif (numFoodsChanged + numFoodsMissing) >= self.numFoodsToPutInFridge:
            self.gameOver = True
            self.gameWon = False
        else:
            self.gameOver = False
            self.gameWon = False


if __name__ == "__main__":
    args = parser_commands()
    main(RefrigerateFoodGame(randomSeed=0), args.commands, args.status)