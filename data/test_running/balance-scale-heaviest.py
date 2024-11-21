# refactor balance-scale-heaviest.py
# Success Haonan Wang and Ziang Xiao(Oct 2024)2

# Changed the main function, easy to test, he is not the final code, is different.

from GameBasic import *

class BalanceScale(GameObject):
    def __init__(self, name):
        GameObject.__init__(self, name)
        self.properties["isMoveable"] = False
        # Initialize both sides of the scale
        self.left = Container(f"left side of the {name}")
        self.left.parentContainer = self
        self.right = Container(f"right side of the {name}")
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
        mass = 0
        for obj in contains.contains:
            mass += obj.getProperty("weight")
        return mass

    # get all objects recursively from both sides
    def getAllContainedObjectsRecursive(self):
        outList = [self.left, self.right]
        for obj in self.left.contains:
            # Add self
            outList.append(obj)
            # Add all contained objects
            outList.extend(obj.getAllContainedObjectsRecursive())
        for obj in self.right.contains:
            # Add self
            outList.append(obj)
            # Add all contained objects
            outList.extend(obj.getAllContainedObjectsRecursive())
        return outList

class Cube(GameObject):
    def __init__(self, name, mass):
        GameObject.__init__(self, name)
        self.properties['weight'] = mass

    def makeDescriptionStr(self, makeDetailed=False):
        return "a " + self.name


class BalanceGame(TextGame):
    def __init__(self, randomSeed):
        TextGame.__init__(self, randomSeed)

    def initializeWorld(self):
        world = World("room")

        # Add the agent
        world.addObject(self.agent)

        # Add a balance scale
        scale = BalanceScale("balance scale")
        world.addObject(scale)

        # Add cubes to weigh
        all_colors = ["red", "yellow", "blue", "black", "white"]
        # generate 2 to 4 cubes with different colors
        num_cubes = self.random.choice([2,3,4])
        self.random.shuffle(all_colors)
        colors = all_colors[:num_cubes]
        weights = self.random.choices(range(num_cubes*2),k=num_cubes)
        self.max_weight = max(weights)
        for color, mass in zip(colors, weights):
            cube = Cube(f"{color} cube", mass)
            world.addObject(cube)

        # Add an answer box
        box = Container("box")
        world.addObject(box)

        # Return the world
        return world

    def getTaskDescription(self):
        return "Your task is to put all heaviest cubes into the box."

    def generatePossibleActions(self):
        # Get a list of all game objects that could serve as arguments to actions
        allObjects = self.makeNameToObjectDict()

        # Make a dictionary whose keys are possible action strings, and whose values are lists that contain the arguments.
        self.possibleActions = {}

        # Zero-argument actions
        for action in [("look around", "look around"), ("look", "look around"), ("inventory", "inventory")]:
            self.addAction(action[0], [action[1]])

        # One-object actions (Take)
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction(f"take {objReferent}", ["take", obj])
                self.addAction(f"take {objReferent} from {obj.parentContainer.getReferents()[0]}", ["take", obj])

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
            "put": lambda: self.actionPut(action[1], action[2])
        }

        self.observationStr = action_map.get(actionVerb, lambda: "ERROR: Unknown action")()

        # Do one tick of the environment
        self.doWorldTick()

        # Calculate the score
        lastScore = self.score
        self.calculateScore()
        reward = self.score - lastScore

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    def calculateScore(self):

        # Baseline score
        self.score = 0
        allObjects = self.rootObject.getAllContainedObjectsRecursive()
        completed = True
        fail = False
        for obj in allObjects:
            if type(obj) == Cube:
                if obj.getProperty('weight') == self.max_weight and obj.parentContainer.name != 'box':
                    completed = False
                # Game fails if a wrong cube in put into the answer box
                elif obj.getProperty('weight') != self.max_weight and obj.parentContainer.name == 'box':
                    fail = True

        if fail:
            self.score, self.gameOver, self.gameWon = 0, True, False
        elif completed:
            self.score += 1
            self.gameOver, self.gameWon = True, True


# Run the main program
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Execute a game command.")
    parser.add_argument("commands", help="The command to execute in the game")
    args = parser.parse_args()

    print("Command received")
    # Random seed
    randomSeed = 0
    # Create a new game
    game = BalanceGame(randomSeed=randomSeed)
    main(game, args.commands)