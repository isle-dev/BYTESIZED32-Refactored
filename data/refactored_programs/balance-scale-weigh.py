# refactor balance-scale-weigh.py
# Success Haonan Wang and Ziang Xiao(Nov 2024)

#
from data.library.GameBasic import *

    # A balance scale
class BalanceScale(Container):
    def __init__(self, name):
        Container.__init__(self, name)
        self.properties["isMoveable"] = False
        # Initialize both sides of the scale
        self.left = Container(f"left side of the {name}")
        self.left.properties["isMoveable"] = False
        self.left.parentContainer = self
        self.right = Container(f"right side of the {name}")
        self.right.properties["isMoveable"] = False
        self.right.parentContainer = self

    def makeDescriptionStr(self, makeDetailed=False):
        main_string = f"a {self.name} with two plates."
        left_weight = self.get_mass(self.left)
        right_weight = self.get_mass(self.right)

        if left_weight > right_weight:
            state_string = "The left side of the scale is lower than the right side."
        elif left_weight < right_weight:
            state_string = "The left side of the scale is higher than the right side."
        else:
            state_string = "The scale is in balance."

        def makeOneSideDescription(contains):
            effectiveContents = [obj.makeDescriptionStr() for obj in contains.contains]
            if effectiveContents:
                outStr = "contains " + ", ".join(effectiveContents[:-1]) + (
                    ", and " if len(effectiveContents) > 1 else "") + effectiveContents[-1]
            else:
                outStr = "is empty"
            return outStr

        left_desc = makeOneSideDescription(self.left)
        right_desc = makeOneSideDescription(self.right)
        outStr = f"{main_string} {state_string} The left plate {left_desc}. The right plate {right_desc}."
        return outStr

    # compute the total mass of one side
    def get_mass(self, contains):
        return sum(obj.getProperty("weight") for obj in contains.contains)

    # get all objects recursively from both sides
    def getAllContainedObjectsRecursive(self):
        outList = self.left.getAllContainedObjectsRecursive() + self.right.getAllContainedObjectsRecursive()
        outList.extend([self.left, self.right])
        return outList

    def placeObjectInContainer(self, obj):
        return f"You can't put {obj.name} on a balance scale directly. Put it on one side of the scale.", False

    def takeObjectFromContainer(self, obj):
        return f"You can't take {obj.name}.", None, False

# Cubes for testing weights
class Cube(GameObject):
    def __init__(self, mass):
        GameObject.__init__(self, "cube")
        self.properties['weight'] = mass

    def makeDescriptionStr(self, makeDetailed=False):
        return "a " + self.name

# Weights
class Weight(GameObject):
    def __init__(self, name_idx, mass):
        GameObject.__init__(self, f"weight {name_idx}")
        self.properties['weight'] = mass

    def makeDescriptionStr(self, makeDetailed=False):
        return f"{self.properties['weight']}g {self.name}"

# Game Implementation
class BalanceScaleWeighGame(TextGame):
    def __init__(self, randomSeed):
        # Max mass we can weigh
        self.max_mass = 19
        # Initialize the variable to save the player's answer
        self.answer_mass = None
        TextGame.__init__(self, randomSeed)

    # Create/initialize the world/environment for this game
    def initializeWorld(self):
        world = World("room")

        # Add the agent
        world.addObject(self.agent)

        # Add a balance scale
        scale = BalanceScale("balance scale")
        world.addObject(scale)

        # generate weights, 1g*2, 2g*1, 5g*1, 10g*1
        all_mass = [1,1,2,5,10]
        for n, mass in enumerate(all_mass):
            weight = Weight(n, mass)
            world.addObject(weight)

        # Add cubes to weigh
        self.cube_weight = self.random.choice(range(1, self.max_mass + 1))
        cube = Cube(self.cube_weight)
        world.addObject(cube)

        # Add an answer box
        box = Container("box")
        world.addObject(box)

        # Return the world
        return world

    # Get the task description for this game
    def getTaskDescription(self):
        return "Your task is to figure out the weight of the cube. Use the answer action to give your answer."

    # Extend the possible actions to include the answer action
    def generatePossibleActions(self):
        # Get a list of all game objects that could serve as arguments to actions
        allObjects = self.makeNameToObjectDict()

        # Make a dictionary whose keys are possible action strings, and whose values are lists that contain the arguments.
        self.possibleActions = {}
        # Zero-argument actions
        for action in [("look around", "look around"), ("look", "look around"), ("inventory", "inventory")]:
            self.addAction(action[0], [action[1]])

        # One-object actions
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction(f"take {objReferent}", ["take", obj])
                self.addAction(f"take {objReferent} from {obj.parentContainer.getReferents()[0]}", ["take", obj])

        # Answer actions
        for i in range(1, self.max_mass + 1):
            self.addAction(f"answer {i}g", ["answer", i])

        # Two-object actions (Put)
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if obj1 != obj2:
                            containerPrefix = obj2.properties.get("containerPrefix", "in") if obj2.properties.get(
                                "isContainer") else "in"
                            self.addAction(f"put {objReferent1} {containerPrefix} {objReferent2}", ["put", obj1, obj2])

        return self.possibleActions

    #
    #   Interpret actions
    #

    # Answer
    def actionAnswer(self, mass):
        self.answer_mass = mass
        return f"You believe the cube weighs {mass}g."

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

        action_map = {
            "look around": self.rootObject.makeDescriptionStr,
            "inventory": self.actionInventory,
            "take": lambda: self.actionTake(action[1]),
            "put": lambda: self.actionPut(action[1], action[2]),
            "answer": lambda: self.actionAnswer(action[1])
        }

        self.observationStr = action_map.get(actionVerb, lambda: "ERROR: Unknown action")()

        # Do one tick of the environment
        self.doWorldTick()

        # Calculate the score
        lastScore = self.score
        self.calculateScore()
        reward = self.score - lastScore

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    # Calculate the game score
    def calculateScore(self):
        self.score = 0

        if self.answer_mass is not None:
            if self.cube_weight == self.answer_mass:
                self.score += 1
                self.gameOver, self.gameWon = True, True
            else:
                self.score, self.gameOver, self.gameWon = 0, True, False

if __name__ == "__main__":
    # Random seed
    randomSeed = 0

    # Create a new game
    game = BalanceScaleWeighGame(randomSeed=randomSeed)
    main(game)