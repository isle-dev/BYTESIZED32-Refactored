# refactored mix-paint.py
# Process and problem of scoring results
# Success Haonan (2025.2)

# Task: Create a micro-simulation that models mixning paints to get new colors.
# Environment: art studio
# Task-critical Objects: Cup, Paint
# High-level object classes: Container (Cup)
# Critical properties: color (Paint)
# Actions: look, inventory, examine, take/put object, pour X to Y, mix container
# Distractor Items: None
# Distractor Actions: None
# High-level solution procedure: pour the correct source paints into the same cup, mix the paints

from data.library.GameBasic import *


# A cup, which is a container that can hold liquid
class Cup(Container):
    def __init__(self, index=None):
        name = f"cup {index}" if index is not None else "cup"
        GameObject.__init__(self, name)
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

# Paint
class Paint(GameObject):
    def __init__(self, color):
        GameObject.__init__(self, f"{color} paint")
        self.properties["color"] = color
        self.properties["isPaint"] = True
        self.properties["isLiquid"] = True

    def makeDescriptionStr(self, makeDetailed=False):
        return self.name


# The world is the root object of the game object tree.  In single room environments, it's where all the objects are located.
class ArtStudioWorld(World):
    def __init__(self):
        World.__init__(self, "art studio")


# Game Implementation
class MixPaintGame(TextGame):
    def __init__(self, randomSeed):
        # Random number generator, initialized with a seed passed as an argument
        self.random = random.Random(randomSeed)
        # The agent/player
        self.agent = Agent("Agent")
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

        # Add paints
        for n, color in enumerate(paintNames):
            # Add a cup to hold the paint
            cup = Cup(n)
            world.addObject(cup)
            # Create a new paint
            paint = Paint(color=color)
            # Put paint into the cup
            cup.addObject(paint)

        return world

    def getTaskDescription(self):
        return f"Your task is to use chemistry to create {self.targetColor} paint."

    # Get the task description for this game
    def generatePossibleActions(self):
        # Get a list of all game objects that could serve as arguments to actions
        allObjects = self.makeNameToObjectDict()

        # Make a dictionary whose keys are possible action strings, and whose values are lists that contain the arguments.
        self.possibleActions = {}

        # Actions with zero arguments
        # (0-arg) Look around the environment and Look at the agent's current inventory
        for action in [("look around", "look around"), ("look", "look around"), ("inventory", "inventory")]:
            self.addAction(action[0], [action[1]])

        # Actions with one object argument
        # (1-arg) Take, Open/Close, Detailed look/examine, Turn on/Turn off device, Mix container
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
        # Actions with two object arguments
        # (2-arg) Put, Pour
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
        elif not target.getProperty("isLiquidContainer"):
            return f"{target.name} is not a valid container for {liquid.name}."
        else:
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
            "look around": lambda: self.rootObject.makeDescriptionStr(),  # Look around the environment -- i.e. show the description of the world.
            "inventory": lambda: self.actionInventory(),  # Display the agent's inventory
            "examine": lambda: action[1].makeDescriptionStr(makeDetailed=True),  # Examine an object
            "take": lambda: self.actionTake(action[1]),  # Take an object from a container
            "put": lambda: self.actionPut(action[1], action[2]),  # Put an object in a container
            "mix": lambda: self.actionMix(action[1]),
            "pour": lambda: self.actionPour(action[1], action[2]),
            "use": lambda: self.actionUse(action[1], action[2])  ## OMIT, UNUSED (make ice cubes)
        }

        # Catch-all
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
                self.gameOver, self.gameWon  = True, True

if __name__ == "__main__":
    # Set random seed 0 and Create a new game
    main(MixPaintGame(randomSeed=0))