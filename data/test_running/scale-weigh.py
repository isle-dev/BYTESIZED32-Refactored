# Refactored scale-weigh.py



from GameBasic import *


# An object that can be put on the scale
class TestObject(GameObject):
    def __init__(self, name, weight):
        GameObject.__init__(self, name)  # Call superclass constructor
        self.properties["weight"] = weight

    def makeDescriptionStr(self, makeDetailed=False):
        det = 'an' if self.name[0].lower() in ['a', 'e', 'i', 'o', 'u'] else 'a'
        return f"{det} {self.name}"


# A scale that measures the total weight of the objects on it
class Scale(Container):
    def __init__(self):
        Container.__init__(self, "scale")
        # We do not allow the scale to be moved in this game
        self.properties['isMoveable'] = False
        self.properties["containerPrefix"] = "on"

    def makeDescriptionStr(self, makeDetailed=False):
        if len(self.contains) == 0:
            return "a scale which reads 0g"

        total_weights = 0
        outStr = "contains "

        for i, obj in enumerate(self.contains):
            if i == len(self.contains) - 1 and len(self.contains) > 1:
                outStr += "and "
            outStr += obj.makeDescriptionStr() + ", "
            total_weights += obj.getProperty("weight")

        outStr = outStr.rstrip(", ")
        return f"a scale which reads {total_weights}g and {outStr}"


class RoomWorld(World):
    def __init__(self):
        World.__init__(self, "room")


class ScaleWeighGame(TextGame):
    def __init__(self, randomSeed):
        self.answer_weight = None
        super().__init__(randomSeed)

    def initializeWorld(self):
        world = RoomWorld()

        # Add the agent
        world.addObject(self.agent)

        # possible objects to weigh
        possible_objects = ['apple', 'peach', 'pear', 'orange', 'banana']
        self.random.shuffle(possible_objects)

        # Generate 2-5 objects
        num_objects = self.random.randint(2, 5)
        weights = self.random.choices(range(150, 300), k=num_objects)
        target_id = self.random.randint(0, num_objects - 1)

        for i in range(num_objects):
            obj = TestObject(possible_objects[i], weights[i])
            world.addObject(obj)

        self.target_object = possible_objects[target_id]
        self.target_weight = weights[target_id]

        # Add a scale
        scale = Scale()
        world.addObject(scale)

        return world

    def getTaskDescription(self):
        return f"Your task is to figure out the weight of the {self.target_object}."

    def generatePossibleActions(self):
        # Get a list of all game objects that could serve as arguments to actions
        allObjects = self.makeNameToObjectDict()

        # Make a dictionary whose keys are possible action strings, and whose values are lists that contain the arguments.
        self.possibleActions = {}

        # Zero-argument actions
        for action in [("look around", "look around"), ("look", "look around"), ("inventory", "inventory")]:
            self.addAction(action[0], [action[1]])

        # Add actions specific to ScaleWeighGame
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction(f"take {objReferent}", ["take", obj])
                self.addAction(f"take {objReferent} from {obj.parentContainer.getReferents()[0]}", ["take", obj])
                self.addAction(f"examine {objReferent}", ["examine", obj])

        for i in range(150, 300):
            self.addAction(f"answer {i}g", ["answer", i])
            # Actions with two object arguments
            # (2-arg) Put
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

        return self.possibleActions

    def actionAnswer(self, weight):
        self.answer_weight = weight
        return f"You believe the weight of the {self.target_object} is {weight}g."

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

        if (actionVerb == "look around"):
            # Look around the environment -- i.e. show the description of the world.
            self.observationStr = self.rootObject.makeDescriptionStr()
        elif (actionVerb == "inventory"):
            # Display the agent's inventory
            self.observationStr = self.actionInventory()
        elif (actionVerb == "examine"):
            # Examine an object
            thingToExamine = action[1]
            self.observationStr = thingToExamine.makeDescriptionStr(makeDetailed=True)
        elif (actionVerb == "take"):
            # Take an object from a container
            thingToTake = action[1]
            self.observationStr = self.actionTake(thingToTake)
        elif (actionVerb == "put"):
            # Put an object in a container
            thingToMove = action[1]
            newContainer = action[2]
            self.observationStr = self.actionPut(thingToMove, newContainer)
        elif (actionVerb == "answer"):
            # Answer the volume
            answer = action[1]
            self.observationStr = self.actionAnswer(answer)
        # Catch-all
        else:
            self.observationStr = "ERROR: Unknown action."

        # Do one tick of the environment
        self.doWorldTick()

        # Calculate the score
        lastScore = self.score
        self.calculateScore()
        reward = self.score - lastScore

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    def calculateScore(self):
        self.score = 0
        self.gameOver = True
        if self.answer_weight is not None:
            if self.target_weight == self.answer_weight:
                self.score += 1
                self.gameWon = True
            else:
                self.score = 0
                self.gameWon = False


if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser(description="Execute a game command.")
    parser.add_argument("commands", help="The command to execute in the game")
    args = parser.parse_args()

    print("Command received")
    # Random seed
    randomSeed = 1
    # Create a new game
    game = ScaleWeighGame(randomSeed=randomSeed)
    main(game, args.commands)