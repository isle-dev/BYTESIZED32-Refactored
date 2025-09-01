# milk_heating_game.py

from data.library.GameBasic import *

# A pot to hold the milk
class Pot(Container):
    def __init__(self):
        Container.__init__(self, "pot")
        self.properties["isMoveable"] = True

    def makeDescriptionStr(self, makeDetailed=False):
        return "a pot containing milk"

# Milk substance
class Milk(Substance):
    def __init__(self):
        Substance.__init__(self, "solid milk", "liquid milk", "gas milk", boilingPoint=100, meltingPoint=0, currentTemperatureCelsius=5)  # Starting temperature is 5 degrees C

# A stove that heats the pot
class Stove(Device):
    def __init__(self):
        Device.__init__(self, "stove")
        self.properties["max_temperature"] = 100  # Maximum temperature the stove can reach
        self.properties["temperature_increase_per_tick"] = 5  # Temperature increase per tick

    def tick(self):
        if self.properties["isOn"]:
            # Increase the temperature of the pot if it's on
            containedObjects = self.getAllContainedObjectsRecursive()
            for obj in containedObjects:
                if isinstance(obj, Pot):
                    obj.contains[0].properties["temperature"] += self.properties["temperature_increase_per_tick"]
                    if obj.contains[0].properties["temperature"] > self.properties["max_temperature"]:
                        obj.contains[0].properties["temperature"] = self.properties["max_temperature"]

# A fridge that cools the milk
class Fridge(Device, Container):
    def __init__(self):
        Container.__init__(self, "fridge")
        Device.__init__(self, "fridge")
        self.properties["temperature_decrease_per_tick"] = 2  # Temperature decrease per tick
        self.properties["min_temperature"] = 0  # Minimum temperature the fridge can reach

    def tick(self):
        if self.properties["isOn"]:
            # Decrease the temperature of the milk if it's in the fridge
            containedObjects = self.getAllContainedObjectsRecursive()
            for obj in containedObjects:
                if isinstance(obj, Milk):
                    obj.properties["temperature"] -= self.properties["temperature_decrease_per_tick"]
                    if obj.properties["temperature"] < self.properties["min_temperature"]:
                        obj.properties["temperature"] = self.properties["min_temperature"]

# A thermometer to check the temperature of the milk
class Thermometer(GameObject):
    def __init__(self):
        GameObject.__init__(self, "thermometer")

    def useOn(self, obj):
        if isinstance(obj, Milk):
            return f"The milk is currently at {obj.properties['temperature']} degrees Celsius."
        return "You can't use the thermometer on that."

# Game class for heating milk
class HeatMilkGame(TextGame):
    def __init__(self, randomSeed):
        TextGame.__init__(self, randomSeed)

    def initializeWorld(self):
        world = World("kitchen")

        # Add the agent (the player) into the world
        world.addObject(self.agent)

        # Add a fridge
        fridge = Fridge()
        world.addObject(fridge)

        # Add a stove
        stove = Stove()
        world.addObject(stove)

        # Add a pot containing milk
        pot = Pot()
        milk = Milk()
        pot.addObject(milk)
        world.addObject(pot)

        # Add a thermometer
        thermometer = Thermometer()
        world.addObject(thermometer)

        return world

    def getTaskDescription(self):
        return "Your task is to heat the milk to a suitable temperature for a baby."

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
                self.addAction("turn on " + objReferent, ["turn on", obj])
                self.addAction("turn off " + objReferent, ["turn off", obj])
                self.addAction("examine " + objReferent, ["examine", obj])
                if isinstance(obj, Milk):
                    self.addAction("use thermometer on " + objReferent, ["use thermometer", obj])

        # Actions with two object arguments
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if obj1 != obj2:
                            if obj2.getProperty("isContainer"):
                                self.addAction("put " + objReferent1 + " in " + objReferent2, ["put", obj1, obj2])

        return self.possibleActions

    def actionUseThermometer(self, obj):
        if isinstance(obj, Milk):
            return obj.useOn(obj)
        return "You can't use the thermometer on that."

    def actionTurnOff(self, obj):
        if isinstance(obj, Device):
            obj.properties["isOn"] = False
            return f"You turned off the {obj.name}."
        return "You can't turn that off."

    def step(self, actionStr):
        self.observationStr = ""
        reward = 0

        if actionStr not in self.possibleActions:
            self.observationStr = "I don't understand that."
            return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

        self.numSteps += 1
        actions = self.possibleActions[actionStr]
        action = actions[0] if len(actions) == 1 else actions[0]  # Choose the first action for simplicity

        actionVerb = action[0]
        action_map = {
            "look around": self.rootObject.makeDescriptionStr,
            "inventory": self.actionInventory,
            "take": lambda: self.actionTake(action[1]),
            "turn on": lambda: self.actionTurnOn(action[1]),
            "turn off": lambda: self.actionTurnOff(action[1]),
            "examine": lambda: action[1].makeDescriptionStr(),
            "use thermometer": lambda: self.actionUseThermometer(action[1]),
            "put": lambda: self.actionPut(action[1], action[2]),
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
        # Baseline score
        self.score = 0

        # Check if the milk is at a suitable temperature
        allObjects = self.rootObject.getAllContainedObjectsRecursive()
        for obj in allObjects:
            if isinstance(obj, Milk) and obj.properties["temperature"] >= 37 and obj.properties["temperature"] <= 40:
                self.score = 1  # Score 1 if the milk is at a suitable temperature
                self.gameOver = True
                self.gameWon = True

# Main Program
if __name__ == "__main__":
    randomSeed = 0
    game = HeatMilkGame(randomSeed=randomSeed)
    main(game)
