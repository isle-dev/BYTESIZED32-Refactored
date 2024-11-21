# Refactored dishwasher.py
# Process

from GameBasic import *
import itertools
# ----------------------------------------------------------------------------------------------
# Extended Specification
# ----------------------------------------------------------------------------------------------
#                        Task: Simulate how to wash dishes using a dishwasher.
#                   Environment: kitchen
#         Task-critical Objects: water, soap, dish soap bottle, dishwasher, dishes
#     High-level object classes: substance (water), device (dishwasher), container (dish soap bottle)
#           Critical properties: isDirty (whether the dish is dirty), dishwasher cycle stage
#                       Actions: take/put objects, open/close containers, turn on/off devices, use X on Y, eat food
#              Distractor Items: food
# High-level solution procedure: put dirty dishes in dishwasher, add soap, turn on dishwasher, wait for cycle to finish
# ----------------------------------------------------------------------------------------------

# Specific Game Objects

# A Dishwasher, which is a device that can hold dishes. When it's turned on, it washes the dishes (changes them from dirty to clean)
# as long as it has soap in it.
class DishWasher(Container, Device):
    def __init__(self):
        Device.__init__(self, "dishwasher")
        Container.__init__(self, "dishwasher")

        # Set the properties of this object
        self.properties["isOpenable"] = True  # A dishwasher is openable
        self.properties["isOpen"] = False  # A dishwasher is closed by default
        self.properties["isMoveable"] = False  # A dishwasher is too heavy to move

        self.properties["cycleStage"] = 0  # The current stage of the dishwasher's cycle
        self.properties["finishedCycle"] = False  # True when the dishwasher has finished washing

    # Try to turn on the dishwasher.
    def turnOn(self):
        # The dishwasher can't be turned on if it's open
        if self.properties["isOpen"]:
            return ("The " + self.name + " is open, so it can't be turned on.", False)
        return super().turnOn()

    def tick(self):
        # If the dishwasher is opened, then it automatically turns off and resets
        if self.properties["isOpen"]:
            self.properties.update({"isOn": False, "finishedCycle": False, "cycleStage": 0})

        # If the dishwasher is on, then wash the dishes
        elif self.properties["isOn"]:
            # Increment the cycle stage
            self.properties["cycleStage"] = min(self.properties["cycleStage"] + 1, 3)

            # Check for stage 1
            if self.properties["cycleStage"] == 2:
                # Check if there is soap in the dishwasher
                containsSoap = any(obj.name == "soap" for obj in self.getAllContainedObjectsRecursive())

                # If there is soap, wash the dishes
                if containsSoap:
                    for dish in filter(lambda obj: obj.name == "dish", self.getAllContainedObjectsRecursive()):
                        dish.makeClean()
                    # Remove soap from the dishwasher
                    for soap in filter(lambda obj: obj.name == "soap", self.getAllContainedObjectsRecursive()):
                        soap.removeSelfFromContainer()

            # Check for stage 2
            elif self.properties["cycleStage"] == 3:
                # Set washer to finished and turn off
                self.properties.update({"finishedCycle": True, "cycleStage": 0})
                self.turnOff()

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a dishwasher"
        outStr += " with a blinking green light" if self.properties["finishedCycle"] else ""
        outStr += " that is currently on" if self.properties["isOn"] else " that is currently open" if self.properties[
            "isOpen"] else " that is currently closed"

        if not self.properties["isOn"] and self.properties["isOpen"]:
            if len(self.contains) == 0:
                outStr += " and empty"
            else:
                outStr += " and contains one or more items." if not makeDetailed else " and contains the following items:\n" + "".join(
                    "\t" + obj.makeDescriptionStr() + "\n" for obj in self.contains)

        return outStr


class Dish(Container):
    def __init__(self, dishType, isDirty, foodName, containerPrefix="in"):
        Container.__init__(self, "dish")
        self.properties["containerPrefix"] = containerPrefix
        self.properties["dishType"] = dishType
        self.properties["isDirty"] = isDirty
        if isDirty:
            self.makeDirty(foodName)

    def makeDirty(self, foodName):
        self.properties["isDirty"] = True
        self.properties["foodMessName"] = foodName

    def makeClean(self):
        self.properties["isDirty"] = False
        self.properties["foodMessName"] = None

    def getReferents(self):
        descStr = f"{'dirty' if self.properties['isDirty'] else 'clean'} {self.properties['dishType']}"
        return [descStr, self.properties["dishType"]]

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a "
        outStr += "dirty " if self.properties["isDirty"] else "clean "
        outStr += self.properties["dishType"]

        effectiveContents = []
        if self.properties["isDirty"]:
            effectiveContents.append("half-eaten pieces of " + self.properties["foodMessName"])
        for obj in self.contains:
            effectiveContents.append(obj.makeDescriptionStr())

        if effectiveContents:
            outStr += " that looks to have "
            for i, content in enumerate(effectiveContents):
                if (i == len(effectiveContents) - 1) and len(effectiveContents) > 1:
                    outStr += "and "
                outStr += content + ", "
            outStr = outStr[:-2] + " " + self.properties["containerPrefix"] + " it"
        return outStr


class DishSoapBottle(Device):
    def __init__(self):
        Device.__init__(self, "bottle of dish soap")

    def useWithObject(self, patientObject):
        if patientObject.name == "dish":
            patientObject.addObject(Soap())
            return ("You squirt some dish soap on the " + patientObject.getReferents()[0] + ".", True)
        elif patientObject.name == "dishwasher":
            patientObject.addObject(Soap())
            return ("You squirt some dish soap into the dishwasher.", True)
        return ("You're not sure how to use the " + self.name + " with the " + patientObject.name + ".", False)

    def makeDescriptionStr(self, makeDetailed=False):
        return "a bottle of dish soap"


class Soap(GameObject):
    def __init__(self):
        GameObject.__init__(self, "soap")

    def makeDescriptionStr(self, makeDetailed=False):
        return "a squirt of dish soap"


class Food(GameObject):
    def __init__(self, foodName):
        GameObject.__init__(self, foodName)
        self.foodName = foodName
        self.properties["isFood"] = True

    def makeDescriptionStr(self, makeDetailed=False):
        return "a " + self.foodName


class KitchenWorld(World):
    def __init__(self):
        super().__init__("kitchen")


# Game Implementation
class DishWashingGame(TextGame):
    def __init__(self, randomSeed):
        TextGame.__init__(self, randomSeed)

    def getTaskDescription(self):
        return "Your task is to wash the dirty dishes."

    def initializeWorld(self):
        world = KitchenWorld()
        world.addObject(self.agent)

        dishwasher = DishWasher()
        world.addObject(dishwasher)

        dishSoapBottle = DishSoapBottle()
        world.addObject(dishSoapBottle)

        foodNames = ["apple", "orange", "banana", "pizza", "peanut butter", "sandwich", "pasta", "bell pepper"]
        self.random.shuffle(foodNames)

        dishNames = ["plate", "bowl", "cup", "mug", "pot", "pan", "fork", "spoon", "knife", "bottle", "glass"]
        containerPrefixes = {"plate": "on", "bowl": "in", "cup": "in", "mug": "in", "pot": "in", "pan": "in",
                             "fork": "on", "spoon": "on", "knife": "on", "bottle": "in", "glass": "in"}

        self.random.shuffle(dishNames)

        numDirtyDishes = self.random.randint(3, 5)
        self.numStartingDirtyDishes = numDirtyDishes

        for i in range(numDirtyDishes):
            dishType = dishNames[i % len(dishNames)]
            foodName = foodNames[i % len(foodNames)]
            dish = Dish(dishType=dishType, isDirty=True, foodName=foodName, containerPrefix=containerPrefixes[dishType])
            world.addObject(dish)

        numCleanDishes = self.random.randint(1, 3)
        for i in range(numCleanDishes):
            dishType = dishNames[(i + numDirtyDishes) % len(dishNames)]
            dish = Dish(dishType=dishType, isDirty=False, foodName="")
            world.addObject(dish)

        numFoods = self.random.randint(1, 3)
        for i in range(numFoods):
            foodName = foodNames[(i + numDirtyDishes) % len(foodNames)]
            food = Food(foodName=foodName)
            world.addObject(food)

        return world

    def registerAction(self, name, numArgs, delims, functionPointer, ):
        self.actions.append({"name": name, "numArgs": numArgs, "delims": delims, "functionPointer": functionPointer})

    def registerActions(self):
        # Register actions
        self.registerAction("look", 0, [], self.rootObject.makeDescriptionStr)
        self.registerAction("inventory", 0, [], self.actionInventory)
        self.registerAction("eat", 1, [], self.actionEat)
        self.registerAction("take", 1, [], self.actionTake)
        self.registerAction("open", 1, [], self.actionOpen)
        self.registerAction("close", 1, [], self.actionClose)
        self.registerAction("examine", 1, [], self.actionExamine)
        self.registerAction("turn on", 1, [], self.actionTurnOn)
        self.registerAction("turn off", 1, [], self.actionTurnOff)
        self.registerAction("put", 2, ["in/on"], self.actionPut)
        self.registerAction("use", 2, ["on"], self.actionUse)

    def generatePossibleActions(self):
        # Get a list of all game objects that could serve as arguments to actions
        allObjects = self.makeNameToObjectDict()
        # Convert to a list of (key, value) tuples
        allObjects = list(allObjects.items())

        # Make a dictionary whose keys are possible action strings, and whose values are lists that contain the arguments.
        self.possibleActions = {}

        # Enumerate the possible valid actions
        for action in self.actions:
            # Step 1: Generate all possible combinations of N objects, where N is the number of arguments (Use itertools combinations/permutations)
            numArgs = action["numArgs"]
            if (numArgs == 0):
                # No arguments -- just add the action
                self.addAction(action["name"], [action["name"]])
                continue
            else:
                objPerms = list(itertools.permutations(allObjects, numArgs))

                for objPerm in objPerms:
                    if numArgs == 1:
                        # If there's only one argument, just use the object name
                        actionStr = f"{action['name']} {objPerm[0][0]}"
                        paramList = [action["name"], objPerm[0][1][0]]
                    elif numArgs == 2:
                        # If there are two arguments, use the delimiters
                        actionStr = f"{action['name']} {objPerm[0][0]} {action['delims'][0]} {objPerm[1][0]}"
                        paramList = [action["name"], objPerm[0][1][0], objPerm[1][1][0]]
                    else:
                        # Actions with more than 2 arguments not supported
                        continue
                    self.addAction(actionStr, paramList)

        return self.possibleActions

    def actionEat(self, obj):
        if obj.parentContainer != self.agent:
            return "You don't currently have the " + obj.getReferents()[0] + " in your inventory."

        if obj.getProperty("isFood"):
            allObjects = self.rootObject.getAllContainedObjectsRecursive()
            cleanDishes = [dish for dish in allObjects if dish.name == "dish" and not dish.getProperty("isDirty")]

            if not cleanDishes:
                return "There is no clean dish to eat from."

            cleanDish = self.random.choice(cleanDishes)

            obsStr, _, success = obj.parentContainer.takeObjectFromContainer(obj)
            if not success:
                return "You can't see that."

            cleanDish.makeDirty(obj.name)

            return "You eat the " + obj.foodName + " using the " + cleanDish.properties['dishType'] + "."
        return "You can't eat that."

    # Examine an object in detail
    def actionExamine(self, obj):
        return obj.makeDescriptionStr(makeDetailed=True)

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
        args = action[1:]

        # Iterate over the possible actions
        found = False
        for action in self.actions:
            # Step 1: Check if the action name matches the action verb
            if (action["name"] == actionVerb):
                # Step 2: Run the action
                functionPtr = action["functionPointer"]
                # Get the object references for the arguments
                numArgs = action["numArgs"]
                self.observationStr = functionPtr(*args[:numArgs]) if numArgs <= 2 else "ERROR: Too many arguments to action."
                found = True
                break
        # Catch-all
        if (found == False):
            self.observationStr = "ERROR: Unknown action."

        # Do one tick of the environment
        self.doWorldTick()

        # Calculate the score
        lastScore = self.score
        self.calculateScore()
        reward = self.score - lastScore

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    # Call the object update for each object in the environment
    def doWorldTick(self):
        # Get a list of all objects in the environment
        allObjects = self.rootObject.getAllContainedObjectsRecursive()
        # Loop through all objects, and call their tick()
        for obj in allObjects:
            obj.tick()

    def calculateScore(self):
        self.score = self.numStartingDirtyDishes
        allObjects = self.rootObject.getAllContainedObjectsRecursive()
        numDirtyDishes = 0
        for obj in allObjects:
            if obj.name == "dish" and obj.getProperty("isDirty"):
                self.score -= 1
                numDirtyDishes += 1

        if numDirtyDishes == 0:
            self.gameOver = True
            self.gameWon = True

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Execute a game command.")
    parser.add_argument("commands", help="The command to execute in the game")
    args = parser.parse_args()

    print("Command received")
    # Random seed
    randomSeed = 0
    # Create a new game
    game = DishWashingGame(randomSeed=randomSeed)
    main(game, args.commands)