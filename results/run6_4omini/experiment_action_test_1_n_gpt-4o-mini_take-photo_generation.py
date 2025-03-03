# milk_heating_simulation.py
from data.library.GameBasic import *
import random

# A pot that can hold milk
class Pot(Container):
    def __init__(self):
        Container.__init__(self, "pot")
        self.properties["isContainer"] = True
        self.properties["temperature"] = 20.0  # Starting temperature of the milk

    def makeDescriptionStr(self, makeDetailed=False):
        return f"A pot containing milk at {self.properties['temperature']} degrees Celsius."


# A stove that can heat the pot
class Stove(Device):
    def __init__(self):
        Device.__init__(self, "stove")
        self.properties["maxTemperature"] = 100.0  # Max temperature the stove can reach
        self.properties["temperatureIncreasePerTick"] = 5.0  # Temperature increase per tick
        self.properties["isOn"] = False

    def tick(self):
        if self.properties["isOn"]:
            # Increase the temperature of the pot if it's on
            for obj in self.contains:
                if isinstance(obj, Pot):
                    obj.properties["temperature"] += self.properties["temperatureIncreasePerTick"]
                    if obj.properties["temperature"] > self.properties["maxTemperature"]:
                        obj.properties["temperature"] = self.properties["maxTemperature"]

    def makeDescriptionStr(self, makeDetailed=False):
        return f"The stove is currently {'on' if self.properties['isOn'] else 'off'}."


# A fridge that can cool the pot
class Fridge(Device):
    def __init__(self):
        Device.__init__(self, "fridge")
        self.properties["minTemperature"] = 0.0  # Min temperature the fridge can reach
        self.properties["temperatureDecreasePerTick"] = 2.0  # Temperature decrease per tick
        self.properties["isOn"] = True

    def tick(self):
        if self.properties["isOn"]:
            # Decrease the temperature of the pot if it's in the fridge
            for obj in self.contains:
                if isinstance(obj, Pot):
                    obj.properties["temperature"] -= self.properties["temperatureDecreasePerTick"]
                    if obj.properties["temperature"] < self.properties["minTemperature"]:
                        obj.properties["temperature"] = self.properties["minTemperature"]

    def makeDescriptionStr(self, makeDetailed=False):
        return f"The fridge is currently {'on' if self.properties['isOn'] else 'off'}."


# The world is the root object of the game object tree. In this case, it's the kitchen.
class KitchenWorld(World):
    def __init__(self):
        super().__init__("kitchen")


class HeatMilkGame(TextGame):
    def __init__(self, randomSeed):
        TextGame.__init__(self, randomSeed)

    # Create/initialize the world/environment for this game
    def initializeWorld(self):
        world = KitchenWorld()

        # Add the agent
        world.addObject(self.agent)

        # Add a stove
        self.stove = Stove()
        world.addObject(self.stove)

        # Add a fridge
        self.fridge = Fridge()
        world.addObject(self.fridge)

        # Add a pot with milk
        self.pot = Pot()
        world.addObject(self.pot)

        return world

    # Get the task description for this game
    def getTaskDescription(self):
        return "Your task is to heat the milk in the pot to a suitable temperature for a baby."

    # Returns a list of valid actions at the current time step
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
                self.addAction("put " + objReferent + " on stove", ["put", obj, self.stove])
                self.addAction("put " + objReferent + " in fridge", ["put", obj, self.fridge])

        # Actions with two object arguments
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if (obj1 != obj2):
                            self.addAction("use thermometer on " + objReferent1, ["use thermometer", obj1])
                            self.addAction("feed baby with " + objReferent1, ["feed baby", obj1])

        return self.possibleActions

    # Perform the "use thermometer" action
    def actionUseThermometer(self, obj):
        if isinstance(obj, Pot):
            return f"The milk is currently at {obj.properties['temperature']} degrees Celsius."
        return "You can't use the thermometer on that."

    # Perform the "feed baby" action
    def actionFeedBaby(self, obj):
        if isinstance(obj, Pot) and obj.properties['temperature'] >= 37.0:
            return "You feed the baby with the milk. The baby is happy!"
        return "The milk is not at a suitable temperature for the baby."

    # Performs an action in the environment, returns the result (a string observation, the reward, and whether the game is completed).
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
        action = actions[0]  # For simplicity, just take the first action

        actionVerb = action[0]

        actions = {
            "look around": lambda: self.rootObject.makeDescriptionStr(),
            "inventory": lambda: self.actionInventory(),
            "take": lambda: self.actionTake(action[1]),
            "examine": lambda: action[1].makeDescriptionStr(makeDetailed=True),
            "turn on": lambda: action[1].turnOn(),
            "turn off": lambda: action[1].turnOff(),
            "put": lambda: self.actionPut(action[1], action[2]),
            "use thermometer": lambda: self.actionUseThermometer(action[1]),
            "feed baby": lambda: self.actionFeedBaby(action[1]),
        }

        # Catch-all
        self.observationStr = actions.get(actionVerb, lambda: "ERROR: Unknown action.")()

        # Do one tick of the environment
        self.doWorldTick()

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)


# Main Program
if __name__ == "__main__":
    randomSeed = 0
    game = HeatMilkGame(randomSeed=randomSeed)
    main(game)
