from data.library.GameBasic import *

# Stove: a device that can heat objects placed on it
class Stove(Container, Device):
    def __init__(self):
        Container.__init__(self, "stove")
        Device.__init__(self, "stove")
        self.properties["isMoveable"] = False
        self.properties["containerPrefix"] = "on"
        self.properties["temperature_increase_per_tick"] = 5  # degrees per tick
        self.properties["max_temperature"] = 100  # degrees Celsius

    def tick(self):
        # If the stove is on, heat any pot on it
        if self.properties["isOn"]:
            for obj in self.contains:
                if isinstance(obj, Pot):
                    current_temp = obj.getProperty("temperature")
                    new_temp = current_temp + self.properties["temperature_increase_per_tick"]
                    if new_temp > self.properties["max_temperature"]:
                        new_temp = self.properties["max_temperature"]
                    obj.properties["temperature"] = new_temp
                    # Also update the temperature of the milk inside
                    for contained_obj in obj.contains:
                        contained_obj.properties["temperature"] = new_temp

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a stove that is currently "
        if self.properties["isOn"]:
            outStr += "on"
        else:
            outStr += "off"
        
        if len(self.contains) > 0:
            outStr += " with a pot on it" if any(isinstance(obj, Pot) for obj in self.contains) else " with something on it"
        else:
            outStr += " and empty"
        return outStr

# Pot: a container that can hold milk
class Pot(Container):
    def __init__(self):
        Container.__init__(self, "pot")
        self.properties["temperature"] = 20  # initial room temperature

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a pot"
        if len(self.contains) > 0:
            outStr += " containing " + ", ".join([obj.makeDescriptionStr() for obj in self.contains])
        return outStr

# Milk: a substance with temperature
class Milk(GameObject):
    def __init__(self):
        GameObject.__init__(self, "milk")
        self.properties["temperature"] = 4  # initial temperature (cold from fridge)
        self.properties["suitable_temperature"] = False

    def tick(self):
        # Check if temperature is suitable for baby (37-40 degrees)
        temp = self.properties["temperature"]
        if temp >= 37 and temp <= 40:
            self.properties["suitable_temperature"] = True
        else:
            self.properties["suitable_temperature"] = False

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "milk"
        if makeDetailed:
            outStr += f" at {self.properties['temperature']}°C"
        return outStr

# Fridge: a cooling device and container
class Fridge(Container, Device):
    def __init__(self):
        Container.__init__(self, "fridge")
        Device.__init__(self, "fridge")
        self.properties["isOpenable"] = True
        self.properties["isOpen"] = False
        self.properties["isMoveable"] = False
        self.properties["temperature_decrease_per_tick"] = 2  # degrees per tick
        self.properties["min_temperature"] = 4  # degrees Celsius

    def tick(self):
        # If fridge is on and closed, cool its contents
        if self.properties["isOn"] and not self.properties["isOpen"]:
            for obj in self.contains:
                current_temp = obj.getProperty("temperature")
                new_temp = current_temp - self.properties["temperature_decrease_per_tick"]
                if new_temp < self.properties["min_temperature"]:
                    new_temp = self.properties["min_temperature"]
                obj.properties["temperature"] = new_temp
                # Also update the temperature of any contained objects (e.g., milk in pot)
                for contained_obj in obj.getAllContainedObjectsRecursive():
                    contained_obj.properties["temperature"] = new_temp

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a fridge that is currently "
        if self.properties["isOn"]:
            outStr += "on and "
        else:
            outStr += "off and "
        if self.properties["isOpen"]:
            outStr += "open"
        else:
            outStr += "closed"
        return outStr

# Thermometer: a device to check temperature
class Thermometer(GameObject):
    def __init__(self):
        GameObject.__init__(self, "thermometer")

    def makeDescriptionStr(self, makeDetailed=False):
        return "a thermometer"

# The world is the root object of the game object tree.
class KitchenWorld(World):
    def __init__(self):
        World.__init__(self, "kitchen")

# The game class
class HeatMilkGame(TextGame):
    def __init__(self, randomSeed):
        TextGame.__init__(self, randomSeed)
        self.possibleActions = {}  # Initialize possibleActions

    def initializeWorld(self):
        world = KitchenWorld()
        world.addObject(self.agent)

        # Create and add objects
        stove = Stove()
        world.addObject(stove)

        fridge = Fridge()
        fridge.properties["isOn"] = True  # Fridge is always on
        world.addObject(fridge)

        pot = Pot()
        milk = Milk()
        pot.addObject(milk)
        fridge.addObject(pot)  # Start with pot of milk in fridge

        thermometer = Thermometer()
        world.addObject(thermometer)

        return world

    def getTaskDescription(self):
        return "Your task is to heat milk to a suitable temperature for a baby using a stove."

    def generatePossibleActions(self):
        # Get all objects
        allObjects = self.makeNameToObjectDict()

        # Actions with zero arguments
        self.addAction("look around", ["look around"])
        self.addAction("look", ["look around"])
        self.addAction("inventory", ["inventory"])

        # Actions with one object argument
        for objReferent, objs in allObjects.items():
            for obj in objs:
                # Basic actions
                self.addAction("take " + objReferent, ["take", obj])
                self.addAction("open " + objReferent, ["open", obj])
                self.addAction("close " + objReferent, ["close", obj])
                self.addAction("turn on " + objReferent, ["turn on", obj])
                self.addAction("turn off " + objReferent, ["turn off", obj])
                self.addAction("use thermometer on " + objReferent, ["use thermometer", obj])
                self.addAction("drink " + objReferent, ["drink", obj])
                self.addAction("feed baby with " + objReferent, ["feed baby", obj])

        # Actions with two object arguments
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if obj1 != obj2:
                            containerPrefix = "in"
                            if obj2.properties["isContainer"]:
                                containerPrefix = obj2.properties["containerPrefix"]
                            self.addAction("put " + objReferent1 + " " + containerPrefix + " " + objReferent2, ["put", obj1, obj2])

        return self.possibleActions

    def actionTake(self, obj):
        if obj.parentContainer == None:
            return "Something has gone wrong -- that object is dangling in the void. You can't take that."

        # Check if container is open
        if obj.parentContainer.getProperty("isOpenable") and not obj.parentContainer.getProperty("isOpen"):
            return f"You need to open the {obj.parentContainer.name} first."

        obsStr, objRef, success = obj.parentContainer.takeObjectFromContainer(obj)
        if not success:
            return obsStr

        self.agent.addObject(obj)
        return obsStr + " You put the " + obj.getReferents()[0] + " in your inventory."

    def actionPut(self, objToMove, newContainer):
        if not newContainer.getProperty("isContainer"):
            return "You can't put things in the " + newContainer.getReferents()[0] + "."

        if objToMove.parentContainer != self.agent:
            return "You don't currently have the " + objToMove.getReferents()[0] + " in your inventory."

        # Check if container is open if it's openable
        if newContainer.getProperty("isOpenable") and not newContainer.getProperty("isOpen"):
            return f"You need to open the {newContainer.name} first."

        originalContainer = objToMove.parentContainer
        obsStr1, objRef, success = objToMove.parentContainer.takeObjectFromContainer(objToMove)
        if not success:
            return obsStr1

        obsStr2, success = newContainer.placeObjectInContainer(objToMove)
        if not success:
            originalContainer.addObject(objToMove)
            return obsStr2

        return obsStr1 + "\n" + obsStr2

    def actionOpen(self, obj):
        if obj.getProperty("isOpenable"):
            obsStr, success = obj.openContainer()
            return obsStr
        else:
            return "You can't open that."

    def actionClose(self, obj):
        if obj.getProperty("isOpenable"):
            obsStr, success = obj.closeContainer()
            return obsStr
        else:
            return "You can't close that."

    def actionTurnOn(self, obj):
        if obj.getProperty("isActivatable"):
            obsStr, success = obj.turnOn()
            return obsStr
        else:
            return "You can't turn that on."

    def actionTurnOff(self, obj):
        if obj.getProperty("isActivatable"):
            obsStr, success = obj.turnOff()
            return obsStr
        else:
            return "You can't turn that off."

    def actionUseThermometer(self, obj):
        if "thermometer" not in [o.name for o in self.agent.contains]:
            return "You need to have the thermometer in your inventory to use it."
        
        temp = obj.getProperty("temperature")
        if temp is None:
            return "You can't measure the temperature of that."
        
        return f"The {obj.name} is at {temp}°C."

    def actionDrink(self, obj):
        if obj.name != "milk":
            return "You can't drink that."
        
        if obj.parentContainer != self.agent:
            return "You need to have the milk in your inventory to drink it."
        
        temp = obj.getProperty("temperature")
        if temp >= 37 and temp <= 40:
            return "You drink the milk. It's at the perfect temperature for a baby, but you probably shouldn't have drunk it!"
        else:
            return "You drink the milk. It's not at the right temperature for a baby."

    def actionFeedBaby(self, obj):
        if obj.name != "milk":
            return "You can't feed that to a baby."
        
        if obj.parentContainer != self.agent:
            return "You need to have the milk in your inventory to feed the baby."
        
        if obj.getProperty("suitable_temperature"):
            self.score += 1
            self.gameOver = True
            self.gameWon = True
            return "You feed the baby with the milk. The baby is happy and drinks it all. Task completed!"
        else:
            return "The milk is not at the right temperature for a baby. It should be between 37-40°C."

    def step(self, actionStr):
        # Generate possible actions for the current state
        self.possibleActions = self.generatePossibleActions()
        
        self.observationStr = ""
        reward = 0

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
        elif actionVerb == "use thermometer":
            self.observationStr = self.actionUseThermometer(action[1])
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
        # Check if milk is at suitable temperature and in inventory
        allObjects = self.rootObject.getAllContainedObjectsRecursive()
        for obj in allObjects:
            if obj.name == "milk" and obj.getProperty("suitable_temperature") and obj.parentContainer == self.agent:
                self.score = 1
                return

        self.score = 0

if __name__ == "__main__":
    main(HeatMilkGame(randomSeed=0))
