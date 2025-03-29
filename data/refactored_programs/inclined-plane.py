# refactored inclined-plane.py
# Process and problem of code generation
# success Haonan(2025.2)

# Task: Create a micro-simulation that models how to compare the friction of two inclined planes by measuring the time a block sliding down the plane.
# Environment: workshop
# Task-critical Objects: InclinedPlane, Stopwatch
# High-level object classes: Container (InclinedPlane)
# Critical properties: acceleration (InclinedPlane), length (InclinedPlane), objects (InclinedPlane), isActivated (Stopwatch), tick (Stopwatch)
# Actions: look, inventory, examine, take/put objects, activate/deactivate/reset stopwatch, focus on object
# Distractor Items: None
# Distractor Actions: None
# High-level solution procedure: take stopwatch, take the block, put the block on the first inclined plane, activate stopwatch, wait till the block slides down to the bottom, deactivate stopwatch, examine stopwatch, reset stopwatch, take the block, put the block on the second inclined plane, activate the stopwatch, wait till the block slides to the bottom, deactivate stopwatch, examiine stopwatch, focus on the answer inclined plane

from data.library.GameBasic import *


# InclinedPlane class
class InclinedPlane(Container):
    def __init__(self, name, acceleration, length):
        super().__init__(name)
        self.properties["containerPrefix"] = "on"
        self.properties["isMoveable"] = False
        self.properties["acceleration"] = acceleration  # acceleration a block can have when putting on the inclined plane, reflects the angle of the inclined plane
        self.properties["length"] = length  # the length of the surface of the inclined plane
        self.properties["objects"] = {}

    def addObject(self, obj):
        self.properties["objects"][obj] = 0
        super().addObject(obj)

    def removeObject(self, obj):
        self.properties["objects"].pop(obj)
        super().removeObject(obj)

    def tick(self):
        for obj in self.properties["objects"]:
            self.properties["objects"][obj] += 1

    def makeDescriptionStr(self, makeDetailed=False):
        if len(self.contains) == 0:
            return f"an {self.name}"
        else:
            outStr = f"an {self.name}, with:"
            obj_desc = []
            for obj in self.properties["objects"]:
                distance = 0.5 * self.properties["acceleration"] * self.properties["objects"][obj] ** 2
                rate = 1 if distance > self.properties["length"] else round(distance / self.properties["length"], 3)
                obj_desc.append(f"a {obj.name} approximately {rate * 100}% down the plane")
            outStr += ', '.join(obj_desc)
            return outStr


# Stopwatch
class Stopwatch(GameObject):
    def __init__(self, name):
        GameObject.__init__(self, name)
        self.properties["isActivated"] = False
        self.properties["tick"] = 0

    def tick(self):
        if self.properties["isActivated"]:
            self.properties["tick"] += 1

    def reset(self):
        self.properties["isActivated"] = False
        self.properties["tick"] = 0

    def makeDescriptionStr(self, makeDetailed=False):
        activated = "activated" if self.properties["isActivated"] else "deactivated"
        if makeDetailed:
            outStr = f"a {self.name}, which is {activated}. The time reads {self.properties['tick']} ticks."
        else:
            outStr = f"a {self.name}, which is {activated}"
        return outStr


# The world is the root object of the game object tree.  In single room environments, it's where all the objects are located.
class WorkshopWorld(World):
    def __init__(self):
        World.__init__(self, "workshop")

class InclinedPlaneGame(TextGame):
    def __init__(self, randomSeed):
        self.agent_answer = None
        TextGame.__init__(self, randomSeed)

    def initializeWorld(self):
        world = WorkshopWorld()

        # Add the agent
        world.addObject(self.agent)

        # Add two inclined planes
        self.a1, self.a2 = self.random.sample([0.5, 1, 1.5, 2], 2)
        inclined_plane_1 = InclinedPlane("inclined plane 1", self.a1, 100)
        inclined_plane_2 = InclinedPlane("inclined plane 2", self.a2, 100)
        world.addObject(inclined_plane_1)
        world.addObject(inclined_plane_2)

        self.answer = inclined_plane_1 if self.a1 < self.a2 else inclined_plane_2

        # Add block and stopwatch
        block = GameObject("block")
        world.addObject(block)
        stopwatch = Stopwatch("stopwatch")
        world.addObject(stopwatch)

        return world

    # Get the task description for this game
    def getTaskDescription(self):
        return "Here are two inclined planes with the same angle. Your task is to figure out which of the two inclined planes has the most friction. Focus on the inclined plane with the most friction after your experiment."

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
        # (1-arg) Take, Detailed look/examine, activate/deactivate/reset stopwatch, focus
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction("take " + objReferent, ["take", obj])
                self.addAction("take " + objReferent + " from " + obj.parentContainer.getReferents()[0], ["take", obj])
                self.addAction("examine " + objReferent, ["examine", obj])
                self.addAction("activate " + objReferent, ["activate", obj])
                self.addAction("deactivate " + objReferent, ["deactivate", obj])
                self.addAction("reset " + objReferent, ["reset", obj])
                self.addAction("focus on " + objReferent, ["focus", obj])

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

    # Activate a stopwatch
    def actionActivate(self, stopwatch):
        # type checking
        if type(stopwatch) != Stopwatch:
            return f"You can't activate the {stopwatch.name}."

        # check if the agent has the stopwatch
        if type(stopwatch.parentContainer) != Agent:
            return f"You should take the {stopwatch.name} first."

        if not stopwatch.properties["isActivated"]:
            stopwatch.properties["isActivated"] = True
            return f"You activate the {stopwatch.name}."
        else:
            return f"The {stopwatch.name} has already been activated."

    # Deactivate a stopwatch
    def actionDeactivate(self, stopwatch):
        # type checking
        if type(stopwatch) != Stopwatch:
            return f"You can't deactivate the {stopwatch.name}."

        # check if the agent has the stopwatch
        if type(stopwatch.parentContainer) != Agent:
            return f"You should take the {stopwatch.name} first."

        if stopwatch.properties["isActivated"]:
            stopwatch.properties["isActivated"] = False
            return f"You deactivate the {stopwatch.name}."
        else:
            return f"The {stopwatch.name} has already been deactivated."

    # reset a stopwatch
    def actionReset(self, stopwatch):
        # type checking
        if type(stopwatch) != Stopwatch:
            return f"You can't reset the {stopwatch.name}."
        # check if the agent has the stopwatch
        if type(stopwatch.parentContainer) != Agent:
            return f"You should take the {stopwatch.name} first."
        # reset
        stopwatch.reset()
        return f"You reset the {stopwatch.name}."

    # focus on one of the inclined planes
    def actionFocus(self, inclined_plane):
        if not isinstance(inclined_plane, InclinedPlane):
            return f"You can't focus on the {inclined_plane.name}."
        self.agent_answer = inclined_plane
        return f"You focus on the {inclined_plane.name}."

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
            "look around": self.rootObject.makeDescriptionStr,  # Look around the environment -- i.e. show the description of the world.
            "inventory": self.actionInventory,  # Display the agent's inventory
            "examine": lambda: action[1].makeDescriptionStr(makeDetailed=True),  # Examine an object
            "take": lambda: self.actionTake(action[1]),  # Take an object from a container
            "put": lambda: self.actionPut(action[1], action[2]),  # Put an object in a container
            "activate": lambda: self.actionActivate(action[1]),  # activate a stopwatch
            "deactivate": lambda: self.actionDeactivate(action[1]),  # deactivate a stopwatch
            "reset": lambda: self.actionReset(action[1]),  # reset a stopwatch
            "focus": lambda: self.actionFocus(action[1])
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
        # Baseline score
        if self.agent_answer is not None:
            self.gameOver, self.gameWon, self.score= True, (self.agent_answer == self.answer), 1

if __name__ == "__main__":
    # Set random seed 0 and Create a new game
    main(InclinedPlaneGame(randomSeed=0))