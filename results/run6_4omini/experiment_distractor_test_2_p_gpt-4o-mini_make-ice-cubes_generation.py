from data.library.GameBasic import *

# A sink, which is a device that can dispense water.
class Sink(Container, Device):
    def __init__(self):
        super().__init__("sink")
        self.properties["isOpenable"] = False  # A sink is not openable
        self.properties["isOn"] = False  # A sink starts off

    def tick(self):
        # If the sink is on, it dispenses water into any container placed in it
        if self.properties["isOn"]:
            for obj in self.getAllContainedObjectsRecursive():
                if isinstance(obj, MeasuringCup) and obj.contained_volume < obj.properties["max_volume"]:
                    obj.contained_volume += 1  # Dispense 1 unit of water
                    if obj.contained_volume > obj.properties["max_volume"]:
                        obj.contained_volume = obj.properties["max_volume"]

    def makeDescriptionStr(self, makeDetailed=False):
        return f"a sink that is currently {'on' if self.properties['isOn'] else 'off'}"

# A measuring cup, which is a container that can hold a certain volume of water.
class MeasuringCup(Container):
    def __init__(self):
        super().__init__("measuring cup")
        self.properties["max_volume"] = 5  # Maximum volume of the measuring cup
        self.contained_volume = 0  # Current volume of water in the measuring cup

    def makeDescriptionStr(self, makeDetailed=False):
        return f"a measuring cup that contains {self.contained_volume} units of water"

# A pot, which is a container that can hold water.
class Pot(Container):
    def __init__(self):
        super().__init__("pot")
        self.properties["max_volume"] = 10  # Maximum volume of the pot
        self.contained_volume = 0  # Current volume of water in the pot

    def makeDescriptionStr(self, makeDetailed=False):
        return f"a pot that contains {self.contained_volume} units of water"

# An instance of a substance (here, water)
class Water(Substance):
    def __init__(self):
        super().__init__("ice", "water", "steam", boilingPoint=100, meltingPoint=0, currentTemperatureCelsius=20)

# The world is the root object of the game object tree. In single room environments, it's where all the objects are located.
class KitchenWorld(World):
    def __init__(self):
        super().__init__("kitchen")

class AddWaterGame(TextGame):
    def __init__(self, randomSeed):
        super().__init__(randomSeed)

    def initializeWorld(self):
        world = KitchenWorld()

        # Add the agent
        world.addObject(self.agent)

        # Add a sink
        sink = Sink()
        world.addObject(sink)

        # Add a measuring cup
        measuringCup = MeasuringCup()
        world.addObject(measuringCup)

        # Add a pot
        pot = Pot()
        world.addObject(pot)

        return world

    def getTaskDescription(self):
        return "Your task is to add water into the pot using the measuring cup."

    def generatePossibleActions(self):
        allObjects = self.makeNameToObjectDict()
        self.possibleActions = {}

        # Actions with zero arguments
        for action in [("look around", "look around"), ("look", "look around"), ("inventory", "inventory")]:
            self.addAction(action[0], [action[1]])

        # Actions with one object argument
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction("take " + objReferent, ["take", obj])
                self.addAction("examine " + objReferent, ["examine", obj])
                self.addAction("turn on " + objReferent, ["turn on", obj])
                self.addAction("turn off " + objReferent, ["turn off", obj])

        # Actions with two object arguments
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if (obj1 != obj2):
                            self.addAction("pour " + objReferent1 + " into " + objReferent2, ["pour", obj1, obj2])

        return self.possibleActions

    def actionPour(self, measuringCup, pot):
        if measuringCup.contained_volume > 0:
            amount_to_pour = min(measuringCup.contained_volume, pot.properties["max_volume"] - pot.contained_volume)
            pot.contained_volume += amount_to_pour
            measuringCup.contained_volume -= amount_to_pour
            return f"You pour {amount_to_pour} units of water from the measuring cup into the pot."
        else:
            return "The measuring cup is empty."

    def step(self, actionStr):
        self.observationStr = ""
        reward = 0

        if actionStr not in self.possibleActions:
            self.observationStr = "I don't understand that."
            return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

        self.numSteps += 1
        actions = self.possibleActions[actionStr]
        action = actions[0] if len(actions) == 1 else actions[0]

        actionVerb = action[0]
        action_map = {
            "look around": self.rootObject.makeDescriptionStr,
            "inventory": self.actionInventory,
            "examine": lambda: action[1].makeDescriptionStr(makeDetailed=True),
            "take": lambda: self.actionTake(action[1]),
            "turn on": lambda: action[1].turnOn()[0],
            "turn off": lambda: action[1].turnOff()[0],
            "pour": lambda: self.actionPour(action[1], action[2])
        }

        self.observationStr = action_map.get(actionVerb, lambda: "ERROR: Unknown action.")()
        self.doWorldTick()

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

if __name__ == "__main__":
    main(AddWaterGame(randomSeed=0))
