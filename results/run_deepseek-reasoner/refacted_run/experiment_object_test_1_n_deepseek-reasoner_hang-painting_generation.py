from data.library.GameBasic import *

class Stove(Device, Container):
    def __init__(self, name):
        Device.__init__(self, name)
        Container.__init__(self, name)
        self.properties["containerPrefix"] = "on"
        self.properties["temperature_increase_per_tick"] = 5  # degrees per tick
        self.properties["max_temperature"] = 100

    def tick(self):
        if self.properties["isOn"]:
            for obj in self.contains:
                current_temp = obj.getProperty("temperature")
                if current_temp is not None:
                    new_temp = current_temp + self.properties["temperature_increase_per_tick"]
                    if new_temp > self.properties["max_temperature"]:
                        new_temp = self.properties["max_temperature"]
                    obj.properties["temperature"] = new_temp

class Pot(Container):
    def __init__(self, name):
        Container.__init__(self, name)
        self.properties["isOpenable"] = False

    def tick(self):
        for obj in self.contains:
            if obj.getProperty("temperature") is not None:
                obj.properties["temperature"] = self.properties["temperature"]

class Milk(GameObject):
    def __init__(self, name):
        GameObject.__init__(self, name)

class Fridge(Device, Container):
    def __init__(self, name):
        Device.__init__(self, name)
        Container.__init__(self, name)
        self.properties["isOpenable"] = True
        self.properties["isOpen"] = False
        self.properties["containerPrefix"] = "in"
        self.properties["temperature_decrease_per_tick"] = 1  # degrees per tick
        self.properties["min_temperature"] = 4

    def tick(self):
        if self.properties["isOn"] and not self.properties["isOpen"]:
            for obj in self.contains:
                current_temp = obj.getProperty("temperature")
                if current_temp is not None:
                    new_temp = current_temp - self.properties["temperature_decrease_per_tick"]
                    if new_temp < self.properties["min_temperature"]:
                        new_temp = self.properties["min_temperature"]
                    obj.properties["temperature"] = new_temp

class Thermometer(GameObject):
    def __init__(self, name):
        GameObject.__init__(self, name)

    def use(self, obj):
        if obj.getProperty("temperature") is not None:
            return f"The temperature of the {obj.name} is {obj.properties['temperature']:.1f}°C."
        else:
            return f"You can't measure the temperature of the {obj.name}."

class KitchenWorld(World):
    def __init__(self):
        World.__init__(self, "kitchen")

class HeatMilkGame(TextGame):
    def __init__(self, randomSeed):
        super().__init__(randomSeed)
        
    def initializeWorld(self):
        world = KitchenWorld()
        
        # Add agent
        world.addObject(self.agent)
        
        # Add stove
        stove = Stove("stove")
        world.addObject(stove)
        
        # Add fridge
        fridge = Fridge("fridge")
        fridge.properties["isOn"] = True  # Fridge is on by default
        world.addObject(fridge)
        
        # Add pot in fridge
        pot = Pot("pot")
        fridge.addObject(pot)
        
        # Add milk in pot
        milk = Milk("milk")
        milk.properties["temperature"] = fridge.properties["min_temperature"]  # Start cold
        pot.addObject(milk)
        
        # Add thermometer in room
        thermometer = Thermometer("thermometer")
        world.addObject(thermometer)
        
        return world

    def getTaskDescription(self):
        return "Your task is to heat milk to a suitable temperature (37-40°C) for a baby using the stove."

    def generatePossibleActions(self):
        allObjects = self.makeNameToObjectDict()
        self.possibleActions = {}
        
        # Actions with zero arguments
        for action in [("look around", "look around"), ("look", "look around"), ("inventory", "inventory")]:
            self.addAction(action[0], [action[1]])
        
        # Actions with one object argument
        for objReferent, objs in allObjects.items():
            for obj in objs:
                # Open/close
                if obj.getProperty("isOpenable"):
                    self.addAction("open " + objReferent, ["open", obj])
                    self.addAction("close " + objReferent, ["close", obj])
                # Turn on/off
                if obj.getProperty("isDevice"):
                    self.addAction("turn on " + objReferent, ["turn on", obj])
                    self.addAction("turn off " + objReferent, ["turn off", obj])
                # Take
                self.addAction("take " + objReferent, ["take", obj])
                if obj.parentContainer:
                    self.addAction("take " + objReferent + " from " + obj.parentContainer.getReferents()[0], ["take", obj])
                # Drink
                if isinstance(obj, Milk):
                    self.addAction("drink " + objReferent, ["drink", obj])
        
        # Actions with two object arguments
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if obj1 != obj2:
                            # Put
                            if obj2.properties["isContainer"]:
                                containerPrefix = obj2.properties["containerPrefix"]
                                self.addAction(f"put {objReferent1} {containerPrefix} {objReferent2}", ["put", obj1, obj2])
                            # Use thermometer
                            if isinstance(obj1, Thermometer):
                                self.addAction(f"use {objReferent1} on {objReferent2}", ["use", obj1, obj2])
                            # Feed
                            if isinstance(obj1, Milk):
                                self.addAction(f"feed baby with {objReferent1}", ["feed", obj1])
        
        return self.possibleActions

    def actionOpen(self, obj):
        if hasattr(obj, "openContainer"):
            return obj.openContainer()
        return "You can't open that.", False

    def actionClose(self, obj):
        if hasattr(obj, "closeContainer"):
            return obj.closeContainer()
        return "You can't close that.", False

    def actionTurnOn(self, obj):
        if hasattr(obj, "turnOn"):
            return obj.turnOn()
        return "You can't turn that on.", False

    def actionTurnOff(self, obj):
        if hasattr(obj, "turnOff"):
            return obj.turnOff()
        return "You can't turn that off.", False

    def actionUse(self, tool, obj):
        if isinstance(tool, Thermometer) and hasattr(tool, "use"):
            return tool.use(obj)
        return f"You can't use the {tool.name} that way."

    def actionFeed(self, milk):
        if not isinstance(milk, Milk):
            return f"You can't feed the baby with {milk.name}."
        
        if milk.parentContainer != self.agent:
            return "You need to have the milk in your inventory to feed the baby."
        
        temp = milk.getProperty("temperature")
        if temp is None:
            return "You can't feed that to the baby."
        
        if 37 <= temp <= 40:
            self.gameOver = True
            self.gameWon = True
            return "You successfully fed the baby with perfectly warmed milk! The baby is happy and falls asleep."
        else:
            self.gameOver = True
            self.gameWon = False
            return f"The milk is {temp:.1f}°C - too {'cold' if temp < 37 else 'hot'} for the baby! The baby refuses to drink it."

    def actionDrink(self, milk):
        if not isinstance(milk, Milk):
            return f"You can't drink {milk.name}."
        
        if milk.parentContainer != self.agent:
            return "You don't have that in your inventory."
        
        milk.removeSelfFromContainer()
        self.gameOver = True
        self.gameWon = False
        return "You drank the milk. Now there's none left for the baby!"

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
        elif actionVerb == "feed":
            self.observationStr = self.actionFeed(action[1])
        elif actionVerb == "drink":
            self.observationStr = self.actionDrink(action[1])
        else:
            self.observationStr = "ERROR: Unknown action."
        
        # Update world state
        self.doWorldTick()
        
        # Calculate score
        lastScore = self.score
        self.calculateScore()
        reward = self.score - lastScore
        
        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    def doWorldTick(self):
        # First update all objects
        super().doWorldTick()
        
        # Then adjust temperatures for objects not in active environments
        allObjects = self.rootObject.getAllContainedObjectsRecursive()
        room_temp = 20.0
        rate = 0.1
        
        for obj in allObjects:
            # Check if in active environment
            in_active_env = False
            current = obj
            while current is not None:
                if isinstance(current, Fridge) and current.properties["isOn"] and not current.properties["isOpen"]:
                    in_active_env = True
                    break
                if isinstance(current, Stove) and current.properties["isOn"]:
                    in_active_env = True
                    break
                current = current.parentContainer
            
            # Adjust temperature if not in active environment
            if not in_active_env:
                current_temp = obj.getProperty("temperature")
                if current_temp is not None:
                    new_temp = current_temp + (room_temp - current_temp) * rate
                    obj.properties["temperature"] = new_temp

    def calculateScore(self):
        # Only set score at end of game
        if self.gameOver:
            self.score = 1 if self.gameWon else 0

if __name__ == "__main__":
    main(HeatMilkGame(randomSeed=0))
