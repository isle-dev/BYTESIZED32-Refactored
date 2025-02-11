import random

class GameObject:
    def __init__(self, name):
        self.name = name
        self.properties = {}
        self.contains = []

    def addObject(self, obj):
        self.contains.append(obj)

    def makeDescriptionStr(self, makeDetailed=False):
        return self.name

    def getReferents(self):
        return [self.name]

class Container(GameObject):
    def __init__(self, name):
        super().__init__(name)
        self.properties["isContainer"] = True

    def openContainer(self):
        if self.properties.get("isOpenable", False):
            self.properties["isOpen"] = True
            return f"You open the {self.name}.", True
        return f"You can't open the {self.name}.", False

    def closeContainer(self):
        if self.properties.get("isOpenable", False):
            self.properties["isOpen"] = False
            return f"You close the {self.name}.", True
        return f"You can't close the {self.name}.", False

class Device(GameObject):
    def __init__(self, name):
        super().__init__(name)
        self.properties["isDevice"] = True

    def turnOn(self):
        self.properties["isOn"] = True
        return f"You turn on the {self.name}.", True

    def turnOff(self):
        self.properties["isOn"] = False
        return f"You turn off the {self.name}.", True

class Substance(GameObject):
    def __init__(self, solidName, liquidName, gasName, boilingPoint, meltingPoint, currentTemperatureCelsius):
        super().__init__(liquidName)
        self.solidName = solidName
        self.liquidName = liquidName
        self.gasName = gasName
        self.boilingPoint = boilingPoint
        self.meltingPoint = meltingPoint
        self.properties["temperature"] = currentTemperatureCelsius

class Milk(Substance):
    def __init__(self):
        super().__init__("frozen milk", "milk", "steam", boilingPoint=100, meltingPoint=0, currentTemperatureCelsius=4)

class Pot(Container):
    def __init__(self):
        super().__init__("pot")
        self.properties["isOpenable"] = True

class Stove(Device):
    def __init__(self):
        super().__init__("stove")
        self.properties["isOn"] = False
        self.properties["temperature_increase_per_tick"] = 5  # degrees Celsius
        self.properties["max_temperature"] = 100  # degrees Celsius

    def tick(self):
        if self.properties["isOn"]:
            for obj in self.getAllContainedObjectsRecursive():
                if isinstance(obj, Milk):
                    obj.properties["temperature"] = min(obj.properties["temperature"] + self.properties["temperature_increase_per_tick"], self.properties["max_temperature"])

class Fridge(Device, Container):
    def __init__(self):
        super().__init__("fridge")
        self.properties["isOpenable"] = True
        self.properties["isOn"] = True
        self.properties["temperature_decrease_per_tick"] = 2  # degrees Celsius

    def tick(self):
        if self.properties["isOn"]:
            for obj in self.getAllContainedObjectsRecursive():
                if isinstance(obj, Milk):
                    obj.properties["temperature"] = max(obj.properties["temperature"] - self.properties["temperature_decrease_per_tick"], 0)

class Thermometer(GameObject):
    def __init__(self):
        super().__init__("thermometer")

    def useOn(self, obj):
        if isinstance(obj, Milk):
            return f"The milk temperature is {obj.properties['temperature']}°C."
        return "You can't use the thermometer on that."

class Baby(GameObject):
    def __init__(self):
        super().__init__("baby")

class TextGame:
    def __init__(self, randomSeed):
        self.random = random.Random(randomSeed)
        self.score = 0
        self.numSteps = 0
        self.gameOver = False
        self.gameWon = False
        self.agent = GameObject("player")
        self.rootObject = self.initializeWorld()
        self.possibleActions = {}

    def initializeWorld(self):
        world = GameObject("kitchen")
        fridge = Fridge()
        stove = Stove()
        pot = Pot()
        milk = Milk()
        thermometer = Thermometer()
        baby = Baby()

        fridge.addObject(milk)
        world.addObject(fridge)
        world.addObject(stove)
        world.addObject(pot)
        world.addObject(thermometer)
        world.addObject(baby)

        return world

    def getTaskDescription(self):
        return "Your task is to heat milk to a suitable temperature for a baby."

    def generatePossibleActions(self):
        allObjects = self.makeNameToObjectDict()
        self.possibleActions = {}

        for action in [("look around", "look around"), ("inventory", "inventory")]:
            self.addAction(action[0], [action[1]])

        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction("take " + objReferent, ["take", obj])
                self.addAction("open " + objReferent, ["open", obj])
                self.addAction("close " + objReferent, ["close", obj])
                self.addAction("examine " + objReferent, ["examine", obj])
                self.addAction("turn on " + objReferent, ["turn on", obj])
                self.addAction("turn off " + objReferent, ["turn off", obj])
                self.addAction("use thermometer on " + objReferent, ["use thermometer", obj])
                self.addAction("feed baby with milk", ["feed baby", obj])

        return self.possibleActions

    def addAction(self, actionStr, actionArgs):
        self.possibleActions[actionStr] = actionArgs

    def step(self, actionStr):
        self.numSteps += 1
        if actionStr not in self.possibleActions:
            return "I don't understand that."

        actions = self.possibleActions[actionStr]
        action = actions[0]

        action_map = {
            "look around": lambda: self.rootObject.makeDescriptionStr(),
            "inventory": lambda: "You have: " + ", ".join([obj.name for obj in self.agent.contains]),
            "examine": lambda: action[1].makeDescriptionStr(makeDetailed=True),
            "take": lambda: self.actionTake(action[1]),
            "open": lambda: action[1].openContainer()[0],
            "close": lambda: action[1].closeContainer()[0],
            "turn on": lambda: action[1].turnOn()[0],
            "turn off": lambda: action[1].turnOff()[0],
            "use thermometer": lambda: thermometer.useOn(action[1]),
            "feed baby": lambda: self.actionFeedBaby(action[1])
        }

        observationStr = action_map.get(action[0], lambda: "ERROR: Unknown action.")()
        self.doWorldTick()
        self.calculateScore()

        return observationStr

    def actionFeedBaby(self, obj):
        if isinstance(obj, Milk) and obj.properties["temperature"] >= 37 and obj.properties["temperature"] <= 40:
            self.gameOver = True
            self.gameWon = True
            return "You feed the baby with the milk. The baby is happy!"
        return "The milk is not at a suitable temperature to feed the baby."

    def actionTake(self, obj):
        if obj in self.rootObject.contains:
            self.agent.addObject(obj)
            self.rootObject.contains.remove(obj)
            return f"You take the {obj.name}."
        return "You can't take that."

    def doWorldTick(self):
        for obj in self.rootObject.contains:
            if isinstance(obj, Device):
                obj.tick()

    def calculateScore(self):
        if self.gameWon:
            self.score += 1

    def makeNameToObjectDict(self):
        nameToObject = {}
        for obj in self.rootObject.contains:
            nameToObject[obj.name] = nameToObject.get(obj.name, []) + [obj]
        return nameToObject

if __name__ == "__main__":
    game = TextGame(randomSeed=0)
    print(game.getTaskDescription())
    while not game.gameOver:
        action = input("Enter your action: ")
        result = game.step(action)
        print(result)
