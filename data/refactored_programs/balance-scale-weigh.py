# refactor balance-scale-weigh.py
# Success Haonan Wang and Ziang Xiao(Oct)
# Success Haonan (2025.2)

# Task: Create a micro-simulation that models weighing an object using a balance scale.
# Environment: room
# Task-critical Objects: BalanceScale, Cube, Weight
# High-level object classes: None
# Critical properties: left (BalanceScale, the left side of the balance scale), right (BalanceScale, the right side of the balance scale), weight (Cube, Weight)
# Actions: look, inventory, take/put object, answer
# Distractor Items: Cube
# Distractor Actions: None
# High-level solution procedure: take the target cube, put the cube on one side of the balance scale, add or remove weights to the other side of the balance scale till the scale is in balance


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
        # Add self and all contained objects
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

    # Returns a list of valid actions at the current time step
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
        # (1-arg) Take, Answer
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction(f"take {objReferent}", ["take", obj])
                self.addAction(f"take {objReferent} from {obj.parentContainer.getReferents()[0]}", ["take", obj])

        for i in range(1, self.max_mass + 1):
            self.addAction(f"answer {i}g", ["answer", i])

        # Actions with two object arguments
        # (2-arg) Put
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

        action_map = {
            "look around": self.rootObject.makeDescriptionStr,  # Look around the environment -- i.e. show the description of the world.
            "inventory": self.actionInventory,  # Display the agent's inventory
            "take": lambda: self.actionTake(action[1]),  # Take an object from a container
            "put": lambda: self.actionPut(action[1], action[2]),  # Put an object in a container
            "answer": lambda: self.actionAnswer(action[1])  # Answer the weight of the cube
        }

        # Catch-all
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
        # Baseline score
        self.score = 0

        if self.answer_mass is not None:
            if self.cube_weight == self.answer_mass:
                self.score += 1
                self.gameOver, self.gameWon = True, True
            else:
                self.score, self.gameOver, self.gameWon = 0, True, False

if __name__ == "__main__":
    # Set random seed 0 and Create a new game
    main(BalanceScaleWeighGame(randomSeed=0))