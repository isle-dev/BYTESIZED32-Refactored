# refactored wash-clothes.py
# # Success Haonan Wang and Ziang Xiao(Nov 2024)

from data.library.GameBasic import *

# A washing machine, which is a device that can hold clothes. 
class WashingMachine(Container, Device):
    def __init__(self):
        GameObject.__init__(self, "washing machine")
        Container.__init__(self, "washing machine")
        Device.__init__(self, "washing machine")
        self.properties["isOpenable"] = True
        self.properties["isOpen"] = False
        self.properties["isMoveable"] = False

        self.properties["cycleStage"] = 0  # The current stage of the washing machine's cycle.
        self.properties["finishedCycle"] = False

    # Try to turn on the washing machine.
    def turnOn(self):
        if self.properties["isOpen"]:
            return ("The " + self.name + " is opened, so it can't be turned on.", False)
        return super().turnOn()

    # Process tick updates
    def tick(self):
        # If the washing machine is opened, turn it off and reset
        if self.properties["isOpen"]:
            self.properties.update({"isOn": False, "finishedCycle": False, "cycleStage": 0})

        # If the washing machine is on, wash the clothes
        if self.properties["isOn"]:
            if self.properties["cycleStage"] < 3:
                self.properties["cycleStage"] += 1

            # Stage 1: Check for detergent and wash clothes
            if self.properties["cycleStage"] == 2:
                containsDetergent = any(obj.name == "detergent" for obj in self.getAllContainedObjectsRecursive())
                if containsDetergent:
                    for obj in self.getAllContainedObjectsRecursive():
                        if isinstance(obj, Clothes):
                            obj.properties['isDirty'] = False

                # Mark clothes wet
                for obj in self.getAllContainedObjectsRecursive():
                    if isinstance(obj, Clothes):
                        obj.properties['isWet'] = True

            # Stage 2: Finish the cycle and turn off
            elif self.properties["cycleStage"] == 3:
                self.properties["finishedCycle"] = True
                self.properties["cycleStage"] = 0
                self.turnOff()

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a washing machine"
        if self.properties["finishedCycle"]:
            outStr += " with a blinking green light"

        if self.properties["isOn"]:
            outStr += " that is currently on"
        else:
            if self.properties["isOpen"]:
                outStr += " that is currently open"
                if len(self.contains) == 0:
                    outStr += " and empty"
                else:
                    if not makeDetailed:
                        outStr += " and contains one or more items."
                    else:
                        outStr += " and contains the following items: \n"
                        for obj in self.contains:
                            outStr += "\t" + obj.makeDescriptionStr() + "\n"
            else:
                outStr += " that is currently closed"
        return outStr

# A dryer, which is a device that can hold clothes.
class Dryer(Container, Device):
    def __init__(self):
        GameObject.__init__(self, "dryer")
        Container.__init__(self, "dryer")
        Device.__init__(self, "dryer")

        self.properties["isOpenable"] = True
        self.properties["isOpen"] = False
        self.properties["isMoveable"] = False

        self.properties["cycleStage"] = 0  # The current stage of the dryer's cycle.
        self.properties["finishedCycle"] = False

    def turnOn(self):
        if self.properties["isOpen"]:
            return ("The " + self.name + " is opened, so it can't be turned on.", False)
        return super().turnOn()

    def tick(self):
        # If the dryer is opened, then it automatically turns off and resets
        if (self.properties["isOpen"] == True):
            self.properties["isOn"] = False
            self.properties["finishedCycle"] = False
            self.properties["cycleStage"] = 0

        # If the dryer is on, then dry the clothes
        if (self.properties["isOn"] == True):
            # Increment the cycle stage
            if (self.properties["cycleStage"] < 3):
                self.properties["cycleStage"] += 1

            # Check for stage 1
            if self.properties["cycleStage"] == 2:
                # Clothes become dry
                for obj in self.getAllContainedObjectsRecursive():
                    if (type(obj) == Clothes):
                        obj.properties['isWet'] = False

            # Check for stage 2
            elif self.properties["cycleStage"] == 3:
                # Set the dryer to finished
                self.properties["finishedCycle"] = True
                self.properties["cycleStage"] = 0
                # Turn off the dryer
                self.turnOff()

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a dryer"
        if self.properties["finishedCycle"]:
            outStr += " with a blinking green light"

        if self.properties["isOn"]:
            outStr += " that is currently on"
        else:
            if self.properties["isOpen"]:
                outStr += " that is currently open"
                if len(self.contains) == 0:
                    outStr += " and empty"
                else:
                    if not makeDetailed:
                        outStr += " and contains one or more items."
                    else:
                        outStr += " and contains the following items: \n"
                        for obj in self.contains:
                            outStr += "\t" + obj.makeDescriptionStr() + "\n"
            else:
                outStr += " that is currently closed"
        return outStr

class Clothes(GameObject):
    def __init__(self, name, isDirty=True, isWet=False):
        GameObject.__init__(self, name)

        self.properties["isDirty"] = isDirty
        self.properties["isWet"] = isWet

    def getReferents(self):
        is_dirty = "dirty " if self.properties["isDirty"] else "clean "
        is_wet = "wet " if self.properties["isWet"] else "dry "
        return [self.name, f"{is_dirty}{self.name}", f"{is_wet}{self.name}", f"{is_dirty}{is_wet}{self.name}"]

    def makeDescriptionStr(self, makeDetailed=False):
        is_dirty = "dirty " if self.properties["isDirty"] else "clean "
        is_wet = "wet " if self.properties["isWet"] else "dry "
        return f"a {is_dirty}{is_wet}{self.name}"

class DetergentBottle(Device):
    def __init__(self):
        Device.__init__(self, "bottle of detergent")

    def useWithObject(self, patientObject):
        if (patientObject.name == "washing machine"):
            # Add a squirt of soap to the dishwasher
            patientObject.addObject(Detergent())
            return ("You add some detergent into the washing machine.", True)
        return ("You're not sure how to use the " + self.name + " with the " + patientObject.name + ".", False)

    def makeDescriptionStr(self, makeDetailed=False):
        return "a bottle of detergent"

class Detergent(GameObject):
    def __init__(self):
        GameObject.__init__(self, "detergent")

class Basket(Container):
    def __init__(self):
        GameObject.__init__(self, "basket")
        Container.__init__(self, "basket")
        self.properties["isMoveable"] = False
        self.properties["isOpenable"] = False

    def makeDescriptionStr(self, makeDetailed=False):
        return f"a {self.name}"

class RoomWorld(World):
    def __init__(self):
        World.__init__(self, "room")

# Game Implementation
class WashClothesGame(TextGame):
    def __init__(self, randomSeed):
        TextGame.__init__(self, randomSeed)

    def initializeWorld(self):
        world = RoomWorld()

        world.addObject(self.agent)

        washing_machine = WashingMachine()
        world.addObject(washing_machine)

        dryer = Dryer()
        world.addObject(dryer)

        detergent_bottle = DetergentBottle()
        world.addObject(detergent_bottle)

        clothes_names = ["shirt", "coat", "jacket", "dress", "skirt", "vest", "sweater"]
        self.random.shuffle(clothes_names)

        self.num_dirty_clothes = self.random.randint(3, 5)

        for i in range(self.num_dirty_clothes):
            clothes = Clothes(clothes_names[i])
            world.addObject(clothes)

        for i in range(self.num_dirty_clothes, len(clothes_names)):
            clothes = Clothes(clothes_names[i], isDirty=False)
            world.addObject(clothes)

        basket = Basket()
        world.addObject(basket)

        return world

    def getTaskDescription(self):
        return "Your task is to wash the dirty clothes and dry them."

    def generatePossibleActions(self):
        # Get a list of all game objects that could serve as arguments to actions
        allObjects = self.makeNameToObjectDict()

        # Make a dictionary whose keys are possible action strings, and whose values are lists that contain the arguments.
        self.possibleActions = {}
        # Zero-argument actions
        for action in [("look around", "look around"), ("look", "look around"), ("inventory", "inventory"),
                       ("wait", "wait")]:
            self.addAction(action[0], [action[1]])

        for objReferent, objs in allObjects.items():
            for obj in objs:
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

        # Dictionary of actions mapped to their corresponding methods
        action_map = {
            "look around": lambda: self.rootObject.makeDescriptionStr(),
            "inventory": lambda: self.actionInventory(),
            "wait": lambda: "You wait.",
            "examine": lambda: action[1].makeDescriptionStr(makeDetailed=True),
            "open": lambda: self.actionOpen(action[1]),
            "close": lambda: self.actionClose(action[1]),
            "take": lambda: self.actionTake(action[1]),
            "turn on": lambda: self.actionTurnOn(action[1]),
            "turn off": lambda: self.actionTurnOff(action[1]),
            "put": lambda: self.actionPut(action[1], action[2]),
            "use": lambda: self.actionUse(action[1], action[2]),
        }

        # Get the appropriate action handler, or return an error if not found
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
        allObjects = self.rootObject.getAllContainedObjectsRecursive()
        all_complete = all((not obj.getProperty("isDirty") and not obj.getProperty("isWet") and obj.parentContainer.name == 'basket') for obj in allObjects if isinstance(obj, Clothes))

        if all_complete:
            self.score = 1
            self.gameOver = True
            self.gameWon = True

if __name__ == "__main__":
    randomSeed = 0
    game = WashClothesGame(randomSeed=randomSeed)
    main(game)