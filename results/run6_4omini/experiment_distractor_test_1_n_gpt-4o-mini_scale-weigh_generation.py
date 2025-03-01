# MilkHeatingGame.py
from data.library.GameBasic import *

# A class representing the milk with a temperature property
class Milk(GameObject):
    def __init__(self):
        GameObject.__init__(self, "milk")
        self.properties["temperature"] = 4.0  # Starting temperature in Celsius
        self.properties["max_temperature"] = 100.0  # Max temperature for boiling

    def makeDescriptionStr(self, makeDetailed=False):
        return f"some milk at {self.properties['temperature']}°C"

# A class representing a pot that can hold milk
class Pot(Container):
    def __init__(self):
        Container.__init__(self, "pot")

# A class representing a stove that can heat the pot
class Stove(Device):
    def __init__(self):
        Device.__init__(self, "stove")
        self.properties["temperature_increase_per_tick"] = 5.0  # Increase temperature by 5°C per tick
        self.properties["max_temperature"] = 100.0  # Max temperature for the stove

# A class representing a fridge that can cool the milk
class Fridge(Device):
    def __init__(self):
        Device.__init__(self, "fridge")
        self.properties["temperature_decrease_per_tick"] = 2.0  # Decrease temperature by 2°C per tick
        self.properties["min_temperature"] = 0.0  # Min temperature for the fridge

# A class representing a thermometer that can measure the temperature of the milk
class Thermometer(GameObject):
    def __init__(self):
        GameObject.__init__(self, "thermometer")

    def useWithObject(self, milk):
        return f"The thermometer reads {milk.properties['temperature']}°C."

# The world is the root object of the game object tree.  In single room environments, it's where all the objects are located.
class KitchenWorld(World):
    def __init__(self):
        World.__init__(self, "kitchen")

class MilkHeatingGame(TextGame):
    def __init__(self, randomSeed):
        TextGame.__init__(self, randomSeed)

    def initializeWorld(self):
        world = KitchenWorld()

        # Add the agent
        world.addObject(self.agent)

        # Create and add the fridge, stove, pot, milk, and thermometer
        fridge = Fridge()
        stove = Stove()
        pot = Pot()
        milk = Milk()
        thermometer = Thermometer()

        # Add objects to the world
        world.addObject(fridge)
        world.addObject(stove)
        world.addObject(pot)
        pot.addObject(milk)  # Put milk in the pot
        world.addObject(thermometer)

        return world

    # Get the task description for this game
    def getTaskDescription(self):
        return "Your task is to heat the milk to a suitable temperature for a baby."

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
                self.addAction(f"take {objReferent}", ["take", obj])
                self.addAction(f"examine {objReferent}", ["examine", obj])
                if isinstance(obj, Milk):
                    self.addAction(f"use thermometer on {objReferent}", ["use thermometer", obj])
                if isinstance(obj, Stove):
                    self.addAction(f"turn on {objReferent}", ["turn on", obj])
                    self.addAction(f"turn off {objReferent}", ["turn off", obj])
                if isinstance(obj, Fridge):
                    self.addAction(f"turn on {objReferent}", ["turn on", obj])
                    self.addAction(f"turn off {objReferent}", ["turn off", obj])
                if isinstance(obj, Pot):
                    self.addAction(f"put {objReferent} on stove", ["put", obj, stove])

        return self.possibleActions

    # Performs an action in the environment, returns the result (a string observation, the reward, and whether the game is completed).
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

        # Mapping action verbs to corresponding functions
        action_map = {
            "look around": lambda: self.rootObject.makeDescriptionStr(),
            "inventory": self.actionInventory,
            "examine": lambda: action[1].makeDescriptionStr(makeDetailed=True),
            "take": lambda: self.actionTake(action[1]),
            "put": lambda: self.actionPut(action[1], action[2]),
            "turn on": lambda: action[1].turnOn(),
            "turn off": lambda: action[1].turnOff(),
            "use thermometer": lambda: action[1].useWithObject(action[2]),
        }

        self.observationStr = action_map.get(actionVerb, lambda: "ERROR: Unknown action.")()

        # Do one tick of the environment
        self.doWorldTick()

        # Calculate the score
        lastScore = self.score
        self.calculateScore()
        reward = self.score - lastScore

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    # Call the object update for each object in the environment
    def doWorldTick(self):
        # Get the milk object
        milk = self.rootObject.containsItemWithName("milk")[0]
        stove = self.rootObject.containsItemWithName("stove")[0]
        fridge = self.rootObject.containsItemWithName("fridge")[0]

        # If the stove is on, increase the milk temperature
        if stove.getProperty("isOn"):
            milk.properties["temperature"] += stove.properties["temperature_increase_per_tick"]
            if milk.properties["temperature"] > stove.properties["max_temperature"]:
                milk.properties["temperature"] = stove.properties["max_temperature"]

        # If the fridge is on, decrease the milk temperature
        if fridge.getProperty("isOn"):
            milk.properties["temperature"] -= fridge.properties["temperature_decrease_per_tick"]
            if milk.properties["temperature"] < fridge.properties["min_temperature"]:
                milk.properties["temperature"] = fridge.properties["min_temperature"]

    # Calculate the game score
    def calculateScore(self):
        # Baseline score
        self.score = 0
        milk = self.rootObject.containsItemWithName("milk")[0]
        if milk.properties["temperature"] >= 37.0 and milk.properties["temperature"] <= 40.0:
            self.score += 1
            self.gameWon, self.gameOver = True, True

if __name__ == "__main__":
    # Set random seed 1 and Create a new game
    main(MilkHeatingGame(1))
