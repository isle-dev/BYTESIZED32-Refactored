from data.library.GameBasic import *

# A class representing a device that can be turned on or off
class Stove(Device):
    def __init__(self):
        super().__init__("stove")
        self.properties["maxTemperature"] = 100  # Maximum temperature the stove can reach
        self.properties["temperatureIncreasePerTick"] = 5  # Temperature increase per tick when on
        self.properties["isOn"] = False  # Initially off

    def tick(self):
        if self.properties["isOn"]:
            # Increase the temperature of the pot if the stove is on
            for obj in self.parentContainer.contains:
                if isinstance(obj, Pot):
                    obj.properties["temperature"] += self.properties["temperatureIncreasePerTick"]
                    if obj.properties["temperature"] > self.properties["maxTemperature"]:
                        obj.properties["temperature"] = self.properties["maxTemperature"]

# A class representing a fridge
class Fridge(Device):
    def __init__(self):
        super().__init__("fridge")
        self.properties["minTemperature"] = 0  # Minimum temperature the fridge can reach
        self.properties["temperatureDecreasePerTick"] = 2  # Temperature decrease per tick when on
        self.properties["isOn"] = True  # Initially on

    def tick(self):
        if self.properties["isOn"]:
            # Decrease the temperature of the milk if it's in the fridge
            for obj in self.parentContainer.contains:
                if isinstance(obj, Milk):
                    obj.properties["temperature"] -= self.properties["temperatureDecreasePerTick"]
                    if obj.properties["temperature"] < self.properties["minTemperature"]:
                        obj.properties["temperature"] = self.properties["minTemperature"]

# A class representing a pot that can hold milk
class Pot(Container):
    def __init__(self):
        super().__init__("pot")
        self.properties["isOpenable"] = True  # The pot can be opened
        self.properties["isOpen"] = True  # Initially open

# A class representing milk with a temperature property
class Milk(GameObject):
    def __init__(self):
        super().__init__("milk")
        self.properties["temperature"] = 5  # Initial temperature of the milk

# A thermometer to measure the temperature of the milk
class Thermometer(GameObject):
    def __init__(self):
        super().__init__("thermometer")

    def useWithObject(self, obj):
        if isinstance(obj, Milk):
            return f"The thermometer reads {obj.getProperty('temperature')} Celsius degrees.", True
        return "You can't use the thermometer on that.", False

# The world is the root object of the game object tree. In single room environments, it's where all the objects are located.
class KitchenWorld(World):
    def __init__(self):
        super().__init__("kitchen")

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "You find yourself in a kitchen. In the kitchen, you see:\n"
        for obj in self.contains:
            outStr += "\t" + obj.makeDescriptionStr() + "\n"
        return outStr

# Game Implementation
class MilkHeatingGame(TextGame):
    def __init__(self, randomSeed):
        super().__init__(randomSeed)

    # Create/initialize the world/environment for this game
    def initializeWorld(self):
        world = KitchenWorld()

        # Add the agent
        world.addObject(self.agent)

        # Add a fridge
        fridge = Fridge()
        world.addObject(fridge)

        # Add a pot with milk
        pot = Pot()
        milk = Milk()
        pot.addObject(milk)
        world.addObject(pot)

        # Add a stove
        stove = Stove()
        world.addObject(stove)

        # Add a thermometer
        thermometer = Thermometer()
        world.addObject(thermometer)

        return world

    # Get the task description for this game
    def getTaskDescription(self):
        return "Your task is to heat the milk to a suitable temperature for a baby."

    # Returns a list of valid actions at the current time step
    def generatePossibleActions(self):
        allObjects = self.makeNameToObjectDict()
        self.possibleActions = {}

        # Actions with zero arguments
        for action in [("look around", "look around"), ("inventory", "inventory")]:
            self.addAction(action[0], [action[1]])

        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction("take " + objReferent, ["take", obj])
                self.addAction("examine " + objReferent, ["examine", obj])

        # Actions with one object argument
        for objReferent, objs in allObjects.items():
            for obj in objs:
                if isinstance(obj, Pot):
                    self.addAction("open " + objReferent, ["open", obj])
                if isinstance(obj, Device):
                    self.addAction("turn on " + objReferent, ["turn on", obj])
                    self.addAction("turn off " + objReferent, ["turn off", obj])
                if isinstance(obj, Milk):
                    self.addAction("feed baby with " + objReferent, ["feed", obj])

        # Actions with two object arguments
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if (obj1 != obj2):
                            if isinstance(obj2, Stove):
                                self.addAction("put " + objReferent1 + " on " + objReferent2, ["put", obj1, obj2])
                            if isinstance(obj1, Thermometer):
                                self.addAction("use " + objReferent1 + " on " + objReferent2, ["use", obj1, obj2])

        return self.possibleActions

    # Performs an action in the environment, returns the result (a string observation, the reward, and whether the game is completed).
    def step(self, actionStr):
        self.observationStr = ""
        reward = 0

        if actionStr not in self.possibleActions:
            self.observationStr = "I don't understand that."
            return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

        self.numSteps += 1

        actions = self.possibleActions[actionStr]
        action = actions[0]  # For simplicity, just take the first action

        actionVerb = action[0]

        actions = {
            "look around": lambda: self.rootObject.makeDescriptionStr(),
            "inventory": lambda: self.actionInventory(),
            "examine": lambda: action[1].makeDescriptionStr(makeDetailed=True),
            "take": lambda: self.actionTake(action[1]),
            "open": lambda: action[1].openContainer(),
            "turn on": lambda: action[1].turnOn(),
            "turn off": lambda: action[1].turnOff(),
            "put": lambda: self.actionPut(action[1], action[2]),
            "use": lambda: self.actionUse(action[1], action[2]),
            "feed": lambda: self.actionFeed(action[1])
        }

        self.observationStr = actions.get(actionVerb, lambda: "ERROR: Unknown action.")()

        # Do one tick of the environment
        self.doWorldTick()

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    def actionFeed(self, milk):
        if milk.getProperty("temperature") >= 37:  # Suitable temperature for a baby
            self.gameOver = True
            self.gameWon = True
            return "You successfully fed the baby with the milk!"
        return "The milk is not at a suitable temperature for the baby."

if __name__ == "__main__":
    # Set random seed 0 and Create a new game
    main(game=MilkHeatingGame(randomSeed=0))
