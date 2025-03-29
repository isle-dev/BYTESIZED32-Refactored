# Refactor sweep-floor.py
# Process and problem of code
# Sucess Haonan(2025.2)

# Task: Create a micro-simulation that models how to sweep garbage to a garbage can with a broom and a dustpan.
# Environment: room
# Task-critical Objects: Tool, Garbage, GarbageCan, dustpan
# High-level object classes: Container (GarbageCan)
# Critical properties: None
# Actions: look, inventory, take/put objects, sweep garbage to dustpan with broom, dump dustpan to garbage can
# Distractor Items: Tool
# Distractor Actions: None
# High-level solution procedure: take the broom, take the dustpan, sweep all garbage to the dustpan, open garbage can, dump everything in the dustpan to the garbage can

from data.library.GameBasic import *


class Tool(GameObject):
    def __init__(self, name):
        GameObject.__init__(self, name)

    def makeDescriptionStr(self, makeDetailed=False):
        return f"a(n) {self.name}"

class Garbage(GameObject):
    def __init__(self, name):
        GameObject.__init__(self, name)
        self.properties["isMoveable"] = False  # We don't allow the garbage to be directly taken by the agent

    def makeDescriptionStr(self, makeDetailed=False):
        if self.parentContainer.name == "room":
            return f"{self.name} on the ground"
        return self.name

class GarbageCan(Container):
    def __init__(self, name):
        GameObject.__init__(self, name)
        Container.__init__(self, name)
        self.properties["isMoveable"] = False  # We don't allow the garbage can to be directly moved by the agent
        self.properties["isOpenable"] = True
        self.properties["isOpen"] = False

    def makeDescriptionStr(self, makeDetailed=False):
        if len(self.contains) == 0:
            return f"an empty {self.name}"
        else:
            outStr = f"a(n) {self.name}, which contains: \n"
            for obj in self.contains:
                outStr += '\n'.join(["\t\t" + desc for desc in obj.makeDescriptionStr().strip().split('\n')]) + '\n'

            return outStr

class Dustpan(Container):
    def __init__(self, name):
        GameObject.__init__(self, name)
        Container.__init__(self, name)

    def makeDescriptionStr(self, makeDetailed=False):
        if len(self.contains) == 0:
            return f"an empty {self.name}"
        else:
            outStr = f"a(n) {self.name}, which contains: \n"
            for obj in self.contains:
                outStr += '\n'.join(["\t\t" + desc for desc in obj.makeDescriptionStr().strip().split('\n')]) + '\n'

            return outStr

# The world is the root object of the game object tree.  In single room environments, it's where all the objects are located.
class RoomWorld(World):
    def __init__(self):
        Container.__init__(self, "room")

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "You find yourself in a room.  In the room, you see: \n"
        for obj in self.contains:
            outStr += '\n'.join(["\t" + desc for desc in obj.makeDescriptionStr().strip().split('\n')]) + '\n'

        return outStr

# Game implementation for sweeping the floor
class SweepFloorGame(TextGame):
    def __init__(self, randomSeed):
        TextGame.__init__(self, randomSeed)

    # Initialize world and add objects
    def initializeWorld(self):
        world = RoomWorld()

        # Add the agent
        world.addObject(self.agent)
        # Add a broom
        world.addObject(Tool("broom"))
        # Add a dustpan
        world.addObject(Dustpan("dustpan"))
        # Add a garbage can
        world.addObject(GarbageCan("garbage can"))
        # Garbage
        possible_garbage = ["broken glass", "waste paper", "dust", "dog hair", "watermelon rind"]
        num_garbage = self.random.randint(2, 5)
        self.random.shuffle(possible_garbage)
        for garbage_name in possible_garbage[:num_garbage]:
            garbage = Garbage(garbage_name)
            world.addObject(garbage)

        # Distractors
        world.addObject(Tool("mop"))
        return world

    # Get the task description for this game
    def getTaskDescription(self):
        return 'Your task is to clean the garbage on the ground to the garbage can.'

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
        # (1-arg) Take, Open/Close
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction("take " + objReferent, ["take", obj])
                self.addAction("take " + objReferent + " from " + obj.parentContainer.getReferents()[0],
                               ["take", obj])
                self.addAction("open " + objReferent, ["open", obj])
                self.addAction("close " + objReferent, ["close", obj])

        # Actions with two object arguments
        # (2-arg) Put, Empty
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for objReferent3, objs3 in allObjects.items():
                    for obj1 in objs1:
                        for obj2 in objs2:
                            for obj3 in objs3:
                                if obj1 != obj2 and obj2 != obj3 and obj3 != obj1:
                                    self.addAction(f"sweep {objReferent1} to {objReferent2} with {objReferent3}" , ["sweep", obj1, obj2, obj3])

        # Actions with three object arguments
        # (3-arg) Sweep
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if obj1 != obj2:
                            containerPrefix = "in"
                            if obj2.properties["isContainer"]:
                                containerPrefix = obj2.properties["containerPrefix"]
                            self.addAction("put " + objReferent1 + " " + containerPrefix + " " + objReferent2, ["put", obj1, obj2])
                            self.addAction("dump " + objReferent1 + " to " + objReferent2, ["dump", obj1, obj2])

        return self.possibleActions

    # Open a container
    def actionOpen(self, obj):
        # Check if the object is a container
        if (obj.getProperty("isContainer") == True):
            # This is handled by the object itself
            obsStr, success = obj.openContainer()
            return obsStr
        else:
            return "You can't open that."

    # Close a container
    def actionClose(self, obj):
        # Check if the object is a container
        if (obj.getProperty("isContainer") == True):
            # This is handled by the object itself
            obsStr, success = obj.closeContainer()
            return obsStr
        else:
            return "You can't close that."

    def actionSweep(self, garbage, dustpan, broom):
        if not isinstance(garbage, Garbage):
            return f"{garbage.name} is not garbage."

        if dustpan.name != "dustpan":
            return f"You can't sweep {garbage.name} to {dustpan.name}."
        if broom.name != "broom":
            return f"You can't sweep {garbage.name} with {broom.name}."

        # the agent should take the broom before sweeping
        if type(broom.parentContainer) != Agent:
            return f"You should take the {broom.name} before sweeping."

        # the agent should take the dustpan before sweeping
        if type(dustpan.parentContainer) != Agent:
            return f"You should take the {dustpan.name} before sweeping."

        # Only garbage on the ground can be swept
        if garbage.parentContainer.name != "room":
            return "You can only sweep garbage on the ground."

        dustpan.addObject(garbage)
        return f"You sweep {garbage.name} to {dustpan.name}."

    def actionDump(self, dustpan, garbage_can):
        if dustpan.name != "dustpan":
            return f"You can't empty {dustpan.name}."
        if not garbage_can.getProperty("isContainer") or type(garbage_can) == Agent:
            return f"You can't dump to {garbage_can.name}"

        if not garbage_can.getProperty("isOpen"):
            return f"The {self.name} is closed."

        while len(dustpan.contains) > 0:
            garbage_can.addObject(dustpan.contains[0])

        return f"You emptied the {dustpan.name} to the {garbage_can.name}."
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

        actions = {
            "look around": lambda: self.rootObject.makeDescriptionStr(),  # Look around the environment -- i.e. show the description of the world.
            "inventory": lambda: self.actionInventory(),  # Display the agent's inventory
            "take": lambda: self.actionTake(action[1]),  # Take an object from a container
            "put": lambda: self.actionPut(action[1], action[2]),  # Put an object in a container
            "open": lambda: self.actionOpen(action[1]),  # Open a container
            "close": lambda: self.actionClose(action[1]),  # Close a container
            "sweep": lambda: self.actionSweep(action[1], action[2], action[3]),  # Use a device on an object
            "dump": lambda: self.actionDump(action[1], action[2])
        }

        # Catch-all
        self.observationStr = actions.get(actionVerb, lambda: "ERROR: Unknown action.")()

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

        # Check the water temperature when the agent takes a bath
        allObjects = self.rootObject.getAllContainedObjectsRecursive()
        all_cleaned = True
        for obj in allObjects:
            if type(obj) == Garbage and type(obj.parentContainer) != GarbageCan:
                all_cleaned = False

        if all_cleaned:
            self.gameOver, self.gameWon, self.score = True, True, 1

if __name__ == "__main__":
    # Set random seed 0 and Create a new game
    main(SweepFloorGame(randomSeed=0))
