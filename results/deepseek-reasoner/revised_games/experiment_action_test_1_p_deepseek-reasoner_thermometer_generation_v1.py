from data.library.GameBasic import *

class Stove(Container, Device):
    def __init__(self, name):
        GameObject.__init__(self, name)
        Container.__init__(self, name)
        Device.__init__(self, name)
        self.properties["isContainer"] = True
        self.properties["isOpenable"] = False
        self.properties["isOpen"] = True
        self.properties["containerPrefix"] = "on"
        self.properties["temperature_increase_per_tick"] = 5.0
        self.properties["max_temperature"] = 100.0

    def tick(self):
        if self.properties["isOn"]:
            for obj in self.contains:
                if obj.getProperty("temperature") is not None:
                    current_temp = obj.getProperty("temperature")
                    new_temp = current_temp + self.properties["temperature_increase_per_tick"]
                    if new_temp > self.properties["max_temperature"]:
                        new_temp = self.properties["max_temperature"]
                    obj.properties["temperature"] = new_temp

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = f"a {self.name} that is currently "
        if self.properties["isOn"]:
            outStr += "on and heating."
        else:
            outStr += "off."
        if len(self.contains) > 0:
            outStr += f" There is a {self.contains[0].name} on it."
        return outStr

class Fridge(Container, Device):
    def __init__(self, name):
        GameObject.__init__(self, name)
        Container.__init__(self, name)
        Device.__init__(self, name)
        self.properties["isContainer"] = True
        self.properties["isOpenable"] = True
        self.properties["isOpen"] = False
        self.properties["containerPrefix"] = "in"
        self.properties["temperature_decrease_per_tick"] = 2.0
        self.properties["min_temperature"] = 4.0
        self.properties["isOn"] = True

    def tick(self):
        if self.properties["isOn"] and not self.properties["isOpen"]:
            for obj in self.contains:
                if obj.getProperty("temperature") is not None:
                    current_temp = obj.getProperty("temperature")
                    new_temp = current_temp - self.properties["temperature_decrease_per_tick"]
                    if new_temp < self.properties["min_temperature"]:
                        new_temp = self.properties["min_temperature"]
                    obj.properties["temperature"] = new_temp

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = f"a {self.name} that is currently "
        if self.properties["isOpen"]:
            outStr += "open."
        else:
            outStr += "closed."
        return outStr

class Pot(Container):
    def __init__(self, name):
        GameObject.__init__(self, name)
        Container.__init__(self, name)
        self.properties["isContainer"] = True
        self.properties["isOpenable"] = False
        self.properties["isOpen"] = True
        self.properties["containerPrefix"] = "in"

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = f"a {self.name}"
        if len(self.contains) > 0:
            outStr += f" containing {self.contains[0].name}"
        return outStr

class Milk(GameObject):
    def __init__(self, name, temperature):
        GameObject.__init__(self, name)
        self.properties["temperature"] = temperature

    def makeDescriptionStr(self, makeDetailed=False):
        return f"some {self.name} at {self.properties['temperature']:.1f}°C"

class Thermometer(GameObject):
    def __init__(self):
        GameObject.__init__(self, "thermometer")

    def useWithObject(self, obj):
        if obj.getProperty("temperature") is not None:
            return f"The thermometer reads {obj.getProperty('temperature'):.1f}°C.", True
        else:
            return "The thermometer doesn't give a reading for that object.", False

    def makeDescriptionStr(self, makeDetailed=False):
        return "a thermometer"

class Baby(GameObject):
    def __init__(self):
        GameObject.__init__(self, "baby")

    def makeDescriptionStr(self, makeDetailed=False):
        return "a baby"

class KitchenWorld(World):
    def __init__(self):
        World.__init__(self, "kitchen")

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "You find yourself in a kitchen. In the kitchen, you see: \n"
        for obj in self.contains:
            if obj.name != "agent":
                outStr += "\t" + obj.makeDescriptionStr() + "\n"
        return outStr

class HeatMilkGame(TextGame):
    def __init__(self, randomSeed):
        self.agentHasFedBaby = False
        self.milkTemperatureWhenFed = None
        TextGame.__init__(self, randomSeed)

    def initializeWorld(self):
        world = KitchenWorld()
        
        world.addObject(self.agent)
        
        stove = Stove("stove")
        world.addObject(stove)
        
        fridge = Fridge("fridge")
        world.addObject(fridge)
        
        pot = Pot("pot")
        milk = Milk("milk", 4.0)
        pot.addObject(milk)
        fridge.addObject(pot)
        
        thermometer = Thermometer()
        world.addObject(thermometer)
        
        baby = Baby()
        world.addObject(baby)
        
        return world

    def getTaskDescription(self):
        return "Your task is to heat the milk to a suitable temperature for the baby (37-40°C) and then feed the baby."

    def generatePossibleActions(self):
        if not hasattr(self, 'possibleActions'):
            self.possibleActions = {}
        else:
            self.possibleActions.clear()
        
        allObjects = self.makeNameToObjectDict()
        
        self.addAction("look around", ["look around"])
        self.addAction("look", ["look around"])
        self.addAction("inventory", ["inventory"])
        
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction("examine " + objReferent, ["examine", obj])
                self.addAction("take " + objReferent, ["take", obj])
                if obj.parentContainer is not None:
                    self.addAction("take " + objReferent + " from " + obj.parentContainer.getReferents()[0], ["take", obj])
                if obj.getProperty("isOpenable"):
                    if obj.getProperty("isOpen"):
                        self.addAction("close " + objReferent, ["close", obj])
                    else:
                        self.addAction("open " + objReferent, ["open", obj])
                if obj.getProperty("isDevice"):
                    if obj.getProperty("isOn"):
                        self.addAction("turn off " + objReferent, ["turn off", obj])
                    else:
                        self.addAction("turn on " + objReferent, ["turn on", obj])
                if obj.name == "milk":
                    self.addAction("drink " + objReferent, ["drink", obj])
                if obj.name == "milk":
                    self.addAction("feed baby with " + objReferent, ["feed baby", obj])
        
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if obj1 != obj2:
                            if obj2.getProperty("isContainer"):
                                containerPrefix = obj2.properties["containerPrefix"]
                                self.addAction("put " + objReferent1 + " " + containerPrefix + " " + objReferent2, ["put", obj1, obj2])
                            if obj1.name == "thermometer":
                                self.addAction("use " + objReferent1 + " on " + objReferent2, ["use", obj1, obj2])
        
        return self.possibleActions

    def actionOpen(self, obj):
        if obj.getProperty("isOpenable"):
            if not obj.getProperty("isOpen"):
                obsStr, success = obj.openContainer()
                return obsStr
            else:
                return "The " + obj.name + " is already open."
        else:
            return "The " + obj.name + " can't be opened."

    def actionClose(self, obj):
        if obj.getProperty("isOpenable"):
            if obj.getProperty("isOpen"):
                obsStr, success = obj.closeContainer()
                return obsStr
            else:
                return "The " + obj.name + " is already closed."
        else:
            return "The " + obj.name + " can't be closed."

    def actionTurnOn(self, obj):
        if obj.getProperty("isDevice"):
            obsStr, success = obj.turnOn()
            return obsStr
        else:
            return "You can't turn on the " + obj.name + "."

    def actionTurnOff(self, obj):
        if obj.getProperty("isDevice"):
            obsStr, success = obj.turnOff()
            return obsStr
        else:
            return "You can't turn off the " + obj.name + "."

    def actionUse(self, deviceObj, patientObject):
        if isinstance(deviceObj, Thermometer):
            if deviceObj.parentContainer == self.agent:
                obsStr, success = deviceObj.useWithObject(patientObject)
                return obsStr
            else:
                return "You need to take the thermometer first."
        return "You can't use that."

    def actionDrink(self, milk):
        if milk.parentContainer == self.agent:
            return "You drink the milk. It tastes good but this doesn't help the baby.", False
        else:
            return "You need to take the milk first."

    def actionFeedBaby(self, milk):
        if milk.parentContainer == self.agent:
            self.milkTemperatureWhenFed = milk.getProperty("temperature")
            self.agentHasFedBaby = True
            return f"You feed the baby with the milk. The milk was {self.milkTemperatureWhenFed:.1f}°C.", True
        else:
            return "You need to take the milk first."

    def step(self, actionStr):
        self.observationStr = ""
        reward = 0

        if not hasattr(self, 'possibleActions'):
            self.generatePossibleActions()
            
        if actionStr not in self.possibleActions:
            self.observationStr = "I don't understand that."
            return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

        self.numSteps += 1

        actions = self.possibleActions[actionStr]
        action = actions[0]

        actionVerb = action[0]

        if actionVerb == "look around":
            self.observationStr = self.rootObject.makeDescriptionStr()
        elif actionVerb == "inventory":
            self.observationStr = self.actionInventory()
        elif actionVerb == "examine":
            self.observationStr = action[1].makeDescriptionStr(makeDetailed=True)
        elif actionVerb == "take":
            self.observationStr = self.actionTake(action[1])
        elif actionVerb == "put":
            self.observationStr = self.actionPut(action[1], action[2])
        elif actionVerb == "open":
            self.observationStr = self.actionOpen(action[1])
        elif actionVerb == "close":
            self.observationStr = self.actionClose(action[1])
        elif actionVerb == "turn on":
            self.observationStr = self.actionTurnOn(action[1])
        elif actionVerb == "turn off":
            self.observationStr = self.actionTurnOff(action[1])
        elif actionVerb == "use":
            self.observationStr = self.actionUse(action[1], action[2])
        elif actionVerb == "drink":
            self.observationStr = self.actionDrink(action[1])
        elif actionVerb == "feed baby":
            self.observationStr = self.actionFeedBaby(action[1])
        else:
            self.observationStr = "ERROR: Unknown action."

        self.doWorldTick()
        lastScore = self.score
        self.calculateScore()
        reward = self.score - lastScore

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    def calculateScore(self):
        self.score = 0
        if self.agentHasFedBaby:
            if 37 <= self.milkTemperatureWhenFed <= 40:
                self.score = 1
                self.gameOver = True
                self.gameWon = True
            else:
                self.score = 0
                self.gameOver = True
                self.gameWon = False

if __name__ == "__main__":
    main(game=HeatMilkGame(randomSeed=0))
