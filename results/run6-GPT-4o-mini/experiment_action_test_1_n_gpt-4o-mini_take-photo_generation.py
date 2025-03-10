# milk_heating_simulation.py
from data.library.GameBasic import *
import random

# A stove that heats up objects placed on it.
class Stove(Device):
    def __init__(self):
        Device.__init__(self, "stove")
        self.properties["maxTemperature"] = 100.0  # Maximum temperature the stove can reach
        self.properties["temperatureIncreasePerTick"] = 5.0  # Temperature increase per tick
        self.properties["isOn"] = False  # Initially off

    def tick(self):
        if self.properties["isOn"]:
            # Increase the temperature of any pot on the stove
            for obj in self.contains:
                if isinstance(obj, Pot):
                    obj.properties["temperature"] += self.properties["temperatureIncreasePerTick"]
                    if obj.properties["temperature"] > self.properties["maxTemperature"]:
                        obj.properties["temperature"] = self.properties["maxTemperature"]

# A fridge that cools down objects placed inside it.
class Fridge(Device):
    def __init__(self):
        Device.__init__(self, "fridge")
        self.properties["minTemperature"] = 0.0  # Minimum temperature the fridge can reach
        self.properties["temperatureDecreasePerTick"] = 2.0  # Temperature decrease per tick
        self.properties["isOn"] = True  # Always on

    def tick(self):
        # Decrease the temperature of any milk inside the fridge
        for obj in self.contains:
            if isinstance(obj, Milk):
                obj.properties["temperature"] -= self.properties["temperatureDecreasePerTick"]
                if obj.properties["temperature"] < self.properties["minTemperature"]:
                    obj.properties["temperature"] = self.properties["minTemperature"]

# A pot that can hold milk.
class Pot(Container):
    def __init__(self):
        Container.__init__(self, "pot")
        self.properties["isContainer"] = True
        self.properties["temperature"] = 20.0  # Initial temperature of the pot

# A milk object with a specific temperature.
class Milk(GameObject):
    def __init__(self):
        GameObject.__init__(self, "milk")
        self.properties["temperature"] = 5.0  # Initial temperature of the milk

# A thermometer that can be used to check the temperature of objects.
class Thermometer(Device):
    def __init__(self):
        Device.__init__(self, "thermometer")

    def checkTemperature(self, obj):
        return obj.properties["temperature"]

# The world is the root object of the game object tree. In this case, it's the kitchen.
class KitchenWorld(World):
    def __init__(self):
        super().__init__("kitchen")

# The main game class for heating milk.
class HeatMilkGame(TextGame):
    def __init__(self, randomSeed):
        TextGame.__init__(self, randomSeed)

    def initializeWorld(self):
        world = KitchenWorld()

        # Add the agent
        world.addObject(self.agent)

        # Add a stove and a fridge
        self.stove = Stove()
        self.fridge = Fridge()
        world.addObject(self.stove)
        world.addObject(self.fridge)

        # Add a pot and milk
        self.pot = Pot()
        self.milk = Milk()
        world.addObject(self.pot)
        world.addObject(self.milk)

        # Put the milk in the fridge
        self.fridge.addObject(self.milk)

        return world

    def getTaskDescription(self):
        return "Your task is to heat the milk to a suitable temperature for a baby using the stove."

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
                self.addAction("open " + objReferent, ["open", obj])
                self.addAction("close " + objReferent, ["close", obj])
                self.addAction("examine " + objReferent, ["examine", obj])
                self.addAction("turn on " + objReferent, ["turn on", obj])
                self.addAction("turn off " + objReferent, ["turn off", obj])
                if isinstance(obj, Pot):
                    self.addAction("put pot on stove", ["put", self.pot, self.stove])

        # Actions with two object arguments
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if (obj1 != obj2):
                            self.addAction("put " + objReferent1 + " in " + objReferent2, ["put", obj1, obj2])

        # Use thermometer
        self.addAction("use thermometer on milk", ["use", self.thermometer, self.milk])

        return self.possibleActions

    def actionUse(self, deviceObj, patientObject):
        if isinstance(deviceObj, Thermometer) and isinstance(patientObject, Milk):
            temperature = deviceObj.checkTemperature(patientObject)
            return f"The milk is currently at {temperature} degrees Celsius."
        return "You can't use that."

    def step(self, actionStr):
        self.observationStr = ""
        reward = 0

        if actionStr not in self.possibleActions:
            self.observationStr = "I don't understand that."
            return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

        self.numSteps += 1

        actions = self.possibleActions[actionStr]
        action = actions[0]  # For simplicity, just take the first action

        actionVerb = action[0]

        actions = {
            "look around": lambda: self.rootObject.makeDescriptionStr(),
            "inventory": lambda: self.actionInventory(),
            "take": lambda: self.actionTake(action[1]),
            "open": lambda: self.actionOpen(action[1]),
            "close": lambda: self.actionClose(action[1]),
            "examine": lambda: action[1].makeDescriptionStr(makeDetailed=True),
            "turn on": lambda: self.actionTurnOn(action[1]),
            "turn off": lambda: self.actionTurnOff(action[1]),
            "put": lambda: self.actionPut(action[1], action[2]),
            "use": lambda: self.actionUse(action[1], action[2]),
        }

        self.observationStr = actions.get(actionVerb, lambda: "ERROR: Unknown action.")()

        # Do one tick of the environment
        self.doWorldTick()

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    def calculateScore(self):
        if self.milk.properties["temperature"] >= 37.0:  # Suitable temperature for a baby
            self.score = 1
            self.gameOver = True
            self.gameWon = True

# Main Program
def main(game):
    possibleActions = game.generatePossibleActions()
    print("Task Description: " + game.getTaskDescription())
    print("")
    print("Initial Observation: " + game.observationStr)
    print("")
    print("Type 'help' for a list of possible actions.")
    print("")

    while True:
        actionStr = ""
        while ((len(actionStr) == 0) or (actionStr == "help")):
            actionStr = input("> ")
            if (actionStr == "help"):
                print("Possible actions: " + str(possibleActions.keys()))
                print("")
                actionStr = ""
            elif (actionStr == "exit") or (actionStr == "quit"):
                return

        observationStr, score, reward, gameOver, gameWon = game.step(actionStr)

        possibleActions = game.generatePossibleActions()

        print("Observation: " + observationStr)
        print("")
        print("Current step: " + str(game.numSteps))
        print("Score: " + str(score))
        print("Game Over: " + str(gameOver))
        print("Game Won: " + str(gameWon))
        print("")
        print("----------------------------------------")

# Run the main program
if __name__ == "__main__":
    randomSeed = 0
    game = HeatMilkGame(randomSeed=randomSeed)
    main(game)
