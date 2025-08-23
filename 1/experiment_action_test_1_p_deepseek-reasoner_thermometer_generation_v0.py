from data.library.GameBasic import *

# Define game objects
class Milk(GameObject):
    def __init__(self, temperature):
        super().__init__("milk")
        self.properties["temperature"] = temperature

    def makeDescriptionStr(self, makeDetailed=False):
        return "some milk"

class Pot(Container):
    def __init__(self, temperature):
        GameObject.__init__(self, "pot")
        Container.__init__(self, "pot")
        self.properties["temperature"] = temperature
        self.properties["containerPrefix"] = "in"

    def tick(self):
        # Propagate pot temperature to contained objects
        for obj in self.contains:
            if "temperature" in obj.properties:
                obj.properties["temperature"] = self.properties["temperature"]

    def makeDescriptionStr(self, makeDetailed=False):
        if len(self.contains) == 0:
            return "an empty pot"
        else:
            contents = [obj.makeDescriptionStr() for obj in self.contains]
            return f"a pot containing {', '.join(contents)}"

class Stove(Device, Container):
    def __init__(self):
        GameObject.__init__(self, "stove")
        Container.__init__(self, "stove")
        Device.__init__(self, "stove")
        self.properties["temperature_increase_per_tick"] = 5.0
        self.properties["max_temperature"] = 100.0
        self.properties["containerPrefix"] = "on"
        self.properties["isOpenable"] = False

    def tick(self):
        if self.properties["isOn"]:
            for obj in self.contains:
                if "temperature" in obj.properties:
                    current_temp = obj.properties["temperature"]
                    new_temp = current_temp + self.properties["temperature_increase_per_tick"]
                    if new_temp > self.properties["max_temperature"]:
                        new_temp = self.properties["max_temperature"]
                    obj.properties["temperature"] = new_temp

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a stove that is currently "
        if self.properties["isOn"]:
            outStr += "on"
        else:
            outStr += "off"
        return outStr

class Fridge(Device, Container):
    def __init__(self):
        GameObject.__init__(self, "fridge")
        Container.__init__(self, "fridge")
        Device.__init__(self, "fridge")
        self.properties["temperature_decrease_per_tick"] = 2.0
        self.properties["min_temperature"] = 4.0
        self.properties["isOn"] = True
        self.properties["isOpenable"] = True
        self.properties["isOpen"] = False
        self.properties["containerPrefix"] = "in"

    def tick(self):
        if self.properties["isOn"] and not self.properties["isOpen"]:
            for obj in self.contains:
                if "temperature" in obj.properties:
                    current_temp = obj.properties["temperature"]
                    new_temp = current_temp - self.properties["temperature_decrease_per_tick"]
                    if new_temp < self.properties["min_temperature"]:
                        new_temp = self.properties["min_temperature"]
                    obj.properties["temperature"] = new_temp

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a fridge that is currently "
        if self.properties["isOpen"]:
            outStr += "open"
        else:
            outStr += "closed"
        return outStr

class Thermometer(GameObject):
    def __init__(self):
        super().__init__("thermometer")

    def useWithObject(self, patientObject):
        if "temperature" in patientObject.properties:
            temp = patientObject.properties["temperature"]
            return f"The thermometer shows {temp:.1f}°C.", True
        return "The thermometer doesn't work on that object.", False

    def makeDescriptionStr(self, makeDetailed=False):
        return "a thermometer"

class KitchenWorld(World):
    def __init__(self):
        super().__init__("kitchen")

# Game implementation
class BabyMilkGame(TextGame):
    def __init__(self, randomSeed):
        self.drank_milk = False
        self.fed_baby = False
        self.fed_milk = None
        TextGame.__init__(self, randomSeed)

    def initializeWorld(self):
        world = KitchenWorld()
        world.addObject(self.agent)
        
        # Create appliances
        fridge = Fridge()
        stove = Stove()
        thermometer = Thermometer()
        
        # Create pot with milk
        pot = Pot(temperature=4.0)
        milk = Milk(temperature=4.0)
        pot.addObject(milk)
        
        # Put pot in fridge
        fridge.addObject(pot)
        
        # Add objects to world
        world.addObject(fridge)
        world.addObject(stove)
        world.addObject(thermometer)
        
        return world

    def getTaskDescription(self):
        return "Your task is to heat milk to a suitable temperature for a baby (37-40°C) and then feed the baby."

    def generatePossibleActions(self):
        allObjects = self.makeNameToObjectDict()
        self.possibleActions = {}
        
        # Basic actions
        self.addAction("look around", ["look around"])
        self.addAction("look", ["look around"])
        self.addAction("inventory", ["inventory"])
        
        # Actions with single object
        for objReferent, objs in allObjects.items():
            for obj in objs:
                # Open/close for openable containers
                if obj.getProperty("isOpenable"):
                    if not obj.getProperty("isOpen"):
                        self.addAction(f"open {objReferent}", ["open", obj])
                    else:
                        self.addAction(f"close {objReferent}", ["close", obj])
                
                # Turn on/off for devices
                if obj.getProperty("isActivatable"):
                    if not obj.getProperty("isOn"):
                        self.addAction(f"turn on {objReferent}", ["turn on", obj])
                    else:
                        self.addAction(f"turn off {objReferent}", ["turn off", obj])
                
                # Take and examine actions
                self.addAction(f"take {objReferent}", ["take", obj])
                if obj.parentContainer is not None:
                    containerReferent = obj.parentContainer.getReferents()[0]
                    self.addAction(f"take {objReferent} from {containerReferent}", ["take", obj])
                self.addAction(f"examine {objReferent}", ["examine", obj])
        
        # Actions with two objects
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if obj1 != obj2:
                            # Put action
                            if obj2.getProperty("isContainer"):
                                prefix = obj2.properties["containerPrefix"]
                                self.addAction(f"put {objReferent1} {prefix} {objReferent2}", ["put", obj1, obj2])
                            
                            # Use action
                            self.addAction(f"use {objReferent1} on {objReferent2}", ["use", obj1, obj2])
        
        # Special actions for milk
        for obj in self.agent.contains:
            if obj.name == "milk":
                milkReferent = obj.getReferents()[0]
                self.addAction(f"drink {milkReferent}", ["drink", obj])
                self.addAction(f"feed baby with {milkReferent}", ["feed baby", obj])
        
        return self.possibleActions

    # Action implementations
    def actionOpen(self, obj):
        return obj.openContainer()[0]
    
    def actionClose(self, obj):
        return obj.closeContainer()[0]
    
    def actionTurnOn(self, obj):
        return obj.turnOn()[0]
    
    def actionTurnOff(self, obj):
        return obj.turnOff()[0]
    
    def actionDrink(self, milk):
        if milk.parentContainer == self.agent:
            self.agent.removeObject(milk)
            self.drank_milk = True
            return "You drink the milk. It tastes good but is not for you!"
        return "You don't have that milk."
    
    def actionFeedBaby(self, milk):
        if milk.parentContainer == self.agent:
            self.fed_baby = True
            self.fed_milk = milk
            return "You feed the baby with the milk."
        return "You need the milk in your inventory to feed the baby."
    
    def actionUse(self, device, patient):
        if isinstance(device, Thermometer):
            return device.useWithObject(patient)[0]
        return "You're not sure how to use that."

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
        
        # Handle different actions
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
        
        # Update world state
        self.doWorldTick()
        
        # Calculate score
        lastScore = self.score
        self.calculateScore()
        reward = self.score - lastScore
        
        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    def calculateScore(self):
        self.score = 0
        self.gameOver = False
        self.gameWon = False
        
        if self.drank_milk:
            self.gameOver = True
            self.score = 0
            return
        
        if self.fed_baby and self.fed_milk:
            self.gameOver = True
            temp = self.fed_milk.properties["temperature"]
            if 37 <= temp <= 40:
                self.score = 1
                self.gameWon = True
            else:
                self.score = 0
                self.gameWon = False

# Main entry point
if __name__ == "__main__":
    main(game = BabyMilkGame(randomSeed=0))
