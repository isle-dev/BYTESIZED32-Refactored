# milk_heating_game.py

from data.library.GameBasic import *

# A stove, which is a heating device. It holds things on its surface. When turned on, it progressively heats things up to some temperature.
class Stove(Container, Device):
    def __init__(self):
        GameObject.__init__(self, "stove")
        Container.__init__(self, "stove")
        Device.__init__(self, "stove")

        self.properties["containerPrefix"] = "on"
        self.properties["isOpenable"] = False  # A stove is not openable
        self.properties["isMoveable"] = False  # A stove is too heavy to move

        # Set critical properties
        self.properties["maxTemperature"] = 100.0  # Maximum temperature of the stove (in degrees Celsius)
        self.properties["temperatureIncreasePerTick"] = 10.0  # How much the temperature increases per tick (in degrees Celsius)

    # If the stove is on, increase the temperature of anything on the stove, up to the maximum temperature.
    def tick(self):
        if self.properties["isOn"]:
            objectsOnStove = self.getAllContainedObjectsRecursive()
            for obj in objectsOnStove:
                if isinstance(obj, Substance):
                    newTemperature = obj.properties["temperature"] + self.properties["temperatureIncreasePerTick"]
                    obj.properties["temperature"] = min(newTemperature, self.properties["maxTemperature"])

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a stove that is currently " + ("on" if self.properties["isOn"] else "off")
        if len(self.contains) == 0:
            outStr += " and has nothing " + self.properties["containerPrefix"] + " it."
        else:
            if not makeDetailed:
                outStr += " and has one or more items " + self.properties["containerPrefix"] + " it."
            else:
                outStr += " and has the following items " + self.properties["containerPrefix"] + " it:\n"
                for obj in self.contains:
                    outStr += "\t" + obj.makeDescriptionStr() + "\n"
        return outStr


# A fridge, which is a cooling device. It can hold items and cool them down.
class Fridge(Container, Device):
    def __init__(self):
        GameObject.__init__(self, "fridge")
        Container.__init__(self, "fridge")
        Device.__init__(self, "fridge")

        self.properties["isOpenable"] = True  # A fridge can be opened
        self.properties["isMoveable"] = False  # A fridge is too heavy to move
        self.properties["minTemperature"] = 4.0  # Minimum temperature of the fridge (in degrees Celsius)
        self.properties["temperatureDecreasePerTick"] = 2.0  # How much the temperature decreases per tick (in degrees Celsius)

    def tick(self):
        if self.properties["isOn"]:
            containedObjects = self.getAllContainedObjectsRecursive()
            for obj in containedObjects:
                if isinstance(obj, Substance):
                    newTemperature = obj.properties["temperature"] - self.properties["temperatureDecreasePerTick"]
                    obj.properties["temperature"] = max(newTemperature, self.properties["minTemperature"])

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a fridge that is currently " + ("on" if self.properties["isOn"] else "off")
        if len(self.contains) == 0:
            outStr += " and is empty."
        else:
            if not makeDetailed:
                outStr += " and contains one or more items."
            else:
                outStr += " and contains the following items:\n"
                for obj in self.contains:
                    outStr += "\t" + obj.makeDescriptionStr() + "\n"
        return outStr


# A pot, which is a container that can hold liquids.
class Pot(Container):
    def __init__(self):
        GameObject.__init__(self, "pot")
        Container.__init__(self, "pot")

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a pot"
        contents = [obj.makeDescriptionStr() for obj in self.contains]
        if contents:
            outStr += " that contains " + ", ".join(contents)
        else:
            outStr += " that is empty"
        return outStr


# An instance of a substance (here, milk)
class Milk(Substance):
    def __init__(self):
        Substance.__init__(self, "frozen milk", "milk", "steam", boilingPoint=100, meltingPoint=-1, currentTemperatureCelsius=4)
        self.tick()  # Set the initial state of matter


# A thermometer that can be used to check the temperature of substances.
class Thermometer(GameObject):
    def __init__(self):
        GameObject.__init__(self, "thermometer")

    def checkTemperature(self, substance):
        return substance.properties["temperature"]


# The world is the root object of the game object tree. In single room environments, it's where all the objects are located.
class KitchenWorld(World):
    def __init__(self):
        World.__init__(self, "kitchen")


class HeatMilkGame(TextGame):
    def __init__(self, randomSeed):
        TextGame.__init__(self, randomSeed)

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

        # Add milk to the pot
        milk = Milk()
        pot.addObject(milk)

        # Add a thermometer
        thermometer = Thermometer()
        world.addObject(thermometer)

        return world

    def getTaskDescription(self):
        return "Your task is to heat milk to a suitable temperature for a baby."

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
                self.addAction(f"open {objReferent}", ["open", obj])
                self.addAction(f"close {objReferent}", ["close", obj])
                self.addAction(f"examine {objReferent}", ["examine", obj])
                self.addAction(f"turn on {objReferent}", ["turn on", obj])
                self.addAction(f"turn off {objReferent}", ["turn off", obj])
                self.addAction(f"use thermometer on {objReferent}", ["use thermometer", obj])

        # Actions with two object arguments
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if obj1 != obj2:
                            containerPrefix = obj2.properties.get("containerPrefix", "in") if obj2.properties.get("isContainer") else "in"
                            self.addAction(f"put {objReferent1} {containerPrefix} {objReferent2}", ["put", obj1, obj2])
                            self.addAction(f"use {objReferent1} on {objReferent2}", ["use", obj1, obj2])

        return self.possibleActions

    def actionUseThermometer(self, obj):
        if isinstance(obj, Substance):
            temperature = obj.properties["temperature"]
            return f"The temperature of the {obj.name} is {temperature}°C."
        return "You can't use the thermometer on that."

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
            "examine": lambda action: action[1].makeDescriptionStr(makeDetailed=True),
            "take": lambda action: self.actionTake(action[1]),
            "open": lambda action: self.actionOpen(action[1]),
            "close": lambda action: self.actionClose(action[1]),
            "turn on": lambda action: self.actionTurnOn(action[1]),
            "turn off": lambda action: self.actionTurnOff(action[1]),
            "use thermometer": lambda action: self.actionUseThermometer(action[1]),
            "put": lambda action: self.actionPut(action[1], action[2]),
        }

        self.observationStr = action_map.get(actionVerb, lambda: "ERROR: Unknown action.")(action)

        # Do one tick of the environment
        self.doWorldTick()

        # Calculate the score
        lastScore = self.score
        self.calculateScore()
        reward = self.score - lastScore

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    def calculateScore(self):
        self.score = 0
        allObjects = self.rootObject.getAllContainedObjectsRecursive()
        milk = next((obj for obj in allObjects if isinstance(obj, Milk)), None)
        if milk and milk.properties["temperature"] >= 37:  # Suitable temperature for a baby
            self.score, self.gameOver, self.gameWon = 1, True, True

if __name__ == "__main__":
    main(HeatMilkGame(randomSeed=1))
