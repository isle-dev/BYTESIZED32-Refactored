# refactor balance-scale-heaviest.py
# Success Haonan Wang and Ziang Xiao(Oct 2024)
# Success Haonan (2025.2)

# Task: Create a micro-simulation that requires a user to find the heaviest cubes using a balance scale.
# Environment: room
# Task-critical Objects: BalanceScale, Cube, Container
# High-level object classes: None
# Critical properties: left (BalanceScale, the left side of the balance scale), right (BalanceScale, the right side of the balance scale), weight (Cube)
# Actions: look, inventory, take/put object
# Distractor Items: None
# Distractor Actions: None
# High-level solution procedure: take two cubes and put them on each side of the balance scale, replace the lighter cube with another cube, repeat until all heaviest cubes are found


from data.library.GameBasic import *

# A balance scale
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

# Cubes for testing weights
class Cube(GameObject):
    def __init__(self, name, mass):
        GameObject.__init__(self, name)
        self.properties['weight'] = mass

    def makeDescriptionStr(self, makeDetailed=False):
        return "a " + self.name

class BalanceGame(TextGame):
    def __init__(self, randomSeed):
        TextGame.__init__(self, randomSeed)

    # Create/initialize the world/environment for this game
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

    # Get the task description for this game
    def getTaskDescription(self):
        return "Your task is to put all heaviest cubes into the box."

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
        # (1-arg) Take
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction(f"take {objReferent}", ["take", obj])
                self.addAction(f"take {objReferent} from {obj.parentContainer.getReferents()[0]}", ["take", obj])

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
            "put": lambda: self.actionPut(action[1], action[2])  # Put an object in a container
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

    def calculateScore(self):

        # Baseline score
        self.score = 0

        # Check if all cubes with the max weight is in the answer box.
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
    # Set random seed 0 and Create a new game
    main(BalanceGame(randomSeed=0))