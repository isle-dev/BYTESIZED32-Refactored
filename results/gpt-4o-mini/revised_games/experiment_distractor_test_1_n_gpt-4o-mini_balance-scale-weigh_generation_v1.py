from data.library.GameBasic import *

# A stove that can heat objects
class Stove(Device):
    def __init__(self, name):
        Device.__init__(self, name)
        self.properties["max_temperature"] = 100  # Max temperature the stove can reach
        self.properties["temperature_increase_per_tick"] = 5  # Temperature increase per tick

    def tick(self):
        if self.properties["isOn"]:
            # Increase the temperature of the contained object if it's a pot with milk
            for obj in self.contains:
                if isinstance(obj, Pot) and obj.contains:
                    for milk in obj.contains:
                        if isinstance(milk, Milk):
                            milk.properties["temperature"] += self.properties["temperature_increase_per_tick"]
                            if milk.properties["temperature"] > self.properties["max_temperature"]:
                                milk.properties["temperature"] = self.properties["max_temperature"]

# A fridge that can cool objects
class Fridge(Device):
    def __init__(self, name):
        Device.__init__(self, name)
        self.properties["min_temperature"] = 0  # Min temperature the fridge can reach
        self.properties["temperature_decrease_per_tick"] = 2  # Temperature decrease per tick

    def tick(self):
        if self.properties["isOn"]:
            # Decrease the temperature of the contained object if it's a pot with milk
            for obj in self.contains:
                if isinstance(obj, Pot) and obj.contains:
                    for milk in obj.contains:
                        if isinstance(milk, Milk):
                            milk.properties["temperature"] -= self.properties["temperature_decrease_per_tick"]
                            if milk.properties["temperature"] < self.properties["min_temperature"]:
                                milk.properties["temperature"] = self.properties["min_temperature"]

# A pot that can hold milk
class Pot(Container):
    def __init__(self, name):
        Container.__init__(self, name)

# Milk with a temperature property
class Milk(GameObject):
    def __init__(self):
        GameObject.__init__(self, "milk")
        self.properties["temperature"] = 5  # Initial temperature of the milk

    def makeDescriptionStr(self, makeDetailed=False):
        return f"some {self.name} at {self.properties['temperature']}°C"

# The main game class
class HeatMilkGame(TextGame):
    def __init__(self, randomSeed):
        TextGame.__init__(self, randomSeed)

    # Create/initialize the world/environment for this game
    def initializeWorld(self):
        world = World("kitchen")

        # Add the agent
        world.addObject(self.agent)

        # Add a stove
        stove = Stove("stove")
        world.addObject(stove)

        # Add a fridge
        fridge = Fridge("fridge")
        world.addObject(fridge)

        # Add a pot with milk
        pot = Pot("pot")
        milk = Milk()
        pot.addObject(milk)
        world.addObject(pot)

        return world

    # Get the task description for this game
    def getTaskDescription(self):
        return "Your task is to heat the milk to a suitable temperature for a baby. Use the thermometer to monitor the milk temperature and feed the baby when it's ready."

    # Returns a list of valid actions at the current time step
    def generatePossibleActions(self):
        allObjects = self.makeNameToObjectDict()
        self.possibleActions = {}

        # Actions with zero arguments
        for action in [("look around", "look around"), ("inventory", "inventory")]:
            self.addAction(action[0], [action[1]])

        # Actions with one object argument
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction(f"take {objReferent}", ["take", obj])
                self.addAction(f"examine {objReferent}", ["examine", obj])
                self.addAction(f"turn on {objReferent}", ["turn on", obj])
                self.addAction(f"turn off {objReferent}", ["turn off", obj])

        # Actions with two object arguments
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if obj1 != obj2:
                            containerPrefix = obj2.properties.get("containerPrefix", "in") if obj2.properties.get(
                                "isContainer") else "in"
                            self.addAction(f"put {objReferent1} {containerPrefix} {objReferent2}", ["put", obj1, obj2])

        # Use thermometer on milk
        for milk in allObjects.get("milk", []):
            self.addAction(f"use thermometer on {milk.name}", ["use thermometer", milk])

        # Feed baby with milk
        self.addAction("feed baby with milk", ["feed baby", milk])

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

        action_map = {
            "look around": self.rootObject.makeDescriptionStr,
            "inventory": self.actionInventory,
            "take": lambda: self.actionTake(action[1]),
            "put": lambda: self.actionPut(action[1], action[2]),
            "turn on": lambda: action[1].turnOn(),
            "turn off": lambda: action[1].turnOff(),
            "examine": lambda: action[1].makeDescriptionStr(),
            "use thermometer": lambda: self.useThermometer(action[1]),
            "feed baby": lambda: self.feedBaby(action[1])
        }

        self.observationStr = action_map.get(actionVerb, lambda: "ERROR: Unknown action")()

        # Do one tick of the environment
        self.doWorldTick()

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    def useThermometer(self, milk):
        temp = milk.properties["temperature"]
        return f"The milk is currently at {temp}°C."

    def feedBaby(self, milk):
        if milk.properties["temperature"] < 37:
            return "The milk is too cold to feed the baby."
        elif milk.properties["temperature"] > 40:
            return "The milk is too hot to feed the baby."
        else:
            self.gameOver = True
            self.gameWon = True
            return "You successfully fed the baby with the milk!"

if __name__ == "__main__":
    # Set random seed 0 and Create a new game
    main(HeatMilkGame(randomSeed=0))
