from data.library.GameBasic import *

# A stove, which is a device that can heat things up.
class Stove(Device):
    def __init__(self):
        Device.__init__(self, "stove")
        self.properties.update({
            "max_temperature": 100,  # Maximum temperature the stove can reach
            "temperature_increase_per_tick": 10,  # Temperature increase per tick
            "isOn": False  # Initially, the stove is off
        })

    def tick(self):
        if self.properties["isOn"]:
            # Increase the temperature of the pot if the stove is on
            for obj in self.contains:
                if isinstance(obj, Pot):
                    obj.properties["temperature"] += self.properties["temperature_increase_per_tick"]
                    if obj.properties["temperature"] > self.properties["max_temperature"]:
                        obj.properties["temperature"] = self.properties["max_temperature"]

    def makeDescriptionStr(self, makeDetailed=False):
        return "a stove that is currently " + ("on." if self.properties["isOn"] else "off.")

# A fridge, which is a device that can cool things down.
class Fridge(Device):
    def __init__(self):
        Device.__init__(self, "fridge")
        self.properties.update({
            "min_temperature": 0,  # Minimum temperature the fridge can reach
            "temperature_decrease_per_tick": 5,  # Temperature decrease per tick
            "isOn": True  # Fridge is always on
        })

    def tick(self):
        # Decrease the temperature of the milk if it's in the fridge
        for obj in self.contains:
            if isinstance(obj, Milk):
                obj.properties["temperature"] -= self.properties["temperature_decrease_per_tick"]
                if obj.properties["temperature"] < self.properties["min_temperature"]:
                    obj.properties["temperature"] = self.properties["min_temperature"]

    def makeDescriptionStr(self, makeDetailed=False):
        return "a fridge that is currently " + ("on." if self.properties["isOn"] else "off.")

# A pot, which is a container that holds the milk.
class Pot(Container):
    def __init__(self):
        Container.__init__(self, "pot")
        self.properties.update({
            "isOpenable": False,  # A pot is not openable
            "temperature": 20  # Initial temperature of the pot
        })

    def makeDescriptionStr(self, makeDetailed=False):
        return f"a pot containing milk at {self.properties['temperature']} degrees Celsius."

# Milk, which has a temperature property.
class Milk(GameObject):
    def __init__(self):
        GameObject.__init__(self, "milk")
        self.properties.update({
            "temperature": 5  # Initial temperature of the milk
        })

    def makeDescriptionStr(self, makeDetailed=False):
        return f"some milk at {self.properties['temperature']} degrees Celsius."

# A thermometer, which can be used to check the temperature of the milk.
class Thermometer(Device):
    def __init__(self):
        Device.__init__(self, "thermometer")

    def useWithObject(self, patientObject):
        if isinstance(patientObject, Milk):
            return f"The milk is currently at {patientObject.properties['temperature']} degrees Celsius.", True
        return "You can't use the thermometer on that.", False

# The world is the root object of the game object tree. In single room environments, it's where all the objects are located.
class KitchenWorld(World):
    def __init__(self):
        World.__init__(self, "kitchen")

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = f"You find yourself in a {self.room}.  In the {self.room}, you see: \n"
        for obj in self.contains:
            outStr += "\t" + obj.makeDescriptionStr() + "\n"
        return outStr

class HeatMilkGame(TextGame):
    def __init__(self, randomSeed):
        TextGame.__init__(self, randomSeed)

    def initializeWorld(self):
        world = KitchenWorld()

        # Add the agent
        world.addObject(self.agent)

        # Add stove, fridge, pot, milk, and thermometer
        world.addObject(Stove())
        world.addObject(Fridge())
        world.addObject(Pot())
        world.addObject(Milk())
        world.addObject(Thermometer())

        return world

    def getTaskDescription(self):
        return "Your task is to heat the milk to a suitable temperature for a baby."

    def generatePossibleActions(self):
        allObjects = self.makeNameToObjectDict()
        self.possibleActions = {}

        # Actions with zero arguments
        for action in [("look around", "look around"), ("look", "look around"), ("inventory", "inventory")]:
            self.addAction(action[0], [action[1]])

        # Actions with one object argument
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction("take " + objReferent, ["take", obj])
                self.addAction("examine " + objReferent, ["examine", obj])
                self.addAction("turn on " + objReferent, ["turn on", obj])
                self.addAction("turn off " + objReferent, ["turn off", obj])

        # Actions with two object arguments
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if obj1 != obj2:
                            if obj2.properties["isContainer"]:
                                containerPrefix = obj2.properties["containerPrefix"]
                            else:
                                containerPrefix = "on"
                            self.addAction("put " + objReferent1 + " " + containerPrefix + " " + objReferent2,
                                           ["put", obj1, obj2])
                            self.addAction("use " + objReferent1 + " on " + objReferent2, ["use", obj1, obj2])

        return self.possibleActions

    def actionUse(self, deviceObj, patientObject):
        if (deviceObj.getProperty("isDevice") == True):
            if (deviceObj.parentContainer != self.agent):
                return "You don't currently have the " + deviceObj.getReferents()[0] + " in your inventory."
            obsStr, success = deviceObj.useWithObject(patientObject)
            return obsStr
        else:
            return "You can't use that."

    def step(self, actionStr):
        self.observationStr = ""
        reward = 0

        if actionStr not in self.possibleActions:
            self.observationStr = "I don't understand that."
            return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

        self.numSteps += 1
        actions = self.possibleActions[actionStr]
        action = actions[0] if len(actions) == 1 else actions[0]

        actionVerb = action[0]
        action_map = {
            "look around": lambda: self.rootObject.makeDescriptionStr(),
            "inventory": lambda: self.actionInventory(),
            "examine": lambda: action[1].makeDescriptionStr(makeDetailed=True),
            "turn on": lambda: self.actionTurnOn(action[1]),
            "turn off": lambda: self.actionTurnOff(action[1]),
            "take": lambda: self.actionTake(action[1]),
            "put": lambda: self.actionPut(action[1], action[2]),
            "use": lambda: self.actionUse(action[1], action[2]),
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
        milk = next((obj for obj in self.rootObject.contains if isinstance(obj, Milk)), None)
        if milk and milk.properties["temperature"] >= 37:  # Suitable temperature for a baby
            self.score += 1
            self.gameOver = True
            self.gameWon = True

if __name__ == "__main__":
    main(HeatMilkGame(randomSeed=0))
