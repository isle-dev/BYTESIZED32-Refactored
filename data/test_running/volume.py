# Refactored volume.py
# Success Haonan Wang and Ziang Xiao(Oct 2024)
# success junf
from GameBasic import *


# A box with specific size
class Box(GameObject):
    def __init__(self, name, l, w, h):
        GameObject.__init__(self, name)
        self.size = {"length": l, "width": w, "height": h}

    def makeDescriptionStr(self, makeDetailed=False):
        return f"a {self.name}"


# A ruler that can measure a box
class Ruler(GameObject):
    def __init__(self):
        GameObject.__init__(self, "ruler")

    def useWithObject(self, obj, edge):
        # in this game, only boxes can be measured by the ruler
        if type(obj) != Box:
            return "You cannot measure that with a ruler.", False
        elif edge not in obj.size:
            return "I do not understand that."
        else:
            return f"The {edge} of the {obj.name} is {obj.size[edge]} cm", True

    def makeDescriptionStr(self, makeDetailed=False):
        return "a ruler"


# World setup for the game, consisting of a room
class EmergencyRoomWorld(World):
    def __init__(self):
        super().__init__("room")


# The game implementation for measuring the volume of a box
class VolumeMeasurementGame(TextGame):
    def __init__(self, randomSeed):
        self.answer_volume = None
        TextGame.__init__(self, randomSeed)

    # Create/initialize the world and its objects
    def initializeWorld(self):
        world = EmergencyRoomWorld()

        # Add the agent
        world.addObject(self.agent)

        # Possible colors for boxes
        possible_colors = ['red', 'orange', 'yellow', 'green', 'blue', 'black', 'white', 'brown']
        self.random.shuffle(possible_colors)

        # Generate boxes with random sizes and colors
        num_boxes = self.random.randint(2, 8)
        sizes = self.random.choices(range(1, 6), k=num_boxes * 3)

        for i in range(num_boxes):
            box = Box(f"{possible_colors[i]} box", sizes[3 * i] * 10, sizes[3 * i + 1] * 10, sizes[3 * i + 2] * 10)
            if i == 0:  # Determine the target box
                self.target_box_color = possible_colors[0]
                self.target_box_volume = box.size['length'] * box.size['width'] * box.size['height']
            world.addObject(box)

        # Add Ruler
        ruler = Ruler()
        world.addObject(ruler)

        # Return the World
        return world

    def getTaskDescription(self):
        return f"Your task is to calculate the volume of the {self.target_box_color} box."

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
                self.addAction(f"examine {objReferent}", ["examine", obj])
                self.addAction(f"take {objReferent}", ["take", obj])
                self.addAction(f"take {objReferent} from {obj.parentContainer.getReferents()[0]}", ["take", obj])

        # Generate actions for measuring and answering by adding unique actions
        for i in range(1, 125):
            self.addAction(f"answer {i*1000} cubic cm", ["answer", i*1000])

        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if obj1 != obj2:
                            containerPrefix = "in"
                            if obj2.properties["isContainer"]:
                                containerPrefix = obj2.properties["containerPrefix"]
                            self.addAction("put " + objReferent1 + " " + containerPrefix + " " + objReferent2,
                                           ["put", obj1, obj2])

                            for edge in ["length", "width", "height"]:
                                self.addAction(f"measure the {edge} of the {objReferent1} with the {objReferent2}",
                                               ["measure", obj1, obj2, edge])
        return self.possibleActions

    # Interpret eating action
    def actionMeasure(self, patientObject, deviceObj, edge):
        # Only a ruler can be used in this game
        if (type(deviceObj) == Ruler):
            # the agent needs to take the ruler before using it
            if deviceObj.parentContainer.name == "agent":
                # This is handled by the object itself
                obsStr, _ = deviceObj.useWithObject(patientObject, edge)
                return obsStr
            else:
                return "You need to take the ruler first."
        else:
            return "You can't use that."

    def actionAnswer(self, volume):
        self.answer_volume = volume
        return f"You believe the volume of the {self.target_box_color} box is {volume} cubic cm."

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

        # Define a dictionary to map action verbs to their respective methods
        action_map = {
            "look around": lambda: self.rootObject.makeDescriptionStr(),
            "inventory": lambda: self.actionInventory(),
            "examine": lambda: action[1].makeDescriptionStr(makeDetailed = True),
            "take": lambda: self.actionTake(action[1]),
            "put": lambda: self.actionPut(action[1], action[2]),
            "measure": lambda: self.actionMeasure(action[1], action[2], action[3]),
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
        if self.answer_volume is not None:
            if self.target_box_volume == self.answer_volume:
                self.score += 1
                self.gameOver = True
                self.gameWon = True
            else:
                self.score = 0
                self.gameOver = True
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
    game = VolumeMeasurementGame(randomSeed=randomSeed)
    main(game, args.commands)