from data.library.GameBasic import *

class Stove(Container, Device):
    def __init__(self):
        Container.__init__(self, "stove")
        Device.__init__(self, "stove")
        # Properties
        self.properties["containerPrefix"] = "on"
        self.properties["isOpenable"] = False
        self.properties["temperature_increase_per_tick"] = 5.0
        self.properties["max_temperature"] = 100.0

    def tick(self):
        # Heat objects on the stove when it's turned on
        if self.properties["isOn"]:
            for obj in self.contains:
                current_temp = obj.getProperty("temperature")
                if current_temp < self.properties["max_temperature"]:
                    new_temp = current_temp + self.properties["temperature_increase_per_tick"]
                    if new_temp > self.properties["max_temperature"]:
                        new_temp = self.properties["max_temperature"]
                    obj.properties["temperature"] = new_temp

class Pot(Container):
    def __init__(self):
        Container.__init__(self, "pot")
        self.properties["containerPrefix"] = "in"
        # Start at fridge temperature (4°C)
        self.properties["temperature"] = 4.0

    def tick(self):
        # Update contents to match pot temperature
        for obj in self.contains:
            obj.properties["temperature"] = self.properties["temperature"]

class Milk(GameObject):
    def __init__(self):
        GameObject.__init__(self, "milk")
        # Start at fridge temperature (4°C)
        self.properties["temperature"] = 4.0

class Fridge(Container, Device):
    def __init__(self):
        Container.__init__(self, "fridge")
        Device.__init__(self, "fridge")
        self.properties["containerPrefix"] = "in"
        self.properties["isOpenable"] = True
        self.properties["isOpen"] = False  # Start closed
        self.properties["min_temperature"] = 4.0
        self.properties["temperature_decrease_per_tick"] = 1.0
        self.properties["isOn"] = True  # Always running

    def tick(self):
        # Cool objects inside when closed
        if self.properties["isOn"] and not self.properties["isOpen"]:
            for obj in self.contains:
                current_temp = obj.getProperty("temperature")
                if current_temp > self.properties["min_temperature"]:
                    new_temp = current_temp - self.properties["temperature_decrease_per_tick"]
                    if new_temp < self.properties["min_temperature"]:
                        new_temp = self.properties["min_temperature"]
                    obj.properties["temperature"] = new_temp

class Thermometer(GameObject):
    def __init__(self):
        GameObject.__init__(self, "thermometer")

class KitchenWorld(World):
    def __init__(self):
        World.__init__(self, "kitchen")

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = f"You are in a {self.room}. Around you, you see:\n"
        for obj in self.contains:
            outStr += "\t" + obj.makeDescriptionStr() + "\n"
        return outStr

class HeatMilkGame(TextGame):
    def __init__(self, randomSeed):
        TextGame.__init__(self, randomSeed)

    def initializeWorld(self):
        world = KitchenWorld()
        
        # Add agent
        world.addObject(self.agent)
        
        # Create and place objects
        fridge = Fridge()
        stove = Stove()
        pot = Pot()
        milk = Milk()
        thermometer = Thermometer()
        
        # Put milk in pot, pot in fridge
        pot.addObject(milk)
        fridge.addObject(pot)
        
        # Add objects to world
        world.addObject(fridge)
        world.addObject(stove)
        world.addObject(thermometer)
        
        return world

    def getTaskDescription(self):
        return "Your task is to heat milk to a suitable temperature (36-40°C) for a baby using a stove."

    def generatePossibleActions(self):
        # Get all possible objects
        allObjects = self.makeNameToObjectDict()
        self.possibleActions = {}
        
        # Actions with zero arguments
        for action in [("look around", "look around"), ("look", "look around"), ("inventory", "inventory")]:
            self.addAction(action[0], [action[1]])
        
        # Actions with one object argument
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction("take " + objReferent, ["take", obj])
                self.addAction("take " + objReferent + " from " + obj.parentContainer.getReferents()[0], ["take", obj])
                self.addAction("open " + objReferent, ["open", obj])
                self.addAction("close " + objReferent, ["close", obj])
                self.addAction("examine " + objReferent, ["examine", obj])
                self.addAction("turn on " + objReferent, ["turn on", obj])
                self.addAction("turn off " + objReferent, ["turn off", obj])
        
        # Actions with two object arguments
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if obj1 != obj2:
                            containerPrefix = "in"
                            if obj2.properties["isContainer"]:
                                containerPrefix = obj2.properties["containerPrefix"]
                            self.addAction("put " + objReferent1 + " " + containerPrefix + " " + objReferent2,
                                          ["put", obj1, obj2])
                            self.addAction("use " + objReferent1 + " on " + objReferent2, ["use", obj1, obj2])
        
        # Special actions
        self.addAction("feed baby with milk", ["feed baby"])
        self.addAction("drink milk", ["drink milk"])
        
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
        # Thermometer usage
        if isinstance(deviceObj, Thermometer):
            # Check if agent has thermometer
            if deviceObj.parentContainer != self.agent:
                return "You need the thermometer in your inventory to use it."
            
            # Get temperature
            temp = patientObject.getProperty("temperature")
            if temp is None:
                return f"You can't measure the temperature of the {patientObject.name}."
            return f"The thermometer shows {temp:.1f}°C."
        
        return "You're not sure how to use those together."

    def findMilk(self):
        # Check for milk directly in inventory
        milk_list = self.agent.containsItemWithName("milk")
        if milk_list:
            return milk_list[0]
        
        # Check for milk in containers in inventory
        for obj in self.agent.contains:
            if isinstance(obj, Container):
                milk_list = obj.containsItemWithName("milk")
                if milk_list:
                    return milk_list[0]
        return None

    def step(self, actionStr):
        self.observationStr = ""
        reward = 0

        if actionStr not in self.possibleActions:
            self.observationStr = "I don't understand that."
            return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

        self.numSteps += 1
        action = self.possibleActions[actionStr][0]
        actionVerb = action[0]

        # Action handling
        if actionVerb == "look around":
            self.observationStr = self.rootObject.makeDescriptionStr()
        elif actionVerb == "inventory":
            self.observationStr = self.actionInventory()
        elif actionVerb == "examine":
            self.observationStr = action[1].makeDescriptionStr(makeDetailed=True)
        elif actionVerb == "open":
            self.observationStr = self.actionOpen(action[1])
        elif actionVerb == "close":
            self.observationStr = self.actionClose(action[1])
        elif actionVerb == "take":
            self.observationStr = self.actionTake(action[1])
        elif actionVerb == "turn on":
            self.observationStr = self.actionTurnOn(action[1])
        elif actionVerb == "turn off":
            self.observationStr = self.actionTurnOff(action[1])
        elif actionVerb == "put":
            self.observationStr = self.actionPut(action[1], action[2])
        elif actionVerb == "use":
            self.observationStr = self.actionUse(action[1], action[2])
        elif actionVerb == "feed baby":
            milk = self.findMilk()
            if not milk:
                self.observationStr = "You don't have any milk to feed the baby."
            else:
                temp = milk.properties["temperature"]
                if 36 <= temp <= 40:
                    self.observationStr = "You feed the baby with perfectly warmed milk. The baby is happy!"
                    self.gameOver = True
                    self.gameWon = True
                    reward = 1
                else:
                    self.observationStr = f"The milk is {temp:.1f}°C - not suitable for a baby (needs 36-40°C)."
        elif actionVerb == "drink milk":
            milk = self.findMilk()
            if milk:
                self.observationStr = "You drink the milk. It tastes good but doesn't help the baby."
            else:
                self.observationStr = "You don't have any milk to drink."
        else:
            self.observationStr = "ERROR: Unknown action."

        # Update world state
        self.doWorldTick()

        # Calculate score
        lastScore = self.score
        self.calculateScore()
        reward = self.score - lastScore

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    def calculateScore(self):
        # Score is 1 only when baby is successfully fed
        self.score = 1 if self.gameWon else 0


if __name__ == "__main__":
    # Set random seed 0 and Create a new game
    main(HeatMilkGame(randomSeed=0))
