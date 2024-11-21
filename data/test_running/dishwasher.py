# Refactored dishwasher.py
# Process and problem of two files in code but have one playthrough

from GameBasic import *

# A Dishwasher, which is a device that can hold dishes. When it's turned on, it washes the dishes (changes them from dirty to clean)
# as long as it has soap in it. If it doesn't have soap, then it doesn't change them from dirty to clean.
class DishWasher(Container, Device):
    def __init__(self):
        GameObject.__init__(self, "dishwasher")
        Container.__init__(self, "dishwasher")
        Device.__init__(self, "dishwasher")

        # Set properties for a dishwasher
        self.properties["isOpenable"] = True  # Dishwasher can be opened
        self.properties["isOpen"] = False     # Default state is closed
        self.properties["isMoveable"] = False # Too heavy to move

        self.properties["cycleStage"] = 0     # Cycle stage, 0 = not running, 1-2 = washing, 3 = finished
        self.properties["finishedCycle"] = False  # True when finished, reset upon open

    def turnOn(self):
        if self.properties["isOpen"]:
            return ("The " + self.name + " is opened, so it can't be turned on.", False)
        return Device.turnOn(self)  # Otherwise, follow usual turn-on protocol

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
                # Check to see if there is soap in the dishwasher
                containsSoap = any(obj.name == "soap" for obj in self.getAllContainedObjectsRecursive())

                # If there is soap in the dishwasher, then wash the dishes
                if containsSoap:
                    for dish in filter(lambda obj: obj.name == "dish", self.getAllContainedObjectsRecursive()):
                        dish.makeClean()

                    # Remove any soap from the dishwasher
                    for soap in filter(lambda obj: obj.name == "soap", self.getAllContainedObjectsRecursive()):
                        soap.removeSelfFromContainer()

            # Check for stage 2
            elif self.properties["cycleStage"] == 3:
                # Set the washer to finished
                self.properties.update({"finishedCycle": True, "cycleStage": 0})
                # Turn off dishwasher
                self.turnOff()

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a dishwasher"
        outStr += " with a blinking green light" if self.properties["finishedCycle"] else ""
        outStr += " that is currently on" if self.properties["isOn"] else " that is currently open" if self.properties[
            "isOpen"] else " that is currently closed"

        if self.properties["isOpen"] and not self.properties["isOn"]:
            if len(self.contains) == 0:
                outStr += " and empty"
            else:
                outStr += " and contains one or more items." if not makeDetailed else " and contains the following items:\n"
                if makeDetailed:
                    outStr += "".join("\t" + obj.makeDescriptionStr() + "\n" for obj in self.contains)

        return outStr


class Dish(Container):
    def __init__(self, dishType, isDirty, foodName, containerPrefix="in"):
        GameObject.__init__(self, "dish")
        Container.__init__(self, "dish")
        self.properties["containerPrefix"] = containerPrefix

        self.properties["dishType"] = dishType
        self.properties["isDirty"] = isDirty
        if (isDirty):
            self.makeDirty(foodName)

    def makeDirty(self, foodName):
        self.properties["isDirty"] = True
        self.properties["foodMessName"] = foodName

    def makeClean(self):
        self.properties["isDirty"] = False
        self.properties["foodMessName"] = None

    def getReferents(self):
        descStr = f"{'dirty' if self.properties['isDirty'] else 'clean'} {self.properties['dishType']}"
        # Allow reference by either the dish type (e.g. cup) or the description (e.g. clean cup)
        return [descStr, self.properties["dishType"]]

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = f"a {'dirty' if self.properties['isDirty'] else 'clean'} {self.properties['dishType']}"

        effectiveContents = ["half-eaten pieces of " + self.properties["foodMessName"]] if self.properties[
            "isDirty"] else []
        effectiveContents.extend(obj.makeDescriptionStr() for obj in self.contains)

        if effectiveContents:
            outStr += " that looks to have " + ", ".join(
                ("and " + effectiveContents[i] if i == len(effectiveContents) - 1 and len(effectiveContents) > 1 else
                 effectiveContents[i])
                for i in range(len(effectiveContents))
            ) + f" {self.properties['containerPrefix']} it"

        return outStr


class DishSoapBottle(Device):
    def __init__(self):
        Device.__init__(self, "bottle of dish soap")

    def useWithObject(self, patientObject):
        if (patientObject.name == "dish"):
            patientObject.addObject(Soap())
            return "You squirt some dish soap on the " + patientObject.getReferents()[0] + ".", True
        elif patientObject.name == "dishwasher":
            patientObject.addObject(Soap())
            return "You squirt some dish soap into the dishwasher.", True
        else:
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
        return "a " + self.name

class KitchenWorld(World):
    def __init__(self):
        World.__init__(self, "kitchen")



class DishwasherGame(TextGame):
    def __init__(self, randomSeed):
        TextGame.__init__(self, randomSeed)

    def initializeWorld(self):
        world = KitchenWorld()
        world.addObject(self.agent)

        # Add appliances and tools
        world.addObject(DishWasher())
        world.addObject(DishSoapBottle())

        # Add food and dishes
        foodNames = ["apple", "orange", "banana", "pizza", "peanut butter", "sandwhich", "pasta", "bell pepper"]
        dishNames = ["plate", "bowl", "cup", "mug", "pot", "pan", "fork", "spoon", "knife", "bottle", "glass"]
        containerPrefixes = {"plate": "on", "bowl": "in", "cup": "in", "mug": "in", "pot": "in", "pan": "in",
                             "fork": "on", "spoon": "on", "knife": "on", "bottle": "in", "glass": "in"}

        self.random.shuffle(foodNames)
        self.random.shuffle(dishNames)

        # Add some random number of dirty dishes to the world (minimum 3, maximum 8)
        numDirtyDishes = self.random.randint(3, 5)
        # Store the number of starting dirty dishes, so we can calculate a score later
        self.numStartingDirtyDishes = numDirtyDishes

        for i in range(numDirtyDishes):
            # Choose the next dish type
            dishType = dishNames[i % len(dishNames)]
            # Choose the next food name
            foodName = foodNames[i % len(foodNames)]
            # Create a new dish of that type
            dish = Dish(dishType=dishType, isDirty=True, foodName=foodName, containerPrefix=containerPrefixes[dishType])
            # Add the dish to the environment
            world.addObject(dish)

        # Also add a few clean dishes
        numCleanDishes = self.random.randint(1, 3)
        for i in range(numCleanDishes):
            # Choose the next dish type
            dishType = dishNames[(i + numDirtyDishes) % len(dishNames)]
            # Create a new dish of that type
            dish = Dish(dishType=dishType, isDirty=False, foodName="")
            # Add the dish to the environment
            world.addObject(dish)

        # Also add a few random foods
        numFoods = self.random.randint(1, 3)
        for i in range(numFoods):
            # Choose the next food name
            foodName = foodNames[(i + numDirtyDishes) % len(foodNames)]
            # Create a new food item
            food = Food(foodName=foodName)
            # Add the food to the environment
            world.addObject(food)

        return world

    def getTaskDescription(self):
        return "Your task is to wash all dirty dishes."

    def generatePossibleActions(self):
        # Get a list of all game objects that could serve as arguments to actions
        allObjects = self.makeNameToObjectDict()

        # Make a dictionary whose keys are possible action strings, and whose values are lists that contain the arguments.
        self.possibleActions = {}

        # Zero-argument actions
        for action in [("look around", "look around"), ("look", "look around"), ("inventory", "inventory")]:
            self.addAction(action[0], [action[1]])

        # One-object actions
        for objReferent, objs in allObjects.items():
            for obj in objs:
                for action, verb in [("eat", "eat"), ("take", "take"), ("open", "open"), ("close", "close"),
                                     ("examine", "examine"), ("turn on", "turn on"), ("turn off", "turn off")]:
                    self.addAction(f"{action} {objReferent}", [verb, obj])
                # Additional take action with container reference
                self.addAction(f"take {objReferent} from {obj.parentContainer.getReferents()[0]}", ["take", obj])

        # Two-object actions
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

    def actionEat(self, obj):
        # Enforce that the object must be in the inventory to do anything with it
        if (obj.parentContainer != self.agent):
            return "You don't currently have the " + obj.getReferents()[0] + " in your inventory."

        # Check if the object is food
        if (obj.getProperty("isFood") == True):

            # First, find a clean dish in the environment
            # Get a list of all game objects
            allObjects = self.rootObject.getAllContainedObjectsRecursive()
            # Find a clean dish
            cleanDishes = [obj for obj in allObjects if (obj.name == "dish") and not obj.properties["isDirty"]]

            # If there is no clean dish, then fail.
            if len(cleanDishes) == 0:
                return "There is no clean dish to eat from."

            # Otherwise, choose a random clean dish
            cleanDish = self.random.choice(cleanDishes)

            # Try to pick up/take the food
            obsStr, objRef, success = obj.parentContainer.takeObjectFromContainer(obj)
            if (success == False):
                # If it failed, we were unable to take the food (e.g. it was in a closed container)
                return "You can't see that."

            # Dirty the dish with the food
            cleanDish.makeDirty(obj.name)
            # Move the dirty dish to the kitchen
            self.rootObject.addObject(cleanDish)

            # Update the game observation
            return "You eat the " + obj.foodName + " using the " + cleanDish.properties['dishType'] + "."
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

    def actionUse(self, Obj, patientObject):
        # Check if the object is a obj
        if (Obj.getProperty("isDevice") == True):
            # This is handled by the object itself
            obsStr, success = Obj.useWithObject(patientObject)
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

        action_map = {
            "look around": self.rootObject.makeDescriptionStr,
            "inventory": self.actionInventory,
            "examine": lambda: action[1].makeDescriptionStr(makeDetailed=True),
            "eat": lambda: self.actionEat(action[1]),
            "open": lambda: self.actionOpen(action[1]),
            "close": lambda: self.actionClose(action[1]),
            "take": lambda: self.actionTake(action[1]),
            "turn on": lambda: self.actionTurnOn(action[1]),
            "turn off": lambda: self.actionTurnOff(action[1]),
            "put": lambda: self.actionPut(action[1], action[2]),
            "use": lambda: self.actionUse(action[1], action[2])
        }

        self.observationStr = action_map.get(actionVerb, lambda action: "ERROR: Unknown action.")()

        # Do one tick of the environment
        self.doWorldTick()

        # Calculate the score
        lastScore = self.score
        self.calculateScore()
        reward = self.score - lastScore

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    def calculateScore(self):
        # Baseline score is negative one point per starting dirty dish
        self.score = self.numStartingDirtyDishes

        # Subtract one point for every dirty dish in the environment
        allObjects = self.rootObject.getAllContainedObjectsRecursive()
        numDirtyDishes = 0
        for obj in allObjects:
            if (obj.name == "dish"):
                if (obj.getProperty("isDirty") == True):
                    self.score -= 1
                    numDirtyDishes += 1

        # Check if the game is complete
        if (numDirtyDishes == 0):
            self.gameOver, self.gameWon = True, True

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Execute a game command.")
    parser.add_argument("commands", help="The command to execute in the game")
    args = parser.parse_args()

    print("Command received")
    # Random seed
    randomSeed = 0
    # Create a new game
    game = DishwasherGame(randomSeed=randomSeed)
    main(game, args.commands)