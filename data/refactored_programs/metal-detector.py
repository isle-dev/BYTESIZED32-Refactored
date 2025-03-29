# refactored metal-detector.py
# Process
# Success Haonan (2025.2)

# Task Description: Create a micro-simulation that models how to use a metal detector to find a buried metal item on a beach.
# Environment: world
# Task-critical Objects: Room, Item, Shovel, MetalDetector
# High-level object classes: Container (Room)
# Critical properties: connects (Room), buried (Room), isMetal (Item), durability (Shovel)
# Actions: look, inventory, take/put objects, move, detect with detector, dig with shovel
# Distractor Items: Item
# Distractor Actions: None
# High-level solution procedure: take shovel, take metal detector, explore each place of the map and detects each place with the metal detector, if the detector pings, dig with shovel, take the metal case

from data.library.GameBasic import *


# A room
class Room(Container):
    def __init__(self, name):
        GameObject.__init__(self, name)
        Container.__init__(self, name)
        self.properties["isMoveable"] = False
        self.connects = {"north": None, "east": None, "south": None,
                         "west": None}  # other rooms that this room connects to
        self.buried = []  # objects buried in this room

    # bury an object in this "room"
    def bury(self, obj):
        super().addObject(obj)
        self.buried.append(obj)

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = f"You find yourself on a {self.name}. On the {self.name}, you see: \n"
        for obj in self.contains:
            if obj not in self.buried:
                outStr += "\t" + obj.makeDescriptionStr() + "\n"
        return outStr

    # connect to another room
    def connect(self, room, direction):
        self.connects[direction] = room
        couter_direction = {"north": "south", "east": "west", "south": "north", "west": "east"}[direction]
        room.connects[couter_direction] = self

# An item
class Item(GameObject):
    def __init__(self, name, isMetal=False):
        GameObject.__init__(self, name)
        self.properties["isMetal"] = isMetal


# A shovel
class Shovel(GameObject):
    def __init__(self, name, durability=1):
        GameObject.__init__(self, name)
        self.properties["durability"] = durability  # number of times the shovel can dig before broken

    def makeDescriptionStr(self, makeDetailed=False):
        return f"a {'broken ' if self.properties['durability'] == 0 else ''}{self.name}"


# A metal detector
class MetalDetector(GameObject):
    def __init__(self, name):
        GameObject.__init__(self, name)

    def detect(self, room):
        found_metal = False
        for obj in room.buried:
            if obj.getProperty("isMetal"):
                found_metal = True
                break
        return f"The {self.name} pings!" if found_metal else f"Nothing happens."

    def makeDescriptionStr(self, makeDetailed=False):
        return f"a {self.name}"

# The world is the root object of the game object tree.
class BeachWorld(World):
    def __init__(self):
        World.__init__(self, "beach")

    # Describe the a room
    def makeDescriptionStr(self, room, makeDetailed=False):
        outStr = room.makeDescriptionStr()
        # describe room connection information
        outStr += "You also see:\n"
        for direction in room.connects:
            if room.connects[direction] is not None:
                outStr += f"\t a way to {direction}\n"

        return outStr

class MetalDetectorGame(TextGame):
    def __init__(self, randomSeed):
        # Random number generator, initialized with a seed passed as an argument
        self.random = random.Random(randomSeed)
        # The agent/player
        self.agent = Agent("Agent")
        # Game Object Tree
        self.rootObject = self.initializeWorld()
        # Game score
        self.score = 0
        self.numSteps = 0
        # Game over flag
        self.gameOver = False
        self.gameWon = False
        # Last game observation
        self.observationStr = self.rootObject.makeDescriptionStr(self.current_room)
        # Do calculate initial scoring
        self.calculateScore()


    # Create/initialize the world/environment for this game
    def initializeWorld(self):
        world = BeachWorld()

        # Build a 3*3 beach map
        beach_map = [[Room("beach") for _ in range(3)] for _ in range(3)]

        # Connect the rooms
        for i in range(3):
            for j in range(3):
                if i + 1 < 3:
                    beach_map[i][j].connect(beach_map[i + 1][j], "south")
                if j + 1 < 3:
                    beach_map[i][j].connect(beach_map[i][j + 1], "east")
                world.addObject(beach_map[i][j])

        # Randomly select agent's initial position and where items are buried
        positions = self.random.choices(range(9), k=5)

        # Add agent
        agent_init_position = divmod(positions[0], 3)
        beach_map[agent_init_position[0]][agent_init_position[1]].addObject(self.agent)
        self.current_room = beach_map[agent_init_position[0]][agent_init_position[1]]

        # add the target
        metal_case = Item("metal case", isMetal=True)
        beach_map[positions[1] // 3][positions[1] % 3].bury(metal_case)

        # add distractors
        possible_items = ["rubber", "plastic bag", "glass", "wooden bowl", "china bowl"]
        self.random.shuffle(possible_items)
        for i in range(3):
            beach_map[positions[i + 2] // 3][positions[i + 2] % 3].bury(Item(possible_items[i]))

        # add a metal detector
        metal_detector = MetalDetector("metal detector")
        beach_map[agent_init_position[0]][agent_init_position[1]].addObject(metal_detector)

        # add a shovel
        shovel = Shovel("shovel")
        beach_map[agent_init_position[0]][agent_init_position[1]].addObject(shovel)

        return world

    # Get the task description for this game
    def getTaskDescription(self):
        return "Your task is to find the buried metal case on the beach. You win the game by putting the metal case in your inventory."

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
        # (1-arg) Take, Detect, Dig
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction("take " + objReferent, ["take", obj])
                self.addAction("detect with " + objReferent, ["detect", obj])
                self.addAction("dig with " + objReferent, ["dig", obj])

        # (1-arg) Move
        for direction, room in self.current_room.connects.items():
            if room is not None:
                self.addAction("move " + direction, ["move", direction])

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

    #
    #   Interpret actions
    #

    def actionDetect(self, metal_detector):
        # check type of the metal_detector
        if not isinstance(metal_detector, MetalDetector):
            return f"You can't detect with the {metal_detector.name}."

        # The agent should take the metal detector first
        if metal_detector.parentContainer != self.agent:
            return f"You should take the {metal_detector.name} first."

        return metal_detector.detect(self.current_room)

    def actionDig(self, shovel):
        # check shovel type
        if not isinstance(shovel, Shovel):
            return f"You can't dig with the {shovel.name}."
        # check if the agent has the shovel in inventory
        if shovel.parentContainer != self.agent:
            return f"You should take the {shovel.name} first."
        # check if the shovel has non-zero durability
        if shovel.properties["durability"] == 0:
            return f"You can't dig with {shovel.name} because it is broken."

        # dig
        self.current_room.buried = []
        shovel.properties["durability"] -= 1
        return f"You dig with {shovel.name}."

    def actionMove(self, direction):
        room = self.agent.parentContainer.connects[direction]
        self.agent.removeSelfFromContainer()
        room.addObject(self.agent)
        self.current_room = room
        return f"You move {direction}."

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
            "look around": lambda: self.rootObject.makeDescriptionStr(self.agent.parentContainer),  # Look around the environment -- i.e. show the description of the world.
            "inventory": lambda: self.actionInventory(),  # Display the agent's inventory
            "take": lambda: self.actionTake(action[1]),  # Take an object from a container
            "put": lambda: self.actionPut(action[1], action[2]),  # Put an object in a container
            "move": lambda: self.actionMove(action[1]),  # move to a new location
            "detect": lambda: self.actionDetect(action[1]),  # detect whether there are metal items buried in the room
            "dig": lambda: self.actionDig(action[1])  # dig with a shovel
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

    # Calculate the game score
    def calculateScore(self):
        allObjects = self.rootObject.getAllContainedObjectsRecursive()
        for obj in allObjects:
            if obj.name == "metal case" and obj.parentContainer == self.agent:
                self.score, self.gameOver, self.gameWon= 1, True, True

if __name__ == "__main__":
    # Set random seed 1 and Create a new game
    main(MetalDetectorGame(randomSeed=0))
