# refactored sunburn.py
# Process and problem of code
# Success Haonan(2025.2)

# Task Description: Create a micro-simulation that requires a user to put on sunscreen before going outdoor in a shiny summer noon.
# Environment: world
# Task-critical Objects: Room, Items
# High-level object classes: Container (Room)
# Critical properties: is_outdoor (Room), useable (Items),  use_sunscreen (Agent),  sunburn(Agent)
# Actions: look, inventory, take/put objects, move to a room, use X
# Distractor Items: Items, GameObject
# Distractor Actions: None
# High-level solution procedure: use the sunscreen, go to beach, take the ball, go to the house, put the ball into the box

from data.library.GameBasic import *

# A Room
class Room(Container):
    def __init__(self, name, outdoor=False):
        GameObject.__init__(self, name)
        Container.__init__(self, name)
        self.properties["is_outdoor"] = outdoor
        self.properties["isMoveable"] = False
        self.connects = []  # other rooms that this room connects to

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
        GameObject.__init__(self, name)
        self.properties["usable"] = True

    def makeDescriptionStr(self, makeDetailed=False):
        return f"a bottle of {self.name}"

class Box(Container):
    def __init__(self, name):
        Container.__init__(self, name)

    def makeDescriptionStr(self, makeDetailed=False):
        return "a " + self.name


# The agent (just a placeholder for a container for the inventory)
class Agents(Agent):
    def __init__(self, name):
        Agent.__init__(self, name)
        self.properties["use_sunscreen"] = False
        self.properties["sunburn"] = False

    def tick(self):
        if self.parentContainer.getProperty("is_outdoor") and not self.getProperty("use_sunscreen"):
            self.properties["sunburn"] = True


# The world is the root object of the game object tree.
class SunburnWorld(World):
    def __init__(self):
        World.__init__(self, "world")

    # Describe the a room
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
        self.agent = Agents("agent")
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

        # Add two "rooms": a house and a beach
        house = Room("house")
        beach = Room("beach", outdoor=True)
        world.addObject(house)
        world.addObject(beach)
        # Connects two rooms
        house.connects.append(beach)
        beach.connects.append(house)

        # Add objects into the house
        # Add the agent
        house.addObject(self.agent)
        # Add the sunscreen
        sunscreen = UsableItem("sunscreen")
        house.addObject(sunscreen)
        # Add an answer box
        box = Box("box")
        house.addObject(box)
        # Add some distractors
        for distractor in ["detergent", "water"]:
            house.addObject(UsableItem(distractor))

        # Add objects to the beach
        # Add a ball
        beach.addObject(GameObject("ball"))
        beach.addObject(GameObject("chair"))

        return world

    # Get the task description for this game
    def getTaskDescription(self):
        return "It is a summer noon. The sky is clear. Your task is to take a ball from the beach \
and put it in the box in the house. Protect yourself from sunburn!"

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
        # (1-arg) Take, Use, Move
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction("take " + objReferent, ["take", obj])
                self.addAction("take " + objReferent + " from " + obj.parentContainer.getReferents()[0], ["take", obj])
                self.addAction("use " + objReferent, ["use", obj])
                self.addAction("move to " + objReferent, ["move", obj])

        # Actions with two object arguments
        # (2-arg) Put
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if obj1 != obj2 and obj2.getProperty("isContainer"):
                            containerPrefix = obj2.properties["containerPrefix"]
                            self.addAction("put " + objReferent1 + " " + containerPrefix + " " + objReferent2,
                                            ["put", obj1, obj2])
        return self.possibleActions

    ## Use items to the agent
    def actionUse(self, obj):
        # Check if the object is a device
        if obj.getProperty("usable"):
            if obj.name == 'sunscreen':
                self.agent.properties["use_sunscreen"] = True
            return f"You use {obj.name} on yourself."
        else:
            return "You can't use that."

    def actionMove(self, room):
        # Check if the target is a room
        if not isinstance(room, Room):
            return f"Cannot move to the {room.name}"
        # Check if two rooms are connected
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

        # Mapping action verbs to corresponding functions
        action_map = {
            "look around": lambda: self.rootObject.makeDescriptionStr(self.agent.parentContainer),
            # Look around the environment
            "inventory": self.actionInventory,  # Display the agent's inventory
            "take": lambda: self.actionTake(action[1]),  # Take an object from a container
            "put": lambda: self.actionPut(action[1], action[2]),  # Put an object in a container
            "use": lambda: self.actionUse(action[1]),  # Use an item on the agent
            "move": lambda: self.actionMove(action[1]),  # Move to a new location
        }

        #Catch all
        self.observationStr = action_map.get(actionVerb, lambda: "ERROR: Unknown action.")()

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
        # Lose if the agent gets sunburn
        if self.agent.properties["sunburn"]:
            self.score, self.gameOver, self.gameWon = 0, True, False
        else:
            allObjects = self.rootObject.getAllContainedObjectsRecursive()
            for obj in allObjects:
                if obj.name == "box" and any(item.name == 'ball' for item in obj.contains):
                    self.score, self.gameOver, self.gameWon = 1, True, True

if __name__ == "__main__":
    # Set random seed 0 and Create a new game
    main(SunburnGame(randomSeed=0))