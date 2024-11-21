# refactored sunburn.py

# success
from GameBasic import *

# A Room class, derived from Container, represents rooms that can be either indoor or outdoor.
class Room(Container):
    def __init__(self, name, outdoor=False):
        GameObject.__init__(self, name)
        Container.__init__(self, name)
        self.properties["is_outdoor"] = outdoor
        self.properties["isMoveable"] = False
        self.connects = []  # Store connections to other rooms

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = f"You find yourself in a {self.name}.  In the {self.name}, you see: \n"
        for obj in self.contains:
            outStr += "\t" + obj.makeDescriptionStr() + "\n"

        return outStr

    def connectsTo(self, room):
        return any(r.name == room.name for r in self.connects)

# Items that can be used
class UsableItem(GameObject):
    def __init__(self, name):
        super().__init__(name)
        self.properties["usable"] = True

    def makeDescriptionStr(self, makeDetailed=False):
        return f"a bottle of {self.name}"

# The agent, derived from Container, includes additional properties for use_sunscreen and sunburn.
class Agents(Agent):
    def __init__(self):
        Agent.__init__(self)
        self.properties["use_sunscreen"] = False
        self.properties["sunburn"] = False

    def tick(self):
        if self.parentContainer.getProperty("is_outdoor") and not self.getProperty("use_sunscreen"):
            self.properties["sunburn"] = True

class SunburnWorld(World):
    def __init__(self):
        World.__init__(self, "world")

    def makeDescriptionStr(self, room, makeDetailed=False):
        outStr = f"You find yourself in a {room.name}.  In the {room.name}, you see: \n"
        for obj in room.contains:
            outStr += "\t" + obj.makeDescriptionStr() + "\n"
        # describe room connection information
        outStr += "You also see:\n"
        for connected_room in room.connects:
            outStr += f"\t a way to the {connected_room.name}\n"

        return outStr

class SunburnGame(TextGame):
    def __init__(self, randomSeed):
        # Random number generator, initialized with a seed passed as an argument
        self.random = random.Random(randomSeed)
        # The agent/player
        self.agent = Agents()
        # Game Object Tree
        self.rootObject = self.initializeWorld()
        # Game score
        self.score = 0
        self.numSteps = 0
        # Game over flag
        self.gameOver = False
        self.gameWon = False
        # Last game observation
        self.observationStr = self.rootObject.makeDescriptionStr(self.agent.parentContainer)
        # Do calculate initial scoring
        self.calculateScore()

    def initializeWorld(self):
        world = SunburnWorld()

        house = Room("house")
        beach = Room("beach", outdoor=True)
        world.addObject(house)
        world.addObject(beach)
        house.connects.append(beach)
        beach.connects.append(house)

        house.addObject(self.agent)
        sunscreen = UsableItem("sunscreen")
        house.addObject(sunscreen)
        box = Container("box")
        house.addObject(box)
        for distractor in ["detergent", "water"]:
            house.addObject(UsableItem(distractor))

        beach.addObject(GameObject("ball"))
        beach.addObject(GameObject("chair"))

        return world

    def getTaskDescription(self):
        return "It is a summer noon. The sky is clear. Your task is to take a ball from the beach \
and put it in the box in the house. Protect yourself from sunburn!"

    def generatePossibleActions(self):
        # Get a list of all game objects that could serve as arguments to actions
        allObjects = self.makeNameToObjectDict()

        # Make a dictionary whose keys are possible action strings, and whose values are lists that contain the arguments.
        self.possibleActions = {}

        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction("take " + objReferent, ["take", obj])
                self.addAction("take " + objReferent + " from " + obj.parentContainer.getReferents()[0], ["take", obj])
                self.addAction("use " + objReferent, ["use", obj])
                self.addAction("move to " + objReferent, ["move", obj])

            for objReferent1, objs1 in allObjects.items():
                for objReferent2, objs2 in allObjects.items():
                    for obj1 in objs1:
                        for obj2 in objs2:
                            if obj1 != obj2 and obj2.getProperty("isContainer"):
                                containerPrefix = obj2.properties["containerPrefix"]
                                self.addAction("put " + objReferent1 + " " + containerPrefix + " " + objReferent2,
                                                ["put", obj1, obj2])
        return self.possibleActions

    def actionUse(self, obj):
        if obj.getProperty("usable"):
            if obj.name == 'sunscreen':
                self.agent.properties["use_sunscreen"] = True
            return f"You use {obj.name} on yourself."
        else:
            return "You can't use that."

    def actionMove(self, room):
        if not isinstance(room, Room):
            return f"Cannot move to the {room.name}"
        elif not self.agent.parentContainer.connectsTo(room):
            return f"There is no way from {self.agent.parentContainer.name} to {room.name}."
        else:
            current_location = self.agent.parentContainer.name
            self.agent.removeSelfFromContainer()
            room.addObject(self.agent)
            return f"You move from {current_location} to {room.name}."

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
            self.observationStr = self.rootObject.makeDescriptionStr(self.agent.parentContainer)
        elif (actionVerb == "inventory"):
            # Display the agent's inventory
            self.observationStr = self.actionInventory()
        elif (actionVerb == "take"):
            # Take an object from a container
            thingToTake = action[1]
            self.observationStr = self.actionTake(thingToTake)
        elif (actionVerb == "put"):
            # Put an object in a container
            thingToMove = action[1]
            newContainer = action[2]
            self.observationStr = self.actionPut(thingToMove, newContainer)
        elif (actionVerb == "use"):
            # Use an item on the agent
            item = action[1]
            self.observationStr = self.actionUse(item)
        elif (actionVerb == "move"):
            # move to a new location
            target_location = action[1]
            self.observationStr = self.actionMove(target_location)
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
        if self.agent.properties["sunburn"]:
            self.score = 0
            self.gameOver = True
            self.gameWon = False
        else:
            allObjects = self.rootObject.getAllContainedObjectsRecursive()
            for obj in allObjects:
                if obj.name == "box" and any(item.name == 'ball' for item in obj.contains):
                    self.score = 1
                    self.gameOver = True
                    self.gameWon = True

if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser(description="Execute a game command.")
    parser.add_argument("commands", help="The command to execute in the game")
    args = parser.parse_args()

    print("Command received")
    # Random seed
    randomSeed = 0
    # Create a new game
    game = SunburnGame(randomSeed=randomSeed)
    main(game, args.commands)