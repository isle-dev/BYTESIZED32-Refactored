# Refactored bird-life-cycle.py
# Success Haonan Wang and Ziang Xiao(Oct 2024)
# success Haonan (2025.2)

# Task: Create a micro-simulation that models a bird hatching its egg.
# Environment: nest
# Task-critical Objects: Bird
# High-level object classes: Container (Bird)
# Critical properties: stage (Bird, current life stage of the bird), warm (Bird, warmth that an egg gets), food (Bird, food that a young bird gets), hatch (Bird, number of ticks that the egg survives), grow (Bird, number of ticks that the young bird survives)
# Actions: look, inventory, sing, fly around, sit on object, feed object
# Distractor Items: None
# Distractor Actions: sing, fly around
# High-level solution procedure: sit on the egg till it is hatched, feed the young bird till it grows up

from data.library.GameBasic import *


# A bird with three life stages: egg, young bird, adult bird
class Bird(Container):
    def __init__(self, name, stage, warm=3, food=3, hatch=0, grow=0):
        Container.__init__(self, name)
        assert stage in ["egg", "young bird", "adult bird"]
        self.properties["isMoveable"] = False
        self.properties["stage"] = stage
        self.properties["warm"] = warm
        self.properties["food"] = food
        self.properties["hatch"] = hatch
        self.properties["grow"] = grow

    def makeDescriptionStr(self, makeDetailed=False):
        stage = self.properties["stage"]
        if stage == "egg":
            return "an egg" if self.properties["warm"] > 0 else "an egg (dead)"
        elif stage == "young bird":
            return "a young bird" if self.properties["food"] > 1 else f"a hungry {stage}" if self.properties["food"] == 1 else f"a {stage} (dead)"
        else:
            return "an adult bird"

    def getReferents(self):
        return [self.getProperty("stage")]

    def tick(self):
        output_str = None
        stage = self.properties["stage"]

        if stage == "egg":
            # lose 1 point of warm for the egg at each step
            self.properties["warm"] -= 1
            # an egg gain 1 point of hatch at each step, and becomes a young bird when hatch reaches 5
            self.properties["hatch"] += 1
            if self.properties["hatch"] == 5 and self.properties["warm"] > 0:
                self.properties["stage"] = "young bird"
                self.properties["food"] = 3
                output_str = "The egg is hatched!"
        # lose 1 point of food for the young bird at each step
        elif stage == "young bird":
            self.properties["food"] -= 1
            # a young bird gain 1 point of grow at each step, and becomes an adult when grow reaches 5
            self.properties["grow"] += 1
            if self.properties["grow"] == 5 and self.properties["food"] > 0:
                self.properties["stage"] = "adult bird"
                output_str = "The young bird grows up."
        return output_str


# The world is the root object of the game object tree.  In single room environments, it's where all the objects are located.
class NestWorld(World):
    def __init__(self):
        World.__init__(self, "nest")


# The agent (just a placeholder for a container for the inventory)
class Agent(Bird):
    def __init__(self):
        GameObject.__init__(self, "agent")
        Bird.__init__(self, "agent", "adult bird")

    def getReferents(self):
        return ["yourself"]

    def makeDescriptionStr(self, makeDetailed=False):
        return "yourself"

class BirdLifeCycleGame(TextGame):
    def __init__(self, randomSeed):
        TextGame.__init__(self, randomSeed)

    # Create/initialize the world/environment for this game
    def initializeWorld(self):
        world = NestWorld()

        # Add the agent (the mother bird) into the world (nest)
        world.addObject(self.agent)
        # Add an egg into the nest
        egg = Bird("baby", "egg")
        world.addObject(egg)

        return world

    # Get the task description for this game
    def getTaskDescription(self):
        return "Your task is to hatch the egg and raise the baby bird."

    # Returns a list of valid actions at the current time step
    def generatePossibleActions(self):
        # Get a list of all game objects that could serve as arguments to actions
        allObjects = self.makeNameToObjectDict()

        # Make a dictionary whose keys are possible action strings, and whose values are lists that contain the arguments.
        self.possibleActions = {}

        # Actions with zero arguments
        # (0-arg) Look around the environment and look at the agent's current inventory
        # (0-arg) sing, fly
        for action in [("look around", "look around"), ("look", "look around"), ("inventory", "inventory"),
                       ("sing", "sing"), ("fly around", "fly around")]:
            self.addAction(action[0], [action[1]])

        # Actions with one object argument
        # (1-arg) Eat, Hatch an egg, Feed a young bird
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction(f"sit on {objReferent}", ["sit", obj])
                self.addAction(f"feed {objReferent}", ["feed", obj])

        return self.possibleActions

    # Sit on an egg
    def actionSit(self, obj):
        if obj.getProperty("stage") == "egg":
            obj.properties["warm"] = 3
            return "You sit on the egg and keep it warm."
        return "You can't sit on that."

    # Feed a young bird
    def actionFeed(self, obj):
        if obj.getProperty("stage") == "young bird":
            obj.properties["food"] = 3
            return "You feed the young bird."
        return "You can't feed that."

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
            "fly around": lambda: "You fly around.",
            "sing": lambda: "You sing.",
            "sit": lambda action: self.actionSit(action[1]),
            "feed": lambda action: self.actionFeed(action[1])
        }

        # Catch-all
        self.observationStr = action_map.get(actionVerb, lambda action: "ERROR: Unknown action.")(action)

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
            if obj.name != "agent" and obj.getProperty("stage") == "adult bird":
                self.score += 1
                self.gameOver, self.gameWon = True, True
            if obj.getProperty("food") == 0:
                self.score, self.gameOver, self.gameWon = 0, True, False


if __name__ == "__main__":
    # Set random seed 0 and Create a new game
    main(BirdLifeCycleGame(randomSeed=0))