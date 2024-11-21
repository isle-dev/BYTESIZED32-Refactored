# refactored make-ice-cubes.py
# Process

from GameBasic import *

# A freezer, which is a cooling device. It contains things inside of it. It progressively cools them down to some temperature.
class Freezer(Container, Device):
    def __init__(self):
        super().__init__("freezer")
        self.properties["isOpenable"] = True
        self.properties["isOpen"] = False  # A freezer starts out closed
        self.properties["isMoveable"] = False  # A freezer is too heavy to move (and doesn't really need to be moved for this simulation)

        self.properties["isOn"] = True
        self.properties["isActivatable"] = False  # A freezer essentially never is turned off (unless it's unplugged, which is irelevant for this simulation)

        self.properties["minTemperature"] = -4.0
        self.properties["tempDecreasePerTick"] = 5.0

    def tick(self):
        if self.properties["isOn"] and not self.properties["isOpen"]:
            for obj in self.getAllContainedObjectsRecursive():
                newTemperature = max(obj.properties["temperature"] - self.properties["tempDecreasePerTick"],
                                     self.properties["minTemperature"])
                obj.properties["temperature"] = newTemperature

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a freezer"
        if not self.properties["isOn"]:
            outStr += " that is currently off"
        else:
            outStr += f" that is currently {'open' if self.properties['isOpen'] else 'closed'}"
            if self.properties["isOpen"] and len(self.contains) > 0:
                if makeDetailed:
                    outStr += " and contains the following items:\n"
                    for obj in self.contains:
                        outStr += "\t" + obj.makeDescriptionStr() + "\n"
                else:
                    outStr += " and contains one or more items."
        return outStr


class IceCubeTray(Container):
    def __init__(self):
        GameObject.__init__(self, "ice cube tray")
        Container.__init__(self, "ice cube tray")

    def makeDescriptionStr(self, makeDetailed=False):
        contents = [obj.makeDescriptionStr() for obj in self.contains]
        outStr = "an ice cube tray"
        if contents:
            outStr += " that looks to have " + ", ".join(contents) + " in it"
        else:
            outStr += " that is empty"
        return outStr


class Water(Substance):
    def __init__(self):
        Substance.__init__(self, "ice", "water", "steam", boilingPoint=100, meltingPoint=0, currentTemperatureCelsius=20)
        self.tick()

class Sink(Container, Device):
    def __init__(self):
        GameObject.__init__(self, "sink")
        Container.__init__(self, "sink")
        Device.__init__(self, "sink")

    def tick(self):
        if self.properties["isOn"]:
            for obj in self.getAllContainedObjectsRecursive():
                if isinstance(obj, Container) and len(obj.containsItemWithName("water"))==0 :
                    obj.addObject(Water())

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = f"a sink that is currently {'on' if self.properties['isOn'] else 'off'}"
        if len(self.contains) == 0:
            outStr += " and that is empty"
        else:
            if makeDetailed:
                outStr += " and that contains the following items:\n"
                for obj in self.contains:
                    outStr += "\t" + obj.makeDescriptionStr() + "\n"
            else:
                outStr += " and that contains one or more items."
        return outStr

class Pot(Container):
    # Constructor.
    def __init__(self):
        GameObject.__init__(self, "pot")
        Container.__init__(self, "pot")

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a pot"

        effectiveContents = []
        for obj in self.contains:
            effectiveContents.append(obj.makeDescriptionStr())

        if (len(effectiveContents) > 0):
            outStr += " that looks to have "
            for i in range(len(effectiveContents)):
                if (i == len(effectiveContents) - 1) and (len(effectiveContents) > 1):
                    outStr += "and "
                outStr += effectiveContents[i] + ", "
            outStr = outStr[:-2] + " " + self.properties["containerPrefix"] + " it"
        else:
            outStr += " that is empty"

        return outStr

class Food(GameObject):
    def __init__(self, foodName):
        GameObject.__init__(self, foodName)
        self.properties["isFood"] = True

    def makeDescriptionStr(self, makeDetailed=False):
        return "a " + self.name


class KitchenWorld(World):
    def __init__(self):
        World.__init__(self, "kitchen")

class MakeIceCubesGame(TextGame):
    def __init__(self, randomSeed):
        TextGame.__init__(self, randomSeed)

    def initializeWorld(self):
        world = KitchenWorld()

        # Add the agent
        world.addObject(self.agent)

        # Add a freezer with an ice cube tray
        freezer = Freezer()
        iceCubeTray = IceCubeTray()
        freezer.addObject(iceCubeTray)
        world.addObject(freezer)

        # Add a sink
        sink = Sink()
        world.addObject(sink)

        # Add a pot
        pot = Pot()
        world.addObject(pot)

        # Distractor items
        foodNames = ["apple", "orange", "banana", "pizza", "peanut butter", "sandwhich", "pasta", "bell pepper"]
        self.random.shuffle(foodNames)
        for i in range(self.random.randint(1, 3)):
            world.addObject(Food(foodNames[i % len(foodNames)]))

        return world

    def getTaskDescription(self):
        return "Your task is to make ice cubes."

    def generatePossibleActions(self):
        # Get a list of all game objects that could serve as arguments to actions
        allObjects = self.makeNameToObjectDict()

        # Make a dictionary whose keys are possible action strings, and whose values are lists that contain the arguments.
        self.possibleActions = {}

        # Zero-argument actions
        for action in [("look around", "look around"), ("look", "look around"), ("inventory", "inventory")]:
            self.addAction(action[0], [action[1]])

        # Add actions not covered by the superclass
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
                # Actions with two object arguments
                # (2-arg) Put
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if (obj1 != obj2):
                            containerPrefix = "in"
                            if obj2.properties["isContainer"]:
                                containerPrefix = obj2.properties["containerPrefix"]
                            self.addAction("put " + objReferent1 + " " + containerPrefix + " " + objReferent2,
                                           ["put", obj1, obj2])
                            self.addAction("use " + objReferent1 + " on " + objReferent2, ["use", obj1, obj2])

        return self.possibleActions

    def actionEat(self, obj):
        if obj.parentContainer != self.agent:
            return "You don't currently have the " + obj.getReferents()[0] + " in your inventory."
        if obj.getProperty("isFood"):
            obsStr, _, success = obj.parentContainer.takeObjectFromContainer(obj)
            return "You eat the " + obj.name if success else "You can't see that."
        return "You can't eat that."

    def actionOpen(self, obj):
        return obj.openContainer()[0] if obj.getProperty("isContainer") else "You can't open that."

    def actionClose(self, obj):
        return obj.closeContainer()[0] if obj.getProperty("isContainer") else "You can't close that."

    def actionTurnOn(self, obj):
        return obj.turnOn()[0] if obj.getProperty("isDevice") else "You can't turn on that."

    def actionTurnOff(self, obj):
        return obj.turnOff()[0] if obj.getProperty("isDevice") else "You can't turn off that."

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

        # Mapping action verbs to corresponding functions
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

        # Execute the mapped function or return an error if action is unknown
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
        if any(obj.name == "ice cube tray" and any(item.name == "ice" for item in obj.contains) for obj in allObjects):
            self.score += 1
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
    game = MakeIceCubesGame(randomSeed=randomSeed)
    main(game, args.commands)