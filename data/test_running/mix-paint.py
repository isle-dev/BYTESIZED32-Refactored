# refactored mix-paint.py
# Process and problem of scoring results

from GameBasic import *


# A cup, which is a container that can hold liquid
class Cup(Container):
    def __init__(self, index=None):
        name = f"cup {index}" if index is not None else "cup"
        Container.__init__(self, name)
        self.properties["isLiquidContainer"] = True

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = f"a {self.name}"
        effectiveContents = [obj.makeDescriptionStr() for obj in self.contains]

        if len(effectiveContents) > 0:
            outStr += " containing "
            outStr += ", ".join(effectiveContents[:-1])
            if len(effectiveContents) > 1:
                outStr += ", and " + effectiveContents[-1]
            else:
                outStr += effectiveContents[-1]
        else:
            outStr += " that is empty"

        return outStr


# Paint object representing a color
class Paint(GameObject):
    def __init__(self, color):
        GameObject.__init__(self, f"{color} paint")
        self.properties["color"] = color
        self.properties["isPaint"] = True
        self.properties["isLiquid"] = True

    def makeDescriptionStr(self, makeDetailed=False):
        return self.name


# World setup for the painting task
class ArtStudioWorld(World):
    def __init__(self):
        World.__init__(self, "art studio")


# Game Implementation
class MixPaintGame(TextGame):
    def __init__(self, randomSeed):
        # Random number generator, initialized with a seed passed as an argument
        self.random = random.Random(randomSeed)
        # The agent/player
        self.agent = Agent()
        # Target color
        possibleTargets = ["orange", "purple", "green", "black"]
        self.targetColor = self.random.choice(possibleTargets)
        # Game Object Tree
        self.rootObject = self.initializeWorld()
        # Game score
        self.score = 0
        self.numSteps = 0
        # Game over flag
        self.gameOver = False
        self.gameWon = False
        # Last game observation
        self.observationStr = self.rootObject.makeDescriptionStr()
        # Do calculate initial scoring
        self.calculateScore()

    def initializeWorld(self):
        world = ArtStudioWorld()
        world.addObject(self.agent)

        paintNames = ["red", "yellow", "blue"]
        self.random.shuffle(paintNames)

        for n, color in enumerate(paintNames):
            cup = Cup(n)
            world.addObject(cup)
            cup.addObject(Paint(color=color))

        return world

    def getTaskDescription(self):
        return f"Your task is to mix paints to create {self.targetColor} paint."

    def generatePossibleActions(self):
        # Get a list of all game objects that could serve as arguments to actions
        allObjects = self.makeNameToObjectDict()

        # Make a dictionary whose keys are possible action strings, and whose values are lists that contain the arguments.
        self.possibleActions = {}

        # Zero-argument actions
        for action in [("look around", "look around"), ("look", "look around"), ("inventory", "inventory")]:
            self.addAction(action[0], [action[1]])

        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction("take " + objReferent, ["take", obj])
                self.addAction("take " + objReferent + " from " + obj.parentContainer.getReferents()[0], ["take", obj])
                self.addAction("open " + objReferent, ["open", obj])
                self.addAction("close " + objReferent, ["close", obj])
                self.addAction("examine " + objReferent, ["examine", obj])
                self.addAction("turn on " + objReferent, ["turn on", obj])
                self.addAction("turn off " + objReferent, ["turn off", obj])
                if obj.getProperty("isLiquidContainer"):
                    self.addAction("mix " + objReferent, ["mix", obj])
        # Add specific actions exclusive to paint mixing game
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
                            if obj2.getProperty("isLiquidContainer"):
                                containerPrefix = obj2.getProperty("containerPrefix")
                            self.addAction("pour " + objReferent1 + " " + containerPrefix + " " + objReferent2,
                                           ["pour", obj1, obj2])

        return self.possibleActions

    # Perform the "mix" action
    def actionMix(self, obj):
        def mixColor(colors):
            color_dict = {
                "red": (1, 0, 0), "orange": (1, 1, 0), "yellow": (0, 1, 0),
                "green": (0, 1, 1), "blue": (0, 0, 1), "purple": (1, 0, 1), "black": (1, 1, 1)
            }
            color_dict_reverse = {v: k for k, v in color_dict.items()}
            ryb = (0, 0, 0)
            assert len(colors) > 1
            for color in colors:
                assert color in color_dict
                ryb = tuple(x | y for x, y in zip(ryb, color_dict[color]))
            return color_dict_reverse[ryb]

        if not obj.getProperty("isContainer"):
            return f"You can't mix {obj}"
            # We need to change obj.contains later, but not this list
        containedObj = [o for o in obj.contains]
        if len(containedObj) == 0:
            return f"The {obj.makeDescriptionStr()} is empty."
        elif len(containedObj) == 1:
            return f"There should be at least two substances to mix."
        else:
            colors = []
            for paint in containedObj:
                if not paint.getProperty("isPaint"):
                    return "Unknown objects to mix."
                colors.append(paint.getProperty("color"))
            # mix
            resultColor = mixColor(colors)
            # create a new paint and remove old ones
            newColor = Paint(resultColor)
            for paint in containedObj:
                obj.removeObject(paint)
            obj.addObject(newColor)
            return f"The paints mix to produce {resultColor} paint."

    def actionPour(self, liquid, target):
        if not liquid.getProperty("isLiquid"):
            return f"Cannot pour {liquid.name}."
        if not target.getProperty("isLiquidContainer"):
            return f"{target.name} is not a valid container for {liquid.name}."

        liquid.removeSelfFromContainer()
        target.addObject(liquid)
        return f"You pour {liquid.name} in {target.name}"

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

        # Mapping action verbs to corresponding functions
        action_map = {
            "look around": lambda: self.rootObject.makeDescriptionStr(),
            "inventory": lambda: self.actionInventory(),
            "examine": lambda: action[1].makeDescriptionStr(makeDetailed=True),
            "take": lambda: self.actionTake(action[1]),
            "put": lambda: self.actionPut(action[1], action[2]),
            "mix": lambda: self.actionMix(action[1]),
            "pour": lambda: self.actionPour(action[1], action[2]),
            "use": lambda: self.actionUse(action[1], action[2])
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
        allObjects = self.rootObject.getAllContainedObjectsRecursive()
        for obj in allObjects:
            if obj.getProperty("color") == self.targetColor:
                self.score += 1
                self.gameOver = True
                self.gameWon = True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Execute a game command.")
    parser.add_argument("commands", help="The command to execute in the game")
    args = parser.parse_args()

    print("Command received")
    # Random seed
    randomSeed = 0
    # Create a new game
    game = MixPaintGame(randomSeed=randomSeed)
    main(game, args.commands)
