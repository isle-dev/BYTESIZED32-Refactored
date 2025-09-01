from data.library.GameBasic import *

# A class representing a liquid, specifically milk in this case
class Milk(GameObject):
    def __init__(self, initial_temperature):
        GameObject.__init__(self, "milk")
        self.properties["temperature"] = initial_temperature
        self.properties["max_temperature"] = 100  # Maximum temperature for milk

    def makeDescriptionStr(self, makeDetailed=False):
        return f"some milk at {self.properties['temperature']} degrees Celsius"


# A class representing a stove
class Stove(Device):
    def __init__(self):
        Device.__init__(self, "stove")
        self.properties["temperature_increase_per_tick"] = 5  # Increase temperature by 5 degrees per tick
        self.properties["max_temperature"] = 100  # Maximum temperature the stove can reach

    def tick(self):
        if self.properties["isOn"]:
            # Increase the temperature of the pot on the stove
            for obj in self.parentContainer.contains:
                if isinstance(obj, Pot):
                    milk = obj.containsItemWithName("milk")
                    if milk:
                        new_temp = min(milk[0].properties["temperature"] + self.properties["temperature_increase_per_tick"], self.properties["max_temperature"])
                        milk[0].properties["temperature"] = new_temp


# A class representing a fridge
class Fridge(Device):
    def __init__(self):
        Device.__init__(self, "fridge")
        self.properties["temperature_decrease_per_tick"] = 2  # Decrease temperature by 2 degrees per tick

    def tick(self):
        if self.properties["isOn"]:
            # Decrease the temperature of the milk in the fridge
            for obj in self.parentContainer.contains:
                if isinstance(obj, Pot):
                    milk = obj.containsItemWithName("milk")
                    if milk:
                        new_temp = max(milk[0].properties["temperature"] - self.properties["temperature_decrease_per_tick"], 0)
                        milk[0].properties["temperature"] = new_temp


# A class representing a pot that can hold milk
class Pot(Container):
    def __init__(self):
        Container.__init__(self, "pot")
        self.properties["isOpenable"] = False  # A pot is not openable


# The world is the root object of the game object tree. In this case, it's the kitchen.
class KitchenWorld(World):
    def __init__(self):
        World.__init__(self, "kitchen")

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
        milk = Milk(initial_temperature=5)  # Starting temperature of milk
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
        for objReferent in allObjects.keys():
            self.addAction("turn on " + objReferent, ["turn on", allObjects[objReferent][0]])
            self.addAction("turn off " + objReferent, ["turn off", allObjects[objReferent][0]])

        # Actions with two object arguments
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if (obj1 != obj2):
                            self.addAction("put " + objReferent1 + " on " + objReferent2, ["put", obj1, obj2])
                            self.addAction("use thermometer on " + objReferent1, ["use", obj1, obj2])

        # Feed baby action
        self.addAction("feed baby with milk", ["feed", "milk"])

        return self.possibleActions

    # Action to feed the baby
    def actionFeed(self):
        if self.baby_fed:
            return "The baby has already been fed."
        else:
            self.baby_fed = True
            return "You fed the baby with the milk."

    # Performs an action in the environment, returns the result (a string observation, the reward, and whether the game is completed).
    def step(self, actionStr):
        self.observationStr = ""
        reward = 0

        # Check to make sure the action is in the possible actions dictionary
        if actionStr not in self.possibleActions:
            self.observationStr = "I don't understand that."
            return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

        self.numSteps += 1

        # Find the action in the possible actions dictionary
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
            "turn off": lambda: action[1].turnOff(),
            "feed": lambda: self.actionFeed() if action[1] == "milk" else "You can't feed the baby with that."
        }

        self.observationStr = actions.get(actionVerb, lambda: "ERROR: Unknown action.")()

        # Do one tick of the environment
        self.doWorldTick()

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    def doWorldTick(self):
        # Call tick for all devices
        for obj in self.rootObject.getAllContainedObjectsRecursive():
            if isinstance(obj, Device):
                obj.tick()

if __name__ == "__main__":
    # Set random seed 0 and Create a new game
    main(game=MilkHeatingGame(randomSeed=0))
