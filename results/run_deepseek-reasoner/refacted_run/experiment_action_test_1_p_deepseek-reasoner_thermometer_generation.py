from data.library.GameBasic import *

# Define the Milk class
class Milk(GameObject):
    def __init__(self, temperature):
        super().__init__("milk")
        self.properties["temperature"] = temperature
        self.properties["isDrinkable"] = True

    def makeDescriptionStr(self, makeDetailed=False):
        return "some milk"

# Define the Pot class (container for milk)
class Pot(Container):
    def __init__(self):
        GameObject.__init__(self, "pot")
        Container.__init__(self, "pot")
        self.properties["containerPrefix"] = "in"
        self.properties["isHeated"] = False

    def makeDescriptionStr(self, makeDetailed=False):
        if self.contains:
            contents = ", ".join([obj.makeDescriptionStr() for obj in self.contains])
            return f"a pot containing {contents}"
        return "an empty pot"

# Define the Stove class (heating device)
class Stove(Device, Container):
    def __init__(self):
        GameObject.__init__(self, "stove")
        Container.__init__(self, "stove")
        Device.__init__(self, "stove")
        self.properties["temperature_increase_per_tick"] = 5
        self.properties["max_temperature"] = 100
        self.properties["containerPrefix"] = "on"
        self.properties["isContainer"] = True
        self.properties["isOpenable"] = False

    def makeDescriptionStr(self, makeDetailed=False):
        return Device.makeDescriptionStr(self)  # Inherits device status description

# Define the Fridge class (cooling device)
class Fridge(Device, Container):
    def __init__(self):
        GameObject.__init__(self, "fridge")
        Container.__init__(self, "fridge")
        Device.__init__(self, "fridge")
        self.properties["temperature_decrease_per_tick"] = 3
        self.properties["min_temperature"] = 4
        self.properties["isContainer"] = True
        self.properties["isOpenable"] = True
        self.properties["isOpen"] = False  # Start closed

    def makeDescriptionStr(self, makeDetailed=False):
        status = "open" if self.properties["isOpen"] else "closed"
        return f"a fridge (currently {status})"

# Define the Thermometer class
class Thermometer(GameObject):
    def __init__(self):
        super().__init__("thermometer")
        self.properties["isUsable"] = True

    def useWithObject(self, obj):
        if obj.getProperty("temperature") is not None:
            return f"The thermometer reads {obj.getProperty('temperature')}°C.", True
        return "The thermometer doesn't give a reading for that object.", False

    def makeDescriptionStr(self, makeDetailed=False):
        return "a thermometer"

# World class for the kitchen
class KitchenWorld(World):
    def __init__(self):
        super().__init__("kitchen")

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "You are in a kitchen. You see:\n"
        for obj in self.contains:
            outStr += "\t" + obj.makeDescriptionStr() + "\n"
        return outStr

# Main game implementation
class HeatMilkGame(TextGame):
    def __init__(self, randomSeed):
        super().__init__(randomSeed=randomSeed)
        self.fed_baby = False
        self.milk = None
        
    def initializeWorld(self):
        world = KitchenWorld()
        
        # Add agent
        world.addObject(self.agent)
        
        # Create and add objects
        stove = Stove()
        fridge = Fridge()
        pot = Pot()
        milk = Milk(4)  # Start at fridge temperature
        thermometer = Thermometer()
        
        # Add milk to pot
        pot.addObject(milk)
        self.milk = milk  # Save reference for later
        
        # Add pot to fridge
        fridge.addObject(pot)
        
        # Add all objects to world
        world.addObject(stove)
        world.addObject(fridge)
        world.addObject(thermometer)
        
        return world

    def getTaskDescription(self):
        return "Your task is to heat milk to a suitable temperature for a baby (36-40°C) and then feed the baby."

    def registerActions(self):
        # Actions with zero arguments
        self.addAction("look around", ["look around"])
        self.addAction("look", ["look around"])
        self.addAction("inventory", ["inventory"])
        
        # Get all object references
        allObjects = self.makeNameToObjectDict()
        
        # Add actions for each object
        for objName, objs in allObjects.items():
            for obj in objs:
                # Take actions
                self.addAction(f"take {objName}", ["take", obj])
                if obj.parentContainer:
                    containerName = obj.parentContainer.getReferents()[0]
                    self.addAction(f"take {objName} from {containerName}", ["take", obj])
                
                # Examine actions
                self.addAction(f"examine {objName}", ["examine", obj])
                
                # Open/close actions for openable containers
                if obj.getProperty("isOpenable"):
                    self.addAction(f"open {objName}", ["open", obj])
                    self.addAction(f"close {objName}", ["close", obj])
                
                # Turn on/off actions for devices
                if obj.getProperty("isDevice"):
                    self.addAction(f"turn on {objName}", ["turn on", obj])
                    self.addAction(f"turn off {objName}", ["turn off", obj])
                
                # Put actions
                for containerName, containers in allObjects.items():
                    for container in containers:
                        if container != obj and container.getProperty("isContainer"):
                            prefix = container.properties.get("containerPrefix", "in")
                            self.addAction(f"put {objName} {prefix} {containerName}", ["put", obj, container])
                
                # Use thermometer on objects
                if isinstance(obj, Thermometer):
                    for targetName, targets in allObjects.items():
                        for target in targets:
                            if target != obj:
                                self.addAction(f"use {objName} on {targetName}", ["use", obj, target])
                
                # Feed baby with milk
                if "milk" in objName.lower():
                    self.addAction(f"feed baby with {objName}", ["feed baby", obj])
                
                # Drink milk (distractor action)
                if "milk" in objName.lower():
                    self.addAction(f"drink {objName}", ["drink", obj])

    def generatePossibleActions(self):
        self.possibleActions = {}
        self.registerActions()
        return self.possibleActions

    # Action handlers
    def actionOpen(self, obj):
        return obj.openContainer()
    
    def actionClose(self, obj):
        return obj.closeContainer()
    
    def actionTurnOn(self, obj):
        return obj.turnOn()
    
    def actionTurnOff(self, obj):
        return obj.turnOff()
    
    def actionUse(self, deviceObj, patientObject):
        if isinstance(deviceObj, Thermometer):
            if deviceObj.parentContainer == self.agent:
                return deviceObj.useWithObject(patientObject)[0]
            return "You need to take the thermometer first."
        return "You can't use that that way."
    
    def actionFeedBaby(self, milkObj):
        if milkObj.parentContainer != self.agent:
            return "You don't have that in your inventory."
        
        temp = milkObj.getProperty("temperature")
        if 36 <= temp <= 40:
            self.fed_baby = True
            return "You successfully feed the baby with warm milk. Perfect temperature!"
        elif temp < 36:
            return "The milk is too cold for the baby!"
        else:
            return "The milk is too hot for the baby!"
    
    def actionDrink(self, milkObj):
        if milkObj.parentContainer != self.agent:
            return "You don't have that in your inventory."
        return "You drink the milk. It tastes fine, but remember you need to feed the baby!"
    
    def step(self, actionStr):
        self.observationStr = ""
        reward = 0
        
        # Check if game is already over
        if self.gameOver:
            return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)
        
        self.numSteps += 1
        
        # Parse the action
        if actionStr not in self.possibleActions:
            self.observationStr = "I don't understand that."
            return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)
        
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
            self.observationStr, _ = self.actionOpen(action[1])
        elif actionVerb == "close":
            self.observationStr, _ = self.actionClose(action[1])
        elif actionVerb == "turn on":
            self.observationStr, _ = self.actionTurnOn(action[1])
        elif actionVerb == "turn off":
            self.observationStr, _ = self.actionTurnOff(action[1])
        elif actionVerb == "use":
            self.observationStr = self.actionUse(action[1], action[2])
        elif actionVerb == "feed baby":
            self.observationStr = self.actionFeedBaby(action[1])
        elif actionVerb == "drink":
            self.observationStr = self.actionDrink(action[1])
        else:
            self.observationStr = "ERROR: Unknown action."
        
        # Update world state
        self.doWorldTick()
        
        # Calculate reward and score
        lastScore = self.score
        self.calculateScore()
        reward = self.score - lastScore
        
        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)
    
    def doWorldTick(self):
        super().doWorldTick()
        
        # Update milk temperature based on location
        if self.milk:
            # If milk is in fridge and fridge is closed and on
            if self.milk.parentContainer and self.milk.parentContainer.parentContainer:
                fridge = self.milk.parentContainer.parentContainer
                if (isinstance(fridge, Fridge) and 
                    fridge.getProperty("isOn") and 
                    not fridge.getProperty("isOpen")):
                    new_temp = max(
                        self.milk.properties["temperature"] - fridge.getProperty("temperature_decrease_per_tick"),
                        fridge.getProperty("min_temperature")
                    )
                    self.milk.properties["temperature"] = new_temp
            
            # If milk is in pot on stove and stove is on
            if self.milk.parentContainer and self.milk.parentContainer.parentContainer:
                stove = self.milk.parentContainer.parentContainer
                if (isinstance(stove, Stove) and 
                    stove.getProperty("isOn")):
                    new_temp = min(
                        self.milk.properties["temperature"] + stove.getProperty("temperature_increase_per_tick"),
                        stove.getProperty("max_temperature")
                    )
                    self.milk.properties["temperature"] = new_temp
    
    def calculateScore(self):
        # Base score
        self.score = 0
        
        # Winning condition
        if self.fed_baby:
            self.score = 1
            self.gameOver = True
            self.gameWon = True
        elif self.numSteps >= 50:
            self.gameOver = True
            self.gameWon = False

# Run the game
if __name__ == "__main__":
    game = HeatMilkGame(randomSeed=0)
    main(game)
