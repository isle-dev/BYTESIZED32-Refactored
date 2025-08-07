# milk_heating_simulation.py

from data.library.GameBasic import *

# A pot that can hold milk
class Pot(Container):
    def __init__(self):
        Container.__init__(self, "pot")
        self.properties["isOpenable"] = False
        self.properties["temperature"] = 20.0  # Starting temperature of the milk

    def makeDescriptionStr(self, makeDetailed=False):
        return f"a pot containing milk at {self.properties['temperature']} degrees Celsius"

# A stove that can heat the pot
class Stove(Device):
    def __init__(self):
        Device.__init__(self, "stove")
        self.properties["maxTemperature"] = 100.0  # Maximum temperature the stove can reach
        self.properties["temperature_increase_per_tick"] = 5.0  # Temperature increase per tick

    def tick(self):
        if self.properties["isOn"]:
            # Increase the temperature of the pot if it's on
            for obj in self.parentContainer.contains:
                if isinstance(obj, Pot):
                    obj.properties["temperature"] += self.properties["temperature_increase_per_tick"]
                    if obj.properties["temperature"] > self.properties["maxTemperature"]:
                        obj.properties["temperature"] = self.properties["maxTemperature"]

# A fridge that can cool the pot
class Fridge(Device):
    def __init__(self):
        Device.__init__(self, "fridge")
        self.properties["minTemperature"] = 0.0  # Minimum temperature the fridge can reach
        self.properties["temperature_decrease_per_tick"] = 2.0  # Temperature decrease per tick

    def tick(self):
        if self.properties["isOn"]:
            # Decrease the temperature of the pot if it's in the fridge
            for obj in self.parentContainer.contains:
                if isinstance(obj, Pot):
                    obj.properties["temperature"] -= self.properties["temperature_decrease_per_tick"]
                    if obj.properties["temperature"] < self.properties["minTemperature"]:
                        obj.properties["temperature"] = self.properties["minTemperature"]

# A thermometer to check the temperature of the milk
class Thermometer(GameObject):
    def __init__(self):
        GameObject.__init__(self, "thermometer")

    def checkTemperature(self, pot):
        return pot.properties["temperature"]

# World Setup for kitchen
class KitchenWorld(World):
    def __init__(self):
        World.__init__(self, "kitchen")

# Game Implementation
class HeatMilkGame(TextGame):
    def __init__(self, randomSeed):
        TextGame.__init__(self, randomSeed)

    def initializeWorld(self):
        world = KitchenWorld()

        # Create devices
        stove = Stove()
        fridge = Fridge()
        thermometer = Thermometer()

        # Create a pot with milk
        pot = Pot()

        # Add objects to the world
        world.addObject(stove)
        world.addObject(fridge)
        world.addObject(thermometer)
        world.addObject(pot)

        # Add the agent to the world
        world.addObject(self.agent)

        # Store the pot in the game instance for later use
        self.pot = pot

        return world

    def getTaskDescription(self):
        return "Your task is to heat the milk to a suitable temperature for a baby."

    def generatePossibleActions(self):
        allObjects = self.makeNameToObjectDict()
        self.possibleActions = {}

        # Zero-argument actions
        for action in [("look around", "look around"), ("inventory", "inventory")]:
            self.addAction(action[0], [action[1]])

        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction("take " + objReferent, ["take", obj])
                self.addAction("examine " + objReferent, ["examine", obj])
                self.addAction("open " + objReferent, ["open", obj])
                self.addAction("close " + objReferent, ["close", obj])

        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if (obj1 != obj2):
                            if obj2.properties["isContainer"]:
                                self.addAction("put " + objReferent1 + " in " + objReferent2, ["put", obj1, obj2])

        # Device actions
        for objReferent, objs in allObjects.items():
            for obj in objs:
                if isinstance(obj, Device):
                    self.addAction("turn on " + objReferent, ["turn on", obj])
                    self.addAction("turn off " + objReferent, ["turn off", obj])
        
        # Use thermometer action
        self.addAction("use thermometer on pot", ["use thermometer", self.pot])

        # Feed baby action
        self.addAction("feed baby with milk", ["feed baby", self.pot])

        return self.possibleActions

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

        action_map = {
            "look around": lambda: self.rootObject.makeDescriptionStr(),
            "inventory": lambda: self.actionInventory(),
            "examine": lambda: action[1].makeDescriptionStr(makeDetailed=True),
            "open": lambda: action[1].openContainer(),
            "close": lambda: action[1].closeContainer(),
            "take": lambda: self.actionTake(action[1]),
            "put": lambda: self.actionPut(action[1], action[2]),
            "turn on": lambda: action[1].turnOn(),
            "turn off": lambda: action[1].turnOff(),
            "use thermometer": lambda: f"The temperature of the milk is {thermometer.checkTemperature(action[1])} degrees Celsius.",
            "feed baby": lambda: self.feedBaby(action[1]),
        }

        self.observationStr = action_map.get(actionVerb, lambda: "ERROR: Unknown action.")()

        # Do one tick of the environment
        self.doWorldTick()

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    def feedBaby(self, pot):
        if pot.properties["temperature"] >= 37.0:  # Suitable temperature for a baby
            self.gameOver = True
            self.gameWon = True
            return "You successfully fed the baby with the milk!"
        else:
            return "The milk is not warm enough to feed the baby."

    def doWorldTick(self):
        # Call tick for all devices
        for obj in self.rootObject.getAllContainedObjectsRecursive():
            if isinstance(obj, Device):
                obj.tick()

# Main Program
def main(game):
    possibleActions = game.generatePossibleActions()
    print("Task Description: " + game.getTaskDescription())
    print("")
    print("Initial Observation: " + game.observationStr)
    print("")
    print("Type 'help' for a list of possible actions.")
    print("")

    while True:
        actionStr = ""
        while ((len(actionStr) == 0) or (actionStr == "help")):
            actionStr = input("> ")
            if (actionStr == "help"):
                print("Possible actions: " + str(possibleActions.keys()))
                print("")
                actionStr = ""
            elif (actionStr == "exit") or (actionStr == "quit"):
                return

        observationStr, score, reward, gameOver, gameWon = game.step(actionStr)

        possibleActions = game.generatePossibleActions()

        print("Observation: " + observationStr)
        print("")
        print("Current step: " + str(game.numSteps))
        print("Score: " + str(score))
        print("Game Over: " + str(gameOver))
        print("Game Won: " + str(gameWon))
        print("")
        print("----------------------------------------")

# Run the main program
if __name__ == "__main__":
    randomSeed = 0
    game = HeatMilkGame(randomSeed=randomSeed)
    main(game)
