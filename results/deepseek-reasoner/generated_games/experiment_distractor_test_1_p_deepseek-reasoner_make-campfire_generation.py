# Task: Create a micro-simulation that models how to heat milk to a temperature that is suitable for a baby using a stove.
# Environment: kitchen
# Task-critical Objects: Stove, Pot, Milk, Fridge, Thermometer
# High-level object classes: Device (Stove, Fridge), Container (Stove, Pot, Fridge) 
# Critical properties: temperature (Milk), temperature_increase_per_tick (Stove), temperature_decrease_per_tick (fridge), max_temperature (Stove), min_temperature (fridge)
# Actions: look, inventory, examine, take/put object, open/close container, turn on/off device, use thermometer on object, feed baby with milk
# Distractor Items: None
# Distractor Actions: drink milk
# High-level solution procedure: open fridge, take pot containing milk, put the pot on the stove, turn on the stove, use the thermometer to moniter the milk temperature till the temperature is suitable for a baby to drink, feed baby

from data.library.GameBasic import *

class Stove(Container, Device):
    def __init__(self):
        GameObject.__init__(self, "stove")
        Container.__init__(self, "stove")
        Device.__init__(self, "stove")
        
        self.properties["isContainer"] = True
        self.properties["isOpenable"] = False
        self.properties["containerPrefix"] = "on"
        self.properties["temperature_increase_per_tick"] = 5
        self.properties["max_temperature"] = 100

    def tick(self):
        if self.properties["isOn"]:
            for obj in self.contains:
                current_temp = obj.getProperty("temperature")
                if current_temp is not None:
                    new_temp = min(current_temp + self.properties["temperature_increase_per_tick"], self.properties["max_temperature"])
                    obj.properties["temperature"] = new_temp

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a stove"
        if self.properties["isOn"]:
            outStr += " that is on"
        else:
            outStr += " that is off"
            
        if self.contains:
            outStr += " with " + ", ".join([obj.makeDescriptionStr() for obj in self.contains]) + " on it"
        return outStr

class Pot(Container):
    def __init__(self):
        Container.__init__(self, "pot")
        self.properties["isOpenable"] = False
        self.properties["containerPrefix"] = "in"

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a pot"
        if self.contains:
            outStr += " containing " + ", ".join([obj.makeDescriptionStr() for obj in self.contains])
        return outStr

class Milk(GameObject):
    def __init__(self):
        GameObject.__init__(self, "milk")
        self.properties["temperature"] = 4.0

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "some milk"
        if self.properties["temperature"] < 35:
            outStr += " that is cold"
        elif self.properties["temperature"] > 40:
            outStr += " that is hot"
        else:
            outStr += " that is warm"
        return outStr

class Fridge(Container, Device):
    def __init__(self):
        GameObject.__init__(self, "fridge")
        Container.__init__(self, "fridge")
        Device.__init__(self, "fridge")
        
        self.properties["isContainer"] = True
        self.properties["isOpenable"] = True
        self.properties["isOpen"] = False
        self.properties["containerPrefix"] = "in"
        self.properties["temperature_decrease_per_tick"] = 2
        self.properties["min_temperature"] = 4

    def tick(self):
        if self.properties["isOn"] and not self.properties["isOpen"]:
            for obj in self.contains:
                current_temp = obj.getProperty("temperature")
                if current_temp is not None:
                    new_temp = max(current_temp - self.properties["temperature_decrease_per_tick"], self.properties["min_temperature"])
                    obj.properties["temperature"] = new_temp

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a fridge"
        if self.properties["isOpen"]:
            outStr += " that is open"
        else:
            outStr += " that is closed"
        return outStr

class Thermometer(Device):
    def __init__(self):
        Device.__init__(self, "thermometer")

    def useWithObject(self, patientObject):
        temp = patientObject.getProperty("temperature")
        if temp is not None:
            return f"The thermometer shows the {patientObject.name} is {temp}°C.", True
        return f"You can't measure the temperature of the {patientObject.name}.", False

    def makeDescriptionStr(self, makeDetailed=False):
        return "a thermometer"

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
        world.addObject(self.agent)
        
        # Create objects
        stove = Stove()
        pot = Pot()
        milk = Milk()
        fridge = Fridge()
        thermometer = Thermometer()
        
        # Start with milk in pot, pot in fridge
        pot.addObject(milk)
        fridge.addObject(pot)
        
        # Add objects to world
        world.addObject(stove)
        world.addObject(fridge)
        world.addObject(thermometer)
        
        return world

    def getTaskDescription(self):
        return "Your task is to heat milk to a suitable temperature for a baby using the stove."

    def generatePossibleActions(self):
        allObjects = self.makeNameToObjectDict()
        self.possibleActions = {}

        # Basic actions
        for action in [("look around", "look around"), ("look", "look around"), ("inventory", "inventory")]:
            self.addAction(action[0], [action[1]])

        # Actions with one object
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction("take " + objReferent, ["take", obj])
                self.addAction("take " + objReferent + " from " + obj.parentContainer.getReferents()[0], ["take", obj])
                self.addAction("open " + objReferent, ["open", obj])
                self.addAction("close " + objReferent, ["close", obj])
                self.addAction("examine " + objReferent, ["examine", obj])
                self.addAction("turn on " + objReferent, ["turn on", obj])
                self.addAction("turn off " + objReferent, ["turn off", obj])
                self.addAction("drink " + objReferent, ["drink", obj])

        # Actions with two objects
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if obj1 != obj2:
                            containerPrefix = "in"
                            if obj2.properties["isContainer"]:
                                containerPrefix = obj2.properties["containerPrefix"]
                            self.addAction("put " + objReferent1 + " " + containerPrefix + " " + objReferent2, ["put", obj1, obj2])
                            self.addAction("use " + objReferent1 + " on " + objReferent2, ["use", obj1, obj2])
                            self.addAction("feed baby with " + objReferent1, ["feed baby", obj1])

        return self.possibleActions

    def actionOpen(self, obj):
        if obj.getProperty("isContainer"):
            obsStr, success = obj.openContainer()
            return obsStr
        return "You can't open that."

    def actionClose(self, obj):
        if obj.getProperty("isContainer"):
            obsStr, success = obj.closeContainer()
            return obsStr
        return "You can't close that."

    def actionTurnOn(self, obj):
        if obj.getProperty("isDevice"):
            obsStr, success = obj.turnOn()
            return obsStr
        return "You can't turn on that."

    def actionTurnOff(self, obj):
        if obj.getProperty("isDevice"):
            obsStr, success = obj.turnOff()
            return obsStr
        return "You can't turn off that."

    def actionUse(self, deviceObj, patientObject):
        if deviceObj.getProperty("isDevice"):
            if deviceObj.parentContainer != self.agent:
                return "You don't currently have the " + deviceObj.getReferents()[0] + " in your inventory."
            obsStr, success = deviceObj.useWithObject(patientObject)
            return obsStr
        return "You can't use that."

    def actionDrink(self, obj):
        if obj.name == "milk":
            temp = obj.getProperty("temperature")
            if temp < 35:
                return "The milk is too cold to drink comfortably."
            elif temp > 40:
                return "The milk is too hot to drink comfortably."
            else:
                return "You drink the milk. It's just the right temperature."
        return "You can't drink that."

    def actionFeedBaby(self, obj):
        if obj.name == "milk":
            if obj.parentContainer != self.agent:
                return "You need to have the milk in your inventory to feed the baby."
            temp = obj.getProperty("temperature")
            if 35 <= temp <= 40:
                self.score += 1
                self.gameOver = True
                self.gameWon = True
                return "You feed the baby with the milk. The temperature is perfect! Task completed."
            elif temp < 35:
                return "The milk is too cold for the baby."
            else:
                return "The milk is too hot for the baby."
        return "You can't feed the baby with that."

    def step(self, actionStr):
        self.observationStr = ""
        reward = 0

        if actionStr not in self.possibleActions:
            self.observationStr = "I don't understand that."
            return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

        self.numSteps += 1
        actions = self.possibleActions[actionStr]
        action = actions[0]

        actionVerb = action[0]
        action_map = {
            "look around": lambda: self.rootObject.makeDescriptionStr(),
            "inventory": lambda: self.actionInventory(),
            "examine": lambda: action[1].makeDescriptionStr(makeDetailed=True),
            "open": lambda: self.actionOpen(action[1]),
            "close": lambda: self.actionClose(action[1]),
            "take": lambda: self.actionTake(action[1]),
            "turn on": lambda: self.actionTurnOn(action[1]),
            "turn off": lambda: self.actionTurnOff(action[1]),
            "put": lambda: self.actionPut(action[1], action[2]),
            "use": lambda: self.actionUse(action[1], action[2]),
            "drink": lambda: self.actionDrink(action[1]),
            "feed baby": lambda: self.actionFeedBaby(action[1]),
        }

        self.observationStr = action_map.get(actionVerb, lambda: "ERROR: Unknown action.")()

        self.doWorldTick()
        lastScore = self.score
        self.calculateScore()
        reward = self.score - lastScore

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    def calculateScore(self):
        # Score is calculated in actionFeedBaby when task is completed
        pass

if __name__ == "__main__":
    main(HeatMilkGame(randomSeed=0))
