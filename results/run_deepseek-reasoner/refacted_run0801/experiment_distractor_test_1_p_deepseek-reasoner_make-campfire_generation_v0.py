from data.library.GameBasic import *

class Stove(Container, Device):
    def __init__(self):
        Container.__init__(self, "stove")
        Device.__init__(self, "stove")
        self.properties.update({
            "containerPrefix": "on",
            "temperature_increase_per_tick": 10.0,
            "max_temperature": 100.0,
            "isOpenable": False
        })
    
    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a stove"
        if self.properties["isOn"]:
            outStr += " that is currently on"
        else:
            outStr += " that is currently off"
        return outStr

class Pot(Container):
    def __init__(self):
        Container.__init__(self, "pot")
        self.on_stove = None  # Reference to stove if placed on it
    
    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a pot"
        if self.contains:
            outStr += f" containing {self.contains[0].makeDescriptionStr()}"
        if self.on_stove:
            outStr += " that is on the stove"
        return outStr

class Milk(GameObject):
    def __init__(self):
        GameObject.__init__(self, "milk")
        self.properties["temperature"] = 4.0  # Start at fridge temperature
    
    def makeDescriptionStr(self, makeDetailed=False):
        return "some milk"

class Fridge(Container, Device):
    def __init__(self):
        Container.__init__(self, "fridge")
        Device.__init__(self, "fridge")
        self.properties.update({
            "isOpenable": True,
            "isOpen": False,
            "temperature_decrease_per_tick": 1.0,
            "min_temperature": 4.0
        })
    
    def tick(self):
        # Cool contents when closed and turned on
        if self.properties["isOn"] and not self.properties["isOpen"]:
            for obj in self.getAllContainedObjectsRecursive():
                if "temperature" in obj.properties:
                    obj.properties["temperature"] = max(
                        obj.properties["temperature"] - self.properties["temperature_decrease_per_tick"],
                        self.properties["min_temperature"]
                    )
    
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
        if "temperature" in patientObject.properties:
            temp = patientObject.properties["temperature"]
            return f"The thermometer shows {temp:.1f}°C. Ideal temperature for baby milk is between 37-40°C.", True
        return f"You can't measure the temperature of the {patientObject.name}.", False
    
    def makeDescriptionStr(self, makeDetailed=False):
        return "a thermometer"

class KitchenWorld(World):
    def __init__(self):
        World.__init__(self, "kitchen")

class HeatMilkGame(TextGame):
    def __init__(self, randomSeed):
        TextGame.__init__(self, randomSeed)
    
    def initializeWorld(self):
        world = KitchenWorld()
        
        # Add agent
        world.addObject(self.agent)
        
        # Create and add objects
        fridge = Fridge()
        stove = Stove()
        pot = Pot()
        milk = Milk()
        thermometer = Thermometer()
        
        # Set initial positions
        pot.addObject(milk)
        fridge.addObject(pot)
        world.addObject(fridge)
        world.addObject(stove)
        world.addObject(thermometer)
        
        # Turn on devices by default
        fridge.properties["isOn"] = True
        stove.properties["isOn"] = False  # Stove starts off
        
        return world
    
    def getTaskDescription(self):
        return "Your task is to heat milk to the ideal temperature (37-40°C) for a baby using the stove."
    
    def generatePossibleActions(self):
        # Get all objects
        allObjects = self.makeNameToObjectDict()
        
        # Initialize possible actions dictionary
        self.possibleActions = {}
        
        # Actions with zero arguments
        self.addAction("look around", ["look around"])
        self.addAction("look", ["look around"])
        self.addAction("inventory", ["inventory"])
        
        # Actions with one object argument
        for objName, objs in allObjects.items():
            for obj in objs:
                self.addAction(f"take {objName}", ["take", obj])
                self.addAction(f"examine {objName}", ["examine", obj])
                self.addAction(f"open {objName}", ["open", obj])
                self.addAction(f"close {objName}", ["close", obj])
                self.addAction(f"turn on {objName}", ["turn on", obj])
                self.addAction(f"turn off {objName}", ["turn off", obj])
        
        # Actions with two object arguments
        for obj1Name, objs1 in allObjects.items():
            for obj2Name, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if obj1 != obj2:
                            # Put action
                            containerPrefix = "in"
                            if obj2.properties.get("isContainer", False):
                                containerPrefix = obj2.properties.get("containerPrefix", "in")
                            self.addAction(f"put {obj1Name} {containerPrefix} {obj2Name}", ["put", obj1, obj2])
                            
                            # Use action
                            self.addAction(f"use {obj1Name} on {obj2Name}", ["use", obj1, obj2])
        
        # Custom actions for milk
        milkObjs = allObjects.get("milk", [])
        for milk in milkObjs:
            self.addAction(f"feed baby with {milk.getReferents()[0]}", ["feed_baby", milk])
            self.addAction(f"drink {milk.getReferents()[0]}", ["drink", milk])
        
        return self.possibleActions
    
    def actionOpen(self, obj):
        if obj.getProperty("isOpenable"):
            return obj.openContainer()
        return "You can't open that."
    
    def actionClose(self, obj):
        if obj.getProperty("isOpenable"):
            return obj.closeContainer()
        return "You can't close that."
    
    def actionTurnOn(self, obj):
        if obj.getProperty("isDevice"):
            return obj.turnOn()
        return "You can't turn that on."
    
    def actionTurnOff(self, obj):
        if obj.getProperty("isDevice"):
            return obj.turnOff()
        return "You can't turn that off."
    
    def actionUse(self, device, patient):
        if device.getProperty("isDevice"):
            # Must have device in inventory
            if device.parentContainer != self.agent:
                return f"You need to have the {device.name} in your inventory to use it."
            return device.useWithObject(patient)
        return "You can't use that as a device."
    
    def actionFeedBaby(self, milk):
        if milk.parentContainer != self.agent:
            return "You need to have the milk in your inventory to feed the baby."
        
        temp = milk.properties["temperature"]
        if 37 <= temp <= 40:
            self.gameOver = True
            self.gameWon = True
            return "You feed the baby with the milk. The temperature is perfect! The baby is happy and stops crying. Task completed!"
        elif temp < 37:
            return "The milk is too cold for the baby! It needs to be between 37-40°C."
        else:
            return "The milk is too hot for the baby! It needs to be between 37-40°C."
    
    def actionDrink(self, milk):
        # Remove milk from game
        milk.removeSelfFromContainer()
        temp = milk.properties["temperature"]
        
        if temp < 37:
            msg = "cold"
        elif temp > 40:
            msg = "hot"
        else:
            msg = "perfect"
        
        return f"You drink the milk. It's too {msg}! Now there's no milk left for the baby."
    
    def step(self, actionStr):
        self.observationStr = ""
        reward = 0
        
        if actionStr not in self.possibleActions:
            self.observationStr = "I don't understand that."
            return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)
        
        self.numSteps += 1
        action = self.possibleActions[actionStr][0]
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
        elif actionVerb == "open":
            self.observationStr = self.actionOpen(action[1])
        elif actionVerb == "close":
            self.observationStr = self.actionClose(action[1])
        elif actionVerb == "turn on":
            self.observationStr = self.actionTurnOn(action[1])
        elif actionVerb == "turn off":
            self.observationStr = self.actionTurnOff(action[1])
        elif actionVerb == "put":
            self.observationStr = self.actionPut(action[1], action[2])
            
            # Special handling for putting pot on stove
            if isinstance(action[1], Pot) and isinstance(action[2], Stove):
                action[1].on_stove = action[2]
            # Handle removing pot from stove
            elif isinstance(action[1], Pot) and not isinstance(action[2], Stove) and action[1].on_stove:
                action[1].on_stove = None
        elif actionVerb == "use":
            self.observationStr = self.actionUse(action[1], action[2])
        elif actionVerb == "feed_baby":
            self.observationStr = self.actionFeedBaby(action[1])
        elif actionVerb == "drink":
            self.observationStr = self.actionDrink(action[1])
        
        # Update world state
        self.doWorldTick()
        
        # Update score
        lastScore = self.score
        self.calculateScore()
        reward = self.score - lastScore
        
        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)
    
    def calculateScore(self):
        # Check win condition
        if self.gameWon:
            self.score = 100
            return
        
        # Check if milk is gone (drunk)
        milk_exists = any(obj.name == "milk" for obj in self.rootObject.getAllContainedObjectsRecursive())
        if not milk_exists:
            self.gameOver = True
            self.score = -10
            return
        
        # Base score based on steps
        self.score = max(0, 10 - self.numSteps // 2)

if __name__ == "__main__":
    main(HeatMilkGame(randomSeed=0))
