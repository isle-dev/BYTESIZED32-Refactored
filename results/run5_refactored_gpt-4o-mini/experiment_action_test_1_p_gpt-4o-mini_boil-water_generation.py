import random

class GameObject:
    def __init__(self, name):
        self.name = name
        self.properties = {}
        self.contains = []

    def addObject(self, obj):
        self.contains.append(obj)

    def getReferents(self):
        return [self.name]

    def makeDescriptionStr(self, makeDetailed=False):
        return self.name

class Container(GameObject):
    def __init__(self, name):
        super().__init__(name)
        self.properties["isContainer"] = True

    def openContainer(self):
        return f"You open the {self.name}.", True

    def closeContainer(self):
        return f"You close the {self.name}.", True

class Device(GameObject):
    def __init__(self, name):
        super().__init__(name)
        self.properties["isDevice"] = True
        self.properties["isOn"] = False

    def turnOn(self):
        self.properties["isOn"] = True
        return f"You turn on the {self.name}.", True

    def turnOff(self):
        self.properties["isOn"] = False
        return f"You turn off the {self.name}.", True

class Substance(GameObject):
    def __init__(self, name, temperature):
        super().__init__(name)
        self.properties["temperature"] = temperature

class Pot(Container):
    def __init__(self):
        super().__init__("pot")

class Milk(Substance):
    def __init__(self):
        super().__init__("milk", 4)  # Starting temperature in Celsius

class Stove(Device):
    def __init__(self):
        super().__init__("stove")
        self.properties["maxTemperature"] = 100  # Max temperature in Celsius
        self.properties["temperatureIncreasePerTick"] = 10  # Temperature increase per tick

    def tick(self):
        if self.properties["isOn"]:
            for obj in self.contains:
                if isinstance(obj, Milk):
                    new_temp = obj.properties["temperature"] + self.properties["temperatureIncreasePerTick"]
                    obj.properties["temperature"] = min(new_temp, self.properties["maxTemperature"])

class Fridge(Device):
    def __init__(self):
        super().__init__("fridge")
        self.properties["minTemperature"] = 0  # Min temperature in Celsius
        self.properties["temperatureDecreasePerTick"] = 2  # Temperature decrease per tick

    def tick(self):
        if self.properties["isOn"]:
            for obj in self.contains:
                if isinstance(obj, Milk):
                    new_temp = obj.properties["temperature"] - self.properties["temperatureDecreasePerTick"]
                    obj.properties["temperature"] = max(new_temp, self.properties["minTemperature"])

class Thermometer(GameObject):
    def __init__(self):
        super().__init__("thermometer")

    def useOn(self, obj):
        if isinstance(obj, Milk):
            return f"The milk temperature is {obj.properties['temperature']}°C."
        return "You can't use the thermometer on that."

class TextGame:
    def __init__(self, randomSeed):
        self.random = random.Random(randomSeed)
        self.score = 0
        self.gameOver = False
        self.gameWon = False
        self.numSteps = 0
        self.rootObject = self.initializeWorld()
        self.agent = GameObject("player")

    def initializeWorld(self):
        world = GameObject("kitchen")
        fridge = Fridge()
        stove = Stove()
        pot = Pot()
        milk = Milk()
        thermometer = Thermometer()

        fridge.addObject(milk)
        world.addObject(fridge)
        world.addObject(stove)
        world.addObject(pot)
        world.addObject(thermometer)

        return world

    def getTaskDescription(self):
        return "Your task is to heat milk to a suitable temperature for a baby."

    def generatePossibleActions(self):
        self.possibleActions = {
            "look around": ["look around"],
            "inventory": ["inventory"],
            "examine milk": ["examine", self.rootObject.contains[0].contains[0]],  # Milk
            "open fridge": ["open", self.rootObject.contains[0]],
            "take milk from fridge": ["take", self.rootObject.contains[0].contains[0]],
            "put pot on stove": ["put", self.rootObject.contains[0].contains[0], self.rootObject.contains[1]],
            "turn on stove": ["turn on", self.rootObject.contains[1]],
            "use thermometer on milk": ["use", self.rootObject.contains[0].contains[0], self.rootObject.contains[3]],
            "feed baby with milk": ["feed", self.rootObject.contains[0].contains[0]],
        }
        return self.possibleActions

    def step(self, actionStr):
        self.numSteps += 1
        if actionStr not in self.possibleActions:
            return "I don't understand that."

        action = self.possibleActions[actionStr]
        actionVerb = action[0]

        if actionVerb == "open":
            return action[1].openContainer()
        elif actionVerb == "take":
            return f"You take the {action[1].name}."
        elif actionVerb == "put":
            return f"You put the pot on the stove."
        elif actionVerb == "turn on":
            return action[1].turnOn()
        elif actionVerb == "use":
            return action[1].useOn(action[2])
        elif actionVerb == "feed":
            if action[1].properties["temperature"] >= 37:  # Suitable temperature for a baby
                self.gameWon = True
                return "You feed the baby with the milk. The baby is happy!"
            else:
                return "The milk is not warm enough to feed the baby."
        elif actionVerb == "look around":
            return "You are in a kitchen with a fridge, stove, and a pot."
        elif actionVerb == "inventory":
            return "You have a pot and a thermometer."
        elif actionVerb == "examine":
            return f"The milk temperature is {action[1].properties['temperature']}°C."

        return "Action not recognized."

    def tick(self):
        for obj in self.rootObject.contains:
            if isinstance(obj, Device):
                obj.tick()

    def calculateScore(self):
        if self.gameWon:
            self.score += 1

if __name__ == "__main__":
    game = TextGame(randomSeed=1)
    print(game.getTaskDescription())
    while not game.gameOver:
        action = input("Enter your action: ")
        result = game.step(action)
        print(result)
        game.tick()
        game.calculateScore()
        if game.gameWon:
            print("Congratulations! You've completed the task.")
            break
