from data.library.GameBasic import *

# A pot to hold the milk
class Pot(Container):
    def __init__(self):
        Container.__init__(self, "pot")
        self.properties["isContainer"] = True
        self.properties["temperature"] = 20.0  # Starting temperature of the milk

    def makeDescriptionStr(self, makeDetailed=False):
        return f"a pot containing milk at {self.properties['temperature']} degrees Celsius."


# A stove to heat the pot
class Stove(Device):
    def __init__(self):
        Device.__init__(self, "stove")
        self.properties["maxTemperature"] = 100.0  # Maximum temperature the stove can reach
        self.properties["temperature_increase_per_tick"] = 10.0  # Temperature increase per tick

    def tick(self):
        if self.properties["isOn"]:
            # Increase the temperature of the pot if it's on
            for obj in self.parentContainer.contains:
                if isinstance(obj, Pot):
                    obj.properties["temperature"] += self.properties["temperature_increase_per_tick"]
                    if obj.properties["temperature"] > self.properties["maxTemperature"]:
                        obj.properties["temperature"] = self.properties["maxTemperature"]


# A fridge to store the milk
class Fridge(Device):
    def __init__(self):
        Device.__init__(self, "fridge")
        self.properties["minTemperature"] = 0.0  # Minimum temperature the fridge can reach
        self.properties["temperature_decrease_per_tick"] = 5.0  # Temperature decrease per tick

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
        if isinstance(pot, Pot):
            return f"The milk is at {pot.properties['temperature']} degrees Celsius."
        return "You can only check the temperature of the pot."


# The world is the root object of the game object tree.  In single room environments, it's where all the objects are located.
class KitchenWorld(World):
    def __init__(self):
        World.__init__(self, "kitchen")


class HeatMilkGame(TextGame):
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

        # Add a stove
        stove = Stove()
        world.addObject(stove)

        # Add a pot with milk
        pot = Pot()
        world.addObject(pot)

        # Add a thermometer
        thermometer = Thermometer()
        world.addObject(thermometer)

        # Set parent container for the objects
        fridge.parentContainer = world
        stove.parentContainer = world
        pot.parentContainer = world
        thermometer.parentContainer = world

        # Return the world
        return world

    # Get the task description for this game
    def getTaskDescription(self):
        return "Your task is to heat the milk in the pot to a suitable temperature for a baby."

    # Generate possible actions
    def generatePossibleActions(self):
        allObjects = self.makeNameToObjectDict()
        self.possibleActions = {}

        # Actions with zero arguments
        for action in [("look around", "look around"), ("inventory", "inventory")]:
            self.addAction(action[0], [action[1]])

        # Actions with one object argument
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction("take " + objReferent, ["take", obj])
                self.addAction("use " + objReferent + " on pot", ["use", obj, allObjects["pot"][0]])

        # Actions with two object arguments
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if obj1 != obj2:
                            if isinstance(obj2, Stove):
                                self.addAction("put " + objReferent1 + " on " + objReferent2, ["put", obj1, obj2])
                            if isinstance(obj2, Thermometer):
                                self.addAction("use " + objReferent1 + " on " + objReferent2, ["use", obj1, obj2])

        return self.possibleActions

    # Perform an action in the environment
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

        action_map = {
            "look around": self.rootObject.makeDescriptionStr,
            "inventory": self.actionInventory,
            "take": lambda: self.actionTake(action[1]),
            "put": lambda: self.actionPut(action[1], action[2]),
            "use": lambda: self.actionUse(action[1], action[2]) if hasattr(self, 'actionUse') else "ERROR: actionUse method not defined."
        }

        self.observationStr = action_map.get(actionVerb, lambda: "ERROR: Unknown action.")()

        # Do one tick of the environment
        self.doWorldTick()

        # Calculate the score
        lastScore = self.score
        self.calculateScore()
        reward = self.score - lastScore

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    # Calculate the game score
    def calculateScore(self):
        allObjects = self.rootObject.getAllContainedObjectsRecursive()
        for obj in allObjects:
            if isinstance(obj, Pot):
                if obj.properties["temperature"] >= 37.0 and obj.properties["temperature"] <= 40.0:
                    self.score += 1
                    self.gameOver = True
                    self.gameWon = True
                elif obj.properties["temperature"] > 40.0:
                    self.score = 0
                    self.gameOver = True
                    self.gameWon = False

if __name__ == "__main__":
    # Set random seed 0 and Create a new game
    main(HeatMilkGame(randomSeed=0))
