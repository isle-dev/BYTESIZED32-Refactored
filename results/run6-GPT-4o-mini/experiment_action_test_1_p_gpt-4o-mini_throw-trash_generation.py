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

class Milk(Substance):
    def __init__(self):
        Substance.__init__(self, "solid milk", "liquid milk", "gas milk", boilingPoint=100, meltingPoint=0, currentTemperatureCelsius=4)
        self.properties["temperature"] = 4  # Starting temperature of milk in Celsius

class Stove(Device):
    def __init__(self):
        Device.__init__(self, "stove")
        self.properties["max_temperature"] = 100  # Max temperature the stove can reach
        self.properties["temperature_increase_per_tick"] = 5  # Temperature increase per tick

class Fridge(Device):
    def __init__(self):
        Device.__init__(self, "fridge")
        self.properties["min_temperature"] = 0  # Min temperature the fridge can maintain
        self.properties["temperature_decrease_per_tick"] = 2  # Temperature decrease per tick

class Thermometer(GameObject):
    def __init__(self):
        GameObject.__init__(self, "thermometer")

    def makeDescriptionStr(self, makeDetailed=False):
        return "a thermometer to measure temperature"

class Baby(GameObject):
    def __init__(self):
        GameObject.__init__(self, "baby")

    def makeDescriptionStr(self, makeDetailed=False):
        return "a baby waiting to be fed"

# The agent (just a placeholder for a container for the inventory)
class Agent(Agent):
    def __init__(self, name):
        Agent.__init__(self, name)
        self.properties["has_milk"] = False

# The world is the root object of the game object tree.
class MilkHeatingWorld(World):
    def __init__(self):
        World.__init__(self, "kitchen")
        self.addObject(Kitchen())
        self.addObject(Stove())
        self.addObject(Fridge())
        self.addObject(Pot())
        self.addObject(Milk())
        self.addObject(Thermometer())
        self.addObject(Baby())

# The main game class
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
        world = MilkHeatingWorld()
        kitchen = world.contains[0]  # Get the kitchen
        fridge = world.contains[2]  # Get the fridge
        pot = world.contains[1]  # Get the pot
        milk = world.contains[4]  # Get the milk
        thermometer = world.contains[5]  # Get the thermometer
        baby = world.contains[6]  # Get the baby

        # Add objects to the kitchen
        kitchen.addObject(fridge)
        kitchen.addObject(pot)
        kitchen.addObject(milk)
        kitchen.addObject(thermometer)
        kitchen.addObject(baby)

        # Add the agent to the kitchen
        kitchen.addObject(self.agent)

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
                self.addAction("put " + objReferent + " on stove", ["put", obj, self.rootObject.contains[1]])  # Put on stove

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

    def actionUseThermometer(self, obj):
        if isinstance(obj, Milk):
            return f"The milk is currently at {obj.properties['temperature']} degrees Celsius."
        return "You can't use the thermometer on that."

    def actionFeedBaby(self):
        if self.agent.properties["has_milk"]:
            self.gameWon = True
            return "You feed the baby with the milk. The baby is happy!"
        return "You don't have milk to feed the baby."

    def step(self, actionStr):
        self.observationStr = ""
        reward = 0

        if actionStr not in self.possibleActions:
            self.observationStr = "I don't understand that."
            return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

        self.numSteps += 1

        actions = self.possibleActions[actionStr]
        action = actions[0] if len(actions) == 1 else actions[0]  # Take the first action

        actionVerb = action[0]

        action_map = {
            "look around": lambda: self.rootObject.makeDescriptionStr(),
            "inventory": self.actionInventory,
            "take": lambda: self.actionTake(action[1]),
            "put": lambda: self.actionPut(action[1], action[2]),
            "turn on": lambda: action[1].turnOn(),
            "turn off": lambda: action[1].turnOff(),
            "use thermometer": lambda: self.actionUseThermometer(action[1]),
            "feed baby": self.actionFeedBaby,
        }

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
        milk = self.rootObject.contains[4]  # Get the milk
        if milk.properties["temperature"] >= 37:  # Suitable temperature for a baby
            self.agent.properties["has_milk"] = True
            self.score += 1
        if self.gameWon:
            self.score += 10  # Bonus for winning

# Main Program
if __name__ == "__main__":
    randomSeed = 0
    game = MilkHeatingGame(randomSeed=randomSeed)
    main(game)
