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
        if obj not in self.contains:
            return f"The {obj.name} is not contained in the {self.name}.", None, False
        self.removeObject(obj)
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


class Stove(Container, Device):
    def __init__(self):
        super().__init__("stove")
        self.properties["maxTemperature"] = 100.0  # Max temperature for heating
        self.properties["temperatureIncreasePerTick"] = 10.0  # Temperature increase per tick

    def tick(self):
        if self.properties["isOn"]:
            for obj in self.contains:
                if isinstance(obj, Pot):
                    newTemperature = obj.properties["temperature"] + self.properties["temperatureIncreasePerTick"]
                    if newTemperature > self.properties["maxTemperature"]:
                        newTemperature = self.properties["maxTemperature"]
                    obj.properties["temperature"] = newTemperature


class Fridge(Container, Device):
    def __init__(self):
        super().__init__("fridge")
        self.properties["minTemperature"] = 0.0  # Min temperature for cooling
        self.properties["temperatureDecreasePerTick"] = 5.0  # Temperature decrease per tick

    def tick(self):
        if self.properties["isOn"]:
            for obj in self.contains:
                if isinstance(obj, Pot):
                    newTemperature = obj.properties["temperature"] - self.properties["temperatureDecreasePerTick"]
                    if newTemperature < self.properties["minTemperature"]:
                        newTemperature = self.properties["minTemperature"]
                    obj.properties["temperature"] = newTemperature


class Pot(Container):
    def __init__(self):
        super().__init__("pot")


class Milk(GameObject):
    def __init__(self):
        super().__init__("milk")
        self.properties["temperature"] = 20.0  # Initial temperature


class Thermometer(GameObject):
    def __init__(self):
        super().__init__("thermometer")

    def checkTemperature(self, obj):
        return f"The temperature of the {obj.getReferents()[0]} is {obj.properties['temperature']}°C."


class Baby(GameObject):
    def __init__(self):
        super().__init__("baby")


class TextGame:
    def __init__(self, randomSeed):
        self.random = random.Random(randomSeed)
        self.agent = GameObject("agent")
        self.rootObject = self.initializeWorld()
        self.score = 0
        self.numSteps = 0
        self.gameOver = False
        self.gameWon = False
        self.observationStr = self.rootObject.makeDescriptionStr()

    def initializeWorld(self):
        world = Container("kitchen")
        world.addObject(self.agent)

        stove = Stove()
        world.addObject(stove)

        fridge = Fridge()
        world.addObject(fridge)

        pot = Pot()
        world.addObject(pot)

        milk = Milk()
        fridge.addObject(milk)

        thermometer = Thermometer()
        world.addObject(thermometer)

        baby = Baby()
        world.addObject(baby)

        return world

    def getTaskDescription(self):
        return "Your task is to heat milk to a suitable temperature for a baby."

    def generatePossibleActions(self):
        actions = {
            "look around": ["look around"],
            "inventory": ["inventory"],
            "open fridge": ["open", self.rootObject.contains[1]],  # Fridge
            "take milk": ["take", self.rootObject.contains[1].contains[0]],  # Milk
            "put pot on stove": ["put", self.rootObject.contains[2], self.rootObject.contains[0]],  # Pot on Stove
            "turn on stove": ["turn on", self.rootObject.contains[0]],  # Stove
            "check temperature": ["use", self.rootObject.contains[3], self.rootObject.contains[2]],  # Thermometer on Pot
            "feed baby": ["feed", self.rootObject.contains[4]],  # Feed baby with milk
        }
        return actions

    def step(self, actionStr):
        self.observationStr = ""
        if actionStr == "look around":
            self.observationStr = self.rootObject.makeDescriptionStr()
        elif actionStr == "inventory":
            self.observationStr = "You have nothing in your inventory."
        elif actionStr == "open fridge":
            self.observationStr = self.rootObject.contains[1].openContainer()[0]
        elif actionStr == "take milk":
            self.observationStr = self.rootObject.contains[1].takeObjectFromContainer(self.rootObject.contains[1].contains[0])[0]
        elif actionStr == "put pot on stove":
            self.observationStr = self.rootObject.contains[2].placeObjectInContainer(self.rootObject.contains[0])[0]
        elif actionStr == "turn on stove":
            self.observationStr = self.rootObject.contains[0].turnOn()[0]
        elif actionStr == "check temperature":
            self.observationStr = self.rootObject.contains[3].checkTemperature(self.rootObject.contains[2])[0]
        elif actionStr == "feed baby":
            self.observationStr = "You feed the baby with milk."

        self.numSteps += 1
        self.doWorldTick()
        return self.observationStr

    def doWorldTick(self):
        for obj in self.rootObject.getAllContainedObjectsRecursive():
            if isinstance(obj, Device):
                obj.tick()

    def play(self):
        print("Task Description: " + self.getTaskDescription())
        print("Initial Observation: " + self.observationStr)

        while not self.gameOver:
            actionStr = input("> ")
            if actionStr in self.generatePossibleActions():
                self.observationStr = self.step(actionStr)
                print("Observation: " + self.observationStr)
            else:
                print("I don't understand that.")


def main():
    randomSeed = 0
    game = TextGame(randomSeed)
    game.play()


if __name__ == "__main__":
    main()
