# Task: Create a micro-simulation that models how to heat milk to a temperature that is suitable for a baby using a stove.
# Environment: kitchen
# Task-critical Objects: Stove, Pot, Milk, Fridge, Thermometer
# High-level object classes: Device (Stove, Fridge), Container (Stove, Pot, Fridge) 
# Critical properties: temperature (Milk), temperature_increase_per_tick (Stove), temperature_decrease_per_tick (fridge), max_temperature (Stove), min_temperature (fridge)
# Actions: look, inventory, examine, take/put object, open/close container, turn on/off device, use thermometer on object, feed baby with milk
# Distractor Actions: drink milk
# High-level solution procedure: open fridge, take pot containing milk, put the pot on the stove, turn on the stove, use the thermometer to moniter the milk temperature till the temperature is suitable for a baby to drink, feed baby

from data.library.GameBasic import *

class Stove(Container, Device):
    def __init__(self, name):
        # Prevent multiple constructor runs
        if hasattr(self, "constructorsRun"):
            return
        GameObject.__init__(self, name)
        Container.__init__(self, name)
        Device.__init__(self, name)
        self.constructorsRun.append("Stove")
        
        # Set properties
        self.properties["isContainer"] = True
        self.properties["isMoveable"] = False
        self.properties["temperature_increase_per_tick"] = 5.0
        self.properties["max_temperature"] = 100.0
        
    def makeDescriptionStr(self, makeDetailed=False):
        return f"a {self.name}"

class Fridge(Container, Device):
    def __init__(self, name):
        # Prevent multiple constructor runs
        if hasattr(self, "constructorsRun"):
            return
        GameObject.__init__(self, name)
        Container.__init__(self, name)
        Device.__init__(self, name)
        self.constructorsRun.append("Fridge")
        
        # Set properties
        self.properties["isContainer"] = True
        self.properties["isOpenable"] = True
        self.properties["isOpen"] = False
        self.properties["isMoveable"] = False
        self.properties["temperature_decrease_per_tick"] = 2.0
        self.properties["min_temperature"] = 4.0
        
    def makeDescriptionStr(self, makeDetailed=False):
        if self.getProperty("isOpen"):
            return f"an open {self.name}"
        else:
            return f"a closed {self.name}"

class Pot(Container):
    def __init__(self, name):
        GameObject.__init__(self, name)
        Container.__init__(self, name)
        self.properties["isMoveable"] = True
        
    def tick(self):
        # If the pot is on a stove that is on, heat any milk inside
        if self.parentContainer and isinstance(self.parentContainer, Stove) and self.parentContainer.getProperty("isOn"):
            stove = self.parentContainer
            for obj in self.contains:
                if isinstance(obj, Milk):
                    new_temp = obj.properties["temperature"] + stove.properties["temperature_increase_per_tick"]
                    # Cap at stove max temperature
                    if new_temp > stove.properties["max_temperature"]:
                        new_temp = stove.properties["max_temperature"]
                    obj.properties["temperature"] = new_temp
        
        # If the pot is in a fridge that is on and closed, cool any milk inside
        elif self.parentContainer and isinstance(self.parentContainer, Fridge) and self.parentContainer.getProperty("isOn") and not self.parentContainer.getProperty("isOpen"):
            fridge = self.parentContainer
            for obj in self.contains:
                if isinstance(obj, Milk):
                    new_temp = obj.properties["temperature"] - fridge.properties["temperature_decrease_per_tick"]
                    # Cap at fridge min temperature
                    if new_temp < fridge.properties["min_temperature"]:
                        new_temp = fridge.properties["min_temperature"]
                    obj.properties["temperature"] = new_temp
                    
    def makeDescriptionStr(self, makeDetailed=False):
        return f"a {self.name}"

class Milk(GameObject):
    def __init__(self, initial_temp):
        GameObject.__init__(self, "milk")
        self.properties["temperature"] = initial_temp
        
    def makeDescriptionStr(self, makeDetailed=False):
        return "milk"

class Thermometer(Device):
    def __init__(self):
        GameObject.__init__(self, "thermometer")
        Device.__init__(self, "thermometer")
        self.properties["isMoveable"] = True
        
    def useWithObject(self, patientObject):
        # Check if we're being used on a pot
        if isinstance(patientObject, Pot):
            # Check if pot contains milk
            milk_list = patientObject.containsItemWithName("milk")
            if milk_list:
                milk = milk_list[0]
                return f"The thermometer shows the milk is {milk.properties['temperature']:.1f}°C.", True
            else:
                return "There is no milk in the pot to measure.", False
        # Check if we're being used directly on milk
        elif isinstance(patientObject, Milk):
            return f"The thermometer shows the milk is {patientObject.properties['temperature']:.1f}°C.", True
        else:
            return "You can't use the thermometer on that.", False

class HeatMilkForBabyGame(TextGame):
    def __init__(self, randomSeed):
        # Initialize parent
        TextGame.__init__(self, randomSeed)
        
        # Game state
        self.answer_temp = None
        
    def initializeWorld(self):
        world = World("kitchen")
        
        # Add agent
        world.addObject(self.agent)
        
        # Create stove
        stove = Stove("stove")
        world.addObject(stove)
        
        # Create fridge
        fridge = Fridge("fridge")
        world.addObject(fridge)
        fridge.properties["isOn"] = True  # Fridge is always on
        
        # Create pot
        pot = Pot("pot")
        
        # Create milk (starting cold)
        milk = Milk(4.0)  # 4°C from fridge
        
        # Put milk in pot
        pot.addObject(milk)
        
        # Put pot in fridge
        fridge.addObject(pot)
        
        # Create thermometer
        thermometer = Thermometer()
        world.addObject(thermometer)  # Place in kitchen
        
        return world

    def getTaskDescription(self):
        return "Your task is to heat milk to a suitable temperature for a baby (37-40°C) using the stove and feed the baby."
    
    def generatePossibleActions(self):
        # Get all objects
        allObjects = self.makeNameToObjectDict()
        
        # Make dictionary of actions
        self.possibleActions = {}
        
        # Actions with no arguments
        self.addAction("look around", ["look around"])
        self.addAction("look", ["look around"])
        self.addAction("inventory", ["inventory"])
        
        # Actions with one object argument
        for objName, objs in allObjects.items():
            for obj in objs:
                # Take object
                self.addAction(f"take {objName}", ["take", obj])
                if obj.parentContainer:
                    containerName = obj.parentContainer.getReferents()[0]
                    self.addAction(f"take {objName} from {containerName}", ["take", obj])
                
                # Turn on/off devices
                if isinstance(obj, Device):
                    self.addAction(f"turn on {objName}", ["turn on", obj])
                    self.addAction(f"turn off {objName}", ["turn off", obj])
                
                # Open/close containers
                if obj.getProperty("isOpenable"):
                    self.addAction(f"open {objName}", ["open", obj])
                    self.addAction(f"close {objName}", ["close", obj])
                
                # Use thermometer on object
                if objName != "thermometer":
                    self.addAction(f"use thermometer on {objName}", ["use", allObjects["thermometer"][0], obj])
                
                # Feed baby with object
                self.addAction(f"feed baby with {objName}", ["feed", obj])
                
                # Drink from object (distractor)
                self.addAction(f"drink {objName}", ["drink", obj])
        
        # Actions with two object arguments
        for objName1, objs1 in allObjects.items():
            for objName2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if obj1 != obj2:
                            # Put object in container
                            if obj2.getProperty("isContainer"):
                                containerPrefix = obj2.properties.get("containerPrefix", "in")
                                self.addAction(f"put {objName1} {containerPrefix} {objName2}", ["put", obj1, obj2])
        
        return self.possibleActions

    def actionTurnOn(self, obj):
        if not isinstance(obj, Device):
            return "You can't turn that on.", False
        return obj.turnOn()

    def actionTurnOff(self, obj):
        if not isinstance(obj, Device):
            return "You can't turn that off.", False
        return obj.turnOff()

    def actionOpen(self, obj):
        if not obj.getProperty("isOpenable"):
            return "You can't open that.", False
        return obj.openContainer()

    def actionClose(self, obj):
        if not obj.getProperty("isOpenable"):
            return "You can't close that.", False
        return obj.closeContainer()

    def actionUse(self, tool, patientObject):
        # Agent must be holding the tool
        if tool.parentContainer != self.agent:
            return f"You need to have the {tool.name} in your inventory to use it.", False
        
        # Use the tool on the patient object
        return tool.useWithObject(patientObject)

    def actionFeed(self, obj):
        # Agent must be holding the object
        if obj.parentContainer != self.agent:
            return "You need to have that in your inventory to feed the baby.", False
        
        # Check what we're feeding with
        temp = None
        if isinstance(obj, Pot):
            # Check if pot contains milk
            milk_list = obj.containsItemWithName("milk")
            if milk_list:
                milk = milk_list[0]
                temp = milk.properties["temperature"]
            else:
                return "There is no milk in the pot to feed the baby.", False
        elif isinstance(obj, Milk):
            temp = obj.properties["temperature"]
        else:
            return "You can't feed the baby with that.", False
        
        # Check temperature
        if 37.0 <= temp <= 40.0:
            self.gameOver = True
            self.gameWon = True
            return "You successfully fed the baby with milk at the perfect temperature!", True
        else:
            self.gameOver = True
            self.gameWon = False
            return f"The milk is {temp:.1f}°C, which is not suitable for a baby (needs 37-40°C).", False

    def actionDrink(self, obj):
        # Agent must be holding the object
        if obj.parentContainer != self.agent:
            return "You need to have that in your inventory to drink it.", False
        
        # Check what we're drinking
        if isinstance(obj, Pot):
            milk_list = obj.containsItemWithName("milk")
            if milk_list:
                return "You drink the milk directly from the pot. It tastes good, but the baby is still hungry.", True
            else:
                return "There is no milk in the pot to drink.", False
        elif isinstance(obj, Milk):
            return "You drink the milk. It tastes good, but the baby is still hungry.", True
        else:
            return "You can't drink that.", False

    def step(self, actionStr):
        # Reset observation
        self.observationStr = ""
        reward = 0
        
        # Check if action is in possible actions
        if actionStr not in self.possibleActions:
            self.observationStr = "I don't understand that."
            return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)
        
        # Increment step count
        self.numSteps += 1
        
        # Get the action
        actions = self.possibleActions[actionStr]
        action = actions[0]  # Take the first matching action
        
        # Execute action
        actionVerb = action[0]
        
        if actionVerb == "look around":
            self.observationStr = self.rootObject.makeDescriptionStr()
        elif actionVerb == "inventory":
            self.observationStr = self.actionInventory()
        elif actionVerb == "take":
            item = action[1]
            self.observationStr = self.actionTake(item)
        elif actionVerb == "put":
            item = action[1]
            container = action[2]
            self.observationStr = self.actionPut(item, container)
        elif actionVerb == "turn on":
            device = action[1]
            self.observationStr, success = self.actionTurnOn(device)
        elif actionVerb == "turn off":
            device = action[1]
            self.observationStr, success = self.actionTurnOff(device)
        elif actionVerb == "open":
            container = action[1]
            self.observationStr, success = self.actionOpen(container)
        elif actionVerb == "close":
            container = action[1]
            self.observationStr, success = self.actionClose(container)
        elif actionVerb == "use":
            tool = action[1]
            patient = action[2]
            self.observationStr, success = self.actionUse(tool, patient)
        elif actionVerb == "feed":
            obj = action[1]
            self.observationStr, success = self.actionFeed(obj)
        elif actionVerb == "drink":
            obj = action[1]
            self.observationStr, success = self.actionDrink(obj)
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
        # Score is 1 if game is won, 0 otherwise
        self.score = 1 if self.gameWon else 0

# Start the game
if __name__ == "__main__":
    main(HeatMilkForBabyGame(randomSeed=0))
