# Refactor volume-stone.py

# success junf


from GameBasic import *

# water
class Water(GameObject):
    def __init__(self, volume):
        GameObject.__init__(self, "water")
        self.properties["isLiquid"] = True
        self.properties["volume"] = volume

    def getReferents(self):
        return [f"water in {self.parentContainer.name}"]

    def makeDescriptionStr(self, makeDetailed=False):
        return f"water"

# A sink
class Sink(Container, Device):
    def __init__(self, water_out_per_tick, isOn=False):
        GameObject.__init__(self, "sink")
        Container.__init__(self, "sink")
        
        self.properties["containerPrefix"] = "in"
        self.properties["isActivatable"] = True
        self.properties["isMoveable"] = False
        self.properties["isOn"] = isOn
        self.properties["water_out_per_tick"] = water_out_per_tick

    def tick(self):
        containedObjects = self.getAllContainedObjectsRecursive()
        if self.properties["isOn"]:
            for obj in containedObjects:
                if obj.getProperty("isWaterContainer"):
                    foundObjects = obj.containsItemWithName("water")
                    if len(foundObjects) == 0:
                        water = Water(min(obj.getProperty("volume"), self.properties["water_out_per_tick"]))
                        obj.addObject(water)
                    else:
                        foundObjects[0].properties["volume"] = min(obj.getProperty("volume"), foundObjects[0].properties["volume"] + self.properties["water_out_per_tick"])

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a sink"
        outStr += " that is currently " + ("on" if self.properties["isOn"] else "off")
        
        if len(self.contains) == 0:
            outStr += " and that is empty"
        else:
            if not makeDetailed:
                outStr += " and that contains one or more items."
            else:
                outStr += " and that contains the following items: \n"
                for obj in self.contains:
                    outStr += "\t" + obj.makeDescriptionStr() + "\n"

        return outStr

# A measuring cup that can measure the volume of water
class MeasuringCup(Container):
    def __init__(self, volume):
        Container.__init__(self, "measuring cup")
        self.properties['isWaterContainer'] = True
        self.properties['containedVolume'] = 0
        self.properties['containsLiquid'] = False
        self.properties["volume"] = volume

    def addObject(self, obj):
        Container.addObject(self, obj)
        if obj.getProperty("isLiquid"):
            self.properties["containsLiquid"] = True
        self.properties['containedVolume'] = min(obj.getProperty("volume") + self.properties["containedVolume"], self.properties["volume"])

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = f"a {self.name}"
        if self.properties['containedVolume'] > 0:
            contained_items = ', '.join([obj.makeDescriptionStr() for obj in self.contains])
            if self.properties['containsLiquid']:
                outStr += f" which reads {self.properties['containedVolume']} mL. In it, you see {contained_items}."
            else:
                outStr += f". In it, you see {contained_items}."
        else:
            outStr += " that is empty"
        return outStr

# A stone
class Stone(GameObject):
    def __init__(self, name, volume):
        GameObject.__init__(self, name)
        self.properties["volume"] = volume

    def makeDescriptionStr(self, makeDetailed=False):
        return f"a {self.name}"

# World Setup
class RoomWorld(World):
    def __init__(self):
        World.__init__(self, "room")

# Game Implementation
class VolumeStoneGame(TextGame):
    def __init__(self, randomSeed):
        self.agent_answer_volume = None
        self.answer_volume = None
        TextGame.__init__(self, randomSeed)

    def initializeWorld(self):
        world = RoomWorld()

        world.addObject(self.agent)

        sink = Sink(500)
        world.addObject(sink)

        self.answer_volume = self.random.randint(300, 400)
        stone = Stone("stone", self.answer_volume)
        world.addObject(stone)

        measuring_cup = MeasuringCup(1000)
        world.addObject(measuring_cup)

        return world

    def getTaskDescription(self):
        return "Your task is to figure out the volume of the stone."

    def generatePossibleActions(self):
        # Get a list of all game objects that could serve as arguments to actions
        allObjects = self.makeNameToObjectDict()

        # Make a dictionary whose keys are possible action strings, and whose values are lists that contain the arguments.
        self.possibleActions = {}

        for action in [("look around", "look around"), ("look", "look around"), ("inventory", "inventory")]:
            self.addAction(action[0], [action[1]])

        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction("examine " + objReferent, ["examine", obj])
                self.addAction("take " + objReferent, ["take", obj])
                self.addAction("take " + objReferent + " from " + obj.parentContainer.getReferents()[0], ["take", obj])
                self.addAction("turn on " + objReferent, ["turn on", obj])
                self.addAction("turn off " + objReferent, ["turn off", obj])
                self.addAction("examine " + objReferent, ["examine", obj])

        for i in range(300, 401):
            self.addAction(f"answer {i}", ["answer", i])

        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if (obj1 != obj2):
                            containerPrefix = "in"
                            if obj2.properties["isContainer"]:
                                containerPrefix = obj2.properties["containerPrefix"]
                            self.addAction("put " + objReferent1 + " " + containerPrefix + " " + objReferent2,
                                           ["put", obj1, obj2])
                            self.addAction(f"pour {objReferent1} into {objReferent2}", ["pour", obj1, obj2])

        return self.possibleActions

    def actionPour(self, water, target):
        if not isinstance(water, Water):
            return f"Cannot pour {water.name}."
        elif not target.getProperty("isWaterContainer"):
            referent = water.getReferents()[0]
            water.removeSelfFromContainer()
            del water
            return f"{referent} is poured."
        else:
            if water.parentContainer.getProperty("volume") > target.getProperty("volume"):
                water.properties["volume"] = water.parentContainer.getProperty("volume") - target.getProperty("volume")
                extra_water = Water(target.getProperty("volume"))
                target.addObject(extra_water)
            else:
                water.removeSelfFromContainer()
                target.addObject(water)

            return f"You pour {water.getReferents()[0]} into {target.name}"

    def actionTurnOn(self, obj):
        # Check if the object is a device
        if (obj.getProperty("isActivatable") == True):
            # This is handled by the object itself
            obsStr, success = obj.turnOn()
            return obsStr
        else:
            return "You can't turn on that."

    def actionTurnOff(self, obj):
        # Check if the object is a device
        if (obj.getProperty("isActivatable") == True):
            # This is handled by the object itself
            obsStr, success = obj.turnOff()
            return obsStr
        else:
            return "You can't turn off that."

    def actionAnswer(self, volume):
        self.agent_answer_volume = volume
        return f"You believe the volume of the stone is {volume} cm^3."

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
        action = None

        # Check for an ambiguous action (i.e. one that has multiple possible arguments)
        if (len(actions) > 1):
            # If there are multiple possible arguments, for now just choose the first one
            action = actions[0]
        else:
            # Otherwise, also just take the first action in the list of possible actions
            action = actions[0]

        # Interpret the action
        actionVerb = action[0]

        # Define a dictionary mapping action verbs to their corresponding methods
        action_map = {
            "look around": lambda: self.rootObject.makeDescriptionStr(),
            "inventory": lambda: self.actionInventory(),
            "examine": lambda: action[1].makeDescriptionStr(makeDetailed=True),
            "take": lambda: self.actionTake(action[1]),
            "turn on": lambda: self.actionTurnOn(action[1]),
            "turn off": lambda: self.actionTurnOff(action[1]),
            "put": lambda: self.actionPut(action[1], action[2]),
            "pour": lambda: self.actionPour(action[1], action[2]),
            "answer": lambda: self.actionAnswer(action[1]),
        }

        # Execute the mapped function or return an error if action is unknown
        self.observationStr = action_map.get(actionVerb, lambda: "ERROR: Unknown action.")()

        # Do one tick of the environment
        self.doWorldTick()

        # Calculate the score
        lastScore = self.score
        self.calculateScore()
        reward = self.score - lastScore

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    def calculateScore(self):
        self.score = 0

        if self.agent_answer_volume is not None and self.answer_volume == self.agent_answer_volume:
            self.score += 1
            self.gameOver = True
            self.gameWon = True
        else:
            self.gameOver = (self.agent_answer_volume is not None)
            self.gameWon = False

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Execute a game command.")
    parser.add_argument("commands", help="The command to execute in the game")
    args = parser.parse_args()

    print("Command received")
    # Random seed
    randomSeed = 0
    # Create a new game
    game = VolumeStoneGame(randomSeed=randomSeed)
    main(game, args.commands)