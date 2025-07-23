# Heating Milk for Baby Simulation
from data.library.GameBasic import *

# Stove class that heats objects placed on it
class Stove(Device, Container):
    def __init__(self):
        Device.__init__(self, "stove")
        Container.__init__(self, "stove")
        self.properties["isContainer"] = True
        self.properties["containerPrefix"] = "on"
        self.properties["temperature_increase_per_tick"] = 5.0
        self.properties["max_temperature"] = 100.0

    def tick(self):
        if self.getProperty("isOn"):
            for obj in self.contains:
                self._adjustTemperature(obj, self.properties["temperature_increase_per_tick"], self.properties["max_temperature"])

    def _adjustTemperature(self, obj, delta, limit):
        if obj.getProperty("temperature") is not None:
            current_temp = obj.getProperty("temperature")
            new_temp = min(limit, current_temp + delta)
            obj.properties["temperature"] = new_temp
        
        if obj.getProperty("isContainer"):
            for containedObj in obj.contains:
                self._adjustTemperature(containedObj, delta, limit)

    def makeDescriptionStr(self, makeDetailed=False):
        state = "on" if self.properties["isOn"] else "off"
        return f"a stove that is currently {state}."

# Fridge class that cools objects inside it
class Fridge(Device, Container):
    def __init__(self):
        Device.__init__(self, "fridge")
        Container.__init__(self, "fridge")
        self.properties["isContainer"] = True
        self.properties["isOpenable"] = True
        self.properties["isOpen"] = False
        self.properties["temperature_decrease_per_tick"] = 2.0
        self.properties["min_temperature"] = 4.0
        self.properties["isOn"] = True

    def tick(self):
        if self.getProperty("isOn") and not self.getProperty("isOpen"):
            for obj in self.contains:
                self._adjustTemperature(obj, -self.properties["temperature_decrease_per_tick"], self.properties["min_temperature"])

    def _adjustTemperature(self, obj, delta, limit):
        if obj.getProperty("temperature") is not None:
            current_temp = obj.getProperty("temperature")
            new_temp = max(limit, current_temp + delta)
            obj.properties["temperature"] = new_temp
        
        if obj.getProperty("isContainer"):
            for containedObj in obj.contains:
                self._adjustTemperature(containedObj, delta, limit)

    def makeDescriptionStr(self, makeDetailed=False):
        state = "open" if self.properties["isOpen"] else "closed"
        return f"a fridge that is currently {state}."

# Pot container for holding milk
class Pot(Container):
    def __init__(self):
        Container.__init__(self, "pot")
        self.properties["containerPrefix"] = "in"

# Milk with temperature property
class Milk(GameObject):
    def __init__(self, temperature):
        GameObject.__init__(self, "milk")
        self.properties["temperature"] = temperature

    def makeDescriptionStr(self, makeDetailed=False):
        return "some milk"

# Thermometer for checking temperatures
class Thermometer(GameObject):
    def __init__(self):
        GameObject.__init__(self, "thermometer")

    def useWithObject(self, patientObject):
        if patientObject.getProperty("temperature") is not None:
            return f"The thermometer shows the {patientObject.name} is {patientObject.getProperty('temperature'):.1f}°C.", True
        else:
            return f"You can't measure the temperature of the {patientObject.name}.", False

# Main game class
class HeatMilkGame(TextGame):
    def __init__(self, randomSeed):
        self.answer = None
        TextGame.__init__(self, randomSeed)

    def initializeWorld(self):
        world = World("kitchen")
        world.addObject(self.agent)
        
        # Create objects
        stove = Stove()
        fridge = Fridge()
        thermometer = Thermometer()
        
        # Create milk and pot
        milk = Milk(4.0)  # Start at fridge temperature
        pot = Pot()
        pot.addObject(milk)
        
        # Add pot to fridge
        fridge.addObject(pot)
        
        # Add objects to world
        world.addObject(stove)
        world.addObject(fridge)
        world.addObject(thermometer)
        
        return world

    def getTaskDescription(self):
        return "Your task is to heat milk to a suitable temperature for a baby (37-40°C) using the stove and thermometer, then feed the baby."

    def generatePossibleActions(self):
        allObjects = self.makeNameToObjectDict()
        self.possibleActions = {}
        
        # Actions with no arguments
        for action in [("look around", "look around"), ("look", "look around"), ("inventory", "inventory")]:
            self.addAction(action[0], [action[1]])
        
        # Actions with one object argument
        for objReferent, objs in allObjects.items():
            for obj in objs:
                # Basic actions
                self.addAction(f"take {objReferent}", ["take", obj])
                self.addAction(f"take {objReferent} from {obj.parentContainer.getReferents()[0]}", ["take", obj])
                
                # Device actions
                if obj.getProperty("isDevice"):
                    self.addAction(f"turn on {objReferent}", ["turnon", obj])
                    self.addAction(f"turn off {objReferent}", ["turnoff", obj])
                
                # Container actions
                if obj.getProperty("isOpenable"):
                    if obj.getProperty("isOpen"):
                        self.addAction(f"close {objReferent}", ["close", obj])
                    else:
                        self.addAction(f"open {objReferent}", ["open", obj])
                
                # Special actions for milk
                if obj.name == "milk":
                    self.addAction(f"feed baby with {objReferent}", ["feed", obj])
                    self.addAction(f"drink {objReferent}", ["drink", obj])
        
        # Actions with two object arguments
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if obj1 != obj2:
                            # Put action
                            containerPrefix = obj2.properties.get("containerPrefix", "in") if obj2.properties.get("isContainer") else "in"
                            self.addAction(f"put {objReferent1} {containerPrefix} {objReferent2}", ["put", obj1, obj2])
                            
                            # Use thermometer on objects
                            if isinstance(obj1, Thermometer):
                                self.addAction(f"use {objReferent1} on {objReferent2}", ["use", obj1, obj2])
        
        return self.possibleActions

    # Action implementations
    def actionTurnOn(self, device):
        return device.turnOn()

    def actionTurnOff(self, device):
        return device.turnOff()

    def actionOpen(self, container):
        return container.openContainer()

    def actionClose(self, container):
        return container.closeContainer()

    def actionUse(self, device, patient):
        return device.useWithObject(patient)[0]

    def actionFeed(self, milk):
        if milk.parentContainer != self.agent:
            return "You need to have the milk to feed the baby."
        
        temp = milk.getProperty("temperature")
        if 37 <= temp <= 40:
            self.gameOver = True
            self.gameWon = True
            return "You feed the baby with the milk. The temperature is perfect. Well done!"
        else:
            self.gameOver = True
            self.gameWon = False
            return f"The milk is {temp:.1f}°C, which is not suitable for the baby. The baby refuses to drink it."

    def actionDrink(self, milk):
        if milk.parentContainer != self.agent:
            return "You don't have the milk to drink."
        
        self.gameOver = True
        self.gameWon = False
        return "You drank the milk. But remember, this milk is for the baby! Game over."

    def step(self, actionStr):
        self.observationStr = ""
        reward = 0
        
        if actionStr not in self.possibleActions:
            self.observationStr = "I don't understand that."
            return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)
        
        self.numSteps += 1
        actions = self.possibleActions[actionStr]
        action = actions[0] if len(actions) > 1 else actions[0]
        actionVerb = action[0]
        
        # Action dispatch
        if actionVerb == "look around":
            self.observationStr = self.rootObject.makeDescriptionStr()
        elif actionVerb == "inventory":
            self.observationStr = self.actionInventory()
        elif actionVerb == "take":
            self.observationStr = self.actionTake(action[1])
        elif actionVerb == "put":
            self.observationStr = self.actionPut(action[1], action[2])
        elif actionVerb == "turnon":
            self.observationStr = self.actionTurnOn(action[1])
        elif actionVerb == "turnoff":
            self.observationStr = self.actionTurnOff(action[1])
        elif actionVerb == "open":
            self.observationStr = self.actionOpen(action[1])
        elif actionVerb == "close":
            self.observationStr = self.actionClose(action[1])
        elif actionVerb == "use":
            self.observationStr = self.actionUse(action[1], action[2])
        elif actionVerb == "feed":
            self.observationStr = self.actionFeed(action[1])
        elif actionVerb == "drink":
            self.observationStr = self.actionDrink(action[1])
        
        # Update world state
        self.doWorldTick()
        
        # Calculate score
        lastScore = self.score
        self.calculateScore()
        reward = self.score - lastScore
        
        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    def calculateScore(self):
        self.score = 0
        if self.gameWon:
            self.score = 1

if __name__ == "__main__":
    main(HeatMilkGame(randomSeed=0))
