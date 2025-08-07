from data.library.GameBasic import *

# A class representing a device that can be turned on or off
class Stove(Device):
    def __init__(self):
        super().__init__("stove")
        self.properties["temperature"] = 20.0  # Initial temperature of the stove
        self.properties["max_temperature"] = 100.0  # Maximum temperature the stove can reach
        self.properties["temperature_increase_per_tick"] = 5.0  # Temperature increase per tick when on

    def tick(self):
        if self.properties["isOn"]:
            self.properties["temperature"] = min(self.properties["temperature"] + self.properties["temperature_increase_per_tick"], self.properties["max_temperature"])

    def makeDescriptionStr(self, makeDetailed=False):
        return f"The stove is currently {'on' if self.properties['isOn'] else 'off'}."


# A class representing a fridge
class Fridge(Device):
    def __init__(self):
        super().__init__("fridge")
        self.properties["temperature"] = 4.0  # Initial temperature of the fridge
        self.properties["min_temperature"] = 0.0  # Minimum temperature the fridge can reach
        self.properties["temperature_decrease_per_tick"] = 1.0  # Temperature decrease per tick when on

    def tick(self):
        if self.properties["isOn"]:
            self.properties["temperature"] = max(self.properties["temperature"] - self.properties["temperature_decrease_per_tick"], self.properties["min_temperature"])

    def makeDescriptionStr(self, makeDetailed=False):
        return f"The fridge is currently {'on' if self.properties['isOn'] else 'off'}."


# A class representing a pot that can hold milk
class Pot(Container):
    def __init__(self):
        super().__init__("pot")
        self.properties["isOpenable"] = True  # The pot can be opened
        self.properties["isOpen"] = True  # The pot is initially open

    def makeDescriptionStr(self, makeDetailed=False):
        contents = [obj.makeDescriptionStr() for obj in self.contains]
        return f"A pot that contains: {', '.join(contents) if contents else 'nothing'}."


# A class representing milk with a specific temperature
class Milk(Substance):
    def __init__(self, temperature):
        super().__init__("milk", "milk", "steam", boilingPoint=100, meltingPoint=0, currentTemperatureCelsius=temperature)

    def makeDescriptionStr(self, makeDetailed=False):
        return f"some {self.name} at {self.properties['temperature']} degrees Celsius."


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
        self.baby_fed = False
        TextGame.__init__(self, randomSeed)

    # Create/initialize the world/environment for this game
    def initializeWorld(self):
        world = KitchenWorld()

        # Add the agent
        world.addObject(self.agent)

        # Add a fridge
        fridge = Fridge()
        world.addObject(fridge)

        # Add a stove
        stove = Stove()
        world.addObject(stove)

        # Add a pot with milk
        pot = Pot()
        milk = Milk(4)  # Starting temperature of milk
        pot.addObject(milk)
        world.addObject(pot)

        return world

    # Get the task description for this game
    def getTaskDescription(self):
        return "Your task is to heat the milk to a suitable temperature for the baby."

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
                    self.addAction("put pot on stove", ["put", obj, allObjects["stove"][0]])  # Fixed to reference stove correctly
                if isinstance(obj, Stove):
                    self.addAction("turn on stove", ["turn on", obj])
                if isinstance(obj, Fridge):
                    self.addAction("turn on fridge", ["turn on", obj])
                if isinstance(obj, Milk):
                    self.addAction("use thermometer on milk", ["use", self.agent.contains[0], obj])  # Assuming thermometer is the first object in inventory

        # Actions with two object arguments
        if 'milk' in allObjects and allObjects['milk']:  # Ensure milk is in the dictionary and not empty
            milk = allObjects['milk'][0]  # Get the first milk object
            self.addAction("feed baby with milk", ["feed", milk])

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
            "put": lambda: self.actionPut(action[1], action[2]),
            "turn on": lambda: action[1].turnOn(),
            "use": lambda: self.actionUse(action[1], action[2]),
            "feed": lambda: self.actionFeed(action[1])
        }

        self.observationStr = actions.get(actionVerb, lambda: "ERROR: Unknown action.")()

        # Do one tick of the environment
        self.doWorldTick()

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    def actionFeed(self, milk):
        if self.baby_fed:
            return "The baby has already been fed."
        if milk.properties["temperature"] < 37:  # Suitable temperature for a baby
            return "The milk is too cold to feed the baby."
        self.baby_fed = True
        return "You fed the baby with the milk."

    def calculateScore(self):
        self.score = 1 if self.baby_fed else 0
        self.gameOver = self.baby_fed
        self.gameWon = self.baby_fed


# Main Program
if __name__ == "__main__":
    randomSeed = 0
    game = MilkHeatingGame(randomSeed=randomSeed)
    main(game)
