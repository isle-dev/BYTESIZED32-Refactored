# milk_heating_simulation.py

from data.library.GameBasic import *

# A class representing the stove
class Stove(Device):
    def __init__(self, name):
        super().__init__(name)
        self.properties["max_temperature"] = 100  # Max temperature the stove can reach
        self.properties["temperature_increase_per_tick"] = 10  # Temperature increase per tick
        self.properties["isOn"] = False  # Initially off

    def tick(self):
        if self.properties["isOn"]:
            # Increase the temperature of the milk if the stove is on
            for obj in self.contains:
                if isinstance(obj, Milk):
                    obj.properties["temperature"] += self.properties["temperature_increase_per_tick"]
                    if obj.properties["temperature"] > self.properties["max_temperature"]:
                        obj.properties["temperature"] = self.properties["max_temperature"]

# A class representing the fridge
class Fridge(Device):
    def __init__(self, name):
        super().__init__(name)
        self.properties["min_temperature"] = 0  # Min temperature the fridge can reach
        self.properties["temperature_decrease_per_tick"] = 5  # Temperature decrease per tick
        self.properties["isOn"] = True  # Initially on

    def tick(self):
        if self.properties["isOn"]:
            # Decrease the temperature of the milk if it's in the fridge
            for obj in self.contains:
                if isinstance(obj, Milk):
                    obj.properties["temperature"] -= self.properties["temperature_decrease_per_tick"]
                    if obj.properties["temperature"] < self.properties["min_temperature"]:
                        obj.properties["temperature"] = self.properties["min_temperature"]

# A class representing the pot
class Pot(Container):
    def __init__(self, name):
        super().__init__(name)

# A class representing the milk
class Milk(Substance):
    def __init__(self):
        super().__init__("milk", "milk", "milk vapor", boilingPoint=100, meltingPoint=0, currentTemperatureCelsius=5)

# The world is the root object of the game object tree. In single room environments, it's where all the objects are located.
class KitchenWorld(World):
    def __init__(self):
        super().__init__("kitchen")

# The agent (just a placeholder for a container for the inventory)
class Agent(Container):
    def __init__(self):
        super().__init__("agent")

    def getReferents(self):
        return ["yourself"]

    def makeDescriptionStr(self, makeDetailed=False):
        return "yourself"

class MilkHeatingGame(TextGame):
    def __init__(self, randomSeed):
        super().__init__(randomSeed)

    # Create/initialize the world/environment for this game
    def initializeWorld(self):
        world = KitchenWorld()

        # Add the agent into the world (kitchen)
        world.addObject(self.agent)

        # Create and add the fridge, stove, pot, and milk
        fridge = Fridge("fridge")
        stove = Stove("stove")
        pot = Pot("pot")
        milk = Milk()

        # Add objects to the world
        world.addObject(fridge)
        world.addObject(stove)
        world.addObject(pot)
        fridge.addObject(milk)  # Milk starts in the fridge

        return world

    # Get the task description for this game
    def getTaskDescription(self):
        return "Your task is to heat the milk to a suitable temperature for the baby."

    # Returns a list of valid actions at the current time step
    def generatePossibleActions(self):
        allObjects = self.makeNameToObjectDict()
        self.possibleActions = {}

        # Actions with zero arguments
        for action in [("look around", "look around"), ("inventory", "inventory"), ("examine", "examine")]:
            self.addAction(action[0], [action[1]])

        # Actions with one object argument
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction(f"take {objReferent}", ["take", obj])
                self.addAction(f"put {objReferent}", ["put", obj])
                self.addAction(f"open {objReferent}", ["open", obj])
                self.addAction(f"close {objReferent}", ["close", obj])
                self.addAction(f"turn on {objReferent}", ["turn on", obj])
                self.addAction(f"turn off {objReferent}", ["turn off", obj])
                self.addAction(f"use thermometer on {objReferent}", ["use thermometer", obj])
                self.addAction(f"feed baby with {objReferent}", ["feed baby", obj])

        return self.possibleActions

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
        action = None

        # Check for an ambiguous action (i.e. one that has multiple possible arguments)
        if len(actions) > 1:
            action = actions[0]  # For simplicity, just take the first action
        else:
            action = actions[0]

        # Interpret the action
        actionVerb = action[0]

        action_map = {
            "look around": self.rootObject.makeDescriptionStr,
            "inventory": self.actionInventory,
            "examine": lambda: "You examine the objects in the kitchen.",
            "turn on": lambda obj: obj.turnOn(),
            "turn off": lambda obj: obj.turnOff(),
            "open": lambda obj: obj.openContainer(),
            "close": lambda obj: obj.closeContainer(),
            "take": lambda obj: self.actionTake(obj),
            "put": lambda obj: self.actionPut(obj, self.agent),
            "use thermometer": lambda obj: self.useThermometer(obj),
            "feed baby": lambda obj: self.feedBaby(obj)
        }

        # Catch-all
        self.observationStr = action_map.get(actionVerb, lambda obj: "ERROR: Unknown action.")(action[1])

        # Do one tick of the environment
        self.doWorldTick()
        # Calculate the score
        lastScore = self.score
        self.calculateScore()
        reward = self.score - lastScore

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    def useThermometer(self, obj):
        if isinstance(obj, Milk):
            temp = obj.properties["temperature"]
            if temp < 37:
                return "The milk is too cold."
            elif temp > 37:
                return "The milk is too hot."
            else:
                return "The milk is at a suitable temperature for the baby."
        return "You can't use the thermometer on that."

    def feedBaby(self, obj):
        if isinstance(obj, Milk) and obj.properties["temperature"] == 37:
            return "You feed the baby with the milk."
        return "You can't feed the baby with that."

    def calculateScore(self):
        self.score = 0
        allObjects = self.rootObject.getAllContainedObjectsRecursive()
        for obj in allObjects:
            if isinstance(obj, Milk) and obj.properties["temperature"] == 37:
                self.score += 1
                self.gameOver, self.gameWon = True, True

# Main Program
if __name__ == "__main__":
    # Set random seed 0 and Create a new game
    main(MilkHeatingGame(randomSeed=0))
