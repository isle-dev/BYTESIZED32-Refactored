# milk_heating_game.py

from data.library.GameBasic import *

# A stove
class Stove(Device):
    def __init__(self):
        Device.__init__(self, "stove")
        self.properties["maxTemperature"] = 100.0  # Maximum temperature the stove can reach
        self.properties["temperatureIncreasePerTick"] = 5.0  # Temperature increase per tick when on
        self.properties["isOn"] = False  # Initially off

    def tick(self):
        if self.properties["isOn"]:
            # Increase the temperature of the pot on the stove
            for obj in self.contains:
                if isinstance(obj, Pot):
                    obj.properties["temperature"] += self.properties["temperatureIncreasePerTick"]
                    if obj.properties["temperature"] > self.properties["maxTemperature"]:
                        obj.properties["temperature"] = self.properties["maxTemperature"]

# A fridge
class Fridge(Device):
    def __init__(self):
        Device.__init__(self, "fridge")
        self.properties["minTemperature"] = 0.0  # Minimum temperature the fridge can reach
        self.properties["temperatureDecreasePerTick"] = 2.0  # Temperature decrease per tick when on
        self.properties["isOn"] = True  # Initially on

    def tick(self):
        if self.properties["isOn"]:
            # Decrease the temperature of the milk inside the fridge
            for obj in self.contains:
                if isinstance(obj, Milk):
                    obj.properties["temperature"] -= self.properties["temperatureDecreasePerTick"]
                    if obj.properties["temperature"] < self.properties["minTemperature"]:
                        obj.properties["temperature"] = self.properties["minTemperature"]

# A pot
class Pot(Container):
    def __init__(self):
        Container.__init__(self, "pot")
        self.properties["temperature"] = 20.0  # Initial temperature of the pot

# Milk
class Milk(GameObject):
    def __init__(self):
        GameObject.__init__(self, "milk")
        self.properties["temperature"] = 5.0  # Initial temperature of the milk

# A thermometer
class Thermometer(GameObject):
    def __init__(self):
        GameObject.__init__(self, "thermometer")

    def checkTemperature(self, milk):
        return milk.properties["temperature"]

# The world is the root object of the game object tree.  In single room environments, it's where all the objects are located.
class KitchenWorld(World):
    def __init__(self):
        World.__init__(self, "kitchen")

class MilkHeatingGame(TextGame):
    def __init__(self, randomSeed):
        super().__init__(randomSeed)

    # Create/initialize the world/environment for this game
    def initializeWorld(self):
        world = KitchenWorld()

        # Add the agent
        world.addObject(self.agent)

        # Add a stove
        stove = Stove()
        world.addObject(stove)

        # Add a fridge
        fridge = Fridge()
        world.addObject(fridge)

        # Add a pot
        pot = Pot()
        world.addObject(pot)

        # Add milk
        milk = Milk()
        pot.addObject(milk)  # Place milk in the pot

        # Add a thermometer
        thermometer = Thermometer()
        world.addObject(thermometer)

        return world

    # Get the task description for this game
    def getTaskDescription(self):
        return "Your task is to heat the milk to a suitable temperature for a baby using the stove."

    # Generate possible actions
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
                self.addAction("open " + objReferent, ["open", obj])
                self.addAction("close " + objReferent, ["close", obj])
                self.addAction("turn on " + objReferent, ["turn on", obj])
                self.addAction("turn off " + objReferent, ["turn off", obj])
                if isinstance(obj, Milk):
                    self.addAction("use thermometer on " + objReferent, ["use thermometer", obj])

        # Actions with two object arguments
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if obj1 != obj2:
                            if isinstance(obj1, Pot) and isinstance(obj2, Stove):
                                self.addAction("put " + objReferent1 + " on " + objReferent2, ["put", obj1, obj2])
                            if isinstance(obj1, Thermometer) and isinstance(obj2, Milk):
                                self.addAction("check temperature of " + objReferent2 + " with " + objReferent1, ["check temperature", obj2, obj1])

        return self.possibleActions

    # Perform an action in the environment
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

        action_map = {
            "look around": self.rootObject.makeDescriptionStr,
            "inventory": self.actionInventory,
            "take": lambda: self.actionTake(action[1]),
            "examine": lambda: f"The {action[1].name} is at {action[1].properties['temperature']} degrees Celsius.",
            "open": lambda: action[1].openContainer(),
            "close": lambda: action[1].closeContainer(),
            "turn on": lambda: action[1].turnOn(),
            "turn off": lambda: action[1].turnOff(),
            "put": lambda: self.actionPut(action[1], action[2]),
            "check temperature": lambda: f"The temperature of the milk is {action[1].checkTemperature(action[2])} degrees Celsius."
        }

        self.observationStr = action_map.get(actionVerb, lambda: "ERROR: Unknown action.")()

        # Do one tick of the environment
        self.doWorldTick()

        # Calculate the score
        lastScore = self.score
        self.calculateScore()
        reward = self.score - lastScore

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    # Calculate the game score
    def calculateScore(self):
        allObjects = self.rootObject.getAllContainedObjectsRecursive()
        for obj in allObjects:
            if isinstance(obj, Milk):
                if obj.properties["temperature"] >= 37.0 and obj.properties["temperature"] <= 40.0:
                    self.score += 1
                    self.gameOver = True
                    self.gameWon = True
                elif obj.properties["temperature"] > 40.0:
                    self.score = 0
                    self.gameOver = True
                    self.gameWon = False

if __name__ == "__main__":
    # Set random seed 0 and Create a new game
    main(MilkHeatingGame(randomSeed=0))
