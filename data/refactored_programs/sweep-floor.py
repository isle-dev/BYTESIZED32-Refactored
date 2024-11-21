# Refactor sweep-floor.py
# Success Haonan Wang and Ziang Xiao(Nov 2024)

from data.library.GameBasic import *

# Tool class representing various tools
class Tool(GameObject):
    def __init__(self, name):
        GameObject.__init__(self, name)

    def makeDescriptionStr(self, makeDetailed=False):
        return f"a(n) {self.name}"

# Garbage class representing garbage items which are immovable by default
class Garbage(GameObject):
    def __init__(self, name):
        GameObject.__init__(self, name)
        self.properties["isMoveable"] = False

    def makeDescriptionStr(self, makeDetailed=False):
        if self.parentContainer.name == "room":
            return f"{self.name} on the ground"
        return self.name

# GarbageCan class representing the garbage can, a container that is openable
class GarbageCan(Container):
    def __init__(self, name):
        GameObject.__init__(self, name)
        Container.__init__(self, name)
        self.properties["isMoveable"] = False
        self.properties["isOpenable"] = True
        self.properties["isOpen"] = False

# Room world setup
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

        world.addObject(self.agent)
        world.addObject(Tool("broom"))
        world.addObject(Container("dustpan"))
        world.addObject(GarbageCan("garbage can"))

        possible_garbage = ["broken glass", "waste paper", "dust", "dog hair", "watermelon rind"]
        self.random.shuffle(possible_garbage)

        for garbage_name in possible_garbage[:self.random.randint(2, 5)]:
            world.addObject(Garbage(garbage_name))

        world.addObject(Tool("mop"))
        return world

    def getTaskDescription(self):
        return 'Your task is to clean the garbage on the ground to the garbage can.'

    def generatePossibleActions(self):
        # Get a list of all game objects that could serve as arguments to actions
        allObjects = self.makeNameToObjectDict()

        # Make a dictionary whose keys are possible action strings, and whose values are lists that contain the arguments.
        self.possibleActions = {}

        # Zero-argument actions
        for action in [("look around", "look around"), ("look", "look around"), ("inventory", "inventory")]:
            self.addAction(action[0], [action[1]])

        # Actions with one object argument
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction("take " + objReferent, ["take", obj])
                self.addAction("take " + objReferent + " from " + obj.parentContainer.getReferents()[0],
                               ["take", obj])
                self.addAction("open " + objReferent, ["open", obj])
                self.addAction("close " + objReferent, ["close", obj])

        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for objReferent3, objs3 in allObjects.items():
                    for obj1 in objs1:
                        for obj2 in objs2:
                            for obj3 in objs3:
                                if obj1 != obj2 and obj2 != obj3 and obj3 != obj1:
                                    self.addAction(f"sweep {objReferent1} to {objReferent2} with {objReferent3}" , ["sweep", obj1, obj2, obj3])

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
            "look around": lambda: self.rootObject.makeDescriptionStr(),
            "inventory": lambda: self.actionInventory(),
            "take": lambda: self.actionTake(action[1]),
            "put": lambda: self.actionPut(action[1], action[2]),
            "open": lambda: self.actionOpen(action[1]),
            "close": lambda: self.actionClose(action[1]),
            "sweep": lambda: self.actionSweep(action[1], action[2], action[3]),
            "dump": lambda: self.actionDump(action[1], action[2])
        }

        # Execute the corresponding action based on the action verb
        self.observationStr = actions.get(actionVerb, lambda: "ERROR: Unknown action.")()

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
        if all(type(obj) == Garbage and obj.parentContainer == GarbageCan for obj in allObjects):
            self.gameOver = True
            self.gameWon = True
            self.score = 1

if __name__ == "__main__":
    randomSeed = 0
    game = SweepFloorGame(randomSeed=randomSeed)
    main(game)