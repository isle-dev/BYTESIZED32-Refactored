import random

class GameObject():
    def __init__(self, name):
        self.name = name
        self.parentContainer = None
        self.contains = []
        self.properties = {}
        self.properties["isContainer"] = False
        self.properties["isMoveable"] = True
        self.properties["temperature"] = 20.0  # Default temperature

    def getProperty(self, propertyName):
        return self.properties.get(propertyName, None)

    def addObject(self, obj):
        obj.removeSelfFromContainer()
        self.contains.append(obj)
        obj.parentContainer = self

    def removeObject(self, obj):
        self.contains.remove(obj)
        obj.parentContainer = None

    def removeSelfFromContainer(self):
        if self.parentContainer is not None:
            self.parentContainer.removeObject(self)

    def getAllContainedObjectsRecursive(self):
        outList = []
        for obj in self.contains:
            outList.append(obj)
            outList.extend(obj.getAllContainedObjectsRecursive())
        return outList

    def getReferents(self):
        return [self.name]

    def makeDescriptionStr(self, makeDetailed=False):
        return self.name


class Container(GameObject):
    def __init__(self, name):
        super().__init__(name)
        self.properties["isContainer"] = True
        self.properties["isOpenable"] = True
        self.properties["isOpen"] = True

    def openContainer(self):
        if not self.getProperty("isOpenable"):
            return f"The {self.name} can't be opened.", False
        if self.getProperty("isOpen"):
            return f"The {self.name} is already open.", False
        self.properties["isOpen"] = True
        return f"The {self.name} is now open.", True

    def closeContainer(self):
        if not self.getProperty("isOpenable"):
            return f"The {self.name} can't be closed.", False
        if not self.getProperty("isOpen"):
            return f"The {self.name} is already closed.", False
        self.properties["isOpen"] = False
        return f"The {self.name} is now closed.", True

    def placeObjectInContainer(self, obj):
        if not self.getProperty("isContainer"):
            return f"The {self.name} is not a container.", False
        if not self.getProperty("isOpen"):
            return f"The {self.name} is closed.", False
        self.addObject(obj)
        return f"The {obj.getReferents()[0]} is placed in the {self.name}.", True

    def takeObjectFromContainer(self, obj):
        if not self.getProperty("isContainer"):
            return f"The {self.name} is not a container.", None, False
        if not self.getProperty("isOpen"):
            return f"The {self.name} is closed.", None, False
        if obj not in self.contains:
            return f"The {obj.name} is not contained in the {self.name}.", None, False
        obj.removeSelfFromContainer()
        return f"The {obj.getReferents()[0]} is removed from the {self.name}.", obj, True


class Device(GameObject):
    def __init__(self, name):
        super().__init__(name)
        self.properties["isDevice"] = True
        self.properties["isActivatable"] = True
        self.properties["isOn"] = False

    def turnOn(self):
        if not self.getProperty("isActivatable"):
            return f"It's not clear how the {self.getReferents()[0]} could be turned on.", False
        if self.properties["isOn"]:
            return f"The {self.getReferents()[0]} is already on.", False
        self.properties["isOn"] = True
        return f"The {self.getReferents()[0]} is now turned on.", True

    def turnOff(self):
        if not self.getProperty("isActivatable"):
            return f"It's not clear how the {self.getReferents()[0]} could be turned off.", False
        if not self.properties["isOn"]:
            return f"The {self.getReferents()[0]} is already off.", False
        self.properties["isOn"] = False
        return f"The {self.getReferents()[0]} is now turned off.", True


class Stove(Device):
    def __init__(self):
        super().__init__("stove")
        self.properties["maxTemperature"] = 100.0  # Max temperature the stove can reach
        self.properties["temperature_increase_per_tick"] = 5.0  # Temperature increase per tick

    def tick(self):
        if self.properties["isOn"]:
            # Increase the temperature of the pot on the stove
            containedObjects = self.getAllContainedObjectsRecursive()
            for obj in containedObjects:
                if isinstance(obj, Pot):
                    newTemperature = obj.properties["temperature"] + self.properties["temperature_increase_per_tick"]
                    if newTemperature > self.properties["maxTemperature"]:
                        newTemperature = self.properties["maxTemperature"]
                    obj.properties["temperature"] = newTemperature


class Fridge(Container, Device):
    def __init__(self):
        super().__init__("fridge")
        self.properties["isOpenable"] = True
        self.properties["isOpen"] = False
        self.properties["temperature_decrease_per_tick"] = 5.0  # Temperature decrease per tick

    def tick(self):
        if self.properties["isOn"] and not self.properties["isOpen"]:
            containedObjects = self.getAllContainedObjectsRecursive()
            for obj in containedObjects:
                if isinstance(obj, Milk):
                    newTemperature = obj.properties["temperature"] - self.properties["temperature_decrease_per_tick"]
                    obj.properties["temperature"] = max(newTemperature, 0)  # Prevent negative temperature


class Pot(Container):
    def __init__(self):
        super().__init__("pot")
        self.properties["isOpenable"] = False  # A pot is not openable


class Milk(GameObject):
    def __init__(self):
        super().__init__("milk")
        self.properties["temperature"] = 4.0  # Starting temperature of milk


class Thermometer(GameObject):
    def __init__(self):
        super().__init__("thermometer")

    def useOn(self, obj):
        if isinstance(obj, Milk):
            return f"The milk temperature is {obj.properties['temperature']}°C."
        return "You can't use the thermometer on that."


class World(Container):
    def __init__(self):
        super().__init__("kitchen")

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "You find yourself in a kitchen. In the kitchen, you see:\n"
        for obj in self.contains:
            outStr += f"\t{obj.makeDescriptionStr()}\n"
        return outStr


class Agent(Container):
    def __init__(self):
        super().__init__("agent")

    def getReferents(self):
        return ["yourself"]

    def makeDescriptionStr(self, makeDetailed=False):
        return "yourself"


class TextGame:
    def __init__(self, randomSeed):
        self.random = random.Random(randomSeed)
        self.agent = Agent()
        self.rootObject = self.initializeWorld()
        self.score = 0
        self.numSteps = 0
        self.gameOver = False
        self.gameWon = False
        self.observationStr = self.rootObject.makeDescriptionStr()
        self.calculateScore()

    def initializeWorld(self):
        world = World()
        world.addObject(self.agent)

        fridge = Fridge()
        world.addObject(fridge)

        stove = Stove()
        world.addObject(stove)

        pot = Pot()
        world.addObject(pot)

        milk = Milk()
        fridge.addObject(milk)

        thermometer = Thermometer()
        world.addObject(thermometer)

        return world

    def getTaskDescription(self):
        return "Your task is to heat milk to a suitable temperature for a baby."

    def generatePossibleActions(self):
        allObjects = self.rootObject.getAllContainedObjectsRecursive()
        self.possibleActions = {}

        # Actions with zero arguments
        self.addAction("look around", ["look around"])
        self.addAction("inventory", ["inventory"])

        # Actions with one object argument
        for obj in allObjects:
            self.addAction(f"examine {obj.name}", ["examine", obj])
            self.addAction(f"take {obj.name}", ["take", obj])
            self.addAction(f"open {obj.name}", ["open", obj])
            self.addAction(f"close {obj.name}", ["close", obj])
            self.addAction(f"turn on {obj.name}", ["turn on", obj])
            self.addAction(f"turn off {obj.name}", ["turn off", obj])
            if isinstance(obj, Milk):
                self.addAction(f"use thermometer on {obj.name}", ["use thermometer", obj])
            if isinstance(obj, Pot):
                self.addAction(f"put pot on stove", ["put", obj, stove])

        return self.possibleActions

    def addAction(self, actionStr, actionArgs):
        if actionStr not in self.possibleActions:
            self.possibleActions[actionStr] = []
        self.possibleActions[actionStr].append(actionArgs)

    def actionTake(self, obj):
        if obj.parentContainer != self.agent:
            obsStr = obj.parentContainer.takeObjectFromContainer(obj)[0]
            self.agent.addObject(obj)
            return obsStr + f" You put the {obj.getReferents()[0]} in your inventory."
        return "You can't take that."

    def actionOpen(self, obj):
        if isinstance(obj, Container):
            return obj.openContainer()[0]
        return "You can't open that."

    def actionClose(self, obj):
        if isinstance(obj, Container):
            return obj.closeContainer()[0]
        return "You can't close that."

    def actionTurnOn(self, obj):
        if isinstance(obj, Device):
            return obj.turnOn()[0]
        return "You can't turn on that."

    def actionTurnOff(self, obj):
        if isinstance(obj, Device):
            return obj.turnOff()[0]
        return "You can't turn off that."

    def actionUseThermometer(self, obj):
        if isinstance(obj, Milk):
            return Thermometer().useOn(obj)
        return "You can't use the thermometer on that."

    def actionPut(self, objToMove, newContainer):
        if isinstance(newContainer, Container):
            return newContainer.placeObjectInContainer(objToMove)[0]
        return "You can't put things in that."

    def actionInventory(self):
        inventory = self.agent.contains
        if len(inventory) == 0:
            return "Your inventory is empty."
        return "You have the following items in your inventory:\n" + "\n".join([obj.makeDescriptionStr() for obj in inventory])

    def step(self, actionStr):
        self.observationStr = ""
        if actionStr not in self.possibleActions:
            self.observationStr = "I don't understand that."
            return self.observationStr, self.score, self.gameOver, self.gameWon

        self.numSteps += 1
        actions = self.possibleActions[actionStr]
        action = actions[0]  # Take the first action for simplicity

        actionVerb = action[0]
        if actionVerb == "look around":
            self.observationStr = self.rootObject.makeDescriptionStr()
        elif actionVerb == "inventory":
            self.observationStr = self.actionInventory()
        elif actionVerb.startswith("examine"):
            self.observationStr = action[1].makeDescriptionStr()
        elif actionVerb.startswith("take"):
            self.observationStr = self.actionTake(action[1])
        elif actionVerb.startswith("open"):
            self.observationStr = self.actionOpen(action[1])
        elif actionVerb.startswith("close"):
            self.observationStr = self.actionClose(action[1])
        elif actionVerb.startswith("turn on"):
            self.observationStr = self.actionTurnOn(action[1])
        elif actionVerb.startswith("turn off"):
            self.observationStr = self.actionTurnOff(action[1])
        elif actionVerb.startswith("use thermometer"):
            self.observationStr = self.actionUseThermometer(action[1])
        elif actionVerb.startswith("put"):
            self.observationStr = self.actionPut(action[1], action[2])

        self.doWorldTick()
        self.calculateScore()

        return self.observationStr, self.score, self.gameOver, self.gameWon

    def doWorldTick(self):
        allObjects = self.rootObject.getAllContainedObjectsRecursive()
        for obj in allObjects:
            if isinstance(obj, Stove):
                obj.tick()
            elif isinstance(obj, Fridge):
                obj.tick()

    def calculateScore(self):
        self.score = 0
        allObjects = self.rootObject.getAllContainedObjectsRecursive()
        for obj in allObjects:
            if isinstance(obj, Milk) and obj.properties["temperature"] >= 37.0:  # Suitable temperature for a baby
                self.score += 1
                self.gameOver = True
                self.gameWon = True


def main():
    randomSeed = 0
    game = TextGame(randomSeed=randomSeed)
    print("Task Description: " + game.getTaskDescription())
    print("Initial Observation: " + game.observationStr)
    print("Type 'help' for a list of possible actions.")

    while not game.gameOver:
        actionStr = input("> ")
        if actionStr == "help":
            print("Possible actions: " + str(game.generatePossibleActions().keys()))
            continue
        observationStr, score, gameOver, gameWon = game.step(actionStr)
        print("Observation: " + observationStr)
        print("Score: " + str(score))
        print("Game Over: " + str(gameOver))
        print("Game Won: " + str(gameWon))
        print("----------------------------------------")


if __name__ == "__main__":
    main()
