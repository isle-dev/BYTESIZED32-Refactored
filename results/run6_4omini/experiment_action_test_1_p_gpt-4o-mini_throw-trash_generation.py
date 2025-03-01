# MilkHeatingGame.py

from data.library.GameBasic import *

# A Room
class Kitchen(Container):
    def __init__(self):
        Container.__init__(self, "kitchen")

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = f"You find yourself in the {self.name}. In the {self.name}, you see:\n"
        for obj in self.contains:
            outStr += "\t" + obj.makeDescriptionStr() + "\n"
        return outStr

class Pot(Container):
    def __init__(self):
        Container.__init__(self, "pot")
        self.properties["isContainer"] = True

    def makeDescriptionStr(self, makeDetailed=False):
        return "a pot containing milk"

class Milk(Substance):
    def __init__(self):
        Substance.__init__(self, "solid milk", "liquid milk", "gas milk", boilingPoint=100, meltingPoint=0, currentTemperatureCelsius=5)
        self.properties["temperature"] = 5  # Initial temperature in fridge

class Stove(Device):
    def __init__(self):
        Device.__init__(self, "stove")
        self.properties["max_temperature"] = 100  # Max temperature the stove can reach
        self.properties["temperature_increase_per_tick"] = 5  # Temperature increase per tick

class Fridge(Device):
    def __init__(self):
        Device.__init__(self, "fridge")
        self.properties["min_temperature"] = 0  # Min temperature the fridge can maintain
        self.properties["temperature_decrease_per_tick"] = 1  # Temperature decrease per tick

class Thermometer(GameObject):
    def __init__(self):
        GameObject.__init__(self, "thermometer")

    def checkTemperature(self, milk):
        return milk.properties["temperature"]

class Baby(GameObject):
    def __init__(self):
        GameObject.__init__(self, "baby")

class MilkHeatingGame(TextGame):
    def __init__(self, randomSeed):
        self.random = random.Random(randomSeed)
        self.agent = Agent("agent")
        self.rootObject = self.initializeWorld()
        self.score = 0
        self.numSteps = 0
        self.gameOver = False
        self.gameWon = False
        self.observationStr = self.rootObject.makeDescriptionStr()
        self.calculateScore()

    def initializeWorld(self):
        world = Kitchen()
        stove = Stove()
        fridge = Fridge()
        pot = Pot()
        milk = Milk()
        thermometer = Thermometer()
        baby = Baby()

        # Add objects to the kitchen
        world.addObject(stove)
        world.addObject(fridge)
        world.addObject(pot)
        pot.addObject(milk)
        world.addObject(thermometer)
        world.addObject(baby)

        return world

    def getTaskDescription(self):
        return "Your task is to heat the milk to a suitable temperature for the baby using the stove."

    def generatePossibleActions(self):
        allObjects = self.makeNameToObjectDict()
        self.possibleActions = {}

        # Actions with zero arguments
        for action in [("look around", "look around"), ("inventory", "inventory")]:
            self.addAction(action[0], [action[1]])

        # Actions with one object argument
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction("take " + objReferent, ["take", obj])
                self.addAction("examine " + objReferent, ["examine", obj])
                self.addAction("turn on " + objReferent, ["turn on", obj])
                self.addAction("turn off " + objReferent, ["turn off", obj])
                self.addAction("use thermometer on " + objReferent, ["use thermometer", obj])

        # Actions with two object arguments
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if obj1 != obj2 and obj2.getProperty("isContainer"):
                            containerPrefix = obj2.properties["containerPrefix"]
                            self.addAction("put " + objReferent1 + " " + containerPrefix + " " + objReferent2,
                                           ["put", obj1, obj2])

        return self.possibleActions

    def actionUseThermometer(self, milk):
        thermometer = self.rootObject.containsItemWithName("thermometer")[0]
        temperature = thermometer.checkTemperature(milk)
        return f"The milk is currently at {temperature} degrees Celsius."

    def actionFeedBaby(self, milk):
        if milk.properties["temperature"] >= 37:  # Suitable temperature for baby
            self.gameWon = True
            return "You feed the baby with the milk. The baby is happy!"
        else:
            return "The milk is not warm enough for the baby."

    def step(self, actionStr):
        self.observationStr = ""
        reward = 0

        if actionStr not in self.possibleActions:
            self.observationStr = "I don't understand that."
            return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

        self.numSteps += 1
        actions = self.possibleActions[actionStr]
        action = actions[0] if len(actions) == 1 else actions[0]  # Choose the first action

        actionVerb = action[0]
        action_map = {
            "look around": lambda: self.rootObject.makeDescriptionStr(),
            "inventory": self.actionInventory,
            "take": lambda: self.actionTake(action[1]),
            "examine": lambda: self.actionUseThermometer(action[1]),
            "turn on": lambda: action[1].turnOn(),
            "turn off": lambda: action[1].turnOff(),
            "put": lambda: self.actionPut(action[1], action[2]),
            "use thermometer": lambda: self.actionUseThermometer(action[1]),
            "feed baby": lambda: self.actionFeedBaby(action[1]),
        }

        self.observationStr = action_map.get(actionVerb, lambda: "ERROR: Unknown action.")()

        # Do one tick of the environment
        self.doWorldTick()

        # Calculate the score
        lastScore = self.score
        self.calculateScore()
        reward = self.score - lastScore

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    def doWorldTick(self):
        # Increase the temperature of the milk if the stove is on
        stove = self.rootObject.containsItemWithName("stove")[0]
        milk = self.rootObject.containsItemWithName("milk")[0]

        if stove.getProperty("isOn"):
            currentTemp = milk.properties["temperature"]
            newTemp = min(currentTemp + stove.properties["temperature_increase_per_tick"], stove.properties["max_temperature"])
            milk.properties["temperature"] = newTemp

        # Decrease the temperature of the milk if it's in the fridge
        fridge = self.rootObject.containsItemWithName("fridge")[0]
        if fridge.getProperty("isOn"):
            currentTemp = milk.properties["temperature"]
            newTemp = max(currentTemp - fridge.properties["temperature_decrease_per_tick"], fridge.properties["min_temperature"])
            milk.properties["temperature"] = newTemp

    def calculateScore(self):
        if self.gameWon:
            self.score = 1
            self.gameOver = True
        elif self.numSteps > 20:  # Arbitrary limit for steps
            self.score = 0
            self.gameOver = True

# Main Program
if __name__ == "__main__":
    randomSeed = 0
    game = MilkHeatingGame(randomSeed=randomSeed)
    main(game)
